"""Fail-fast validation for source provenance and the harmonized dataset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
MANIFEST = ROOT / "data" / "source_manifest.csv"
DIAG = ROOT / "results" / "diagnostics"
DIAG.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> dict:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(condition), "detail": detail})

    manifest = pd.read_csv(MANIFEST, skipinitialspace=True)
    for row in manifest.itertuples(index=False):
        path = ROOT / str(row.local_path).strip()
        exists = path.exists()
        check(f"source_exists:{row.source_id}", exists, str(row.local_path).strip())
        if exists:
            check(f"source_size:{row.source_id}", path.stat().st_size == int(row.bytes), f"expected={row.bytes}; actual={path.stat().st_size}")
            actual_hash = sha256(path)
            check(f"source_hash:{row.source_id}", actual_hash == row.sha256, f"expected={row.sha256}; actual={actual_hash}")

    df = pd.read_csv(DATA)
    check("row_count", len(df) == 49, f"actual={len(df)}; expected=49")
    check("unique_city_round", not df.duplicated(["round_id", "city_id"]).any(), "No duplicated round-city keys")
    expected_n = {"2006_07": 12, "2011": 15, "2014": 4, "2016_17": 18}
    actual_n = df.groupby("round_id").size().to_dict()
    check("round_counts", actual_n == expected_n, f"actual={actual_n}; expected={expected_n}")

    expected_totals = {"2006_07": 49037, "2011": 89178, "2014": 44160}
    actual_totals = df.groupby("round_id")["fsw_total"].sum().astype(int).to_dict()
    check("analytic_round_totals", all(actual_totals[k] == v for k, v in expected_totals.items()), f"actual={actual_totals}; expected analytic rounds={expected_totals}")
    check("round5_city_rows_reproduce_source", actual_totals["2016_17"] == 71315, f"sum of 18 printed city rows={actual_totals['2016_17']}")
    check("round5_reported_total_inconsistency_detected", actual_totals["2016_17"] - 64829 == 6486, "printed city rows sum to 71,315 but printed Grand Total is 64,829")

    mapped = df[df["analysis_status"].isin(["primary", "replication"])]
    check("typology_totals_reconcile", (mapped["typology_sum_difference"].abs() <= 1).all(), f"max_abs_difference={mapped['typology_sum_difference'].abs().max()}")
    share_cols = ["brothel_share_pct", "street_share_pct", "home_share_pct", "kothikhana_share_pct", "cellphone_share_pct", "other_share_pct"]
    share_sums = mapped[share_cols].sum(axis=1, min_count=1)
    check("typology_shares_sum", np.allclose(share_sums, 100, atol=0.15), f"range={share_sums.min():.6f} to {share_sums.max():.6f}")

    primary = df[df["round_id"] == "2011"]
    check("primary_density_complete", primary["fsw_density_per_1000_adult_men"].notna().all(), f"missing={primary['fsw_density_per_1000_adult_men'].isna().sum()}")
    check("nonprimary_density_missing", df[df["round_id"] != "2011"]["fsw_density_per_1000_adult_men"].isna().all(), "No denominator was reconstructed")
    check("primary_exposure_complete", primary["economic_distress_urban_pct"].notna().all(), f"missing={primary['economic_distress_urban_pct'].isna().sum()}")
    check("primary_secondary_exposures_complete", primary[["poverty_headcount_urban_pct", "female_illiteracy_urban_pct", "sanitation_deprivation_urban_pct"]].notna().all().all(), "Poverty, illiteracy, sanitation complete for 15 cities")

    replication = df[df["analysis_status"] == "replication"]
    check("replication_exposure_complete", replication["economic_distress_urban_pct"].notna().all(), f"missing={replication['economic_distress_urban_pct'].isna().sum()}")
    check("crosswalk_complete", df[["economic_geography", "geographic_match_quality"]].notna().all().all() or df[df["analysis_status"] != "context_only"][["economic_geography", "geographic_match_quality"]].notna().all().all(), "All analytic rows have explicit geography")

    pct_cols = [c for c in df.columns if c.endswith("_pct")]
    values = df[pct_cols].stack().dropna()
    check("percent_ranges", values.between(0, 100).all(), f"min={values.min()}; max={values.max()}")
    check("positive_counts", (df["fsw_total"] > 0).all(), f"minimum={df['fsw_total'].min()}")

    failed = [c for c in checks if not c["passed"]]
    report = {"status": "PASS" if not failed else "FAIL", "checks": checks, "failed_count": len(failed)}
    (DIAG / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Data validation report", "", f"Overall status: **{report['status']}**", "", "| Check | Result | Detail |", "|---|---:|---|"]
    for item in checks:
        detail = item["detail"].replace("|", "\\|")
        lines.append(f"| `{item['check']}` | {'PASS' if item['passed'] else 'FAIL'} | {detail} |")
    (DIAG / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit("Validation failed: " + ", ".join(c["check"] for c in failed))
    return report


if __name__ == "__main__":
    result = validate()
    print(f"{result['status']}: {len(result['checks'])} checks; {result['failed_count']} failures")
