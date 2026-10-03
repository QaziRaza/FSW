"""Build the explicitly exploratory, hypothesis-generating analysis layer.

This module does not alter the frozen confirmatory analysis. It distinguishes
acute reported deterioration, chronic deprivation, city/market scale, mapped
density, typology composition, and network organisation.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from analyse_primary import ols_hc3, spearman_values
from analyse_replication import fdr_bh

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
XML = ROOT / "data" / "raw" / "sexwork" / "2011" / "emmanuel_2013_fsw_structure.xml"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
DIAG = ROOT / "results" / "diagnostics"
for folder in (PROCESSED, TABLES, DIAG):
    folder.mkdir(parents=True, exist_ok=True)


def parse_network_table() -> pd.DataFrame:
    """Parse Table 2 from the cached full-text XML rather than transcribing it."""
    root = ET.parse(XML).getroot()
    table = next(
        node for node in root.findall(".//table-wrap")
        if node.attrib.get("id") == "SEXTRANS2013051062TB2"
    )
    rows: list[dict] = []
    for tr in table.findall(".//tbody/tr"):
        cells = [" ".join("".join(td.itertext()).split()) for td in tr.findall("td")]
        # Province is present only on the first city of each province because of rowspan.
        if not cells or "Total" in cells[0]:
            continue
        if len(cells) == 8:
            cells = cells[1:]
        if len(cells) != 7:
            raise ValueError(f"Unexpected network-table row: {cells}")
        city, *values = cells
        rows.append({
            "city": city,
            "network_operators": int(values[0].replace("\u2005", "").replace(" ", "")),
            "avg_home_fsw_per_operator": float(values[1]),
            "avg_kothikhana_fsw_per_operator": float(values[2]),
            "avg_networked_fsw_per_operator": float(values[3]),
            "avg_kothikhanas_per_operator": float(values[4]),
            "avg_kothikhana_fsw_per_kothikhana": float(values[5]),
            "source_file": str(XML.relative_to(ROOT)).replace("\\", "/"),
            "source_locator": "Emmanuel et al. 2013, Table 2",
        })
    network = pd.DataFrame(rows)
    network.to_csv(PROCESSED / "paper1_2011_network_structure.csv", index=False)
    return network


def build_macro_context() -> pd.DataFrame:
    """Encode reviewed national survey values as context, not city predictors."""
    rows = [
        {
            "round_id": "2006_07", "survey_year": "2006-07", "real_gdp_growth_pct": 7.00,
            "cpi_inflation_pct": 7.90, "cpi_period": "Jul-Apr", "open_unemployment_pct": 6.20,
            "unemployment_period": "2005-06", "per_capita_income_usd": 925,
            "source_file": "data/raw/economic/economic_surveys/pakistan_economic_survey_2006_07_overview.pdf",
            "source_locator": "PDF pp. 1 (growth), 5 (income), 6 (inflation), 27 (open unemployment)",
        },
        {
            "round_id": "2011", "survey_year": "2010-11", "real_gdp_growth_pct": 2.40,
            "cpi_inflation_pct": 14.00, "cpi_period": "Jul-May", "open_unemployment_pct": 5.60,
            "unemployment_period": "2009-10", "per_capita_income_usd": 1254,
            "source_file": "data/raw/economic/economic_surveys/pakistan_economic_survey_2010_11_overview.pdf",
            "source_locator": "PDF pp. 1 (shock/growth), 4 (inflation), 9 (income), 17 (unemployment)",
        },
        {
            "round_id": "2014", "survey_year": "2014-15", "real_gdp_growth_pct": 4.24,
            "cpi_inflation_pct": 4.80, "cpi_period": "Jul-Apr", "open_unemployment_pct": 6.00,
            "unemployment_period": "2013-14", "per_capita_income_usd": 1512,
            "source_file": "data/raw/economic/economic_surveys/pakistan_economic_survey_2014_15_overview.pdf",
            "source_locator": "PDF pp. 2 (growth), 6 (income), 10 (inflation), 12 (unemployment)",
        },
        {
            "round_id": "2016_17", "survey_year": "2016-17", "real_gdp_growth_pct": 5.28,
            "cpi_inflation_pct": 4.09, "cpi_period": "Jul-Apr", "open_unemployment_pct": np.nan,
            "unemployment_period": "not encoded", "per_capita_income_usd": 1629,
            "source_file": "data/raw/economic/economic_surveys/pakistan_economic_survey_2016_17_overview.pdf",
            "source_locator": "PDF pp. 1 (growth), 5 (inflation), 10 (income)",
        },
    ]
    macro = pd.DataFrame(rows)
    macro.to_csv(PROCESSED / "paper1_round_macro_context.csv", index=False)
    return macro


def zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / series.std(ddof=1)


def exact_sign_test_p(increases: int, decreases: int) -> float:
    """Two-sided exact sign test, excluding ties."""
    n = increases + decreases
    if n == 0:
        return np.nan
    tail = sum(math.comb(n, i) for i in range(min(increases, decreases) + 1)) / (2**n)
    return min(1.0, 2 * tail)


def build_2011_features(master: pd.DataFrame, network: pd.DataFrame) -> pd.DataFrame:
    d = master[master.round_id == "2011"].copy().sort_values("city").reset_index(drop=True)
    chronic_components = [
        "poverty_headcount_urban_pct",
        "female_illiteracy_urban_pct",
        "sanitation_deprivation_urban_pct",
    ]
    for column in chronic_components:
        d[f"z_{column}"] = zscore(d[column])
    d["chronic_deprivation_index"] = d[[f"z_{c}" for c in chronic_components]].mean(axis=1)
    d["chronic_deprivation_index_z"] = zscore(d.chronic_deprivation_index)
    d["acute_distress_z"] = zscore(d.economic_distress_urban_pct)
    d["log_fsw_total"] = np.log(d.fsw_total)
    d["adult_male_population_implied"] = d.fsw_total * 1000 / d.fsw_density_per_1000_adult_men
    d["log_adult_male_population_implied"] = np.log(d.adult_male_population_implied)
    acute_high = d.economic_distress_urban_pct >= d.economic_distress_urban_pct.median()
    chronic_high = d.chronic_deprivation_index >= d.chronic_deprivation_index.median()
    d["economic_archetype"] = np.select(
        [acute_high & chronic_high, acute_high & ~chronic_high, ~acute_high & chronic_high],
        ["high acute / high chronic", "high acute / low chronic", "low acute / high chronic"],
        default="low acute / low chronic",
    )
    d = d.merge(network.drop(columns=["source_file", "source_locator"]), on="city", how="left", validate="one_to_one")
    d.to_csv(PROCESSED / "paper1_2011_exploratory_features.csv", index=False, float_format="%.8f")
    archetype_columns = [
        "city", "province", "economic_distress_urban_pct", "chronic_deprivation_index",
        "economic_archetype", "fsw_total", "fsw_density_per_1000_adult_men",
        "home_share_pct", "street_share_pct", "kothikhana_share_pct", "cellphone_share_pct",
    ]
    d[archetype_columns].to_csv(TABLES / "exploratory_city_archetypes.csv", index=False, float_format="%.6f")
    return d


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    exposures = {
        "acute urban deterioration": "economic_distress_urban_pct",
        "acute all-area deterioration": "economic_distress_all_pct",
        "urban poverty": "poverty_headcount_urban_pct",
        "female illiteracy": "female_illiteracy_urban_pct",
        "sanitation deprivation": "sanitation_deprivation_urban_pct",
        "chronic deprivation index": "chronic_deprivation_index",
    }
    outcomes = {
        "mapped density": "fsw_density_per_1000_adult_men",
        "mapped total": "fsw_total",
        "implied adult-male population": "adult_male_population_implied",
        "brothel share": "brothel_share_pct",
        "street share": "street_share_pct",
        "home share": "home_share_pct",
        "kothikhana share": "kothikhana_share_pct",
        "cellphone share": "cellphone_share_pct",
        "other share": "other_share_pct",
    }
    rows = []
    for exposure_label, exposure in exposures.items():
        for outcome_label, outcome in outcomes.items():
            pair = df[[exposure, outcome]].dropna()
            rho, p = spearman_values(pair[exposure].to_numpy(float), pair[outcome].to_numpy(float))
            rows.append({
                "family": "2011_exposure_outcome_atlas", "exposure": exposure,
                "exposure_label": exposure_label, "outcome": outcome,
                "outcome_label": outcome_label, "method": "Spearman", "n": len(pair),
                "estimate_rho": rho, "p_value_exploratory": p,
            })
    out = pd.DataFrame(rows)
    out["p_fdr_bh_within_atlas"] = fdr_bh(out.p_value_exploratory)
    out.to_csv(TABLES / "exploratory_2011_association_atlas.csv", index=False, float_format="%.6f")
    return out


def economic_intercorrelations(df: pd.DataFrame) -> pd.DataFrame:
    variables = [
        "economic_distress_urban_pct", "economic_distress_all_pct",
        "poverty_headcount_urban_pct", "female_illiteracy_urban_pct",
        "sanitation_deprivation_urban_pct",
    ]
    rows = []
    for i, left in enumerate(variables):
        for right in variables[i + 1:]:
            pair = df[[left, right]].dropna()
            rho, p = spearman_values(pair[left].to_numpy(float), pair[right].to_numpy(float))
            rows.append({"variable_1": left, "variable_2": right, "n": len(pair), "estimate_rho": rho, "p_value_exploratory": p})
    out = pd.DataFrame(rows)
    out["p_fdr_bh_within_family"] = fdr_bh(out.p_value_exploratory)
    out.to_csv(TABLES / "exploratory_economic_intercorrelations.csv", index=False, float_format="%.6f")
    return out


def network_correlations(df: pd.DataFrame) -> pd.DataFrame:
    exposures = {
        "acute urban deterioration": "economic_distress_urban_pct",
        "chronic deprivation index": "chronic_deprivation_index",
        "mapped density": "fsw_density_per_1000_adult_men",
        "mapped total": "fsw_total",
    }
    outcomes = [
        "network_operators", "avg_home_fsw_per_operator", "avg_kothikhana_fsw_per_operator",
        "avg_networked_fsw_per_operator", "avg_kothikhanas_per_operator",
        "avg_kothikhana_fsw_per_kothikhana",
    ]
    rows = []
    for exposure_label, exposure in exposures.items():
        for outcome in outcomes:
            pair = df[[exposure, outcome]].dropna()
            rho, p = spearman_values(pair[exposure].to_numpy(float), pair[outcome].to_numpy(float))
            rows.append({"exposure": exposure, "exposure_label": exposure_label, "network_outcome": outcome, "n": len(pair), "estimate_rho": rho, "p_value_exploratory": p})
    out = pd.DataFrame(rows)
    out["p_fdr_bh_within_family"] = fdr_bh(out.p_value_exploratory)
    out.to_csv(TABLES / "exploratory_2011_network_associations.csv", index=False, float_format="%.6f")
    return out


def two_exposure_models(df: pd.DataFrame) -> pd.DataFrame:
    outcomes = {
        "mapped_density": "fsw_density_per_1000_adult_men",
        "log_mapped_total": "log_fsw_total",
        "log_implied_population_scale": "log_adult_male_population_implied",
        "street_share": "street_share_pct",
        "home_share": "home_share_pct",
        "kothikhana_share": "kothikhana_share_pct",
        "cellphone_share": "cellphone_share_pct",
    }
    rows = []
    X = np.column_stack([np.ones(len(df)), df.acute_distress_z, df.chronic_deprivation_index_z])
    for model, outcome in outcomes.items():
        y = zscore(df[outcome]).to_numpy(float)
        estimates, extras = ols_hc3(y, X, ["const", "acute_distress_z", "chronic_deprivation_z"])
        for estimate in estimates:
            estimate.update({"model": model, "outcome": outcome, "n": len(df), "r_squared": extras["r_squared"], "coefficient_scale": "standardized"})
            rows.append(estimate)
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exploratory_two_exposure_models.csv", index=False, float_format="%.6f")
    return out


def nonlinear_cv(df: pd.DataFrame) -> pd.DataFrame:
    x = df.economic_distress_urban_pct.to_numpy(float)
    y = df.fsw_density_per_1000_adult_men.to_numpy(float)
    x = (x - x.mean()) / x.std(ddof=1)
    rows = []
    for degree in range(4):
        predictions = []
        for held_out in range(len(x)):
            keep = np.arange(len(x)) != held_out
            coefficients = np.polyfit(x[keep], y[keep], degree)
            predictions.append(float(np.polyval(coefficients, x[held_out])))
        rmse = math.sqrt(float(np.mean((y - np.asarray(predictions)) ** 2)))
        rows.append({"model": "constant" if degree == 0 else f"polynomial_degree_{degree}", "degree": degree, "loocv_rmse_density": rmse, "n": len(x)})
    out = pd.DataFrame(rows)
    out["rmse_relative_to_constant"] = out.loocv_rmse_density / out.loc[out.degree == 0, "loocv_rmse_density"].iloc[0]
    out.to_csv(TABLES / "exploratory_nonlinear_loocv.csv", index=False, float_format="%.6f")
    return out


def cross_round_transitions(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    periods = [("2006_07", "2011"), ("2011", "2014")]
    fields = [
        "economic_distress_urban_pct", "female_illiteracy_urban_pct",
        "sanitation_deprivation_urban_pct", "home_share_pct", "street_share_pct",
        "kothikhana_share_pct", "cellphone_share_pct",
    ]
    detail, summaries, tests = [], [], []
    for start, end in periods:
        a = master[master.round_id == start].set_index("city_id")
        b = master[master.round_id == end].set_index("city_id")
        overlap = a.index.intersection(b.index)
        for city_id in overlap:
            row = {"comparison": f"{start}_to_{end}", "city_id": city_id, "city": b.loc[city_id, "city"]}
            for field in fields:
                row[f"{field}_start"] = a.loc[city_id, field]
                row[f"{field}_end"] = b.loc[city_id, field]
                row[f"delta_{field}"] = b.loc[city_id, field] - a.loc[city_id, field]
            detail.append(row)
        part = pd.DataFrame([r for r in detail if r["comparison"] == f"{start}_to_{end}"])
        summary = {"comparison": f"{start}_to_{end}", "paired_cities": len(part)}
        for field in fields:
            summary[f"median_delta_{field}"] = part[f"delta_{field}"].median()
        summaries.append(summary)
        exposures = ["economic_distress_urban_pct", "female_illiteracy_urban_pct", "sanitation_deprivation_urban_pct"]
        outcomes = ["home_share_pct", "street_share_pct", "kothikhana_share_pct", "cellphone_share_pct"]
        for exposure in exposures:
            for outcome in outcomes:
                pair = part[[f"delta_{exposure}", f"delta_{outcome}"]].dropna()
                if len(pair) >= 3:
                    rho, p = spearman_values(pair.iloc[:, 0].to_numpy(float), pair.iloc[:, 1].to_numpy(float))
                else:
                    rho, p = np.nan, np.nan
                tests.append({
                    "comparison": f"{start}_to_{end}", "exposure_change": exposure,
                    "outcome_change": outcome, "n": len(pair), "estimate_rho": rho,
                    "p_value_exploratory": p if len(pair) >= 6 else np.nan,
                    "inference_status": "exploratory" if len(pair) >= 6 else "descriptive_only_n_below_6",
                })
    detail_df, summary_df, tests_df = pd.DataFrame(detail), pd.DataFrame(summaries), pd.DataFrame(tests)
    detail_df.to_csv(TABLES / "exploratory_cross_round_city_transitions.csv", index=False, float_format="%.6f")
    summary_df.to_csv(TABLES / "exploratory_cross_round_transition_summary.csv", index=False, float_format="%.6f")
    tests_df.to_csv(TABLES / "exploratory_cross_round_change_associations.csv", index=False, float_format="%.6f")
    return detail_df, summary_df, tests_df


def round_descriptives(master: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    analytic = master[master.round_id.isin(["2006_07", "2011", "2014"])]
    out = analytic.groupby("round_id").agg(
        cities=("city_id", "size"), mapped_fsw_total=("fsw_total", "sum"),
        median_acute_distress_pct=("economic_distress_urban_pct", "median"),
        median_urban_poverty_pct=("poverty_headcount_urban_pct", "median"),
        median_female_illiteracy_pct=("female_illiteracy_urban_pct", "median"),
        median_sanitation_deprivation_pct=("sanitation_deprivation_urban_pct", "median"),
        median_home_share_pct=("home_share_pct", "median"),
        median_street_share_pct=("street_share_pct", "median"),
        median_kothikhana_share_pct=("kothikhana_share_pct", "median"),
        median_cellphone_share_pct=("cellphone_share_pct", "median"),
    ).reset_index().merge(macro, on="round_id", how="left", validate="one_to_one")
    out.to_csv(TABLES / "exploratory_round_economic_mapping_context.csv", index=False, float_format="%.6f")
    return out


def macro_improvement_contrasts(master: pd.DataFrame, macro: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare mapped outcomes during deterioration and subsequent improvement.

    Common-city changes are used so changing round coverage does not mechanically
    determine the count comparison. The 2016-17 contrast uses printed city rows;
    the source's inconsistent printed grand total is not used.
    """
    comparisons = [
        ("2006_07", "2011", "deterioration benchmark"),
        ("2011", "2014", "improving national conditions"),
        ("2011", "2016_17", "sustained improved national conditions"),
    ]
    interval_years = {"2006_07_to_2011": 4.5, "2011_to_2014": 3.0, "2011_to_2016_17": 5.5}
    macro_i = macro.set_index("round_id")
    summary_rows, city_rows, test_rows = [], [], []
    for start, end, interpretation in comparisons:
        a = master[master.round_id == start].set_index("city_id")
        b = master[master.round_id == end].set_index("city_id")
        overlap = a.index.intersection(b.index)
        paired_changes, period_city_rows = [], []
        for city_id in overlap:
            start_count = float(a.loc[city_id, "fsw_total"])
            end_count = float(b.loc[city_id, "fsw_total"])
            pct_change = 100 * (end_count - start_count) / start_count
            paired_changes.append(pct_change)
            start_distress = float(a.loc[city_id, "economic_distress_urban_pct"]) if pd.notna(a.loc[city_id, "economic_distress_urban_pct"]) else np.nan
            end_distress = float(b.loc[city_id, "economic_distress_urban_pct"]) if pd.notna(b.loc[city_id, "economic_distress_urban_pct"]) else np.nan
            record = {
                "comparison": f"{start}_to_{end}", "macro_direction": interpretation,
                "city_id": city_id, "city": b.loc[city_id, "city"],
                "fsw_total_start": start_count, "fsw_total_end": end_count,
                "fsw_total_change": end_count - start_count,
                "fsw_total_pct_change": pct_change,
                "log_fsw_total_ratio": math.log(end_count / start_count),
                "economic_distress_urban_start_pct": start_distress,
                "economic_distress_urban_end_pct": end_distress,
                "delta_economic_distress_urban_pct": end_distress - start_distress,
            }
            city_rows.append(record)
            period_city_rows.append(record)
        start_total = float(a.loc[overlap, "fsw_total"].sum())
        end_total = float(b.loc[overlap, "fsw_total"].sum())
        comparison = f"{start}_to_{end}"
        years = interval_years[comparison]
        increases = int(sum(value > 0 for value in paired_changes))
        decreases = int(sum(value < 0 for value in paired_changes))
        distress_pair = pd.DataFrame(period_city_rows)[["delta_economic_distress_urban_pct", "log_fsw_total_ratio"]].dropna()
        if len(distress_pair) >= 3:
            change_rho, change_p = spearman_values(
                distress_pair.delta_economic_distress_urban_pct.to_numpy(float),
                distress_pair.log_fsw_total_ratio.to_numpy(float),
            )
        else:
            change_rho, change_p = np.nan, np.nan
        row = {
            "comparison": comparison, "macro_direction": interpretation,
            "common_cities": len(overlap),
            "local_economic_period_start": ";".join(sorted(a.loc[overlap, "economic_period"].dropna().astype(str).unique())),
            "local_economic_period_end": ";".join(sorted(b.loc[overlap, "economic_period"].dropna().astype(str).unique())),
            "real_gdp_growth_start_pct": macro_i.loc[start, "real_gdp_growth_pct"],
            "real_gdp_growth_end_pct": macro_i.loc[end, "real_gdp_growth_pct"],
            "delta_real_gdp_growth_pp": macro_i.loc[end, "real_gdp_growth_pct"] - macro_i.loc[start, "real_gdp_growth_pct"],
            "cpi_inflation_start_pct": macro_i.loc[start, "cpi_inflation_pct"],
            "cpi_inflation_end_pct": macro_i.loc[end, "cpi_inflation_pct"],
            "delta_cpi_inflation_pp": macro_i.loc[end, "cpi_inflation_pct"] - macro_i.loc[start, "cpi_inflation_pct"],
            "per_capita_income_start_usd": macro_i.loc[start, "per_capita_income_usd"],
            "per_capita_income_end_usd": macro_i.loc[end, "per_capita_income_usd"],
            "delta_per_capita_income_usd": macro_i.loc[end, "per_capita_income_usd"] - macro_i.loc[start, "per_capita_income_usd"],
            "common_city_fsw_total_start": start_total,
            "common_city_fsw_total_end": end_total,
            "aggregate_fsw_total_pct_change": 100 * (end_total - start_total) / start_total,
            "interval_years_approx": years,
            "annualized_aggregate_fsw_change_pct": 100 * ((end_total / start_total) ** (1 / years) - 1),
            "median_city_fsw_pct_change": float(np.median(paired_changes)),
            "cities_with_count_increase": increases,
            "cities_with_count_decrease": decreases,
            "exact_sign_test_p_two_sided": exact_sign_test_p(increases, decreases),
            "paired_n_distress_count_change": len(distress_pair),
            "rho_distress_change_vs_log_count_change": change_rho,
            "p_distress_change_vs_log_count_change": change_p if len(distress_pair) >= 6 else np.nan,
        }
        paired_fields = [
            "economic_distress_urban_pct", "home_share_pct", "street_share_pct",
            "kothikhana_share_pct", "cellphone_share_pct",
        ]
        for field in paired_fields:
            pair = pd.DataFrame({"start": a.loc[overlap, field], "end": b.loc[overlap, field]}).dropna()
            row[f"paired_n_{field}"] = len(pair)
            row[f"median_delta_{field}"] = float((pair.end - pair.start).median()) if len(pair) else np.nan
        summary_rows.append(row)
    summary, cities = pd.DataFrame(summary_rows), pd.DataFrame(city_rows)
    test_columns = [
        "comparison", "macro_direction", "common_cities", "aggregate_fsw_total_pct_change",
        "annualized_aggregate_fsw_change_pct", "median_city_fsw_pct_change",
        "cities_with_count_increase", "cities_with_count_decrease", "exact_sign_test_p_two_sided",
        "paired_n_distress_count_change", "rho_distress_change_vs_log_count_change",
        "p_distress_change_vs_log_count_change",
    ]
    tests = summary[test_columns].copy()
    tests["count_change_test"] = "exact two-sided sign test"
    tests["distress_change_test"] = "Spearman on district-distress change and log mapped-count ratio"
    summary.to_csv(TABLES / "exploratory_macro_improvement_contrasts.csv", index=False, float_format="%.6f")
    cities.to_csv(TABLES / "exploratory_macro_improvement_city_counts.csv", index=False, float_format="%.6f")
    tests.to_csv(TABLES / "exploratory_paired_count_tests.csv", index=False, float_format="%.6f")
    return summary, cities, tests


