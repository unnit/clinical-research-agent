from pydantic import BaseModel, Field
from app.llm import structured


class PICO(BaseModel):
    population: str = Field(..., description="Patient group or condition")
    intervention: str = Field(..., description="Treatment, drug, or exposure")
    comparison: str = Field("", description="Alternative or control (may be empty)")
    outcome: str = Field(..., description="Clinical outcome of interest")
    search_terms: list[str] = Field(
        ..., description="3-5 optimized search query strings for medical databases"
    )
    study_types: list[str] = Field(
        default_factory=list,
        description="Preferred study types, e.g. 'randomized controlled trial', 'meta-analysis'",
    )


SYSTEM = """You are a clinical research librarian. Decompose the user's question into PICO components and generate optimized search queries.

Rules for search_terms:
- Use plain natural-language phrases (2-6 words each), NOT database-specific syntax
- Do NOT use MeSH brackets like [Mesh], field tags like [tiab], boolean operators (AND/OR), or quotes
- Do NOT use parentheses or special characters
- Each term should be a simple keyword phrase that works in any search engine
- Provide 3-5 varied terms covering different angles (drug class, specific drug, condition, outcome)

Good examples: "SGLT2 inhibitors heart failure", "dapagliflozin HFpEF", "empagliflozin preserved ejection fraction"
Bad examples: "Heart Failure, Diastolic"[Mesh] AND SGLT2, (dapagliflozin OR empagliflozin)[tiab]"""

async def decompose(question: str) -> PICO:
    return await structured(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
        schema=PICO,
    )
