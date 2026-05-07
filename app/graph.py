from typing import TypedDict
from langgraph.graph import StateGraph, START, END
import structlog

from app.clients.pubmed import PubMedClient, PubMedArticle
from app.clients.clinicaltrials import ClinicalTrialsClient, ClinicalTrial
from app.agents.pico import decompose, PICO
from app.agents.screening import screen
from app.agents.synthesis import synthesize, EvidenceReport
from app.agents.factcheck import factcheck, FactCheckResult
from app.vectorstore import VectorStore

log = structlog.get_logger()


class ResearchState(TypedDict, total=False):
    question: str
    max_per_source: int
    trace_id: str
    pico: PICO
    cached_articles: list[PubMedArticle]
    articles: list[PubMedArticle]
    trials: list[ClinicalTrial]
    relevance: dict[str, int]
    report: EvidenceReport
    factcheck: FactCheckResult


async def node_decompose(state: ResearchState) -> ResearchState:
    log.info("node_decompose", question=state["question"])
    pico = await decompose(state["question"])
    return {"pico": pico}


async def node_cache_lookup(state: ResearchState) -> ResearchState:
    """Check vector cache for relevant articles before hitting APIs."""
    pico = state["pico"]
    vs = VectorStore()
    cached_articles: dict[str, PubMedArticle] = {}
    try:
        for term in pico.search_terms[:3]:
            try:
                hits = await vs.search_fresh(term, limit=10, min_score=0.70)
                for h in hits:
                    pmid = h.get("pmid")
                    if pmid and pmid not in cached_articles:
                        cached_articles[pmid] = PubMedArticle(
                            pmid=pmid,
                            title=h.get("title", ""),
                            abstract=h.get("abstract", ""),
                            authors=[],
                            journal=h.get("journal", ""),
                            year=h.get("year"),
                        )
            except Exception as e:
                log.warning("cache_lookup_failed", term=term, error=str(e))

        log.info("cache_hits", count=len(cached_articles))
        return {"cached_articles": list(cached_articles.values())}
    finally:
        await vs.close()


async def node_search(state: ResearchState) -> ResearchState:
    pico = state["pico"]
    max_results = state.get("max_per_source", 8)
    cached = state.get("cached_articles", [])

    # Start from cache
    articles_by_id: dict[str, PubMedArticle] = {a.pmid: a for a in cached}
    trials_by_id: dict[str, ClinicalTrial] = {}

    log.info(
        "node_search_start",
        cached_articles=len(articles_by_id),
        terms=pico.search_terms,
    )

    # If cache already gave us enough, skip PubMed entirely
    cache_threshold = max_results * 2  # heuristic: enough cached articles
    skip_pubmed = len(articles_by_id) >= cache_threshold

    pm = PubMedClient()
    ct = ClinicalTrialsClient()
    vs = VectorStore()
    new_articles: list[PubMedArticle] = []

    try:
        for term in pico.search_terms[:3]:
            if not skip_pubmed:
                try:
                    for a in await pm.search_and_fetch(term, max_results=max_results):
                        if a.pmid not in articles_by_id:
                            articles_by_id[a.pmid] = a
                            new_articles.append(a)
                except Exception as e:
                    log.warning("pubmed_term_failed", term=term, error=str(e))

            # Trials always fetched fresh — they have their own status that changes
            try:
                for t in await ct.search(term, max_results=max_results):
                    trials_by_id[t.nct_id] = t
            except Exception as e:
                log.warning("trials_term_failed", term=term, error=str(e))

        # Only index newly fetched articles (cached ones are already indexed)
        if new_articles:
            try:
                await vs.upsert_articles(new_articles)
            except Exception as e:
                log.warning("vector_upsert_failed", error=str(e))

        log.info(
            "node_search_done",
            total_articles=len(articles_by_id),
            new_fetched=len(new_articles),
            from_cache=len(cached),
            trials=len(trials_by_id),
            skip_pubmed=skip_pubmed,
        )
        return {
            "articles": list(articles_by_id.values()),
            "trials": list(trials_by_id.values()),
        }
    finally:
        await pm.close()
        await ct.close()
        await vs.close()


async def node_screen(state: ResearchState) -> ResearchState:
    log.info(
        "node_screen",
        n_articles=len(state.get("articles", [])),
        n_trials=len(state.get("trials", [])),
    )
    scores = await screen(
        state["question"],
        state.get("articles", []),
        state.get("trials", []),
    )
    return {"relevance": scores}


async def node_synthesize(state: ResearchState) -> ResearchState:
    scores = state.get("relevance", {})
    threshold = 6

    top_articles = [
        a for a in state.get("articles", []) if scores.get(a.pmid, 0) >= threshold
    ]
    top_trials = [
        t for t in state.get("trials", []) if scores.get(t.nct_id, 0) >= threshold
    ]

    # Fallback: if too aggressive, take top-N by score
    if len(top_articles) + len(top_trials) < 3:
        all_items = [
            ("article", a, scores.get(a.pmid, 0)) for a in state.get("articles", [])
        ] + [
            ("trial", t, scores.get(t.nct_id, 0)) for t in state.get("trials", [])
        ]
        all_items.sort(key=lambda x: x[2], reverse=True)
        top_articles = [x[1] for x in all_items if x[0] == "article"][:5]
        top_trials = [x[1] for x in all_items if x[0] == "trial"][:5]

    log.info(
        "node_synthesize",
        kept_articles=len(top_articles),
        kept_trials=len(top_trials),
    )
    report = await synthesize(state["question"], top_articles, top_trials)
    return {"report": report}

async def node_factcheck(state: ResearchState) -> ResearchState:
    result = factcheck(
        state["report"],
        state.get("articles", []),
        state.get("trials", []),
    )
    return {"factcheck": result}


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("decompose", node_decompose)
    g.add_node("cache_lookup", node_cache_lookup)
    g.add_node("search", node_search)
    g.add_node("screen", node_screen)
    g.add_node("synthesize", node_synthesize)
    g.add_node("factcheck", node_factcheck)

    g.add_edge(START, "decompose")
    g.add_edge("decompose", "cache_lookup")
    g.add_edge("cache_lookup", "search")
    g.add_edge("search", "screen")
    g.add_edge("screen", "synthesize")
    g.add_edge("synthesize", "factcheck")
    g.add_edge("factcheck", END)

    return g.compile()


graph = build_graph()
