import hashlib
import time

import structlog
from google import genai
from google.genai import types
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.clients.pubmed import PubMedArticle
from app.config import settings

log = structlog.get_logger()

COLLECTION = "clinical_articles"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

_genai_client = genai.Client(api_key=settings.gemini_api_key)


class VectorStore:
    def __init__(self, url: str | None = None):
        self.client = AsyncQdrantClient(url=url or settings.qdrant_url)

    async def ensure_collection(self):
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION not in names:
            await self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
            )
            log.info("collection_created", name=COLLECTION)

    def _embed(self, text: str, task: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        resp = _genai_client.models.embed_content(
            model=EMBED_MODEL,
            contents=text[:8000],
            config=types.EmbedContentConfig(
                task_type=task,
                output_dimensionality=EMBED_DIM,
            ),
        )
        return resp.embeddings[0].values

    def _embed_query(self, text: str) -> list[float]:
        return self._embed(text, task="RETRIEVAL_QUERY")

    @staticmethod
    def _pmid_to_uuid(pmid: str) -> str:
        h = hashlib.md5(pmid.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    async def upsert_articles(self, articles: list[PubMedArticle]) -> int:
        if not articles:
            return 0
        await self.ensure_collection()
        points = []
        for a in articles:
            if not a.abstract:
                continue
            text = f"{a.title}\n\n{a.abstract}"
            vec = self._embed(text)
            points.append(PointStruct(
                id=self._pmid_to_uuid(a.pmid),
                vector=vec,
                payload={
                    "pmid": a.pmid,
                    "title": a.title,
                    "abstract": a.abstract,
                    "journal": a.journal,
                    "year": a.year,
                    "indexed_at": int(time.time()),
                },
            ))
        if points:
            await self.client.upsert(collection_name=COLLECTION, points=points)
        log.info("articles_upserted", count=len(points))
        return len(points)

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        await self.ensure_collection()
        vec = self._embed_query(query)
        results = await self.client.query_points(
            collection_name=COLLECTION,
            query=vec,
            limit=limit,
        )
        return [{**p.payload, "score": p.score} for p in results.points]

    async def close(self):
        try:
            await self.client.close()
        except Exception:
            pass

    async def search_fresh(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.65,
        max_age_days: int = 30,
    ) -> list[dict]:
        """Semantic search filtered by similarity threshold and freshness."""
        await self.ensure_collection()
        vec = self._embed_query(query)
        results = await self.client.query_points(
            collection_name=COLLECTION,
            query=vec,
            limit=limit,
        )
        cutoff = int(time.time()) - max_age_days * 86400
        fresh = [
            {**p.payload, "score": p.score}
            for p in results.points
            if p.score >= min_score
            and p.payload.get("indexed_at", 0) >= cutoff
        ]
        return fresh
