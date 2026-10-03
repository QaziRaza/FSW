"""Create the authoritative combined analysis and repository evidence index."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analyse_primary import spearman_values

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
DIAG = ROOT / "results" / "diagnostics"
SUMMARY = ROOT / "results" / "analysis_summary.md"
KNOWLEDGE = ROOT / "WHAT_WE_KNOW.md"


def md_table(df: pd.DataFrame, columns: list[str], digits: dict[str, int] | None = None) -> str:
    digits = digits or {}
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in df[columns].iterrows():
        rendered = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                rendered.append("NA")
            elif column in digits:
                rendered.append(f"{float(value):.{digits[column]}f}")
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_summary() -> None:
    master = pd.read_csv(PROCESSED / "paper1_city_round_master.csv")
    manifest = pd.read_csv(ROOT / "data" / "source_manifest.csv")
    features = pd.read_csv(PROCESSED / "paper1_2011_exploratory_features.csv")
    comparability = pd.read_csv(PROCESSED / "round_comparability.csv")
    primary = pd.read_csv(TABLES / "table_primary_result.csv").iloc[0]
    secondary = pd.read_csv(TABLES / "table_secondary_correlations.csv")
    sensitivity = pd.read_csv(TABLES / "table_sensitivity_correlations.csv")
    structural = pd.read_csv(TABLES / "table_structural_replication.csv")
    atlas = pd.read_csv(TABLES / "exploratory_2011_association_atlas.csv")
    economic = pd.read_csv(TABLES / "exploratory_economic_intercorrelations.csv")
    network = pd.read_csv(TABLES / "exploratory_2011_network_associations.csv")
    models = pd.read_csv(TABLES / "exploratory_two_exposure_models.csv")
    nonlinear = pd.read_csv(TABLES / "exploratory_nonlinear_loocv.csv")
    rounds = pd.read_csv(TABLES / "exploratory_round_economic_mapping_context.csv")
    improvement = pd.read_csv(TABLES / "exploratory_macro_improvement_contrasts.csv")
    paired_tests = pd.read_csv(TABLES / "exploratory_paired_count_tests.csv")
    macro_panel = pd.read_csv(TABLES / "macro_marker_round_panel.csv")
    macro_correlations = pd.read_csv(TABLES / "macro_marker_correlations.csv")
    macro_assumptions = pd.read_csv(TABLES / "macro_marker_assumption_tests.csv")
    stock_signal = pd.read_csv(TABLES / "stock_persistence_signal.csv")

    def atlas_row(exposure: str, outcome: str):
        return atlas[(atlas.exposure_label == exposure) & (atlas.outcome_label == outcome)].iloc[0]

    def macro_row(indicator: str, marker: str):
        return macro_correlations[
            (macro_correlations.economic_indicator_label == indicator) &
            (macro_correlations.fsw_marker_label == marker)
        ].iloc[0]

    acute_density = atlas_row("acute urban deterioration", "mapped density")
    acute_total = atlas_row("acute urban deterioration", "mapped total")
    acute_scale = atlas_row("acute urban deterioration", "implied adult-male population")
    chronic_density = atlas_row("chronic deprivation index", "mapped density")
    chronic_total = atlas_row("chronic deprivation index", "mapped total")
    chronic_scale = atlas_row("chronic deprivation index", "implied adult-male population")
    acute_kk = atlas_row("acute urban deterioration", "kothikhana share")
    acute_phone = atlas_row("acute urban deterioration", "cellphone share")
    all_kk = atlas_row("acute all-area deterioration", "kothikhana share")
    all_phone = atlas_row("acute all-area deterioration", "cellphone share")
    acute_chronic_rho, acute_chronic_p = spearman_values(
        features.economic_distress_urban_pct.to_numpy(float),
        features.chronic_deprivation_index.to_numpy(float),
    )
    subset = sensitivity[~sensitivity.analysis.str.startswith("leave_out_")]
    loo = sensitivity[sensitivity.analysis.str.startswith("leave_out_")]
    network_key = network[
        ((network.exposure_label == "acute urban deterioration") & (network.network_outcome == "avg_kothikhana_fsw_per_operator")) |
        ((network.exposure_label == "mapped density") & network.network_outcome.isin(["avg_home_fsw_per_operator", "avg_networked_fsw_per_operator"]))
    ]
    scale_table = pd.DataFrame([
        {"economic dimension": "recent deterioration", "mapped density rho": acute_density.estimate_rho, "mapped total rho": acute_total.estimate_rho, "city scale rho": acute_scale.estimate_rho},
        {"economic dimension": "chronic deprivation", "mapped density rho": chronic_density.estimate_rho, "mapped total rho": chronic_total.estimate_rho, "city scale rho": chronic_scale.estimate_rho},
    ])
    round_table = rounds[[
        "round_id", "cities", "median_acute_distress_pct", "median_home_share_pct",
        "median_street_share_pct", "median_kothikhana_share_pct",
        "real_gdp_growth_pct", "cpi_inflation_pct",
    ]]
    improvement_table = improvement[[
        "comparison", "common_cities", "aggregate_fsw_total_pct_change",
        "annualized_aggregate_fsw_change_pct", "median_city_fsw_pct_change",
        "cities_with_count_increase", "cities_with_count_decrease",
        "median_delta_economic_distress_urban_pct", "median_delta_home_share_pct",
        "median_delta_street_share_pct", "median_delta_kothikhana_share_pct",
    ]]
    paired_table = paired_tests[[
        "comparison", "exact_sign_test_p_two_sided", "paired_n_distress_count_change",
        "rho_distress_change_vs_log_count_change", "p_distress_change_vs_log_count_change",
    ]]
    macro_key = macro_correlations[
        macro_correlations.economic_indicator_label.isin(["GDP growth", "CPI inflation"]) &
        macro_correlations.fsw_marker_label.isin([
            "round mapped total", "median city mapped total", "home share", "street share",
            "kothikhana share", "home minus street balance", "reported household distress",
        ])
    ][[
        "economic_indicator_label", "fsw_marker_label", "n_rounds", "spearman_rho",
        "exact_permutation_p", "p_fdr_bh_across_macro_marker_atlas",
    ]]
    stock_display = stock_signal[[
        "recovery_round", "common_cities", "mapped_total_2006_07", "mapped_total_2011",
        "mapped_total_recovery_round", "deterioration_annualized_growth_pct",
        "recovery_annualized_growth_pct", "annualized_growth_slowdown_pp",
        "recovery_growth_rate_as_pct_of_deterioration",
    ]]
    economic_key = economic[(economic.variable_1 == "economic_distress_urban_pct") | (economic.variable_1 == "poverty_headcount_urban_pct")][[
        "variable_1", "variable_2", "estimate_rho", "p_value_exploratory", "p_fdr_bh_within_family"
    ]]
    structural_display = structural[["round_id", "outcome", "n", "estimate_rho", "p_value", "p_fdr_bh"]]
    validation = read_json(DIAG / "validation_report.json")
    exploratory_validation = read_json(DIAG / "exploratory_validation.json").get("summary", {})
    source_table = manifest[["source_id", "category", "period", "title", "analysis_role"]]
    findings = pd.DataFrame([
        {"claim_id": "F01", "status": "confirmatory result", "domain": "2011 density", "finding": "Recent urban deterioration has a weak inverse association with mapped FSW density.", "estimate": primary.estimate_rho, "ci_95_low": primary.ci_95_low_bootstrap, "ci_95_high": primary.ci_95_high_bootstrap, "p_value": primary.p_permutation_two_sided, "adjusted_p": None, "n": int(primary.n), "evidence_file": "results/tables/table_primary_result.csv"},
        {"claim_id": "F02", "status": "exploratory association", "domain": "market size", "finding": "Recent deterioration is positively associated with absolute mapped FSW total.", "estimate": acute_total.estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": acute_total.p_value_exploratory, "adjusted_p": acute_total.p_fdr_bh_within_atlas, "n": int(acute_total.n), "evidence_file": "results/tables/exploratory_2011_association_atlas.csv"},
        {"claim_id": "F03", "status": "exploratory association", "domain": "chronic deprivation", "finding": "Chronic deprivation is inversely associated with absolute mapped total and weakly positively associated with density.", "estimate": chronic_total.estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": chronic_total.p_value_exploratory, "adjusted_p": chronic_total.p_fdr_bh_within_atlas, "n": int(chronic_total.n), "evidence_file": "results/tables/exploratory_2011_association_atlas.csv"},
        {"claim_id": "F04", "status": "exploratory association", "domain": "organisation", "finding": "Recent urban deterioration is positively associated with kothikhana share.", "estimate": acute_kk.estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": acute_kk.p_value_exploratory, "adjusted_p": acute_kk.p_fdr_bh_within_atlas, "n": int(acute_kk.n), "evidence_file": "results/tables/exploratory_2011_association_atlas.csv"},
        {"claim_id": "F05", "status": "multiplicity-adjusted exploratory", "domain": "organisation", "finding": "All-area deterioration is positively associated with kothikhana share and survives atlas-wide FDR adjustment.", "estimate": all_kk.estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": all_kk.p_value_exploratory, "adjusted_p": all_kk.p_fdr_bh_within_atlas, "n": int(all_kk.n), "evidence_file": "results/tables/exploratory_2011_association_atlas.csv"},
        {"claim_id": "F06", "status": "exploratory association", "domain": "organisation", "finding": "Recent deterioration is inversely associated with cellphone share.", "estimate": acute_phone.estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": acute_phone.p_value_exploratory, "adjusted_p": acute_phone.p_fdr_bh_within_atlas, "n": int(acute_phone.n), "evidence_file": "results/tables/exploratory_2011_association_atlas.csv"},
        {"claim_id": "F07", "status": "exploratory network association", "domain": "network organisation", "finding": "Recent deterioration is positively associated with kothikhana FSWs per operator.", "estimate": network_key.iloc[0].estimate_rho, "ci_95_low": None, "ci_95_high": None, "p_value": network_key.iloc[0].p_value_exploratory, "adjusted_p": network_key.iloc[0].p_fdr_bh_within_family, "n": int(network_key.iloc[0].n), "evidence_file": "results/tables/exploratory_2011_network_associations.csv"},
        {"claim_id": "F08", "status": "exploratory period contrast", "domain": "deterioration", "finding": "The ten common-city mapped total expanded 66.25% from 2006-07 to 2011.", "estimate": improvement.iloc[0].aggregate_fsw_total_pct_change, "ci_95_low": None, "ci_95_high": None, "p_value": improvement.iloc[0].exact_sign_test_p_two_sided, "adjusted_p": None, "n": int(improvement.iloc[0].common_cities), "evidence_file": "results/tables/exploratory_macro_improvement_contrasts.csv"},
        {"claim_id": "F09", "status": "exploratory period contrast", "domain": "recovery", "finding": "The four common-city mapped total rose 16.77% from 2011 to 2014, but its annualized growth was substantially slower than during deterioration.", "estimate": improvement.iloc[1].aggregate_fsw_total_pct_change, "ci_95_low": None, "ci_95_high": None, "p_value": improvement.iloc[1].exact_sign_test_p_two_sided, "adjusted_p": None, "n": int(improvement.iloc[1].common_cities), "evidence_file": "results/tables/stock_persistence_signal.csv"},
        {"claim_id": "F10", "status": "exploratory period contrast", "domain": "recovery", "finding": "The mapped total broadly plateaued through 2016-17 while remaining above its 2011 level.", "estimate": improvement.iloc[2].aggregate_fsw_total_pct_change, "ci_95_low": None, "ci_95_high": None, "p_value": improvement.iloc[2].exact_sign_test_p_two_sided, "adjusted_p": None, "n": int(improvement.iloc[2].common_cities), "evidence_file": "results/tables/stock_persistence_signal.csv"},
        {"claim_id": "F11", "status": "falsification result", "domain": "city change", "finding": "Local distress changes do not show a stable directional relationship with mapped-count changes.", "estimate": None, "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": None, "evidence_file": "results/tables/exploratory_paired_count_tests.csv"},
        {"claim_id": "F12", "status": "falsification result", "domain": "nonlinearity", "finding": "Linear, quadratic and cubic density models all have worse LOOCV error than a constant-only model.", "estimate": nonlinear.loc[nonlinear.degree == 0, "loocv_rmse_density"].iloc[0], "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": 15, "evidence_file": "results/tables/exploratory_nonlinear_loocv.csv"},
        {"claim_id": "F13", "status": "overall synthesis", "domain": "economic signal", "finding": "The complete available series shows expansion during deterioration followed by strong growth deceleration and persistence during recovery (protocol category C).", "estimate": None, "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": None, "evidence_file": "results/analysis_summary.md"},
        {"claim_id": "F14", "status": "exploratory round-level association", "domain": "work setting", "finding": "Inflation is perfectly rank-aligned with the home-minus-street balance across the three rounds with typology data, while GDP growth has a weaker inverse alignment.", "estimate": macro_row("CPI inflation", "home minus street balance").spearman_rho, "ci_95_low": None, "ci_95_high": None, "p_value": macro_row("CPI inflation", "home minus street balance").exact_permutation_p, "adjusted_p": macro_row("CPI inflation", "home minus street balance").p_fdr_bh_across_macro_marker_atlas, "n": int(macro_row("CPI inflation", "home minus street balance").n_rounds), "evidence_file": "results/tables/macro_marker_correlations.csv"},
        {"claim_id": "F15", "status": "falsification result", "domain": "organisation", "finding": "Kothikhana share is not a consistent standalone temporal marker of weak national economic conditions; it rose during both deterioration and recovery.", "estimate": macro_row("CPI inflation", "kothikhana share").spearman_rho, "ci_95_low": None, "ci_95_high": None, "p_value": macro_row("CPI inflation", "kothikhana share").exact_permutation_p, "adjusted_p": macro_row("CPI inflation", "kothikhana share").p_fdr_bh_across_macro_marker_atlas, "n": int(macro_row("CPI inflation", "kothikhana share").n_rounds), "evidence_file": "results/tables/macro_marker_assumption_tests.csv"},
        {"claim_id": "F16", "status": "data-availability result", "domain": "longitudinal measurement", "finding": "Density and cellphone share cannot be tested as multi-round macro markers because comparable values are available in only one and two rounds, respectively.", "estimate": None, "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": None, "evidence_file": "results/tables/macro_marker_assumption_tests.csv"},
        {"claim_id": "F17", "status": "exploratory continuous-panel signal", "domain": "stock persistence", "finding": "In six cities observed continuously through 2016-17, annualized mapped-population growth slowed from 14.39% during deterioration to 0.87% during recovery.", "estimate": stock_signal.iloc[1].annualized_growth_slowdown_pp, "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": int(stock_signal.iloc[1].common_cities), "evidence_file": "results/tables/stock_persistence_signal.csv"},
        {"claim_id": "F18", "status": "mechanism interpretation", "domain": "entry and exit", "finding": "The plateau is consistent with fewer net newcomers combined with difficulty leaving the profession, although the surveys do not separately count entries and exits.", "estimate": None, "ci_95_low": None, "ci_95_high": None, "p_value": None, "adjusted_p": None, "n": None, "evidence_file": "results/tables/stock_persistence_signal.csv"},
    ])
    findings.to_csv(TABLES / "current_findings.csv", index=False, float_format="%.6f")

    lines = [
        "# Economic deterioration tracks FSW expansion; recovery tracks a plateau", "",
        "> Authoritative synthesis of the currently assembled Pakistani evidence. The frozen primary test remains distinct from the later exploratory analyses.", "",
        "## Executive summary", "",
        "- **Simple answer: yes, the complete available Pakistani survey series contains an economic signal.** The mapped FSW population expanded rapidly as growth weakened and inflation rose, then its growth sharply decelerated toward a plateau as the economy improved.",
        f"- **The same-city stock comparison is the clearest test.** In the four-city continuous panel, annualized mapped-population growth slowed from {stock_signal.iloc[0].deterioration_annualized_growth_pct:.2f}% during deterioration to {stock_signal.iloc[0].recovery_annualized_growth_pct:.2f}% during recovery. In the six-city panel followed through 2016-17, it slowed from {stock_signal.iloc[1].deterioration_annualized_growth_pct:.2f}% to {stock_signal.iloc[1].recovery_annualized_growth_pct:.2f}%.",
        "- **The plateau should be read as a stock-flow result.** Economic recovery need not remove people who already entered sex work. The sharp fall in net population growth is consistent with fewer newcomers while the existing population persists because exit into other work is difficult. The surveys observe the resulting population stock, not entry and exit separately.",
        f"- **Density is not the main economic signal.** In 2011, recent household economic deterioration had only a weak inverse association with mapped FSW density (rho={primary.estimate_rho:+.3f}; bootstrap 95% CI {primary.ci_95_low_bootstrap:+.3f} to {primary.ci_95_high_bootstrap:+.3f}; permutation p={primary.p_permutation_two_sided:.4f}).",
        f"- **Market scale is the clearest 2011 relationship.** Recent deterioration was positively associated with absolute mapped FSW numbers (rho={acute_total.estimate_rho:+.3f}) and implied adult-male population scale (rho={acute_scale.estimate_rho:+.3f}), while chronic deprivation was negatively associated with both total (rho={chronic_total.estimate_rho:+.3f}) and scale (rho={chronic_scale.estimate_rho:+.3f}) but weakly positively associated with density (rho={chronic_density.estimate_rho:+.3f}).",
        f"- **Sex-work organisation carries a stronger economic pattern than density.** Recent deterioration was associated with greater kothikhana share (rho={acute_kk.estimate_rho:+.3f}) and lower cellphone share (rho={acute_phone.estimate_rho:+.3f}); the separately published network table showed more kothikhana-based FSWs per operator (rho={network_key.iloc[0].estimate_rho:+.3f}).",
        "- **The cross-period pattern is expansion followed by deceleration, not expansion followed by disappearance.** The ten common cities' mapped total expanded 66.25% during the 2006-07 to 2011 deterioration. Later recovery left the accumulated population in place while its growth slowed sharply.",
        f"- **Across economic indicators and FSW markers, work setting is the clearest longitudinal signal.** Inflation was perfectly rank-aligned with the home-minus-street balance across the three rounds with typology data (rho={macro_row('CPI inflation', 'home minus street balance').spearman_rho:+.3f}); GDP growth showed the expected but weaker inverse direction (rho={macro_row('GDP growth', 'home minus street balance').spearman_rho:+.3f}). Kothikhana share did not behave as a clean temporal macro marker.",
        "- **What this supports:** the signal lies in changes in population growth and organisation, not in expecting density or the total population to fall immediately when conditions improve.", "",
        "## 1. Evidence assembled and usable", "",
        md_table(comparability, ["round_id", "mapping_period", "cities", "density_available", "typology_available", "economic_period", "status"]), "",
        "The repository contains 49 unique city-round records. These rounds constitute the complete published Pakistani series available for this FSW-economic comparison; there is no separate national longitudinal dataset waiting to validate it. The analysis therefore asks what the total available evidence shows, while preserving the measurement differences between rounds. Only 2011 reports city-specific FSW density per 1,000 adult men. The 2006-07 and 2014 sources support typology comparisons. The 2016-17 source supports printed city counts only; its 18 city rows sum to 71,315 while its printed grand total is 64,829, so common-city rows are used without substituting the inconsistent grand total.", "",
        "The economic evidence has two levels:", "",
        "- **Local household conditions:** urban district percentages reporting a worse or much worse economic situation than one year earlier, plus poverty, female illiteracy and sanitation deprivation where available.",
        "- **National context:** GDP growth, CPI inflation, unemployment where reported, and per-capita income from the corresponding Pakistan Economic Survey overviews.", "",
        "## 2. Frozen primary result: 2011 density", "",
        f"The prespecified question was whether cities with greater recent urban economic deterioration had a higher mapped FSW density. The observed relationship was weakly inverse: rho={primary.estimate_rho:+.3f}, not positive. The bootstrap interval ({primary.ci_95_low_bootstrap:+.3f} to {primary.ci_95_high_bootstrap:+.3f}) spans both directions and the permutation p-value is {primary.p_permutation_two_sided:.4f}.", "",
        f"The estimate was directionally stable to individual-city omission: all leave-one-city-out estimates remained negative, ranging from {loo.estimate.min():+.3f} to {loo.estimate.max():+.3f}. Across the prespecified city subsets, estimates ranged from {subset.estimate.min():+.3f} to {subset.estimate.max():+.3f}. This means no single city creates the inverse direction, but the magnitude is small and sensitive enough that density is not a strong signal.", "",
        md_table(secondary, ["analysis", "method", "n", "estimate", "p_value"], {"estimate": 3, "p_value": 4}), "",
        "The secondary domains are not interchangeable. Poverty and female illiteracy have positive density correlations, while recent deterioration and sanitation deprivation are weakly inverse. This contradiction becomes coherent only after distinguishing recent change from chronic deprivation.", "",
        "![Primary density result](figures/figure_1_primary_scatter.png)", "",
        "## 3. Recent deterioration and chronic deprivation are different economic dimensions", "",
        f"The exploratory chronic-deprivation index is the equal-weight mean of standardized urban poverty, female illiteracy and sanitation deprivation. Recent deterioration and this index were inversely associated (rho={acute_chronic_rho:+.3f}, p={acute_chronic_p:.4f}). Cities reporting the greatest recent worsening were often large and relatively less chronically deprived; persistently deprived cities were generally smaller.", "",
        md_table(economic_key, economic_key.columns.tolist(), {"estimate_rho": 3, "p_value_exploratory": 4, "p_fdr_bh_within_family": 4}), "",
        md_table(scale_table, scale_table.columns.tolist(), {"mapped density rho": 3, "mapped total rho": 3, "city scale rho": 3}), "",
        "This produces the central count-versus-rate result: recent deterioration is associated with **more mapped workers in absolute terms**, but not with more workers per 1,000 adult men. Chronic deprivation is associated with **fewer workers in absolute terms** but somewhat higher density. The implied population measure is algebraically derived from published count and density and is used only to diagnose city scale.", "",
        "![Acute and chronic economic dimensions](figures/exploratory_figure_2_acute_vs_chronic.png)", "",
        "![Count, population scale and density](figures/exploratory_figure_3_scale_contrast.png)", "",
        "## 4. Sex-work structure is more economically patterned than density", "",
        f"In 2011, recent urban deterioration was associated with kothikhana share (rho={acute_kk.estimate_rho:+.3f}, raw p={acute_kk.p_value_exploratory:.4f}) and inversely associated with cellphone share (rho={acute_phone.estimate_rho:+.3f}, raw p={acute_phone.p_value_exploratory:.4f}). Using the all-area deterioration measure, the same directions were stronger: kothikhana rho={all_kk.estimate_rho:+.3f} and cellphone rho={all_phone.estimate_rho:+.3f}.", "",
        md_table(network_key, ["exposure_label", "network_outcome", "estimate_rho", "p_value_exploratory", "p_fdr_bh_within_family"], {"estimate_rho": 3, "p_value_exploratory": 4, "p_fdr_bh_within_family": 4}), "",
        "The most coherent reading is organisational: recent economic worsening is associated with larger urban markets and more kothikhana/intermediary-linked organisation, while cellphone-based work is more prominent in a different economic profile. This is a structural association, not evidence that individual workers changed categories because of hardship.", "",
        f"One of the 54 exploratory exposure-outcome associations survives a 5% Benjamini-Hochberg correction: all-area reported deterioration versus kothikhana share (rho={all_kk.estimate_rho:+.3f}; raw p={all_kk.p_value_exploratory:.5f}; q={all_kk.p_fdr_bh_within_atlas:.4f}). The structural pattern therefore includes one multiplicity-adjusted association; the urban-stratum and other typology results remain supporting exploratory evidence.", "",
        "![Organisation patterns](figures/exploratory_figure_4_organisation.png)", "",
        "## 5. What changed across economic deterioration and recovery", "",
        md_table(round_table, round_table.columns.tolist(), {c: 2 for c in round_table.columns if c not in {"round_id", "cities"}}), "",
        md_table(improvement_table, improvement_table.columns.tolist(), {c: 2 for c in improvement_table.columns if c not in {"comparison", "common_cities", "cities_with_count_increase", "cities_with_count_decrease"}}), "",
        "From 2006-07 to 2011, GDP growth fell 4.60 percentage points, inflation rose 6.10 points and median reported district distress rose 20.84 points among the ten common cities. Their combined mapped FSW total rose 66.25%; eight of ten cities increased. Median home share rose 18.32 points, street share fell 24.16 points and kothikhana share rose 6.99 points.", "",
        "From 2011 to 2014, growth improved and inflation fell sharply. Reported distress declined modestly in the four common Punjab cities, yet mapped counts increased in all four and their combined total rose 16.77%. Home share fell 26.10 points, street share rose 17.11 points and kothikhana share rose another 7.85 points.", "",
        "Across the longer 2011 to 2016-17 comparison, the ten common-city total was broadly stable (+3.36%): four cities increased and six decreased. The approximate annualized combined-count change slowed from 11.96% during the deterioration interval to 5.30% through 2014 and 0.60% through 2016-17.", "",
        "The stricter continuous-panel comparison holds the cities fixed across deterioration and recovery:", "",
        md_table(stock_display, stock_display.columns.tolist(), {c: 2 for c in stock_display.columns if c not in {"recovery_round", "common_cities"}}), "",
        f"The four cities observed in 2006-07, 2011 and 2014 grew at {stock_signal.iloc[0].deterioration_annualized_growth_pct:.2f}% per year during deterioration and {stock_signal.iloc[0].recovery_annualized_growth_pct:.2f}% during recovery. The six cities observed in 2006-07, 2011 and 2016-17 grew at {stock_signal.iloc[1].deterioration_annualized_growth_pct:.2f}% during deterioration and only {stock_signal.iloc[1].recovery_annualized_growth_pct:.2f}% during recovery. The later rate is just {stock_signal.iloc[1].recovery_growth_rate_as_pct_of_deterioration:.1f}% of the earlier rate. This is a strong descriptive expansion-to-plateau signal.", "",
        "A stock-flow interpretation resolves the apparent puzzle. A downturn can increase entry into sex work and rapidly enlarge the population. When the economy improves, fewer people may enter, but the people already in the profession may remain because leaving and obtaining other work is difficult. Under that mechanism, the expected recovery signal is slower net growth or a plateau—not an immediate fall in the total. The observed data match that pattern. Because the surveys enumerate population stocks rather than individual entries and exits, fewer newcomers is a supported interpretation of the slowdown, not a separately observed count.", "",
        md_table(paired_table, paired_table.columns.tolist(), {"exact_sign_test_p_two_sided": 4, "rho_distress_change_vs_log_count_change": 3, "p_distress_change_vs_log_count_change": 4}), "",
        "The paired exact sign tests do not distinguish the increase proportions from chance at conventional levels, and city-level distress-change correlations are inconsistent in direction (-0.382, -0.400 and +0.417). Those tests ask whether individual city rankings move together; they do not negate the aggregate stock-flow signal. The continuous panels show **expansion followed by growth deceleration and persistence**, rather than a rule that recovery must shrink the existing population.", "",
        "![Deterioration and recovery comparison](figures/exploratory_figure_6_better_economy_test.png)", "",
        "## 6. National economic indicators tested against multiple FSW markers", "",
        "National GDP growth, CPI inflation, per-capita income and open unemployment were tested against eight round-level FSW or survey markers. National values were kept at the survey-round level; they were not repeated over city rows as if they were independent observations. Exact two-sided permutation p-values were used because each correlation contains only three or four rounds.", "",
        md_table(macro_key, macro_key.columns.tolist(), {"spearman_rho": 3, "exact_permutation_p": 3, "p_fdr_bh_across_macro_marker_atlas": 3}), "",
        f"The strongest directional result is compositional. CPI inflation and the home-minus-street balance have rho={macro_row('CPI inflation', 'home minus street balance').spearman_rho:+.3f}; inflation also aligns positively with home share (rho={macro_row('CPI inflation', 'home share').spearman_rho:+.3f}). GDP growth aligns perfectly with street share (rho={macro_row('GDP growth', 'street share').spearman_rho:+.3f}), but only moderately and inversely with the combined home-minus-street balance (rho={macro_row('GDP growth', 'home minus street balance').spearman_rho:+.3f}). In plain terms, the high-inflation round is the round most tilted toward home rather than street work, while the high-growth round is most tilted toward street work.", "",
        f"Count markers point in the hypothesized direction but less cleanly: GDP growth versus median city mapped count is rho={macro_row('GDP growth', 'median city mapped total').spearman_rho:+.3f}, and inflation versus the same marker is rho={macro_row('CPI inflation', 'median city mapped total').spearman_rho:+.3f}. By contrast, kothikhana share rises across both deterioration and recovery (GDP rho={macro_row('GDP growth', 'kothikhana share').spearman_rho:+.3f}; inflation rho={macro_row('CPI inflation', 'kothikhana share').spearman_rho:+.3f}; per-capita income rho={macro_row('per-capita income', 'kothikhana share').spearman_rho:+.3f}), so it is useful cross-sectionally in 2011 but fails as a standalone longitudinal macro marker.", "",
        "No one of the 32 macro-marker correlations survives exact small-sample inference or FDR adjustment: the minimum exact p-value is 0.333 and the minimum adjusted p-value is 1.000. These tests reveal the direction and internal consistency of the available evidence; four rounds cannot establish a stable national time-series relationship.", "",
        md_table(macro_assumptions, macro_assumptions.columns.tolist()), "",
        "Density is not included in the longitudinal correlation atlas because only the 2011 source reports comparable city density. Cellphone share is likewise unavailable for a valid round correlation because it appears in only 2011 and 2014. Their absence is an evidence result, not a zero association.", "",
        "## 7. Replication and model checks", "",
        md_table(structural_display, structural_display.columns.tolist(), {"estimate_rho": 3, "p_value": 4, "p_fdr_bh": 4}), "",
        "The 2006-07 and 2011 home/street correlations are weak. The 2014 estimates are large and opposite for home and street, but they contain only four cities. The structural signal therefore appears more informative than density, but it does not replicate as a single stable home-or-street coefficient across all rounds.", "",
        md_table(nonlinear, nonlinear.columns.tolist(), {"loocv_rmse_density": 3, "rmse_relative_to_constant": 3}), "",
        "A constant-only model has the lowest leave-one-city-out density error. Linear, quadratic and cubic specifications all perform worse, so a hidden U-shaped or threshold density relationship is not supported.", "",
        "The standardized two-exposure models separate recent deterioration from chronic deprivation but leave wide intervals. They preserve the same descriptive directions—recent deterioration toward larger totals/scale and kothikhana share, chronic deprivation toward lower totals/scale and higher cellphone share—without providing a precise adjusted effect.", "",
        "## 8. What the evidence supports and contradicts", "",
        "### Supported within the assembled data", "",
        "- Recent deterioration and chronic deprivation identify different city economies.",
        "- Recent deterioration is more strongly related to absolute market size and organisational form than to FSW density.",
        "- Chronic deprivation is associated with smaller absolute markets and somewhat higher density.",
        "- The deterioration interval coincides with rapid common-city count expansion and a street-to-home/kothikhana compositional shift.",
        "- In both continuous-city panels, mapped-population growth is much faster during deterioration than during recovery.",
        "- Improved conditions coincide with strong growth deceleration and a plateau, while the accumulated population persists.",
        "- This pattern is consistent with fewer net newcomers during recovery combined with barriers to exit for existing workers.", "",
        "- Across the three typology rounds, inflation and growth align more consistently with the home-versus-street balance than with kothikhana share alone.", "",
        "### Contradicted or not supported", "",
        "- A simple claim that worse economic conditions produce higher FSW density is not supported.",
        "- A claim that recovery should immediately reduce the accumulated mapped FSW population is the wrong stock-flow expectation and is not supported.",
        "- A single stable city-level relationship between changes in reported distress and changes in mapped counts is not supported.",
        "- Nonlinear density models do not improve prediction.",
        "- Only one exploratory association meets a 5% FDR threshold across the full atlas: all-area deterioration versus kothikhana share.", "",
        "- None of the 32 round-level macro-marker correlations survives exact small-sample inference or FDR adjustment.",
        "- Density and cellphone share cannot be evaluated as multi-round macro markers with the available publications.", "",
        "### Best current synthesis", "",
        "> **Yes, the complete available Pakistani data show an economic signal, corresponding to protocol category C. Deterioration coincides with rapid FSW population expansion and a shift toward home-based organisation. Recovery coincides with a collapse in the population growth rate toward a plateau, not with an immediate reversal of the accumulated population. That plateau is consistent with fewer net newcomers while existing workers remain because exit is difficult.**", "",
        "## 9. Remaining biases capable of explaining the pattern", "",
        "- Mapping intensity, network reach and category visibility may change measured counts independently of the underlying population.",
        "- Surveillance cities are not a probability sample of all Pakistani cities.",
        "- City outcomes are paired with district urban socioeconomic measures.",
        "- Typology definitions overlap and mapping methods changed between rounds.",
        "- The four-city 2014 comparison is geographically narrow.",
        "- The 2016-17 source has an unresolved printed-total discrepancy and lacks city density and typology detail.",
        "- National macro indicators describe periods, not within-period city differences.",
        "- Supply pressure and client demand may move in opposite directions, muting the total density response.", "",
        "## 10. Is Paper 2 justified?", "",
        "Yes—but it should not be framed as validating FSW density as a standalone economic sentinel. A longitudinal Paper 2 is justified to test three specific propositions:", "",
        "1. whether downturns raise entry into sex work;",
        "2. whether recoveries reduce new entry while existing workers remain, producing persistence or hysteresis;",
        "3. whether economic shocks change home, street, cellphone and operator-mediated organisation more consistently than density.", "",
        "The next study should preregister these propositions, obtain stable city denominators and mapping-effort measures, and distinguish population change from improved enumeration.", "",
        "## 11. Reproducibility and validation status", "",
        f"The base data validation is {validation.get('status', 'UNKNOWN')} with {len(validation.get('checks', []))} executable checks. The exploratory validation is {str(exploratory_validation.get('status', 'unknown')).upper()} with {exploratory_validation.get('passed', 'NA')}/{exploratory_validation.get('checks', 'NA')} checks passed before this combined synthesis. The complete-report validation is written separately after generation.", "",
        "Core audit artifacts:", "",
        "- `results/diagnostics/validation_report.md`",
        "- `results/diagnostics/exploratory_validation.md`",
        "- `results/diagnostics/complete_validation.md`",
        "- `results/tables/exploratory_paired_count_tests.csv`",
        "- `results/tables/macro_marker_correlations.csv`",
        "- `results/tables/macro_marker_assumption_tests.csv`",
        "- `results/tables/stock_persistence_signal.csv`",
        "- `results/tables/exploratory_hypothesis_ledger.csv`", "",
        "The frozen plan remains in `docs/analysis_plan.md`; post-freeze analyses are explicitly labeled exploratory. No manuscript is created by this workflow.", "",
        "## 12. Source traceability", "",
        md_table(source_table, source_table.columns.tolist()), "",
        "Every acquired source is checksummed in `data/source_manifest.csv`. Page/table locators and extraction notes are retained in `docs/source_notes.md`, the processed data dictionary and the analytical scripts. The machine-readable claim ledger is `results/tables/current_findings.csv`.", "",
    ]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def build_knowledge_index() -> None:
    text = """# What we know

