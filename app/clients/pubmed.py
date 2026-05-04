import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel
from typing import Optional
import xml.etree.ElementTree as ET
from app.config import settings

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedArticle(BaseModel):
    pmid: str
    title: str
    abstract: str
    authors: list[str]
    journal: str
    year: Optional[str] = None
    doi: Optional[str] = None


class PubMedClient:
    def __init__(self):
        self.api_key = settings.pubmed_api_key
        self.email = settings.pubmed_email
        self.client = httpx.AsyncClient(timeout=30.0)

    def _params(self, **kwargs) -> dict:
        params = {"tool": "clinical-research-agent", **kwargs}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def search(self, query: str, max_results: int = 10) -> list[str]:
        """Return list of PMIDs matching query."""
        resp = await self.client.get(
            f"{BASE_URL}/esearch.fcgi",
            params=self._params(
                db="pubmed", term=query, retmax=max_results, retmode="json"
            ),
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def fetch(self, pmids: list[str]) -> list[PubMedArticle]:
        """Fetch full article details for given PMIDs."""
        if not pmids:
            return []
        resp = await self.client.get(
            f"{BASE_URL}/efetch.fcgi",
            params=self._params(
                db="pubmed", id=",".join(pmids), retmode="xml"
            ),
        )
        resp.raise_for_status()
        return self._parse_articles(resp.text)

    def _parse_articles(self, xml_text: str) -> list[PubMedArticle]:
        root = ET.fromstring(xml_text)
        articles = []
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID", default="")
            title = art.findtext(".//ArticleTitle", default="").strip()
            abstract_parts = [
                (e.text or "") for e in art.findall(".//Abstract/AbstractText")
            ]
            abstract = " ".join(abstract_parts).strip()
            authors = []
            for a in art.findall(".//Author"):
                last = a.findtext("LastName", "")
                first = a.findtext("ForeName", "")
                if last:
                    authors.append(f"{first} {last}".strip())
            journal = art.findtext(".//Journal/Title", default="")
            year = art.findtext(".//PubDate/Year")
            doi = None
            for id_node in art.findall(".//ArticleId"):
                if id_node.get("IdType") == "doi":
                    doi = id_node.text
            articles.append(PubMedArticle(
                pmid=pmid, title=title, abstract=abstract,
                authors=authors, journal=journal, year=year, doi=doi,
            ))
        return articles

    async def search_and_fetch(self, query: str, max_results: int = 10) -> list[PubMedArticle]:
        pmids = await self.search(query, max_results)
        return await self.fetch(pmids)

    async def close(self):
        await self.client.aclose()

