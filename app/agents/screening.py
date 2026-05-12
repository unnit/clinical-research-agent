from pydantic import BaseModel, Field, field_validator

from app.clients.clinicaltrials import ClinicalTrial
from app.clients.pubmed import PubMedArticle
from app.llm import structured


class ScreenedItem(BaseModel):
    id: str
    relevance: int = Field(..., ge=0, le=10)
    reason: str = Field(..., description="Brief justification, ideally under 200 chars")

    @field_validator("reason")
    @classmethod
    def truncate_reason(cls, v: str) -> str:
        return v[:300] if len(v) > 300 else v


class ScreeningResult(BaseModel):
    items: list[ScreenedItem]


SYSTEM = """You are a clinical evidence reviewer. Score each item's relevance to the research question on a 0-10 scale.

Scoring:
- 9-10: Directly answers the question (RCT, meta-analysis on exact topic)
- 6-8: Strongly relevant (related population, intervention, or outcome)
- 3-5: Tangentially related
- 0-2: Off-topic

Rules:
- Be strict — most items should score 5-7.
- Keep "reason" to one short sentence, under 30 words."""


def _format_articles(articles: list[PubMedArticle]) -> str:
    return "\n\n".join(
        f"ID: {a.pmid}\nTitle: {a.title}\nAbstract: {a.abstract[:500]}" for a in articles
    )


def _format_trials(trials: list[ClinicalTrial]) -> str:
    return "\n\n".join(
        f"ID: {t.nct_id}\nTitle: {t.title}\nStatus: {t.status}\nPhase: {t.phase}\nSummary: {t.summary[:400]}"
        for t in trials
    )


async def screen(
    question: str,
    articles: list[PubMedArticle],
    trials: list[ClinicalTrial],
) -> dict[str, int]:
    """Return dict of {id: relevance_score}."""
    if not articles and not trials:
        return {}

    content = (
        f"Research question: {question}\n\n"
        f"=== ARTICLES ===\n{_format_articles(articles)}\n\n"
        f"=== TRIALS ===\n{_format_trials(trials)}"
    )

    result = await structured(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": content},
        ],
        schema=ScreeningResult,
    )
    return {item.id: item.relevance for item in result.items}
