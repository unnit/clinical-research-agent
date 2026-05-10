import pytest

from app.agents.screening import screen
from app.agents.synthesis import synthesize
from app.clients.clinicaltrials import ClinicalTrialsClient
from app.clients.pubmed import PubMedClient


@pytest.mark.asyncio
async def test_full_pipeline_minus_orchestration():
    question = "Are SGLT2 inhibitors effective for heart failure with preserved ejection fraction?"
    pm = PubMedClient()
    ct = ClinicalTrialsClient()
    try:
        articles = await pm.search_and_fetch("SGLT2 HFpEF", max_results=5)
        trials = await ct.search("SGLT2 heart failure preserved ejection fraction", max_results=5)

        scores = await screen(question, articles, trials)
        print(f"\nRelevance scores: {scores}")

        # Keep top items only (score >= 6)
        top_articles = [a for a in articles if scores.get(a.pmid, 0) >= 6]
        top_trials = [t for t in trials if scores.get(t.nct_id, 0) >= 6]

        report = await synthesize(question, top_articles, top_trials)
        print(f"\n=== {report.question} ===")
        print(f"\nSummary: {report.executive_summary}")
        print(f"\nQuality: {report.evidence_quality}")
        print("\nFindings:")
        for f in report.key_findings:
            print(f"  - {f}")
        print(f"\nCitations: {len(report.citations)}")

        assert report.executive_summary
        assert len(report.key_findings) >= 1
        assert len(report.citations) >= 1
    finally:
        await pm.close()
        await ct.close()
