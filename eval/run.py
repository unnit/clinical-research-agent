"""Run the eval harness. Usage: python -m eval.run"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.graph import graph
from app.tracing import get_client, trace_run
from eval.dataset import DATASET
from eval.metrics import CaseScore, score_case


async def run_one(case) -> CaseScore:
    print(f"\n→ {case.id}: {case.question[:80]}")
    try:
        async with trace_run(
            f"eval:{case.id}",
            {"question": case.question, "expected": case.expected_sources},
        ) as trace:
            result = await graph.ainvoke({
                "question": case.question,
                "max_per_source": 10,
                "trace_id": trace.id if trace else "",
            })

            score = score_case(
                case_id=case.id,
                expected_sources=case.expected_sources,
                articles=result.get("articles", []),
                trials=result.get("trials", []),
                report=result["report"],
                factcheck=result["factcheck"],
            )

            # Push scores to Langfuse
            client = get_client()
            if client and trace:
                for metric, value in [
                    ("citation_validity", score.citation_validity),
                    ("source_recall", score.source_recall),
                    ("source_recall_in_report", score.source_recall_in_report),
                ]:
                    try:
                        client.score(
                            trace_id=trace.id,
                            name=metric,
                            value=value,
                        )
                    except Exception as e:
                        print(f"  warn: score upload failed for {metric}: {e}")

            print(
                f"  ✓ validity={score.citation_validity:.2f} "
                f"recall={score.source_recall:.2f} "
                f"recall_in_report={score.source_recall_in_report:.2f}"
            )
            return score
    except Exception as e:
        print(f"  ✗ error: {e}")
        return CaseScore(
            case_id=case.id,
            completed=False,
            citation_validity=0.0,
            source_recall=0.0,
            source_recall_in_report=0.0,
            error=str(e),
        )


def summarize(scores: list[CaseScore]) -> dict:
    completed = [s for s in scores if s.completed]
    n = len(scores)
    n_completed = len(completed)
    return {
        "total": n,
        "completed": n_completed,
        "completion_rate": n_completed / n if n else 0.0,
        "avg_citation_validity": (
            sum(s.citation_validity for s in completed) / n_completed
            if n_completed else 0.0
        ),
        "avg_source_recall": (
            sum(s.source_recall for s in completed) / n_completed
            if n_completed else 0.0
        ),
        "avg_source_recall_in_report": (
            sum(s.source_recall_in_report for s in completed) / n_completed
            if n_completed else 0.0
        ),
    }


async def main():
    print(f"Running eval on {len(DATASET)} cases...")
    scores = []
    for case in DATASET:
        scores.append(await run_one(case))
        # Be polite to PubMed; pause between calls
        await asyncio.sleep(8)

    summary = summarize(scores)

    print("\n" + "=" * 60)
    print("EVAL SUMMARY")
    print("=" * 60)
    print(f"Cases:                {summary['total']}")
    print(f"Completion rate:      {summary['completion_rate']:.1%}")
    print(f"Avg citation validity: {summary['avg_citation_validity']:.2%}")
    print(f"Avg source recall:    {summary['avg_source_recall']:.2%}")
    print(f"Avg recall in report: {summary['avg_source_recall_in_report']:.2%}")

    # Save results to disk
    out_dir = Path("eval/results")
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"eval_{timestamp}.json"
    out_file.write_text(json.dumps({
        "summary": summary,
        "cases": [s.model_dump() for s in scores],
    }, indent=2))
    print(f"\nResults saved to: {out_file}")


if __name__ == "__main__":
    asyncio.run(main())

