import pytest
from app.clients.clinicaltrials import ClinicalTrialsClient


@pytest.mark.asyncio
async def test_clinicaltrials_search():
    client = ClinicalTrialsClient()
    try:
        trials = await client.search("SGLT2 heart failure", max_results=3)
        assert len(trials) > 0
        assert trials[0].nct_id
        print(f"\nFound {len(trials)} trials")
        print(f"First: {trials[0].title[:80]}")
        print(f"Status: {trials[0].status}")
    finally:
        await client.close()