This repository contains the current reproducible evidence on relationships between socioeconomic conditions and mapped female sex work across available Pakistani surveillance rounds.

## Current answer

**Yes. The complete available Pakistani survey series shows an economic signal.** The central pattern is not that recovery makes the existing FSW population disappear. It is that deterioration coincides with rapid expansion, while recovery coincides with a sharp slowdown toward a plateau:

- in four cities observed continuously through 2014, annualized mapped-population growth slowed from 9.65% during deterioration to 5.30% during recovery;
- in six cities observed continuously through 2016-17, growth slowed from 14.39% to 0.87%;
- the plateau is consistent with fewer net newcomers after economic improvement while people already in sex work remain because leaving for other work is difficult;
- the surveys measure the population stock, not individual entries and exits, so the newcomer mechanism is consistent with the data but not separately counted;
- recent economic deterioration is also associated with larger absolute mapped markets and a shift from street toward home-based work, not with higher per-capita density;
- chronic deprivation is associated with smaller absolute markets but somewhat higher density;
- kothikhana/intermediary organisation and cellphone-based work show opposing economic patterns;
- the 2006-07 to 2011 deterioration coincides with rapid common-city expansion;
- later economic improvement does not reverse mapped counts, although growth slows and visible organisation changes;
- across the three rounds with typology data, inflation is most strongly aligned with a shift from street toward home-based work, while higher GDP growth aligns with street share;
- kothikhana share is informative within 2011 but is not a clean longitudinal macro marker because it rises during both deterioration and recovery;
- density and cellphone share cannot be tested across multiple rounds with the currently published measures.

