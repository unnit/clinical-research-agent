import { useState } from "react";
import { ChevronDown, Zap, CheckCircle2, AlertCircle } from "lucide-react";
import type { Agent, ResearchResult } from "./types";

type Props = {
  agents: Agent[];
  totalMs: number;
  factcheck: ResearchResult["factcheck"];
};

export function PipelineComplete({ agents, totalMs, factcheck }: Props) {
  const [expanded, setExpanded] = useState(false);
  const totalSec = (totalMs / 1000).toFixed(1);
  const verified = factcheck.verified;

  return (
    <section>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center gap-2 rounded-xl border border-neutral-800 bg-neutral-900/50 px-3 py-2.5 text-left transition hover:border-neutral-700 hover:bg-neutral-900"
        aria-expanded={expanded}
      >
        <Zap size={14} className="shrink-0 text-amber-400" />
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-neutral-400">Completed in</span>
            <span className="font-mono tabular-nums text-neutral-100">
              {totalSec}s
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <span className="text-neutral-500">{agents.length} agents</span>
            <span className="text-neutral-700">·</span>
            {verified ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <CheckCircle2 size={11} />
                verified
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-400">
                <AlertCircle size={11} />
                issues
              </span>
            )}
          </div>
        </div>
        <ChevronDown
          size={14}
          className={`shrink-0 text-neutral-500 transition-transform duration-200 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      <div
        className={`grid transition-all duration-300 ease-out ${
          expanded
            ? "mt-2 grid-rows-[1fr] opacity-100"
            : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-2">
            <ul className="divide-y divide-neutral-800/60">
              {agents.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center gap-2 px-2 py-2 text-xs"
                >
                  <span className="text-sm opacity-80">{a.emoji}</span>
                  <span className="min-w-0 flex-1 truncate text-neutral-200">
                    {a.label}
                  </span>
                  <span className="font-mono tabular-nums text-neutral-500">
                    {((a.durationMs ?? 0) / 1000).toFixed(1)}s
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
