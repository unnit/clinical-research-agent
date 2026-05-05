import pytest
from app.agents.pico import decompose


@pytest.mark.asyncio
async def test_pico_decompose():
    pico = await decompose(
        "Are SGLT2 inhibitors effective for heart failure with preserved ejection fraction?"
    )
    assert pico.population
    assert pico.intervention
    assert pico.outcome
    assert len(pico.search_terms) >= 3

    print(f"\nPopulation: {pico.population}")
    print(f"Intervention: {pico.intervention}")
    print(f"Comparison: {pico.comparison}")
    print(f"Outcome: {pico.outcome}")
    print(f"Search terms: {pico.search_terms}")
    print(f"Study types: {pico.study_types}")
