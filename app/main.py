from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import structlog
import logging

from app.config import settings
from app.graph import graph
from app.agents.synthesis import EvidenceReport
from app.agents.pico import PICO
from app.agents.factcheck import FactCheckResult
from app.vectorstore import VectorStore
from app.tracing import trace_run

logging.basicConfig(level=settings.log_level)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("app_started", model=settings.llm_model)
    yield
    log.info("app_stopped")


app = FastAPI(
    title="Clinical Research Agent",
    version="0.2.0",
    lifespan=lifespan,
)


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    max_per_source: int = Field(8, ge=3, le=20)


class ResearchResponse(BaseModel):
    pico: PICO
    report: EvidenceReport
    factcheck: FactCheckResult
    counts: dict


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}


@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest):
    async with trace_run("research", {"question": req.question}) as trace:
        try:
            result = await graph.ainvoke({
                "question": req.question,
                "max_per_source": req.max_per_source,
                "trace_id": trace.id if trace else "",
            })
        except Exception as e:
            log.error("research_failed", error=str(e))
            if trace:
                trace.update(output={"error": str(e)}, level="ERROR")
            raise HTTPException(status_code=500, detail=str(e))

        if trace:
            trace.update(output={
                "summary": result["report"].executive_summary,
                "evidence_quality": result["report"].evidence_quality,
                "valid_citations": len(result["factcheck"].valid_citations),
                "invalid_citations": len(result["factcheck"].invalid_citations),
            })

        return ResearchResponse(
            pico=result["pico"],
            report=result["report"],
            factcheck=result["factcheck"],
            counts={
                "articles_found": len(result.get("articles", [])),
                "trials_found": len(result.get("trials", [])),
                "items_synthesized": len(result["report"].citations),
                "valid_citations": len(result["factcheck"].valid_citations),
                "invalid_citations": len(result["factcheck"].invalid_citations),
            },
        )


@app.get("/library/search")
async def library_search(q: str, limit: int = 5):
    """Semantic search over previously-indexed articles."""
    vs = VectorStore()
    try:
        results = await vs.search(q, limit=limit)
        return {"query": q, "results": results}
    finally:
        await vs.close()


@app.get("/library/stats")
async def library_stats():
    """Cache health stats."""
    vs = VectorStore()
    try:
        await vs.ensure_collection()
        info = await vs.client.get_collection(collection_name="clinical_articles")
        return {
            "collection": "clinical_articles",
            "indexed_articles": info.points_count,
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance.value,
        }
    finally:
        await vs.close()
