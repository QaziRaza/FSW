"""Cross-output validation for the authoritative combined analysis."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
DIAG = ROOT / "results" / "diagnostics"
SUMMARY = ROOT / "results" / "analysis_summary.md"
KNOWLEDGE = ROOT / "WHAT_WE_KNOW.md"


def exact_sign_test(increases: int, decreases: int) -> float:
    n = increases + decreases
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(increases, decreases) + 1)) / (2**n))


def run() -> dict:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})

    master = pd.read_csv(PROCESSED / "paper1_city_round_master.csv")
    primary = pd.read_csv(TABLES / "table_primary_result.csv").iloc[0]
    atlas = pd.read_csv(TABLES / "exploratory_2011_association_atlas.csv")
    contrasts = pd.read_csv(TABLES / "exploratory_macro_improvement_contrasts.csv")
    city_counts = pd.read_csv(TABLES / "exploratory_macro_improvement_city_counts.csv")
    paired_tests = pd.read_csv(TABLES / "exploratory_paired_count_tests.csv")
    macro_panel = pd.read_csv(TABLES / "macro_marker_round_panel.csv")
    macro_correlations = pd.read_csv(TABLES / "macro_marker_correlations.csv")
    macro_assumptions = pd.read_csv(TABLES / "macro_marker_assumption_tests.csv")
    stock_signal = pd.read_csv(TABLES / "stock_persistence_signal.csv")
    findings = pd.read_csv(TABLES / "current_findings.csv")
    base_validation = json.loads((DIAG / "validation_report.json").read_text(encoding="utf-8"))
    exploratory_validation = json.loads((DIAG / "exploratory_validation.json").read_text(encoding="utf-8"))["summary"]
    report = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    knowledge = KNOWLEDGE.read_text(encoding="utf-8") if KNOWLEDGE.exists() else ""

    d2011 = master[master.round_id == "2011"]
    x_rank = d2011.economic_distress_urban_pct.rank(method="average")
    y_rank = d2011.fsw_density_per_1000_adult_men.rank(method="average")
    recomputed_rho = float(np.corrcoef(x_rank, y_rank)[0, 1])
    check("primary rho independently recomputed", np.isclose(recomputed_rho, primary.estimate_rho, atol=5e-7), f"recomputed={recomputed_rho:.9f}; table={primary.estimate_rho:.9f}")
    check("primary interval ordered", primary.ci_95_low_bootstrap < primary.estimate_rho < primary.ci_95_high_bootstrap, f"CI {primary.ci_95_low_bootstrap:.3f} to {primary.ci_95_high_bootstrap:.3f}")
    check("primary permutation p bounded", 0 <= primary.p_permutation_two_sided <= 1, f"p={primary.p_permutation_two_sided:.6f}")

    expected_comparisons = ["2006_07_to_2011", "2011_to_2014", "2011_to_2016_17"]
    check("paired comparison set", contrasts.comparison.tolist() == expected_comparisons, f"comparisons={contrasts.comparison.tolist()}")
    for row in contrasts.itertuples():
        detail = city_counts[city_counts.comparison == row.comparison]
        start_total, end_total = detail.fsw_total_start.sum(), detail.fsw_total_end.sum()
        pct = 100 * (end_total - start_total) / start_total
        annualized = 100 * ((end_total / start_total) ** (1 / row.interval_years_approx) - 1)
        increases = int((detail.fsw_total_change > 0).sum())
        decreases = int((detail.fsw_total_change < 0).sum())
        test = paired_tests[paired_tests.comparison == row.comparison].iloc[0]
        check(f"{row.comparison}: totals reconcile", np.isclose(start_total, row.common_city_fsw_total_start) and np.isclose(end_total, row.common_city_fsw_total_end), f"{start_total:.0f}->{end_total:.0f}")
        check(f"{row.comparison}: percent change", np.isclose(pct, row.aggregate_fsw_total_pct_change, atol=5e-7), f"recomputed={pct:.6f}")
        check(f"{row.comparison}: annualized change", np.isclose(annualized, row.annualized_aggregate_fsw_change_pct, atol=5e-7), f"recomputed={annualized:.6f}")
        check(f"{row.comparison}: exact sign test", np.isclose(exact_sign_test(increases, decreases), test.exact_sign_test_p_two_sided, atol=5e-7), f"up/down={increases}/{decreases}; p={test.exact_sign_test_p_two_sided:.6f}")

    check("atlas family complete", len(atlas) == 54 and atlas.exposure.nunique() == 6 and atlas.outcome.nunique() == 9, "54 cells = 6 exposures x 9 outcomes")
    fdr_hits = atlas[atlas.p_fdr_bh_within_atlas < .05]
    check("atlas FDR result", len(fdr_hits) == 1 and fdr_hits.iloc[0].exposure_label == "acute all-area deterioration" and fdr_hits.iloc[0].outcome_label == "kothikhana share", f"hits={len(fdr_hits)}; minimum q={atlas.p_fdr_bh_within_atlas.min():.6f}")

    expected_rounds = ["2006_07", "2011", "2014", "2016_17"]
    check("macro-marker round panel", macro_panel.round_id.tolist() == expected_rounds, f"rounds={macro_panel.round_id.tolist()}")
    check("macro-marker atlas complete", len(macro_correlations) == 32 and macro_correlations.economic_indicator.nunique() == 4 and macro_correlations.fsw_marker.nunique() == 8, "32 cells = 4 indicators x 8 markers")
    check("macro-marker sample grain", macro_correlations.n_rounds.between(3, 4).all(), f"n range={macro_correlations.n_rounds.min()}-{macro_correlations.n_rounds.max()}")
    check("macro-marker exact p bounded", macro_correlations.exact_permutation_p.between(0, 1).all(), f"minimum p={macro_correlations.exact_permutation_p.min():.6f}")
    macro_fdr_hits = macro_correlations[macro_correlations.p_fdr_bh_across_macro_marker_atlas < .05]
    check("macro-marker FDR result", len(macro_fdr_hits) == 0 and np.isclose(macro_correlations.p_fdr_bh_across_macro_marker_atlas.min(), 1.0), f"hits={len(macro_fdr_hits)}; minimum q={macro_correlations.p_fdr_bh_across_macro_marker_atlas.min():.6f}")
    typology_rounds = macro_panel.dropna(subset=["cpi_inflation_pct", "home_minus_street_balance_pp"])
    cpi_balance_rho = float(np.corrcoef(
        typology_rounds.cpi_inflation_pct.rank(method="average"),
        typology_rounds.home_minus_street_balance_pp.rank(method="average"),
    )[0, 1])
    stored_cpi_balance = macro_correlations[
        (macro_correlations.economic_indicator_label == "CPI inflation") &
        (macro_correlations.fsw_marker_label == "home minus street balance")
    ].iloc[0]
    check("inflation-composition result independently recomputed", np.isclose(cpi_balance_rho, 1.0) and np.isclose(cpi_balance_rho, stored_cpi_balance.spearman_rho), f"rho={cpi_balance_rho:.6f}; exact p={stored_cpi_balance.exact_permutation_p:.6f}")
    check("macro assumptions ledger", len(macro_assumptions) == 8 and macro_assumptions.assumption_id.tolist() == [f"A{i}" for i in range(1, 9)], f"rows={len(macro_assumptions)}")
    check("continuous stock panels", stock_signal.panel_id.tolist() == ["continuous_to_2014", "continuous_to_2016_17"] and stock_signal.common_cities.tolist() == [4, 6], f"panels={stock_signal.panel_id.tolist()}; cities={stock_signal.common_cities.tolist()}")
    for row in stock_signal.itertuples():
        rounds = ["2006_07", "2011", row.recovery_round]
        city_sets = [set(master.loc[master.round_id == round_id, "city"]) for round_id in rounds]
        common = set.intersection(*city_sets)
        totals = [master[(master.round_id == round_id) & master.city.isin(common)].fsw_total.sum() for round_id in rounds]
        check(f"{row.panel_id}: common cities independently reconstructed", len(common) == row.common_cities, f"n={len(common)}")
        check(f"{row.panel_id}: stock totals independently reconstructed", np.allclose(totals, [row.mapped_total_2006_07, row.mapped_total_2011, row.mapped_total_recovery_round]), f"totals={totals}")
        check(f"{row.panel_id}: recovery growth is slower", row.recovery_annualized_growth_pct < row.deterioration_annualized_growth_pct, f"annualized {row.deterioration_annualized_growth_pct:.2f}% -> {row.recovery_annualized_growth_pct:.2f}%")
    check("base validation current", base_validation.get("status") == "PASS" and base_validation.get("failed_count") == 0, f"status={base_validation.get('status')}; checks={len(base_validation.get('checks', []))}")
    check("exploratory validation current", exploratory_validation.get("status") == "pass" and exploratory_validation.get("failed") == 0, f"status={exploratory_validation.get('status')}; checks={exploratory_validation.get('checks')}")

    required_sections = [
        "Executive summary", "Evidence assembled and usable", "Frozen primary result",
        "Recent deterioration and chronic deprivation", "Sex-work structure",
        "What changed across economic deterioration and recovery", "National economic indicators tested against multiple FSW markers", "Replication and model checks",
        "What the evidence supports and contradicts", "Is Paper 2 justified?",
        "Reproducibility and validation status",
        "Source traceability",
    ]
    for section in required_sections:
        check(f"report section: {section}", section.lower() in report.lower(), "present")
    required_claim_fragments = [
        "rho=-0.138", "66.25%", "16.77%", "+3.36%", "11.96%", "category C",
        "71,315", "64,829", "not supported", "Paper 2", "minimum exact p-value is 0.333",
        "home-minus-street balance", "Kothikhana share did not behave as a clean temporal macro marker",
        "Simple answer: yes", "9.65%", "14.39%", "0.87%", "fewer net newcomers",
    ]
    for fragment in required_claim_fragments:
        check(f"report claim: {fragment}", fragment.lower() in report.lower(), "present")
    check("report avoids prohibited certainty", not re.search(r"\b(proves|causes|validated sentinel|early-warning system)\b", report, flags=re.I), "no prohibited certainty language")
    referenced_figures = re.findall(r"\]\(figures/([^\)]+)\)", report)
    missing_figures = [name for name in referenced_figures if not (ROOT / "results" / "figures" / name).exists()]
    check("all report figures exist", len(referenced_figures) >= 5 and not missing_figures, f"referenced={len(referenced_figures)}; missing={missing_figures}")
    check("knowledge index exists", KNOWLEDGE.exists() and "Current answer" in knowledge and "Reproduce" in knowledge, "WHAT_WE_KNOW.md")
    check("confirmatory summary preserved", (ROOT / "results" / "confirmatory_analysis_summary.md").exists(), "prespecified-only narrative retained separately")
    check("source manifest retained", (ROOT / "data" / "source_manifest.csv").exists(), "source provenance available")
    check("hypothesis ledger retained", (TABLES / "exploratory_hypothesis_ledger.csv").exists(), "six hypotheses with later tests available")
    check("current findings ledger", len(findings) == 18 and findings.claim_id.nunique() == 18, f"rows={len(findings)}; unique IDs={findings.claim_id.nunique()}")
    check("findings preserve confirmatory boundary", (findings.status == "confirmatory result").sum() == 1 and (findings.status == "multiplicity-adjusted exploratory").sum() == 1, "one confirmatory result and one FDR-adjusted exploratory result")

    failures = [item for item in checks if not item["passed"]]
    summary = {"status": "PASS" if not failures else "FAIL", "checks": len(checks), "passed": len(checks) - len(failures), "failed": len(failures)}
    DIAG.mkdir(parents=True, exist_ok=True)
    (DIAG / "complete_validation.json").write_text(json.dumps({"summary": summary, "checks": checks}, indent=2), encoding="utf-8")
    lines = [
        "# Complete-analysis validation", "",
        f"Status: **{summary['status']}** — {summary['passed']}/{summary['checks']} checks passed.", "",
        "| Check | Result | Detail |", "|---|---:|---|",
        *[f"| {item['check']} | {'PASS' if item['passed'] else 'FAIL'} | {str(item['detail']).replace('|', '/')} |" for item in checks], "",
        "This layer independently recomputes the primary rank correlation, every paired-count contrast, both continuous-city stock panels and the key inflation-composition result; checks exact tests and multiplicity results; confirms required synthesis sections and claims; and ensures referenced artifacts exist.", "",
    ]
    (DIAG / "complete_validation.md").write_text("\n".join(lines), encoding="utf-8")
    if failures:
        raise AssertionError(f"Complete-analysis validation failed: {failures}")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
