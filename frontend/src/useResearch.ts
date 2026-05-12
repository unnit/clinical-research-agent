import { useCallback, useState } from "react";
import type { Agent, ProgressEvent, ResearchResult } from "./types";
import { INITIAL_AGENTS } from "./agents";
import { summarizeNodeEnd } from "./summary";

type State = {
  agents: Agent[];
  result: ResearchResult | null;
  error: string | null;
  isRunning: boolean;
  elapsedMs: number;
};

const initialState: State = {
  agents: INITIAL_AGENTS,
  result: null,
  error: null,
  isRunning: false,
  elapsedMs: 0,
};

export function useResearch() {
  const [state, setState] = useState<State>(initialState);

  const reset = useCallback(() => setState(initialState), []);

  const run = useCallback(async (question: string) => {
    setState({
      agents: INITIAL_AGENTS.map((a) => ({ ...a, status: "pending" })),
      result: null,
      error: null,
      isRunning: true,
      elapsedMs: 0,
    });

    try {
      const resp = await fetch("/api/research/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, max_per_source: 5 }),
      });

      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE frames are separated by blank lines
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";

        for (const frame of frames) {
          const line = frame.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          const json = line.slice(6).trim();
          if (!json) continue;

          let ev: ProgressEvent;
          try {
            ev = JSON.parse(json);
          } catch {
            continue;
          }

          setState((prev) => applyEvent(prev, ev));
        }
      }

      setState((prev) => ({ ...prev, isRunning: false }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isRunning: false,
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, []);

  return { ...state, run, reset };
}

function applyEvent(state: State, ev: ProgressEvent): State {
  const next = { ...state, elapsedMs: ev.elapsed_ms };

  if (ev.type === "node_start") {
    next.agents = state.agents.map((a) =>
      a.id === ev.node ? { ...a, status: "running" } : a,
    );
  } else if (ev.type === "node_end") {
    const duration = (ev.detail.duration_ms as number) ?? 0;
    next.agents = state.agents.map((a) =>
      a.id === ev.node
        ? {
            ...a,
            status: "done",
            durationMs: duration,
            summary: summarizeNodeEnd(ev.node, ev.detail),
          }
        : a,
    );
  } else if (ev.type === "node_error") {
    next.agents = state.agents.map((a) =>
      a.id === ev.node ? { ...a, status: "error" } : a,
    );
    next.error = (ev.detail.error as string) ?? "Node failed";
  } else if (ev.type === "complete") {
    next.result = ev.detail as unknown as ResearchResult;
  } else if (ev.type === "error") {
    next.error = (ev.detail.error as string) ?? "Pipeline failed";
  }

  return next;
}
