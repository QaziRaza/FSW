"""Executable validation for the exploratory extension."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
DIAG = ROOT / "results" / "diagnostics"
REPORT = ROOT / "results" / "exploratory_report.md"


def run() -> dict:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})

    master = pd.read_csv(PROCESSED / "paper1_city_round_master.csv")
    features = pd.read_csv(PROCESSED / "paper1_2011_exploratory_features.csv")
    network = pd.read_csv(PROCESSED / "paper1_2011_network_structure.csv")
    macro = pd.read_csv(PROCESSED / "paper1_round_macro_context.csv")
    atlas = pd.read_csv(TABLES / "exploratory_2011_association_atlas.csv")
    econ = pd.read_csv(TABLES / "exploratory_economic_intercorrelations.csv")
    net_assoc = pd.read_csv(TABLES / "exploratory_2011_network_associations.csv")
    models = pd.read_csv(TABLES / "exploratory_two_exposure_models.csv")
    cv = pd.read_csv(TABLES / "exploratory_nonlinear_loocv.csv")
    transitions = pd.read_csv(TABLES / "exploratory_cross_round_city_transitions.csv")
    hypotheses = pd.read_csv(TABLES / "exploratory_hypothesis_ledger.csv")
    archetypes = pd.read_csv(TABLES / "exploratory_city_archetypes.csv")
    improvement = pd.read_csv(TABLES / "exploratory_macro_improvement_contrasts.csv")
    improvement_cities = pd.read_csv(TABLES / "exploratory_macro_improvement_city_counts.csv")
    paired_count_tests = pd.read_csv(TABLES / "exploratory_paired_count_tests.csv")

    check("feature row count", len(features) == 15, f"observed {len(features)}, expected 15")
    check("feature city uniqueness", features.city.nunique() == 15, f"unique cities {features.city.nunique()}")
    check("network row count", len(network) == 15, f"observed {len(network)}, expected 15")
    check("network city uniqueness", network.city.nunique() == 15, f"unique cities {network.city.nunique()}")
    check("network city coverage", set(network.city) == set(features.city), "network and 2011 city sets match")
    check("network operator total", network.network_operators.sum() == 12162, f"observed {network.network_operators.sum()}, published 12162")
    check("no missing network values", network.select_dtypes(include=[np.number]).notna().all().all(), "all 15x6 numeric network cells present")

    chronic_components = ["z_poverty_headcount_urban_pct", "z_female_illiteracy_urban_pct", "z_sanitation_deprivation_urban_pct"]
    reconstructed = features[chronic_components].mean(axis=1)
    check("chronic index reconstruction", np.allclose(reconstructed, features.chronic_deprivation_index, atol=1e-7), "index equals mean of three z-scored chronic measures")
    check("chronic index centering", abs(features.chronic_deprivation_index.mean()) < 1e-7, f"mean {features.chronic_deprivation_index.mean():.3g}")
    check("acute z centering", abs(features.acute_distress_z.mean()) < 1e-7, f"mean {features.acute_distress_z.mean():.3g}")
    implied = features.fsw_total * 1000 / features.fsw_density_per_1000_adult_men
    check("implied population reconstruction", np.allclose(implied, features.adult_male_population_implied, rtol=1e-7), "count*1000/density reproduced")
    check("archetypes complete", features.economic_archetype.notna().all() and features.economic_archetype.nunique() == 4, f"four archetypes; counts {features.economic_archetype.value_counts().to_dict()}")
    check("archetype table coverage", len(archetypes) == 15 and set(archetypes.city) == set(features.city), "dedicated table contains all 15 cities")

    check("macro context rows", set(macro.round_id) == {"2006_07", "2011", "2014", "2016_17"}, f"rounds {macro.round_id.tolist()}")
    check("2011 macro values", np.isclose(macro.loc[macro.round_id == "2011", "real_gdp_growth_pct"].iloc[0], 2.4) and np.isclose(macro.loc[macro.round_id == "2011", "cpi_inflation_pct"].iloc[0], 14.0), "2011 growth 2.4 and CPI 14.0")
    check("macro sources and locators", macro.source_file.notna().all() and macro.source_locator.notna().all(), "every macro row has source file and locator")

    check("association atlas dimensions", len(atlas) == 54 and atlas.exposure.nunique() == 6 and atlas.outcome.nunique() == 9, f"{len(atlas)} rows, {atlas.exposure.nunique()}x{atlas.outcome.nunique()}")
    check("association bounds", atlas.estimate_rho.between(-1, 1).all() and atlas.p_value_exploratory.between(0, 1).all(), "all rho and p values within bounds")
    check("atlas FDR dominates p", (atlas.p_fdr_bh_within_atlas + 1e-12 >= atlas.p_value_exploratory).all(), "all adjusted p values are at least raw p values")
    check("economic family dimensions", len(econ) == 10, f"observed {len(econ)}, expected 10 pairwise tests")
    check("network association dimensions", len(net_assoc) == 24, f"observed {len(net_assoc)}, expected 24")
    check("model dimensions", len(models) == 21 and models.model.nunique() == 7, f"{len(models)} rows across {models.model.nunique()} models")
    check("model confidence intervals ordered", (models.ci_95_low <= models.coefficient).all() and (models.coefficient <= models.ci_95_high).all(), "all coefficients lie inside own intervals")
    check("constant wins nonlinear LOOCV", cv.loc[cv.loocv_rmse_density.idxmin(), "degree"] == 0, f"minimum-RMSE degree {int(cv.loc[cv.loocv_rmse_density.idxmin(), 'degree'])}")
    check("paired transition coverage", transitions.groupby("comparison").size().to_dict() == {"2006_07_to_2011": 10, "2011_to_2014": 4}, f"counts {transitions.groupby('comparison').size().to_dict()}")
    check("hypothesis ledger complete", len(hypotheses) == 6 and hypotheses.notna().all().all(), f"{len(hypotheses)} fully specified hypotheses")
    check("macro contrast coverage", improvement.common_cities.tolist() == [10, 4, 10], f"common-city counts {improvement.common_cities.tolist()}")
    check("macro contrast city rows", len(improvement_cities) == 24, f"observed {len(improvement_cities)}, expected 24")
    recovery = improvement[improvement.comparison.isin(["2011_to_2014", "2011_to_2016_17"])]
    check("improvement direction encoded", (recovery.delta_real_gdp_growth_pp > 0).all() and (recovery.delta_cpi_inflation_pp < 0).all(), "post-2011 contrasts have higher growth and lower inflation")
    check("improvement count result", np.isclose(recovery.aggregate_fsw_total_pct_change.iloc[0], 16.769792, atol=1e-5) and np.isclose(recovery.aggregate_fsw_total_pct_change.iloc[1], 3.359798, atol=1e-5), f"aggregate changes {recovery.aggregate_fsw_total_pct_change.round(3).tolist()}")
    check("paired count tests complete", len(paired_count_tests) == 3 and paired_count_tests.common_cities.tolist() == [10, 4, 10], f"rows={len(paired_count_tests)}")
    check("exact sign tests", np.allclose(paired_count_tests.exact_sign_test_p_two_sided, [0.109375, 0.125, 0.75390625], atol=1e-6), f"p={paired_count_tests.exact_sign_test_p_two_sided.round(6).tolist()}")
    check("annualized contrast ordering", paired_count_tests.annualized_aggregate_fsw_change_pct.is_monotonic_decreasing, f"annualized={paired_count_tests.annualized_aggregate_fsw_change_pct.round(3).tolist()}")

    source_2011 = master[master.round_id == "2011"][["city", "fsw_total", "fsw_density_per_1000_adult_men"]].sort_values("city").reset_index(drop=True)
    joined = features[["city", "fsw_total", "fsw_density_per_1000_adult_men"]].sort_values("city").reset_index(drop=True)
    check("2011 source values preserved", source_2011.equals(joined), "city, total and density unchanged from frozen master")

    figure_names = [f"exploratory_figure_{i}_{suffix}.png" for i, suffix in [
        (1, "association_atlas"), (2, "acute_vs_chronic"), (3, "scale_contrast"),
        (4, "organisation"), (5, "round_context"), (6, "better_economy_test"),
    ]]
    for name in figure_names:
        path = FIGURES / name
        dimensions = Image.open(path).size if path.exists() else (0, 0)
        check(f"figure {name}", path.exists() and dimensions[0] >= 1600 and dimensions[1] >= 700, f"dimensions {dimensions}")
    report_text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    check("report status label", "hypothesis-generating" in report_text, "exploratory status explicitly stated")
    check("atlas FDR result", (atlas.p_fdr_bh_within_atlas < .05).sum() == 1 and atlas.loc[atlas.p_fdr_bh_within_atlas.idxmin(), "outcome_label"] == "kothikhana share", "one adjusted association: all-area deterioration versus kothikhana share")
    check("report multiplicity statement", "One association in the 54-cell outcome atlas survives" in report_text, "correct FDR result stated")
    check("report scale distinction", "absolute mapped FSW total" in report_text and "mapped density" in report_text, "count and density distinction stated")
    check("report mechanism boundary", "cannot show" in report_text and "not a demonstrated transition mechanism" in report_text, "mechanistic limits stated")

    failed = [row for row in checks if not row["passed"]]
    payload = {"status": "pass" if not failed else "fail", "checks": len(checks), "passed": len(checks) - len(failed), "failed": len(failed), "failures": failed}
    DIAG.mkdir(parents=True, exist_ok=True)
    (DIAG / "exploratory_validation.json").write_text(json.dumps({"summary": payload, "checks": checks}, indent=2), encoding="utf-8")
    lines = [
        "# Exploratory validation report", "",
        f"Status: **{payload['status'].upper()}** — {payload['passed']}/{payload['checks']} checks passed.", "",
        "| Check | Status | Detail |", "|---|---|---|",
        *[f"| {row['check']} | {'PASS' if row['passed'] else 'FAIL'} | {row['detail']} |" for row in checks], "",
        "This validation covers structure, exact source invariants, derived-feature reconstruction, statistical-output bounds, figure production, and interpretive guardrails. It does not make exploratory associations confirmatory.", "",
    ]
    (DIAG / "exploratory_validation.md").write_text("\n".join(lines), encoding="utf-8")
    if failed:
        raise AssertionError(f"Exploratory validation failed: {failed}")
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
