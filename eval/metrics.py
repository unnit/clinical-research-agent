from pydantic import BaseModel

from app.agents.factcheck import FactCheckResult
from app.agents.synthesis import EvidenceReport
from app.clients.clinicaltrials import ClinicalTrial
from app.clients.pubmed import PubMedArticle


class CaseScore(BaseModel):
    case_id: str
    completed: bool
    citation_validity: float  # 0-1: valid_citations / total_citations
    source_recall: float  # 0-1: expected sources found in retrieval
    source_recall_in_report: float  # 0-1: expected sources cited in final report
    error: str = ""


def score_case(
    case_id: str,
    expected_sources: list[str],
    articles: list[PubMedArticle],
    trials: list[ClinicalTrial],
    report: EvidenceReport,
    factcheck: FactCheckResult,
) -> CaseScore:
    # Citation validity
    total_citations = len(report.citations)
    valid = len(factcheck.valid_citations)
    citation_validity = valid / total_citations if total_citations else 0.0

    # Source recall in retrieval (did we even find the landmark studies?)
    retrieved_ids = {a.pmid for a in articles} | {t.nct_id for t in trials}
    found_in_retrieval = sum(1 for s in expected_sources if s in retrieved_ids)
    source_recall = found_in_retrieval / len(expected_sources) if expected_sources else 0.0

    # Source recall in final report (did synthesis cite them?)
    cited_ids = {c.id.replace("PMID:", "").strip() for c in factcheck.valid_citations}
    found_in_report = sum(1 for s in expected_sources if s in cited_ids)
    source_recall_in_report = found_in_report / len(expected_sources) if expected_sources else 0.0

    return CaseScore(
        case_id=case_id,
        completed=True,
        citation_validity=citation_validity,
        source_recall=source_recall,
        source_recall_in_report=source_recall_in_report,
    )

