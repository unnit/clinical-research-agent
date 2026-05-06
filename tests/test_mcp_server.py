import pytest
from mcp_server import pubmed_search, drug_label_lookup, trial_lookup


@pytest.mark.asyncio
async def test_mcp_tools_callable():
    articles = await pubmed_search("metformin diabetes", max_results=2)
    assert len(articles) > 0
    assert "title" in articles[0]

    trials = await trial_lookup("metformin", max_results=2)
    assert len(trials) > 0

    labels = await drug_label_lookup("metformin")
    assert len(labels) > 0

    print(f"\n✓ pubmed_search: {len(articles)} articles")
    print(f"✓ trial_lookup: {len(trials)} trials")
    print(f"✓ drug_label_lookup: {len(labels)} labels")
