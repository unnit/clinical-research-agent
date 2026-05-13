import { Loader2 } from "lucide-react";
import type { Agent } from "./types";

export function PipelineRunning({ agents }: { agents: Agent[] }) {
  // Find the index of the currently running agent
  const runningIdx = agents.findIndex((a) => a.status === "running");
  const done = agents.filter((a) => a.status === "done" || a.status === "error");
  const active = runningIdx >= 0 ? agents[runningIdx] : null;

  return (
    <section className="mb-8 space-y-2">
      {/* Compact done rows */}
      {done.map((a) => (
        <div
          key={a.id}
          className="flex items-center gap-3 rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-4 py-2.5 text-sm"
        >
          <span className="text-base opacity-70">{a.emoji}</span>
          <span className="flex-1 text-neutral-400">{a.label}</span>
          {a.summary && (
            <span className="hidden text-xs text-neutral-500 sm:inline">
              {a.summary}
            </span>
          )}
          <span className="font-mono text-xs tabular-nums text-neutral-600">
            {((a.durationMs ?? 0) / 1000).toFixed(1)}s
          </span>
          <span className="text-emerald-500">✓</span>
        </div>
      ))}

      {/* Active row — expanded with live indicator */}
      {active && (
        <div className="rounded-xl border border-violet-900/50 bg-violet-950/20 px-4 py-3.5 shadow-lg shadow-violet-900/10">
          <div className="flex items-center gap-3">
            <span className="text-xl">{active.emoji}</span>
            <div className="flex-1">
              <div className="font-medium text-neutral-100">{active.label}</div>
              <div className="mt-0.5 text-xs text-violet-300/70">
                in progress…
              </div>
            </div>
            <Loader2
              size={18}
              className="animate-spin text-violet-400"
              strokeWidth={2.5}
            />
          </div>
        </div>
      )}
    </section>
  );
}