def hypothesis_ledger() -> pd.DataFrame:
    rows = [
        {
            "hypothesis": "Acute-versus-chronic distinction",
            "observed_pattern": "Reported deterioration is inversely associated with poverty, illiteracy and sanitation deprivation; it is not a general deprivation score.",
            "competing_explanation": "Response style, district-city mismatch or survey measurement may create the contrast.",
            "later_test": "Use repeated city-level economic shocks and levels from independent administrative or price/labour data.",
        },
        {
            "hypothesis": "Market-scale channel",
            "observed_pattern": "Acute deterioration rises with mapped FSW totals and implied adult-male population, but not mapped density.",
            "competing_explanation": "Large-city mapping effort or visibility can jointly inflate counts and measured distress.",
            "later_test": "Model counts with independent population offsets and measured mapping effort across more cities/rounds.",
        },
        {
            "hypothesis": "Intermediation/venue channel",
            "observed_pattern": "Acute deterioration aligns with kothikhana share and kothikhana FSWs per operator, while cellphone share declines.",
            "competing_explanation": "Compositional dependence, overlapping typologies and city-specific mapping practice.",
            "later_test": "Use worker-level transitions or repeated network mapping with mutually exclusive typology definitions.",
        },
        {
            "hypothesis": "Chronic vulnerability channel",
            "observed_pattern": "Chronic deprivation is weakly positive with density but strongly negative with absolute mapped total.",
            "competing_explanation": "A small-city denominator effect can create higher density without more workers.",
            "later_test": "Estimate density and count models jointly with reliable adult-population denominators and urbanicity controls.",
        },
        {
            "hypothesis": "Mapping-visibility artifact",
            "observed_pattern": "Large cross-round typology shifts do not track city-level economic change consistently.",
            "competing_explanation": "Changing mapping instruments, coverage and visibility may dominate real behavioural change.",
            "later_test": "Recover field protocols, effort metrics and stable-city re-enumeration data before treating round differences as trends.",
        },
        {
            "hypothesis": "Asymmetric recovery or persistence",
            "observed_pattern": "The 2006-07 to 2011 deterioration coincided with a 66% expansion in the ten-city mapped total, but improving post-2011 macro conditions did not reduce common-city totals; composition partly reversed instead.",
            "competing_explanation": "Changes in mapping intensity or coverage can produce apparent persistence even if the underlying population changed.",
            "later_test": "Use repeated enumeration with stable methods to test whether downturn expansions persist after employment, growth and inflation recover.",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exploratory_hypothesis_ledger.csv", index=False)
    return out


def run() -> dict:
    master = pd.read_csv(MASTER)
    network = parse_network_table()
    macro = build_macro_context()
    features = build_2011_features(master, network)
    atlas = correlation_table(features)
    economic = economic_intercorrelations(features)
    networks = network_correlations(features)
    models = two_exposure_models(features)
    cv = nonlinear_cv(features)
    _, transitions, _ = cross_round_transitions(master)
    rounds = round_descriptives(master, macro)
    improvement, improvement_cities, improvement_tests = macro_improvement_contrasts(master, macro)
    hypotheses = hypothesis_ledger()
    payload = {
        "status": "exploratory_hypothesis_generating",
        "cities_2011": len(features), "network_rows": len(network),
        "atlas_tests": len(atlas), "network_tests": len(networks),
        "hypotheses": len(hypotheses),
        "best_nonlinear_cv_model": cv.loc[cv.loocv_rmse_density.idxmin(), "model"],
        "cross_round_comparisons": transitions.comparison.tolist(),
        "round_context_rows": len(rounds),
        "macro_improvement_contrasts": len(improvement),
        "macro_improvement_paired_city_rows": len(improvement_cities),
        "paired_count_tests": len(improvement_tests),
        "acute_chronic_spearman": float(economic.loc[
            (economic.variable_1 == "economic_distress_urban_pct") &
            (economic.variable_2 == "poverty_headcount_urban_pct"), "estimate_rho"
        ].iloc[0]),
    }
    (DIAG / "exploratory_analysis_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
