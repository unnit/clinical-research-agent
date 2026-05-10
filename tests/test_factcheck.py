from app.agents.factcheck import factcheck
from app.agents.synthesis import Citation, EvidenceReport
from app.clients.clinicaltrials import ClinicalTrial
from app.clients.pubmed import PubMedArticle


def _article(pmid: str) -> PubMedArticle:
    return PubMedArticle(
        pmid=pmid, title="t", abstract="a", authors=[], journal="j", year="2024"
    )


def _trial(nct: str) -> ClinicalTrial:
    return ClinicalTrial(nct_id=nct, title="t", status="COMPLETED")


def _report(citations, findings):
    return EvidenceReport(
        question="Q",
        executive_summary="s",
        key_findings=findings,
        evidence_quality="High: clear",
        citations=citations,
    )


def test_factcheck_all_valid():
    articles = [_article("12345"), _article("67890")]
    trials = [_trial("NCT01234567")]
    report = _report(
        citations=[
            Citation(id="12345", source="pubmed", title="t", url="u"),
            Citation(id="NCT01234567", source="clinicaltrials", title="t", url="u"),
        ],
        findings=["Effective per [PMID:12345]", "Confirmed by [NCT01234567]"],
    )
    result = factcheck(report, articles, trials)
    assert result.verified is True
    assert len(result.invalid_citations) == 0
    assert len(result.unsupported_findings) == 0


def test_factcheck_catches_hallucinated_pmid():
    articles = [_article("12345")]
    report = _report(
        citations=[
            Citation(id="99999", source="pubmed", title="t", url="u"),  # not in articles
        ],
        findings=["Per [PMID:99999]"],
    )
    result = factcheck(report, articles, [])
    assert result.verified is False
    assert len(result.invalid_citations) == 1
    assert len(result.unsupported_findings) == 1


def test_factcheck_normalizes_pmid_prefix():
    articles = [_article("12345")]
    report = _report(
        citations=[
            Citation(id="PMID:12345", source="pubmed", title="t", url="u"),  # prefix variant
        ],
        findings=["Per [PMID:12345]"],
    )
    result = factcheck(report, articles, [])
    assert result.verified is True
