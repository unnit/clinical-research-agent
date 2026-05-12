import { CitationText } from "./CitationText";

export function FindingsList({ findings }: { findings: string[] }) {
  if (findings.length === 0) return null;

  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900/50 p-6">
      <h2 className="mb-4 text-xl font-semibold">Key Findings</h2>
      <ul className="space-y-3">
        {findings.map((finding, i) => (
          <li key={i} className="flex gap-3 text-neutral-200">
            <span className="mt-0.5 text-neutral-600">{i + 1}.</span>
            <div className="flex-1 leading-relaxed">
              <CitationText text={finding} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
