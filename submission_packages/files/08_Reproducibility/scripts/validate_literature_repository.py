"""Validate the internal consistency of the Paper 1 literature repository."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIT = ROOT / "literature"
DISCUSSION = ROOT / "manuscript" / "discussion_draft.md"

REQUIRED_FILES = {
    "README.md",
    "review_synthesis.md",
    "discussion_comparison_map.md",
    "source_summaries.md",
    "evidence_matrix.csv",
    "references.bib",
    "search_protocol.md",
    "search_log.csv",
}

REQUIRED_COLUMNS = {
    "source_id",
    "bibkey",
    "priority",
    "evidence_grade",
    "geography",
    "year",
    "source_type",
    "design",
    "sample_or_scope",
    "economic_or_structural_driver",
    "sex_work_marker",
    "plain_finding",
    "relevance_to_paper1",
    "comparison_direction",
    "doi",
    "pmid",
    "pmcid",
    "abstract_or_report_url",
    "full_text_url",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    existing = {path.name for path in LIT.iterdir() if path.is_file()}
    check(REQUIRED_FILES <= existing, f"Missing files: {sorted(REQUIRED_FILES - existing)}")

    with (LIT / "evidence_matrix.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        check(reader.fieldnames is not None, "Evidence matrix has no header")
        check(REQUIRED_COLUMNS <= set(reader.fieldnames), "Evidence matrix is missing required columns")
        rows = list(reader)

    check(len(rows) >= 30, f"Expected at least 30 sources, found {len(rows)}")
    ids = [row["source_id"] for row in rows]
    keys = [row["bibkey"] for row in rows]
    check(len(ids) == len(set(ids)), "Duplicate source_id values")
    check(len(keys) == len(set(keys)), "Duplicate bibkey values")
    check(all(row["evidence_grade"] in {"A", "B", "C"} for row in rows), "Invalid evidence grade")
    check(all(row["year"].isdigit() for row in rows), "Non-numeric year")
    check(all(row["abstract_or_report_url"].startswith("http") for row in rows), "Missing source URL")
    check(all(row["full_text_url"].startswith("http") for row in rows), "Missing full-text or landing URL")

    summaries = (LIT / "source_summaries.md").read_text(encoding="utf-8")
    missing_summary_ids = [source_id for source_id in ids if f"### {source_id} " not in summaries]
    check(not missing_summary_ids, f"Missing source summaries: {missing_summary_ids}")

    bib_text = (LIT / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib_text))
    check(set(keys) == bib_keys, f"BibTeX mismatch: matrix-only={sorted(set(keys)-bib_keys)}; bib-only={sorted(bib_keys-set(keys))}")

    cited_keys: set[str] = set()
    if DISCUSSION.exists():
        discussion_text = DISCUSSION.read_text(encoding="utf-8")
        cited_keys = set(re.findall(r"@([A-Za-z0-9]+)", discussion_text))
        check(cited_keys, "Discussion exists but contains no BibTeX citation keys")
        missing_citations = cited_keys - bib_keys
        check(not missing_citations, f"Discussion cites missing BibTeX keys: {sorted(missing_citations)}")
        check(
            "directly measured" in discussion_text or "directly observed" in discussion_text,
            "Discussion should distinguish observed evidence from interpreted mechanisms",
        )

    with (LIT / "search_log.csv").open(encoding="utf-8-sig", newline="") as handle:
        search_rows = list(csv.DictReader(handle))
    check(len(search_rows) >= 8, "Search log is unexpectedly short")
    check(all(row["status"] == "complete" for row in search_rows), "Incomplete search-log item")

    pakistan = sum(row["geography"] == "Pakistan" for row in rows)
    zimbabwe = sum(row["geography"] == "Zimbabwe" for row in rows)
    comparative = len(rows) - pakistan - zimbabwe
    print(f"PASS: {len(rows)} sources ({pakistan} Pakistan, {zimbabwe} Zimbabwe, {comparative} other/comparative)")
    print(f"PASS: {len(bib_keys)} matching BibTeX records and {len(search_rows)} completed search themes")
    if cited_keys:
        print(f"PASS: Discussion uses {len(cited_keys)} valid BibTeX citation keys")


if __name__ == "__main__":
    main()
