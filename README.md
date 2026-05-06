# Clinical Research Agent

A multi-agent system that answers clinical questions by searching PubMed, ClinicalTrials.gov, and FDA drug labels, then produces evidence-graded research summaries with verified citations.

🚧 **Work in progress** — building in public.

## Features

- **Multi-agent pipeline** — PICO decomposition → search → relevance screening → evidence synthesis → fact-checking
- **Semantic cache** — Qdrant vector store with freshness-aware retrieval; repeat queries skip external API calls
- **Custom MCP server** — exposes clinical search tools to any MCP client (Claude Desktop, Cursor, etc.)
- **Citation verification** — deterministic fact-checker catches hallucinated PMIDs and unsupported findings
- **Three data sources** — PubMed (E-utilities), ClinicalTrials.gov (API v2), openFDA drug labels

## Stack

- Python 3.11+, FastAPI, async throughout
- LangGraph for agent orchestration
- LiteLLM + Gemini 2.5 Flash
- Qdrant for vector storage and semantic search
- Gemini embeddings (`gemini-embedding-001`, 768-dim)
- MCP Python SDK (`mcp[cli]`)

## Architecture

```
User question
  ↓
[PICO Decomposer]    → structured Population/Intervention/Comparison/Outcome
  ↓
[Cache Lookup]       → Qdrant semantic search with similarity + freshness filters
  ↓
[Search]             → PubMed + ClinicalTrials.gov; skip-fetch if cache sufficient
  ↓
[Screening]          → relevance scoring 0-10
  ↓
[Synthesis]          → evidence summary with GRADE-lite quality rating
  ↓
[Fact-check]         → verifies every citation maps to a real retrieved source
  ↓
Structured Report
```

## Endpoints

- `POST /research` — full pipeline; returns PICO, evidence report, factcheck results
- `GET /library/search?q=...` — semantic search over indexed articles
- `GET /library/stats` — cache health stats
- `GET /health` — liveness check

## MCP Tools (standalone server)

- `pubmed_search(query, max_results)`
- `trial_lookup(query, max_results)`
- `drug_label_lookup(drug_name)`

## Status

- [x] Data source clients (PubMed, ClinicalTrials.gov, openFDA)
- [x] Multi-agent orchestration with LangGraph
- [x] Citation fact-checker
- [x] MCP server
- [x] Qdrant semantic cache with TTL and similarity thresholds
- [ ] Langfuse tracing & evaluation harness
- [ ] Containerization & CI/CD
- [ ] Deployment & demo

## Quick start

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GEMINI_API_KEY

# Start Qdrant
docker run -d --name qdrant -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# Run the API
python -m uvicorn app.main:app --reload

# Or run the MCP server standalone
python mcp_server.py
```