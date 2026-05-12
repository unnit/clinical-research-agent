import pytest

from app.clients.pubmed import PubMedClient


@pytest.mark.asyncio
async def test_pubmed_search_and_fetch():
    client = PubMedClient()
    try:
        articles = await client.search_and_fetch("SGLT2 inhibitors heart failure", max_results=3)
        assert len(articles) > 0
        assert articles[0].title
        assert articles[0].pmid
        print(f"\nFound {len(articles)} articles")
        print(f"First: {articles[0].title[:80]}")
    finally:
        await client.close()
