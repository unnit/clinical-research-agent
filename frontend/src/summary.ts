export function summarizeNodeEnd(
  node: string,
  detail: Record<string, unknown>,
): string {
  switch (node) {
    case "decompose": {
      const n = detail.n_search_terms as number;
      return `${n} search terms generated`;
    }
    case "cache_lookup": {
      const hits = detail.cache_hits as number;
      return hits > 0 ? `${hits} cached articles` : "no cache hits";
    }
    case "search": {
      const total = detail.total_articles as number;
      const trials = detail.trials as number;
      const cached = detail.from_cache as number;
      return `${total} articles (${cached} cached), ${trials} trials`;
    }
    case "screen": {
      const scored = detail.scored as number;
      const high = detail.high_relevance as number;
      return `${scored} scored, ${high} high relevance`;
    }
    case "synthesize": {
      const findings = detail.key_findings_count as number;
      const citations = detail.citations_count as number;
      return `${findings} findings, ${citations} citations`;
    }
    case "factcheck": {
      const valid = detail.valid_citations as number;
      const invalid = detail.invalid_citations as number;
      return invalid > 0
        ? `${valid} valid, ${invalid} invalid`
        : `${valid} citations verified`;
    }
    default:
      return "";
  }
}
