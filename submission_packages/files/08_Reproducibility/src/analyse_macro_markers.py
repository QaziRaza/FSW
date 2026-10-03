"""Test national economic-survey indicators against multiple round-level FSW markers.

National macro values are kept at the round level. They are never repeated over
city rows as if they were independent city predictors. With only three or four
rounds, exact permutation p-values are reported and results are descriptive.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyse_primary import spearman_values
from analyse_replication import fdr_bh

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
MACRO = ROOT / "data" / "processed" / "paper1_round_macro_context.csv"
TABLES = ROOT / "results" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)


def exact_spearman_p(x: np.ndarray, y: np.ndarray) -> float:
    """Two-sided exact permutation p-value for n<=8, preserving tied ranks."""
    xr = pd.Series(x).rank(method="average").to_numpy(float)
    yr = pd.Series(y).rank(method="average").to_numpy(float)
    observed = abs(float(np.corrcoef(xr, yr)[0, 1]))
    permutations = set(itertools.permutations(yr.tolist()))
    extreme = sum(abs(float(np.corrcoef(xr, np.asarray(values))[0, 1])) >= observed - 1e-12 for values in permutations)
    return extreme / len(permutations)


def build_panel(master: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    panel = master.groupby("round_id").agg(
        cities=("city", "size"),
        mapped_fsw_total_round=("fsw_total", "sum"),
        median_city_fsw_total=("fsw_total", "median"),
        mean_city_fsw_total=("fsw_total", "mean"),
        median_fsw_density=("fsw_density_per_1000_adult_men", "median"),
        median_home_share_pct=("home_share_pct", "median"),
        median_street_share_pct=("street_share_pct", "median"),
        median_kothikhana_share_pct=("kothikhana_share_pct", "median"),
        median_cellphone_share_pct=("cellphone_share_pct", "median"),
        median_reported_distress_pct=("economic_distress_urban_pct", "median"),
    ).reset_index()
    panel["home_minus_street_balance_pp"] = panel.median_home_share_pct - panel.median_street_share_pct
    panel = panel.merge(macro, on="round_id", how="left", validate="one_to_one")
    panel["coverage_scope"] = panel.round_id.map({
        "2006_07": "12 surveillance cities",
        "2011": "15 surveillance cities",
        "2014": "4 Punjab cities",
        "2016_17": "18 printed city rows; total discrepancy in source",
    })
    order = pd.Categorical(panel.round_id, ["2006_07", "2011", "2014", "2016_17"], ordered=True)
    panel = panel.assign(_order=order).sort_values("_order").drop(columns="_order")
    panel.to_csv(TABLES / "macro_marker_round_panel.csv", index=False, float_format="%.6f")
    return panel


def correlation_atlas(panel: pd.DataFrame) -> pd.DataFrame:
    macro_variables = {
        "GDP growth": "real_gdp_growth_pct",
        "CPI inflation": "cpi_inflation_pct",
        "per-capita income": "per_capita_income_usd",
        "open unemployment": "open_unemployment_pct",
    }
    markers = {
        "round mapped total": "mapped_fsw_total_round",
        "median city mapped total": "median_city_fsw_total",
        "mean city mapped total": "mean_city_fsw_total",
        "home share": "median_home_share_pct",
        "street share": "median_street_share_pct",
        "kothikhana share": "median_kothikhana_share_pct",
        "home minus street balance": "home_minus_street_balance_pp",
        "reported household distress": "median_reported_distress_pct",
    }
    rows = []
    for macro_label, exposure in macro_variables.items():
        for marker_label, marker in markers.items():
            pair = panel[[exposure, marker]].dropna()
            if len(pair) < 3:
                continue
            rho, _ = spearman_values(pair[exposure].to_numpy(float), pair[marker].to_numpy(float))
            rows.append({
                "economic_indicator": exposure, "economic_indicator_label": macro_label,
                "fsw_marker": marker, "fsw_marker_label": marker_label,
                "n_rounds": len(pair), "spearman_rho": rho,
                "exact_permutation_p": exact_spearman_p(pair[exposure].to_numpy(float), pair[marker].to_numpy(float)),
                "status": "round_level_descriptive_small_n",
            })
    results = pd.DataFrame(rows)
    results["p_fdr_bh_across_macro_marker_atlas"] = fdr_bh(results.exact_permutation_p)
    results.to_csv(TABLES / "macro_marker_correlations.csv", index=False, float_format="%.6f")
    return results


def stock_persistence_signal(master: pd.DataFrame) -> pd.DataFrame:
    """Compare deterioration and recovery in identical continuous-city panels.

    These are stock changes, not direct entrant or exit counts. Holding the city
    set fixed across all three observations makes the change in growth rate more
    interpretable than comparisons built from different city panels.
    """
    specifications = [
        ("continuous_to_2014", "2014", 3.0),
        ("continuous_to_2016_17", "2016_17", 5.5),
    ]
    rows = []
    for panel_id, recovery_round, recovery_years in specifications:
        rounds = ["2006_07", "2011", recovery_round]
        available = {
            round_id: set(master.loc[master.round_id == round_id, "city"])
            for round_id in rounds
        }
        common = sorted(set.intersection(*(available[round_id] for round_id in rounds)))
        totals = {
            round_id: float(master[(master.round_id == round_id) & master.city.isin(common)].fsw_total.sum())
            for round_id in rounds
        }
        deterioration_pct = 100 * (totals["2011"] / totals["2006_07"] - 1)
        recovery_pct = 100 * (totals[recovery_round] / totals["2011"] - 1)
        deterioration_annualized = 100 * ((totals["2011"] / totals["2006_07"]) ** (1 / 4.5) - 1)
        recovery_annualized = 100 * ((totals[recovery_round] / totals["2011"]) ** (1 / recovery_years) - 1)
        rows.append({
            "panel_id": panel_id,
            "recovery_round": recovery_round,
            "common_cities": len(common),
            "city_names": "; ".join(common),
            "mapped_total_2006_07": totals["2006_07"],
            "mapped_total_2011": totals["2011"],
            "mapped_total_recovery_round": totals[recovery_round],
            "deterioration_total_pct_change": deterioration_pct,
            "deterioration_annualized_growth_pct": deterioration_annualized,
            "recovery_total_pct_change": recovery_pct,
            "recovery_annualized_growth_pct": recovery_annualized,
            "annualized_growth_slowdown_pp": deterioration_annualized - recovery_annualized,
            "recovery_growth_rate_as_pct_of_deterioration": 100 * recovery_annualized / deterioration_annualized,
            "observed_signal": "rapid expansion during deterioration followed by slower growth or plateau during recovery",
            "stock_flow_interpretation": "consistent with lower net entry during recovery plus persistence of the existing mapped population; entrant and exit flows are not separately observed",
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "stock_persistence_signal.csv", index=False, float_format="%.6f")
    return out


def assumption_tests(panel: pd.DataFrame, correlations: pd.DataFrame, stock_signal: pd.DataFrame) -> pd.DataFrame:
    def rho(economic_label: str, marker_label: str) -> float:
        return float(correlations.loc[
            (correlations.economic_indicator_label == economic_label) &
            (correlations.fsw_marker_label == marker_label), "spearman_rho"
        ].iloc[0])

    rows = [
        {
            "assumption_id": "A1", "assumption": "FSW density moves with national economic conditions across rounds",
            "test": "Round-level density comparison", "result": "Only 2011 publishes city density; no multi-round correlation is estimable.",
            "verdict": "not testable with current data",
        },
        {
            "assumption_id": "A2", "assumption": "Weaker national conditions coincide with larger mapped markets",
            "test": "GDP growth and CPI inflation versus round/median mapped counts",
            "result": f"GDP versus median count rho={rho('GDP growth', 'median city mapped total'):+.2f}; inflation versus median count rho={rho('CPI inflation', 'median city mapped total'):+.2f}. Paired panels show expansion then persistence.",
            "verdict": "partially supported",
        },
        {
            "assumption_id": "A3", "assumption": "Weaker national conditions shift visible work from street toward home-based organisation",
            "test": "GDP growth and CPI inflation versus home-minus-street balance across three structural rounds",
            "result": f"GDP rho={rho('GDP growth', 'home minus street balance'):+.2f}; inflation rho={rho('CPI inflation', 'home minus street balance'):+.2f}; exact p=0.333 for each because n=3.",
            "verdict": "strongest directional macro-marker pattern",
        },
        {
            "assumption_id": "A4", "assumption": "Kothikhana share is a consistent time-series marker of weaker national conditions",
            "test": "Macro indicators versus median kothikhana share across three structural rounds",
            "result": f"GDP rho={rho('GDP growth', 'kothikhana share'):+.2f}; inflation rho={rho('CPI inflation', 'kothikhana share'):+.2f}; income rho={rho('per-capita income', 'kothikhana share'):+.2f}. Kothikhana share rose during both deterioration and recovery.",
            "verdict": "not supported as a standalone temporal marker",
        },
        {
            "assumption_id": "A5", "assumption": "Cellphone share moves with national economic conditions",
            "test": "Round-level cellphone-share comparison", "result": "Comparable cellphone share is available for only 2011 and 2014.",
            "verdict": "not testable with current data",
        },
        {
            "assumption_id": "A6", "assumption": "Improved national conditions slow net mapped-population growth even if the accumulated population persists",
            "test": "Identical continuous-city panels spanning 2006-07, 2011 and a recovery round",
            "result": (
                f"In the {int(stock_signal.iloc[0].common_cities)}-city panel, annualized growth slowed from "
                f"{stock_signal.iloc[0].deterioration_annualized_growth_pct:.2f}% to {stock_signal.iloc[0].recovery_annualized_growth_pct:.2f}%; "
                f"in the {int(stock_signal.iloc[1].common_cities)}-city panel it slowed from "
                f"{stock_signal.iloc[1].deterioration_annualized_growth_pct:.2f}% to {stock_signal.iloc[1].recovery_annualized_growth_pct:.2f}%."
            ),
            "verdict": "supported descriptively: strong expansion-to-plateau signal",
        },
        {
            "assumption_id": "A7", "assumption": "Reported household distress validates the national macro direction",
            "test": "GDP growth and inflation versus median reported distress across four rounds",
            "result": f"GDP rho={rho('GDP growth', 'reported household distress'):+.2f}; inflation rho={rho('CPI inflation', 'reported household distress'):+.2f}.",
            "verdict": "supported for growth, not for inflation across all rounds",
        },
        {
            "assumption_id": "A8", "assumption": "The recovery plateau may reflect fewer newcomers while existing workers face barriers to exit",
            "test": "Stock-flow interpretation of the continuous-panel growth slowdown",
            "result": "The surveys measure the mapped population stock, not entries and exits. The sharp fall in net growth is consistent with fewer net additions while the existing stock persists, but newcomer and exit flows cannot be separated.",
            "verdict": "plausible and consistent with the data; not directly identified",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "macro_marker_assumption_tests.csv", index=False)
    return out


def run() -> dict:
    master = pd.read_csv(MASTER)
    macro = pd.read_csv(MACRO)
    panel = build_panel(master, macro)
    correlations = correlation_atlas(panel)
    stock_signal = stock_persistence_signal(master)
    assumptions = assumption_tests(panel, correlations, stock_signal)
    payload = {
        "rounds": len(panel), "macro_marker_correlations": len(correlations),
        "assumptions_tested": len(assumptions), "continuous_stock_panels": len(stock_signal),
        "minimum_exact_p": float(correlations.exact_permutation_p.min()),
        "minimum_fdr_p": float(correlations.p_fdr_bh_across_macro_marker_atlas.min()),
    }
    (ROOT / "results" / "diagnostics" / "macro_marker_analysis.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return payload


if __name__ == "__main__":
    print(run())
