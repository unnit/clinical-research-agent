from typing import TypedDict
from langgraph.graph import StateGraph, START, END
import structlog

from app.clients.pubmed import PubMedClient, PubMedArticle
from app.clients.clinicaltrials import ClinicalTrialsClient, ClinicalTrial
from app.agents.pico import decompose, PICO
from app.agents.screening import screen
from app.agents.synthesis import synthesize, EvidenceReport

log = structlog.get_logger()


class ResearchState(TypedDict, total=False):
    question: str
    max_per_source: int
    pico: PICO
    articles: list[PubMedArticle]
    trials: list[ClinicalTrial]
    relevance: dict[str, int]
    report: EvidenceReport


async def node_decompose(state: ResearchState) -> ResearchState:
    log.info("node_decompose", question=state["question"])
    pico = await decompose(state["question"])
    return {"pico": pico}


async def node_search(state: ResearchState) -> ResearchState:
    pico = state["pico"]
    max_results = state.get("max_per_source", 8)
    log.info("node_search", terms=pico.search_terms)

    pm = PubMedClient()
    ct = ClinicalTrialsClient()
    articles_by_id: dict[str, PubMedArticle] = {}
    trials_by_id: dict[str, ClinicalTrial] = {}

    try:
        for term in pico.search_terms[:3]:
            try:
                for a in await pm.search_and_fetch(term, max_results=max_results):
                    articles_by_id[a.pmid] = a
            except Exception as e:
                log.warning("pubmed_term_failed", term=term, error=str(e))
            try:
                for t in await ct.search(term, max_results=max_results):
                    trials_by_id[t.nct_id] = t
            except Exception as e:
                log.warning("trials_term_failed", term=term, error=str(e))

        log.info(
            "search_complete",
            articles=len(articles_by_id),
            trials=len(trials_by_id),
        )
        return {
            "articles": list(articles_by_id.values()),
            "trials": list(trials_by_id.values()),
        }
    finally:
        await pm.close()
        await ct.close()


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


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("decompose", node_decompose)
    g.add_node("search", node_search)
    g.add_node("screen", node_screen)
    g.add_node("synthesize", node_synthesize)

    g.add_edge(START, "decompose")
    g.add_edge("decompose", "search")
    g.add_edge("search", "screen")
    g.add_edge("screen", "synthesize")
    g.add_edge("synthesize", END)

    return g.compile()


graph = build_graph()
