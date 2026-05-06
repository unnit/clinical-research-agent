"""Standalone MCP server exposing clinical research tools."""
import asyncio
from mcp.server.fastmcp import FastMCP

from app.clients.pubmed import PubMedClient
from app.clients.clinicaltrials import ClinicalTrialsClient
from app.clients.openfda import OpenFDAClient

mcp = FastMCP("clinical-research")


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
