import type { ResearchResult } from "./types";

const FIELD_LABELS: Record<
  keyof Pick<
    ResearchResult["pico"],
    "population" | "intervention" | "comparison" | "outcome"
  >,
  string
> = {
  population: "Population",
  intervention: "Intervention",
  comparison: "Comparison",
  outcome: "Outcome",
};

export function PicoCard({ pico }: { pico: ResearchResult["pico"] }) {
  return (
    <details className="group rounded-lg border border-neutral-800 bg-neutral-900/50">
      <summary className="cursor-pointer list-none px-4 py-3 font-medium hover:bg-neutral-900">
        <span className="text-neutral-400">PICO Decomposition</span>
        <span className="ml-2 text-xs text-neutral-600 group-open:hidden">
          click to expand
        </span>
      </summary>
      <div className="border-t border-neutral-800 px-4 py-3">
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {(Object.keys(FIELD_LABELS) as Array<keyof typeof FIELD_LABELS>).map(
            (field) => (
              <div key={field}>
                <dt className="text-xs uppercase tracking-wider text-neutral-500">
                  {FIELD_LABELS[field]}
                </dt>
                <dd className="mt-1 text-sm text-neutral-200">
                  {pico[field] || <span className="text-neutral-600">—</span>}
                </dd>
              </div>
            ),
          )}
        </dl>
        {pico.search_terms.length > 0 && (
          <div className="mt-4 border-t border-neutral-800 pt-3">
            <div className="text-xs uppercase tracking-wider text-neutral-500">
              Search Terms
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {pico.search_terms.map((term) => (
                <span
                  key={term}
                  className="rounded-md bg-neutral-800 px-2 py-1 text-xs text-neutral-300"
                >
                  {term}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </details>
  );
}
