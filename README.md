# Clinical Research Agent

A multi-agent system that answers clinical questions by searching PubMed and ClinicalTrials.gov, then produces evidence-graded research summaries.

🚧 **Work in progress** — building in public.

## Stack
- Python 3.11+, FastAPI, LangGraph
- Gemini 2.5 Flash via LiteLLM
- Custom MCP server
- Qdrant for semantic caching
- Langfuse for tracing & evaluation

## Status
- [x] Data source clients (PubMed, ClinicalTrials.gov)
- [x] FastAPI scaffold
- [ ] Multi-agent orchestration
- [ ] MCP server
- [ ] Evaluation harness
- [ ] Containerization & CI

