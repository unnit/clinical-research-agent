import type { Agent } from "./types";

export const INITIAL_AGENTS: Agent[] = [
  {
    id: "decompose",
    label: "Decompose (PICO)",
    emoji: "🧠",
    status: "pending",
  },
  { id: "cache_lookup", label: "Cache lookup", emoji: "🔍", status: "pending" },
  {
    id: "search",
    label: "Search PubMed + Trials",
    emoji: "📚",
    status: "pending",
  },
  { id: "screen", label: "Screen relevance", emoji: "⚖️", status: "pending" },
  {
    id: "synthesize",
    label: "Synthesize report",
    emoji: "✍️",
    status: "pending",
  },
  {
    id: "factcheck",
    label: "Fact-check citations",
    emoji: "✅",
    status: "pending",
  },
];
