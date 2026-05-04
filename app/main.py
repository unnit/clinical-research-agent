from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import structlog
import logging

from app.config import settings
from app.clients.pubmed import PubMedClient, PubMedArticle
from app.clients.clinicaltrials import ClinicalTrialsClient, ClinicalTrial

logging.basicConfig(level=settings.log_level)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pubmed = PubMedClient()
    app.state.trials = ClinicalTrialsClient()
    log.info("clients_initialized")
    yield
    await app.state.pubmed.close()
    await app.state.trials.close()
    log.info("clients_closed")


app = FastAPI(
    title="Clinical Research Agent",
    version="0.1.0",
    lifespan=lifespan,
)


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    max_results_per_source: int = Field(5, ge=1, le=20)


class ResearchResponse(BaseModel):
    question: str
    articles: list[PubMedArticle]
    trials: list[ClinicalTrial]
    counts: dict


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}


@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest):
    log.info("research_request", question=req.question)
    try:
        articles = await app.state.pubmed.search_and_fetch(
            req.question, max_results=req.max_results_per_source
        )
        trials = await app.state.trials.search(
            req.question, max_results=req.max_results_per_source
        )
    except Exception as e:
        log.error("research_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return ResearchResponse(
        question=req.question,
        articles=articles,
        trials=trials,
        counts={"articles": len(articles), "trials": len(trials)},
    )

