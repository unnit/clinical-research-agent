import type { Agent } from "./types";

const statusIcon: Record<Agent["status"], string> = {
  pending: "○",
  running: "⠋",
  done: "✓",
  error: "✗",
};

const statusColor: Record<Agent["status"], string> = {
  pending: "text-neutral-500",
  running: "text-blue-400 animate-pulse",
  done: "text-emerald-400",
  error: "text-rose-400",
};

export function AgentRow({ agent }: { agent: Agent }) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-neutral-800 bg-neutral-900/50 px-4 py-3">
      <span className="text-xl">{agent.emoji}</span>
      <div className="flex-1">
        <div className="font-medium">{agent.label}</div>
        {agent.summary && (
          <div className="text-sm text-neutral-400">{agent.summary}</div>
        )}
      </div>
      <div
        className={`flex items-center gap-2 text-sm ${statusColor[agent.status]}`}
      >
        {agent.durationMs !== undefined && (
          <span className="tabular-nums text-neutral-500">
            {(agent.durationMs / 1000).toFixed(1)}s
          </span>
        )}
        <span className="text-lg">{statusIcon[agent.status]}</span>
      </div>
    </div>
  );
}
