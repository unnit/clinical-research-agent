"""Standalone MCP server exposing clinical research tools."""
import asyncio
from mcp.server.fastmcp import FastMCP

from app.clients.pubmed import PubMedClient
from app.clients.clinicaltrials import ClinicalTrialsClient
from app.clients.openfda import OpenFDAClient

mcp = FastMCP(
    "clinical-research",
    icons=[
        {
            "src": "data:image/png;base64,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",
            "mimeType": "image/png",
            "sizes": ["128x128"],
        }
    ]
)


@mcp.tool()
async def pubmed_search(query: str, max_results: int = 10) -> list[dict]:
    """Search PubMed for biomedical literature.

    Args:
        query: Plain-language search query (e.g., "SGLT2 inhibitors heart failure").
            Do not use MeSH brackets or boolean syntax.
        max_results: Number of articles to return (1-20).

    Returns:
        List of articles with pmid, title, abstract, authors, journal, year, doi.
    """
    max_results = min(max(max_results, 1), 20)
    client = PubMedClient()
    try:
        articles = await client.search_and_fetch(query, max_results=max_results)
        return [a.model_dump() for a in articles]
    finally:
        await client.close()


@mcp.tool()
async def trial_lookup(query: str, max_results: int = 10) -> list[dict]:
    """Search ClinicalTrials.gov for clinical trials.

    Args:
        query: Plain-language search query.
        max_results: Number of trials to return (1-20).

    Returns:
        List of trials with nct_id, title, status, phase, conditions,
        interventions, summary, enrollment, dates, url.
    """
    max_results = min(max(max_results, 1), 20)
    client = ClinicalTrialsClient()
    try:
        trials = await client.search(query, max_results=max_results)
        return [t.model_dump() for t in trials]
    finally:
        await client.close()


@mcp.tool()
async def drug_label_lookup(drug_name: str) -> list[dict]:
    """Look up FDA-approved drug label information from openFDA.

    Args:
        drug_name: Generic or brand name (e.g., "dapagliflozin", "Farxiga").

    Returns:
        List of label entries with brand_name, generic_name, indications,
        warnings, adverse_reactions, dosage.
    """
    client = OpenFDAClient()
    try:
        labels = await client.lookup(drug_name)
        return [l.model_dump() for l in labels]
    finally:
        await client.close()


if __name__ == "__main__":
    mcp.run()
