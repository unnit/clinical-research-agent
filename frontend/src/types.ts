// Mirrors the Python ProgressEvent schema in app/streaming.py
export type ProgressEvent = {
  type: "node_start" | "node_end" | "node_error" | "complete" | "error";
  node: string;
  elapsed_ms: number;
  detail: Record<string, unknown>;
};

// One row in the agent progress list
export type AgentStatus = "pending" | "running" | "done" | "error";

export type Agent = {
  id: string; // matches `node` field from events
  label: string;
  emoji: string;
  status: AgentStatus;
  durationMs?: number;
  summary?: string; // short human-readable status, e.g. "6 cached articles"
};

// Final payload from the "complete" event
export type ResearchResult = {
  pico: {
    population: string;
    intervention: string;
    comparison: string;
    outcome: string;
    search_terms: string[];
    study_types: string[];
  };
  report: {
    question: string;
    executive_summary: string;
    key_findings: string[];
    evidence_quality: string;
    limitations: string[];
    citations: Array<{
      id: string;
      source: "pubmed" | "clinicaltrials";
      title: string;
      url: string;
    }>;
  };
  factcheck: {
    verified: boolean;
    valid_citations: Array<{ id: string; title: string; url: string }>;
    invalid_citations: Array<{ id: string; title: string; url: string }>;
    unsupported_findings: string[];
  };
  counts: {
    articles_found: number;
    trials_found: number;
  };
};
