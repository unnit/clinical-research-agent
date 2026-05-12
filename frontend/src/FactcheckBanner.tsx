import type { ResearchResult } from "./types";

export function FactcheckBanner({
  factcheck,
}: {
  factcheck: ResearchResult["factcheck"];
}) {
  const validCount = factcheck.valid_citations.length;
  const invalidCount = factcheck.invalid_citations.length;
  const unsupportedCount = factcheck.unsupported_findings.length;

  if (factcheck.verified) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-emerald-900 bg-emerald-950/40 px-4 py-3 text-emerald-300">
        <span className="text-xl">✓</span>
        <div className="text-sm">
          <span className="font-medium">
            All {validCount} citations verified
          </span>
          <span className="ml-2 text-emerald-400/70">
            against retrieved sources
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-900 bg-amber-950/40 px-4 py-3 text-amber-200">
      <span className="text-xl">⚠</span>
      <div className="text-sm">
        <div className="font-medium">Fact-check found issues</div>
        <ul className="mt-1 list-inside list-disc text-amber-300/80">
          {invalidCount > 0 && (
            <li>
              {invalidCount} citation{invalidCount === 1 ? "" : "s"} not in
              retrieved sources
            </li>
          )}
          {unsupportedCount > 0 && (
            <li>
              {unsupportedCount} finding{unsupportedCount === 1 ? "" : "s"}{" "}
              without supporting citations
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