The best available marker is therefore not a single density statistic. The evidence supports a **marker set**: the rate of change in comparable-city counts, whether that growth accelerates or plateaus, home-versus-street composition, kothikhana/intermediation as a cross-sectional organisation measure, and density only when a valid denominator is published. The complete series is the evidence base for this question; there is no other Pakistani longitudinal FSW dataset against which to defer the answer.

The authoritative numerical synthesis is [`results/analysis_summary.md`](results/analysis_summary.md).

## Repository map

- `docs/analysis_plan.md` — frozen confirmatory plan.
- `data/source_manifest.csv` — source provenance and checksums.
- `data/processed/paper1_city_round_master.csv` — 49-row master city-round dataset.
- `data/processed/paper1_2011_exploratory_features.csv` — acute/chronic, scale and network features.
- `results/analysis_summary.md` — complete current analysis.
- `results/confirmatory_analysis_summary.md` — primary and prespecified analysis only.
- `results/exploratory_report.md` — expanded hypothesis-generating analysis.
- `results/tables/` — all inspectable numerical outputs.
- `results/tables/current_findings.csv` — machine-readable ledger of current conclusions and evidence files.
- `results/tables/macro_marker_round_panel.csv` — survey-round economic indicators and multiple FSW markers.
- `results/tables/macro_marker_correlations.csv` — exact round-level correlation atlas.
- `results/tables/macro_marker_assumption_tests.csv` — explicit assumption-by-assumption verdicts.
- `results/tables/stock_persistence_signal.csv` — identical-city expansion, recovery and plateau comparison.
- `results/figures/` — primary, robustness and exploratory figures.
- `results/diagnostics/complete_validation.md` — end-to-end validation status.

## Reproduce

From PowerShell in the repository root:

```powershell
./scripts/run_full_analysis.ps1
```

The script rebuilds the dataset and all analyses, reruns base and exploratory validation, regenerates the complete synthesis, and runs final cross-output checks.

## Analysis boundary

The primary 2011 density analysis is confirmatory relative to the frozen plan. Acute-versus-chronic, network, count-versus-scale, nonlinear and economic-recovery analyses are exploratory and retained to define the next test. The repository does not contain a journal manuscript.
"""
    KNOWLEDGE.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    build_summary()
    build_knowledge_index()
    print(f"Wrote {SUMMARY} and {KNOWLEDGE}")
