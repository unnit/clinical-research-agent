from typing import Optional

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://api.fda.gov/drug/label.json"


class DrugLabel(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    indications: str = ""
    warnings: str = ""
    adverse_reactions: str = ""
    dosage: str = ""


class OpenFDAClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def lookup(self, drug_name: str, limit: int = 1) -> list[DrugLabel]:
        resp = await self.client.get(
            BASE_URL,
            params={
                "search": f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"',
                "limit": limit,
            },
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, data: dict) -> list[DrugLabel]:
        results = []
        for r in data.get("results", []):
            openfda = r.get("openfda", {})
            results.append(DrugLabel(
                brand_name=(openfda.get("brand_name") or [None])[0],
                generic_name=(openfda.get("generic_name") or [None])[0],
                indications=" ".join(r.get("indications_and_usage", []))[:1500],
                warnings=" ".join(r.get("warnings", []))[:1500],
                adverse_reactions=" ".join(r.get("adverse_reactions", []))[:1500],
                dosage=" ".join(r.get("dosage_and_administration", []))[:1500],
            ))
        return results

    async def close(self):
        await self.client.aclose()
