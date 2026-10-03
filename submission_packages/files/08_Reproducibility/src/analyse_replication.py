"""Run prespecified structural replication and exploratory change analyses."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from analyse_primary import spearman_values

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
TABLES = ROOT / "results" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def fdr_bh(p_values: pd.Series) -> list[float]:
    """Benjamini-Hochberg adjusted p-values, preserving input order."""
    p = p_values.to_numpy(float)
    order = p.argsort()
    ranked = p[order]
    adjusted = ranked * len(p) / (pd.Series(range(1, len(p) + 1)).to_numpy())
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1].clip(max=1)
    original = [0.0] * len(p)
    for sorted_position, original_position in enumerate(order):
        original[original_position] = float(adjusted[sorted_position])
    return original


def run() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(DATA)
    tests = []
    for round_id in ["2006_07", "2011", "2014"]:
        part = df[df.round_id == round_id]
        for outcome in ["home_share_pct", "street_share_pct"]:
            pair = part[["economic_distress_urban_pct", outcome]].dropna()
            estimate, p_value = spearman_values(pair.economic_distress_urban_pct.to_numpy(float), pair[outcome].to_numpy(float))
            tests.append({
                "round_id": round_id, "exposure": "economic_distress_urban_pct",
                "outcome": outcome, "method": "Spearman", "n": len(pair),
                "estimate_rho": estimate, "p_value": p_value,
            })
    results = pd.DataFrame(tests)
    results["p_fdr_bh"] = fdr_bh(results.p_value)
    results.to_csv(TABLES / "table_structural_replication.csv", index=False, float_format="%.6f")

    a = df[df.round_id == "2006_07"].set_index("city_id")
    b = df[df.round_id == "2011"].set_index("city_id")
    overlap = a.index.intersection(b.index)
    change = pd.DataFrame(index=overlap)
    change["city"] = b.loc[overlap, "city"]
    change["distress_rank_2006"] = a.loc[overlap, "economic_distress_urban_pct"].rank(pct=True)
    change["distress_rank_2011"] = b.loc[overlap, "economic_distress_urban_pct"].rank(pct=True)
    change["delta_distress_percentile"] = change.distress_rank_2011 - change.distress_rank_2006
    for outcome in ["home_share_pct", "street_share_pct"]:
        change[f"{outcome}_2006"] = a.loc[overlap, outcome]
        change[f"{outcome}_2011"] = b.loc[overlap, outcome]
        change[f"delta_{outcome}"] = change[f"{outcome}_2011"] - change[f"{outcome}_2006"]
    change = change.reset_index()
    change.to_csv(TABLES / "table_cross_round_change_data.csv", index=False, float_format="%.6f")

    change_tests = []
    for outcome in ["home_share_pct", "street_share_pct"]:
        estimate, p_value = spearman_values(change.delta_distress_percentile.to_numpy(float), change[f"delta_{outcome}"].to_numpy(float))
        change_tests.append({
            "comparison": "2006_07_to_2011", "exposure": "change_in_within_round_distress_percentile",
            "outcome": f"delta_{outcome}", "method": "Spearman", "n": len(change),
            "estimate_rho": estimate, "p_value": p_value,
            "status": "exploratory_small_paired_sample",
        })
    change_results = pd.DataFrame(change_tests)
    change_results.to_csv(TABLES / "table_cross_round_change_tests.csv", index=False, float_format="%.6f")

    descriptive = df.groupby("round_id").agg(
        cities=("city_id", "size"), total_mapped_fsw=("fsw_total", "sum"),
        median_home_share_pct=("home_share_pct", "median"),
        median_street_share_pct=("street_share_pct", "median"),
        median_distress_urban_pct=("economic_distress_urban_pct", "median"),
    ).reset_index()
    descriptive.to_csv(TABLES / "table_round_descriptives.csv", index=False, float_format="%.6f")
    return results, change_results


if __name__ == "__main__":
    replication, changes = run()
    print(replication.to_string(index=False))
    print("\nExploratory change tests\n", changes.to_string(index=False))
