import type { ResearchResult } from "./types";

export function CitationsList({
  citations,
}: {
  citations: ResearchResult["report"]["citations"];
}) {
  if (citations.length === 0) return null;

  return (
    <details className="rounded-lg border border-neutral-800 bg-neutral-900/50">
      <summary className="cursor-pointer list-none px-4 py-3 font-medium hover:bg-neutral-900">
        <span>Sources</span>
        <span className="ml-2 text-sm text-neutral-500">
          ({citations.length})
        </span>
      </summary>
      <ul className="divide-y divide-neutral-800 border-t border-neutral-800">
        {citations.map((c) => (
          <li key={`${c.source}-${c.id}`} className="px-4 py-3">
            <a
              href={c.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block hover:bg-neutral-900"
            >
              <div className="flex items-baseline gap-2">
                <span
                  className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                    c.source === "pubmed"
                      ? "bg-blue-950 text-blue-300"
                      : "bg-purple-950 text-purple-300"
                  }`}
                >
                  {c.source === "pubmed" ? `PMID:${c.id}` : c.id}
                </span>
                <span className="text-xs text-neutral-500">
                  {c.source === "pubmed" ? "PubMed" : "ClinicalTrials.gov"}
                </span>
              </div>
              <div className="mt-1 text-sm text-neutral-200">{c.title}</div>
            </a>
          </li>
        ))}
      </ul>
    </details>
  );
}
