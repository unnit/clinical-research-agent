from typing import Literal

from pydantic import BaseModel, Field

from app.clients.clinicaltrials import ClinicalTrial
from app.clients.pubmed import PubMedArticle
from app.llm import structured


class Citation(BaseModel):
    id: str = Field(
        ..., description="Just the bare ID: '12345678' for PubMed or 'NCT01234567' for trials"
    )
    source: Literal["pubmed", "clinicaltrials"]
    title: str
    url: str


class EvidenceReport(BaseModel):
    question: str
    executive_summary: str = Field(..., description="2-3 sentence answer")
    key_findings: list[str] = Field(
        ..., description="3-6 bullet findings with citations like [PMID:12345]"
    )
    evidence_quality: str = Field(
        ..., description="High / Moderate / Low / Very Low with one-line justification"
    )
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation]


SYSTEM = """You are a clinical evidence synthesizer. Given screened literature, produce a structured evidence summary.

Citation rules (CRITICAL):
- Cite ONLY sources provided in the input. Do NOT invent PMIDs or NCT IDs.
- In findings, reference sources EXACTLY as [PMID:12345678] for articles or [NCT01234567] for trials.
- NEVER mix prefixes — [PMID:NCT...] is invalid. NCT IDs go alone in brackets.
- For each Citation object:
  - "id" must be the bare identifier (e.g., "12345678" or "NCT01234567"), not the title or journal
  - "source" must be exactly "pubmed" OR "clinicaltrials" — nothing else
  - "title" is the study title
  - "url" is the full URL

Content rules:
- Every key finding must reference at least one source
- Be precise about effect sizes, sample sizes, and confidence intervals when given
- Grade evidence using GRADE-lite: High / Moderate / Low / Very Low with one-line justification
- State limitations honestly (small samples, short follow-up, surrogate endpoints, etc.)
- Do NOT invent findings beyond what the sources support"""


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
