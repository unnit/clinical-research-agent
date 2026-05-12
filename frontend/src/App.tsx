import { useState, type SubmitEvent } from "react";
import { useResearch } from "./useResearch";
import { AgentRow } from "./AgentRow";
import { PicoCard } from "./PicoCard";
import { FindingsList } from "./FindingsList";
import { FactcheckBanner } from "./FactcheckBanner";
import { CitationsList } from "./CitationsList";

function App() {
  const [question, setQuestion] = useState("");
  const { agents, result, error, isRunning, elapsedMs, run } = useResearch();

  const handleSubmit = (e: SubmitEvent) => {
    e.preventDefault();
    if (!question.trim() || isRunning) return;
    run(question.trim());
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Clinical Research Agent
          </h1>
          <p className="mt-2 text-neutral-400">
            Multi-agent evidence synthesis from PubMed, ClinicalTrials.gov, and
            FDA.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Are SGLT2 inhibitors effective for HFpEF?"
              disabled={isRunning}
              className="flex-1 rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-3 outline-none placeholder:text-neutral-600 focus:border-neutral-600 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isRunning || !question.trim()}
              className="rounded-lg bg-blue-600 px-6 py-3 font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRunning ? "Running…" : "Run"}
            </button>
          </div>
        </form>

        {(isRunning || elapsedMs > 0) && (
          <section className="mb-8">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-400">
                Pipeline
              </h2>
              <span className="text-sm tabular-nums text-neutral-500">
                {(elapsedMs / 1000).toFixed(1)}s
              </span>
            </div>
            <div className="space-y-2">
              {agents.map((agent) => (
                <AgentRow key={agent.id} agent={agent} />
              ))}
            </div>
          </section>
        )}

        {error && (
          <div className="mb-8 rounded-lg border border-rose-900 bg-rose-950/50 px-4 py-3 text-rose-300">
            {error}
          </div>
        )}

        {result && (
          <section className="space-y-6">
            <PicoCard pico={result.pico} />

            <div className="rounded-lg border border-neutral-800 bg-neutral-900/50 p-6">
              <h2 className="mb-3 text-xl font-semibold">Executive Summary</h2>
              <p className="leading-relaxed text-neutral-200">
                {result.report.executive_summary}
              </p>
              <div className="mt-4 inline-flex items-center gap-2 rounded-md bg-neutral-800 px-3 py-1 text-xs">
                <span className="text-neutral-400">Evidence quality:</span>
                <span className="text-neutral-200">
                  {result.report.evidence_quality}
                </span>
              </div>
            </div>

            <FactcheckBanner factcheck={result.factcheck} />

            <FindingsList findings={result.report.key_findings} />

            {result.report.limitations.length > 0 && (
              <div className="rounded-lg border border-neutral-800 bg-neutral-900/50 p-6">
                <h2 className="mb-3 text-xl font-semibold">Limitations</h2>
                <ul className="list-inside list-disc space-y-1 text-neutral-300">
                  {result.report.limitations.map((lim, i) => (
                    <li key={i} className="leading-relaxed">
                      {lim}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <CitationsList citations={result.report.citations} />
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
