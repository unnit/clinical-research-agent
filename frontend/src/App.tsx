import { useState, useEffect, type SubmitEvent } from "react";
import { ArrowUp } from "lucide-react";
import { useResearch } from "./useResearch";
import { PipelineRunning } from "./PipelineRunning";
import { PicoCard } from "./PicoCard";
import { ResultsSidebar } from "./ResultsSidebar";
import { FindingsList } from "./FindingsList";
import { FactcheckBanner } from "./FactcheckBanner";
import { CitationsList } from "./CitationsList";

const EXAMPLE_QUESTIONS = [
  "Are SGLT2 inhibitors effective for HFpEF?",
  "What is the evidence for finerenone in chronic kidney disease?",
  "How does tirzepatide compare to semaglutide for type 2 diabetes?",
  "Do PCSK9 inhibitors reduce cardiovascular events on statin therapy?",
  "Is aspirin recommended for primary prevention in older adults?",
];

function useRotatingPlaceholder(isActive: boolean) {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (!isActive) return;
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % EXAMPLE_QUESTIONS.length);
    }, 3500);
    return () => clearInterval(id);
  }, [isActive]);
  return EXAMPLE_QUESTIONS[index];
}

function App() {
  const [question, setQuestion] = useState("");
  const { agents, result, error, isRunning, elapsedMs, run } = useResearch();
  const placeholder = useRotatingPlaceholder(!question && !isRunning);

  const handleSubmit = (e: SubmitEvent) => {
    e.preventDefault();
    if (!question.trim() || isRunning) return;
    run(question.trim());
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="mx-auto max-w-6xl px-3 py-12 sm:px-6">
        <header className="mb-8 flex items-start gap-4">
          <img
            src="/logo.svg"
            alt=""
            aria-hidden="true"
            className="h-12 w-12 shrink-0 text-neutral-300"
          />
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">
              Clinical Research Agent
            </h1>
            <p className="mt-2 text-neutral-400">
              Multi-agent evidence synthesis from PubMed, ClinicalTrials.gov,
              and FDA.
            </p>
          </div>
        </header>

        <form onSubmit={handleSubmit} className="mb-8">
          <div className="relative">
            {!question && !isRunning && (
              <div className="pointer-events-none absolute left-5 right-5 top-4 overflow-hidden">
                <span
                  key={placeholder}
                  className="block text-base text-neutral-600 animate-placeholder-slide"
                >
                  {placeholder}
                </span>
              </div>
            )}

            <textarea
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                // Auto-grow up to max-height
                e.target.style.height = "auto";
                e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e as unknown as SubmitEvent);
                }
              }}
              placeholder=""
              disabled={isRunning}
              rows={2}
              data-gramm="false"
              className="block w-full resize-none rounded-2xl border border-neutral-800 bg-neutral-900 px-5 py-4 pr-16 text-base leading-6 outline-none focus:border-neutral-600 disabled:opacity-50"
            />

            <button
              type="submit"
              disabled={isRunning || !question.trim()}
              aria-label="Submit question"
              className="absolute right-3 bottom-3 flex h-9 w-9 items-center justify-center rounded-full bg-violet-600 text-white shadow-lg shadow-violet-600/30 transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:bg-neutral-800 disabled:text-neutral-600 disabled:shadow-none"
            >
              <ArrowUp size={18} strokeWidth={2.5} />
            </button>
          </div>
          <p className="mt-2 ml-1 text-xs text-neutral-600">
            Press{" "}
            <kbd className="rounded bg-neutral-800 px-1.5 py-0.5 font-sans text-[10px]">
              Enter
            </kbd>{" "}
            to submit ·{" "}
            <kbd className="rounded bg-neutral-800 px-1.5 py-0.5 font-sans text-[10px]">
              Shift + Enter
            </kbd>{" "}
            for new line
          </p>
        </form>

        {isRunning && <PipelineRunning agents={agents} />}

        {error && (
          <div className="mb-8 rounded-lg border border-rose-900 bg-rose-950/50 px-4 py-3 text-rose-300">
            {error}
          </div>
        )}

        {result && (
          <div className="grid gap-8 lg:grid-cols-[1fr_260px]">
            <main className="space-y-6 min-w-0">
              <FactcheckBanner factcheck={result.factcheck} />

              <section
                id="summary"
                className="scroll-mt-6 rounded-lg border border-neutral-800 bg-neutral-900/50 p-6"
              >
                <h2 className="mb-3 text-xl font-semibold">
                  Executive Summary
                </h2>
                <p className="leading-relaxed text-neutral-200">
                  {result.report.executive_summary}
                </p>
                <div className="mt-4 inline-flex items-center gap-2 rounded-md bg-neutral-800 px-3 py-1 text-xs">
                  <span className="text-neutral-400">Evidence quality:</span>
                  <span className="text-neutral-200">
                    {result.report.evidence_quality}
                  </span>
                </div>
              </section>

              <section id="findings" className="scroll-mt-6">
                <FindingsList findings={result.report.key_findings} />
              </section>

              <section id="pico" className="scroll-mt-6">
                <PicoCard pico={result.pico} />
              </section>

              {result.report.limitations.length > 0 && (
                <section
                  id="limitations"
                  className="scroll-mt-6 rounded-lg border border-neutral-800 bg-neutral-900/50 p-6"
                >
                  <h2 className="mb-3 text-xl font-semibold">Limitations</h2>
                  <ul className="list-inside list-disc space-y-1 text-neutral-300">
                    {result.report.limitations.map((lim, i) => (
                      <li key={i} className="leading-relaxed">
                        {lim}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section id="sources" className="scroll-mt-6">
                <CitationsList citations={result.report.citations} />
              </section>
            </main>

            <ResultsSidebar
              agents={agents}
              totalMs={elapsedMs}
              result={result}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
