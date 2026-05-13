import { useEffect, useState } from "react";
import { PipelineComplete } from "./PipelineComplete";
import type { Agent, ResearchResult } from "./types";

type SectionId = "summary" | "findings" | "pico" | "limitations" | "sources";

type SectionDef = {
  id: SectionId;
  label: string;
  count?: number;
};

type Props = {
  agents: Agent[];
  totalMs: number;
  result: ResearchResult;
};

export function ResultsSidebar({ agents, totalMs, result }: Props) {
  const sections: SectionDef[] = [
    { id: "summary", label: "Summary" },
    {
      id: "findings",
      label: "Findings",
      count: result.report.key_findings.length,
    },
    { id: "pico", label: "PICO" },
    ...(result.report.limitations.length > 0
      ? [{ id: "limitations" as const, label: "Limitations" }]
      : []),
    { id: "sources", label: "Sources", count: result.report.citations.length },
  ];

  const activeId = useActiveSection(sections.map((s) => s.id));

  return (
    <aside className="space-y-6 lg:sticky lg:top-6 lg:self-start">
      <PipelineComplete
        agents={agents}
        totalMs={totalMs}
        factcheck={result.factcheck}
      />

      <nav>
        <div className="mb-3 text-[11px] font-medium uppercase tracking-wider text-neutral-500">
          On this page
        </div>
        <ul className="space-y-1">
          {sections.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                className={`flex items-center justify-between rounded-md px-3 py-1.5 text-sm transition ${
                  activeId === s.id
                    ? "bg-neutral-900 text-neutral-100"
                    : "text-neutral-500 hover:bg-neutral-900/50 hover:text-neutral-300"
                }`}
              >
                <span>{s.label}</span>
                {s.count !== undefined && (
                  <span className="font-mono text-xs text-neutral-600">
                    {s.count}
                  </span>
                )}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

/**
 * Watches the page and returns whichever section is currently in view.
 * Uses IntersectionObserver — modern, performant, no scroll-event spam.
 */
function useActiveSection(ids: readonly SectionId[]): SectionId | null {
  const [active, setActive] = useState<SectionId | null>(null);

  useEffect(() => {
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);

    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // Pick the topmost intersecting entry
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visible[0]) {
          setActive(visible[0].target.id as SectionId);
        }
      },
      {
        // A section becomes "active" when its top is in the upper third of the viewport
        rootMargin: "-10% 0px -60% 0px",
        threshold: 0,
      },
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [ids]);

  return active;
}
