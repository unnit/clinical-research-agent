import asyncio
import json
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app.agents.factcheck import FactCheckResult
from app.agents.pico import PICO
from app.agents.synthesis import EvidenceReport
from app.config import settings
from app.graph import graph
from app.redaction import redact_payload
from app.streaming import ProgressQueue
from app.tracing import trace_run
from app.vectorstore import VectorStore

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


class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """Redact PII from JSON request bodies on routes that handle user input."""

    REDACT_PATHS = {"/research"}  # extend as you add user-facing endpoints

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in self.REDACT_PATHS:
            return await call_next(request)

        body = await request.body()
        if not body:
            return await call_next(request)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return await call_next(request)

        redacted_payload, counts = redact_payload(payload)
        if counts:
            log.info("pii_redacted", counts=counts, path=request.url.path)

        # Rebuild the request with the redacted body
        new_body = json.dumps(redacted_payload).encode()

        async def receive():
            return {"type": "http.request", "body": new_body, "more_body": False}

        request._receive = receive
        return await call_next(request)


app.add_middleware(PIIRedactionMiddleware)


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
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
            result = await graph.ainvoke(
                {
                    "question": req.question,
                    "max_per_source": req.max_per_source,
                    "trace_id": trace.id if trace else "",
                }
            )
        except Exception as e:
            log.error("research_failed", error=str(e))
            if trace:
                trace.update(output={"error": str(e)}, level="ERROR")
            raise HTTPException(status_code=500, detail=str(e)) from e

        if trace:
            trace.update(
                output={
                    "summary": result["report"].executive_summary,
                    "evidence_quality": result["report"].evidence_quality,
                    "valid_citations": len(result["factcheck"].valid_citations),
                    "invalid_citations": len(result["factcheck"].invalid_citations),
                }
            )

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


@app.post("/research/stream")
async def research_stream(req: ResearchRequest):
    pq = ProgressQueue()

    async def runner():
        try:
            async with trace_run("research_stream", {"question": req.question}) as trace:
                result = await graph.ainvoke(
                    {
                        "question": req.question,
                        "max_per_source": req.max_per_source,
                        "trace_id": trace.id if trace else "",
                        "progress": pq,
                    }
                )
                # Final event with full payload
                await pq.emit(
                    "complete",
                    pico=result["pico"].model_dump(),
                    report=result["report"].model_dump(),
                    factcheck=result["factcheck"].model_dump(),
                    counts={
                        "articles_found": len(result.get("articles", [])),
                        "trials_found": len(result.get("trials", [])),
                    },
                )
        except Exception as e:
            await pq.emit("error", error=str(e))
        finally:
            await pq.close()

    asyncio.create_task(runner())

    return StreamingResponse(
        pq.events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
