from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception_type
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2"


class ClinicalTrial(BaseModel):
    nct_id: str
    title: str
    status: str
    phase: Optional[str] = None
    conditions: list[str] = []
    interventions: list[str] = []
    summary: str = ""
    enrollment: Optional[int] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    url: str = ""


class ClinicalTrialsClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def search(self, query: str, max_results: int = 10) -> list[ClinicalTrial]:
        resp = await self.client.get(
            f"{BASE_URL}/studies",
            params={
                "query.term": query,
                "pageSize": max_results,
                "format": "json",
            },
        )
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, data: dict) -> list[ClinicalTrial]:
        trials = []
        for study in data.get("studies", []):
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            cond = proto.get("conditionsModule", {})
            arms = proto.get("armsInterventionsModule", {})
            desc = proto.get("descriptionModule", {})

            nct_id = ident.get("nctId", "")
            phases = design.get("phases", [])
            interventions = [
                i.get("name", "") for i in arms.get("interventions", [])
            ]

            trials.append(ClinicalTrial(
                nct_id=nct_id,
                title=ident.get("briefTitle", ""),
                status=status.get("overallStatus", ""),
                phase=", ".join(phases) if phases else None,
                conditions=cond.get("conditions", []),
                interventions=interventions,
                summary=desc.get("briefSummary", ""),
                enrollment=design.get("enrollmentInfo", {}).get("count"),
                start_date=status.get("startDateStruct", {}).get("date"),
                completion_date=status.get("completionDateStruct", {}).get("date"),
                url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
            ))
        return trials

    async def close(self):
        await self.client.aclose()

