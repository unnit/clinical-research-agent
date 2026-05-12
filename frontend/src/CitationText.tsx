import type { JSX } from "react";

// Matches [PMID:12345678] or [NCT01234567]
const REF_RE = /\[(PMID:\d+|NCT\d+)\]/g;

function refUrl(ref: string): string {
  if (ref.startsWith("PMID:")) {
    const pmid = ref.replace("PMID:", "");
    return `https://pubmed.ncbi.nlm.nih.gov/${pmid}`;
  }
  return `https://clinicaltrials.gov/study/${ref}`;
}

export function CitationText({ text }: { text: string }) {
  const parts: (string | JSX.Element)[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(REF_RE)) {
    const [full, ref] = match;
    const start = match.index ?? 0;
    if (start > lastIndex) parts.push(text.slice(lastIndex, start));
    parts.push(
      <a
        key={`${ref}-${start}`}
        href={refUrl(ref)}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded bg-blue-950 px-1.5 py-0.5 text-xs font-medium text-blue-300 hover:bg-blue-900"
      >
        {ref}
      </a>,
    );
    lastIndex = start + full.length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));

  return <span>{parts}</span>;
}
