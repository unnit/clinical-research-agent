from pydantic import BaseModel, Field
from app.llm import structured
from app.clients.pubmed import PubMedArticle
from app.clients.clinicaltrials import ClinicalTrial


class Citation(BaseModel):
    id: str
    source: str  # "pubmed" or "clinicaltrials"
    title: str
    url: str


class EvidenceReport(BaseModel):
    question: str
    executive_summary: str = Field(..., description="2-3 sentence answer")
    key_findings: list[str] = Field(..., description="3-6 bullet findings with citations like [PMID:12345]")
    evidence_quality: str = Field(..., description="High / Moderate / Low / Very Low with one-line justification")
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation]


SYSTEM = """You are a clinical evidence synthesizer. Given screened literature, produce a structured evidence summary.

Rules:
- Every key finding must reference a specific source like [PMID:12345678] or [NCT01234567]
- Be precise about effect sizes, sample sizes, and confidence intervals when available
- Grade evidence quality using GRADE-lite: High / Moderate / Low / Very Low
- State limitations honestly (small samples, short follow-up, etc.)
- Do NOT invent findings or citations not in the source material"""


def _format_sources(articles: list[PubMedArticle], trials: list[ClinicalTrial]) -> str:
    parts = []
    for a in articles:
        parts.append(
            f"[PMID:{a.pmid}] {a.title} ({a.journal}, {a.year or 'n.d.'})\n{a.abstract[:800]}"
        )
    for t in trials:
        parts.append(
            f"[{t.nct_id}] {t.title} | Status: {t.status} | Phase: {t.phase}\n{t.summary[:600]}"
        )
    return "\n\n---\n\n".join(parts)


async def synthesize(
    question: str,
    articles: list[PubMedArticle],
    trials: list[ClinicalTrial],
) -> EvidenceReport:
    sources = _format_sources(articles, trials)
    return await structured(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Question: {question}\n\nSources:\n{sources}",
            },
        ],
        schema=EvidenceReport,
        temperature=0.3,
    )
