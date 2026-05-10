import re

import structlog
from pydantic import BaseModel

from app.agents.synthesis import Citation, EvidenceReport
from app.clients.clinicaltrials import ClinicalTrial
from app.clients.pubmed import PubMedArticle

log = structlog.get_logger()


class FactCheckResult(BaseModel):
    verified: bool
    valid_citations: list[Citation]
    invalid_citations: list[Citation]
    unsupported_findings: list[str]


# Matches [PMID:12345678] or [NCT01234567]
CITATION_RE = re.compile(r"\[(PMID:\d+|NCT\d+)\]")


def factcheck(
    report: EvidenceReport,
    articles: list[PubMedArticle],
    trials: list[ClinicalTrial],
) -> FactCheckResult:
    """Deterministic verification — no LLM call needed."""
    valid_pmids = {a.pmid for a in articles}
    valid_ncts = {t.nct_id for t in trials}

    valid, invalid = [], []
    for c in report.citations:
        # Normalize: strip prefix if present
        cid = c.id.replace("PMID:", "").replace("pmid:", "").strip()
        if c.source == "pubmed" and cid in valid_pmids:
            valid.append(c)
        elif c.source == "clinicaltrials" and cid in valid_ncts:
            valid.append(c)
        else:
            invalid.append(c)

    # Check findings reference real sources
    unsupported = []
    for finding in report.key_findings:
        refs = CITATION_RE.findall(finding)
        if not refs:
            unsupported.append(finding)
            continue
        for ref in refs:
            if ref.startswith("PMID:"):
                if ref.replace("PMID:", "") not in valid_pmids:
                    unsupported.append(finding)
                    break
            elif ref.startswith("NCT"):
                if ref not in valid_ncts:
                    unsupported.append(finding)
                    break

    result = FactCheckResult(
        verified=len(invalid) == 0 and len(unsupported) == 0,
        valid_citations=valid,
        invalid_citations=invalid,
        unsupported_findings=unsupported,
    )
    log.info(
        "factcheck",
        verified=result.verified,
        valid=len(valid),
        invalid=len(invalid),
        unsupported=len(unsupported),
    )
    return result
