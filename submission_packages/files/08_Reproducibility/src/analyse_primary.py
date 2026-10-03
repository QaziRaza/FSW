"""Run the frozen 2011 analysis using NumPy/Pandas only.

The included helpers implement standard correlation t approximations, HC3
covariance, and influence diagnostics so the workflow stays portable.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
TABLES = ROOT / "results" / "tables"
DIAG = ROOT / "results" / "diagnostics"
TABLES.mkdir(parents=True, exist_ok=True)
DIAG.mkdir(parents=True, exist_ok=True)
SEED = 20261002


def _betacf(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d, tiny = 1.0, 1.0 - qab * x / qap, 3e-14
    d = 1.0 / (d if abs(d) >= tiny else tiny)
    h = d
    for m in range(1, 301):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c; c = tiny if abs(c) < tiny else c
        d = 1.0 / d; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c; c = tiny if abs(c) < tiny else c
        d = 1.0 / d; delta = d * c; h *= delta
        if abs(delta - 1.0) < 3e-12:
            break
    return h


def regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def t_two_sided_p(t_value: float, df: int) -> float:
    if not math.isfinite(t_value): return 0.0
    return regularized_beta(df / (df + t_value * t_value), df / 2.0, 0.5)


def t_critical_975(df: int) -> float:
    lo, hi = 0.0, 20.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if 1 - t_two_sided_p(mid, df) / 2 < 0.975: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def pearson_values(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    r = float(np.corrcoef(x, y)[0, 1])
    df = len(x) - 2
    t_value = r * math.sqrt(df / max(1e-15, 1 - r * r))
    return r, t_two_sided_p(t_value, df)


def rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(float)


def spearman_values(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    return pearson_values(rank(x), rank(y))


def paired(df: pd.DataFrame, x: str, y: str) -> tuple[np.ndarray, np.ndarray]:
    pair = df[[x, y]].dropna()
    return pair[x].to_numpy(float), pair[y].to_numpy(float)


def permutation_p(x: np.ndarray, y: np.ndarray, permutations: int = 100_000) -> float:
    rng, xr, yr = np.random.default_rng(SEED), rank(x), rank(y)
    observed = abs(np.corrcoef(xr, yr)[0, 1])
    extreme = sum(abs(np.corrcoef(xr, rng.permutation(yr))[0, 1]) >= observed - 1e-15 for _ in range(permutations))
    return (extreme + 1) / (permutations + 1)


def bootstrap_ci(x: np.ndarray, y: np.ndarray, draws: int = 20_000) -> tuple[float, float, int]:
    rng, n, values = np.random.default_rng(SEED + 1), len(x), []
    for _ in range(draws):
        idx = rng.integers(0, n, n)
        if len(np.unique(x[idx])) > 1 and len(np.unique(y[idx])) > 1:
            values.append(spearman_values(x[idx], y[idx])[0])
    low, high = np.percentile(values, [2.5, 97.5])
    return float(low), float(high), len(values)


def correlation_row(df: pd.DataFrame, name: str, x_name: str, y_name: str, method: str = "spearman") -> dict:
    x, y = paired(df, x_name, y_name)
    estimate, p_value = spearman_values(x, y) if method == "spearman" else pearson_values(x, y)
    return {"analysis": name, "x": x_name, "y": y_name, "method": method, "n": len(x), "estimate": estimate, "p_value": p_value}


def ols_hc3(y: np.ndarray, X: np.ndarray, names: list[str]) -> tuple[list[dict], dict]:
    n, k = X.shape
    inv = np.linalg.inv(X.T @ X)
    beta = inv @ X.T @ y
    fitted = X @ beta
    residual = y - fitted
    h = np.einsum("ij,jk,ik->i", X, inv, X)
    scaled = residual / np.maximum(1e-12, 1 - h)
    cov = inv @ (X.T @ (X * (scaled * scaled)[:, None])) @ inv
    se, df, crit = np.sqrt(np.diag(cov)), n - k, t_critical_975(n - k)
    rows = []
    for term, coef, std in zip(names, beta, se):
        rows.append({"term": term, "coefficient": coef, "robust_se_hc3": std, "p_value": t_two_sided_p(coef / std, df), "ci_95_low": coef - crit * std, "ci_95_high": coef + crit * std})
    sse, sst = float(residual @ residual), float(((y - y.mean()) ** 2).sum())
    mse = sse / df
    cooks = residual**2 / (k * mse) * h / np.maximum(1e-12, (1 - h) ** 2)
    deleted_var = np.maximum(0, (sse - residual**2 / np.maximum(1e-12, 1 - h)) / max(1, df - 1))
    ext_student = residual / np.sqrt(np.maximum(1e-12, deleted_var * (1 - h)))
    return rows, {"fitted": fitted, "leverage": h, "cooks": cooks, "studentized_external": ext_student, "r_squared": 1 - sse / sst}


def run() -> dict:
    df = pd.read_csv(DATA)
    d = df[df.round_id == "2011"].copy().sort_values("city").reset_index(drop=True)
    x, y = paired(d, "economic_distress_urban_pct", "fsw_density_per_1000_adult_men")
    rho, asym_p = spearman_values(x, y)
    ci_low, ci_high, valid_boot = bootstrap_ci(x, y)
    headline = pd.DataFrame([{"analysis": "primary_2011_density_vs_urban_economic_distress", "method": "Spearman", "n": len(x), "estimate_rho": rho, "ci_95_low_bootstrap": ci_low, "ci_95_high_bootstrap": ci_high, "p_asymptotic_two_sided": asym_p, "p_permutation_two_sided": permutation_p(x, y), "permutations": 100000, "bootstrap_draws_valid": valid_boot, "seed": SEED}])
    headline.to_csv(TABLES / "table_primary_result.csv", index=False, float_format="%.6f")

    d["log_density"] = np.log1p(d.fsw_density_per_1000_adult_men)
    secondary = [
        correlation_row(d, "primary_pair_pearson", "economic_distress_urban_pct", "fsw_density_per_1000_adult_men", "pearson"),
        correlation_row(d, "urban_poverty", "poverty_headcount_urban_pct", "fsw_density_per_1000_adult_men"),
        correlation_row(d, "urban_female_illiteracy", "female_illiteracy_urban_pct", "fsw_density_per_1000_adult_men"),
        correlation_row(d, "urban_sanitation_deprivation", "sanitation_deprivation_urban_pct", "fsw_density_per_1000_adult_men"),
        correlation_row(d, "all_area_economic_distress", "economic_distress_all_pct", "fsw_density_per_1000_adult_men"),
        correlation_row(d, "log_density_pearson", "economic_distress_urban_pct", "log_density", "pearson"),
    ]
    pd.DataFrame(secondary).to_csv(TABLES / "table_secondary_correlations.csv", index=False, float_format="%.6f")

    subsets = {"all_cities": d, "exclude_karachi": d[d.city != "Karachi"], "exclude_lahore": d[d.city != "Lahore"], "exclude_karachi_lahore": d[~d.city.isin(["Karachi", "Lahore"])], "close_matches_only": d[d.geographic_match_quality == "close"], "close_or_composite": d[d.geographic_match_quality.isin(["close", "composite"])]}
    sensitivities = [correlation_row(part, name, "economic_distress_urban_pct", "fsw_density_per_1000_adult_men") for name, part in subsets.items()]
    for city in d.city:
        row = correlation_row(d[d.city != city], f"leave_out_{city}", "economic_distress_urban_pct", "fsw_density_per_1000_adult_men")
        row["omitted_city"] = city; sensitivities.append(row)
    pd.DataFrame(sensitivities).to_csv(TABLES / "table_sensitivity_correlations.csv", index=False, float_format="%.6f")

    d["log_fsw_total"] = np.log(d.fsw_total)
    specs = [("unadjusted_density", "fsw_density_per_1000_adult_men", ["economic_distress_urban_pct"]), ("scale_adjusted_density", "fsw_density_per_1000_adult_men", ["economic_distress_urban_pct", "log_fsw_total"]), ("unadjusted_log_density", "log_density", ["economic_distress_urban_pct"])]
    model_rows, primary_extras = [], None
    for model, outcome, predictors in specs:
        X = np.column_stack([np.ones(len(d)), *[d[p].to_numpy(float) for p in predictors]])
        rows, extras = ols_hc3(d[outcome].to_numpy(float), X, ["const", *predictors])
        if model == "unadjusted_density": primary_extras = extras
        for row in rows:
            row.update({"model": model, "outcome": outcome, "n": len(d), "r_squared_plain_ols": extras["r_squared"]}); model_rows.append(row)
    pd.DataFrame(model_rows).to_csv(TABLES / "table_ols_models.csv", index=False, float_format="%.6f")

    diag = d[["city", "economic_distress_urban_pct", "fsw_density_per_1000_adult_men"]].copy()
    diag["fitted"] = primary_extras["fitted"]
    diag["studentized_residual_external"] = primary_extras["studentized_external"]
    diag["leverage"] = primary_extras["leverage"]
    diag["cooks_distance"] = primary_extras["cooks"]
    diag.to_csv(DIAG / "influence_diagnostics_2011.csv", index=False, float_format="%.6f")
    payload = {"primary": headline.iloc[0].to_dict(), "largest_cooks_distance_city": str(diag.loc[diag.cooks_distance.idxmax(), "city"]), "largest_cooks_distance": float(diag.cooks_distance.max())}
    (DIAG / "primary_analysis.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run()["primary"]
    print(f"Primary: rho={result['estimate_rho']:.3f}; bootstrap 95% CI {result['ci_95_low_bootstrap']:.3f} to {result['ci_95_high_bootstrap']:.3f}; permutation p={result['p_permutation_two_sided']:.4f}")
