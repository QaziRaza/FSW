"""Create static PNG figures and the integrated analysis summary."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "paper1_city_round_master.csv"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
SUMMARY = ROOT / "results" / "confirmatory_analysis_summary.md"
FIGURES.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GREEN, GRAY, GRID = "#1f5a7a", "#c7652d", "#3f7d5b", "#59636e", "#e5e9ec"


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def canvas(title: str, width: int = 1600, height: int = 1000):
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    d.text((width // 2, 32), title, fill="#18232d", font=font(32, True), anchor="ma")
    return im, d


def vertical_text(im: Image.Image, text: str, x: int, y: int, size: int = 20):
    """Paste a centered, rotated y-axis label."""
    fnt = font(size)
    box = fnt.getbbox(text)
    layer = Image.new("RGBA", (box[2] - box[0] + 12, box[3] - box[1] + 12), (255, 255, 255, 0))
    ImageDraw.Draw(layer).text((6, 6), text, fill="#25313b", font=fnt, anchor="la")
    layer = layer.rotate(90, expand=True)
    im.paste(layer, (x - layer.width // 2, y - layer.height // 2), layer)


def bounds(values, pad=0.08):
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    span = hi - lo or 1
    return lo - pad * span, hi + pad * span


def axes(draw, box, xlim, ylim, xlabel="", ylabel=""):
    x0, y0, x1, y1 = box
    draw.line((x0, y1, x1, y1), fill=GRAY, width=2)
    draw.line((x0, y0, x0, y1), fill=GRAY, width=2)
    for i in range(6):
        xp = x0 + (x1 - x0) * i / 5
        yp = y1 - (y1 - y0) * i / 5
        xv = xlim[0] + (xlim[1] - xlim[0]) * i / 5
        yv = ylim[0] + (ylim[1] - ylim[0]) * i / 5
        draw.line((xp, y0, xp, y1), fill=GRID, width=1)
        draw.line((x0, yp, x1, yp), fill=GRID, width=1)
        draw.text((xp, y1 + 12), f"{xv:.0f}", fill=GRAY, font=font(17), anchor="ma")
        draw.text((x0 - 12, yp), f"{yv:.0f}", fill=GRAY, font=font(17), anchor="rm")
    draw.text(((x0 + x1) / 2, y1 + 52), xlabel, fill="#25313b", font=font(20), anchor="ma")


def xy(value_x, value_y, box, xlim, ylim):
    x0, y0, x1, y1 = box
    x = x0 + (value_x - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0)
    y = y1 - (value_y - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0)
    return x, y


def save(im: Image.Image, name: str):
    im.save(FIGURES / f"{name}.png", dpi=(220, 220), optimize=True)


def markdown_table(df: pd.DataFrame, columns: list[str], formats=None) -> str:
    formats = formats or {}
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in df[columns].iterrows():
        values = []
        for col in columns:
            value = row[col]
            values.append("NA" if pd.isna(value) else (formats[col].format(value) if col in formats else str(value)))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_figures(df: pd.DataFrame):
    primary = pd.read_csv(TABLES / "table_primary_result.csv").iloc[0]
    d2011 = df[df.round_id == "2011"].copy()
    im, dr = canvas("2011 mapped FSW density and district urban economic distress")
    box = (145, 125, 1510, 855)
    xlim, ylim = bounds(d2011.economic_distress_urban_pct), bounds(d2011.fsw_density_per_1000_adult_men)
    axes(dr, box, xlim, ylim, "Urban households reporting worse/much worse economic situation (%)", "Mapped FSWs per 1,000 adult men")
    vertical_text(im, "Mapped FSWs per 1,000 adult men", 38, (box[1] + box[3]) // 2, 20)
    coef = np.polyfit(d2011.economic_distress_urban_pct, d2011.fsw_density_per_1000_adult_men, 1)
    a = xy(xlim[0], np.polyval(coef, xlim[0]), box, xlim, ylim); b = xy(xlim[1], np.polyval(coef, xlim[1]), box, xlim, ylim)
    dr.line((*a, *b), fill=ORANGE, width=4)
    for row in d2011.itertuples():
        x, y = xy(row.economic_distress_urban_pct, row.fsw_density_per_1000_adult_men, box, xlim, ylim)
        dr.ellipse((x - 7, y - 7, x + 7, y + 7), fill=BLUE, outline="white", width=2)
        dr.text((x + 10, y - 18), row.city, fill="#24313a", font=font(15))
    annotation = f"Spearman rho = {primary.estimate_rho:.2f}\nBootstrap 95% CI {primary.ci_95_low_bootstrap:.2f} to {primary.ci_95_high_bootstrap:.2f}\nPermutation p = {primary.p_permutation_two_sided:.3f}"
    dr.rounded_rectangle((1010, 145, 1480, 255), radius=10, fill="white", outline="#aeb8c0", width=2)
    dr.multiline_text((1030, 160), annotation, fill="#18232d", font=font(20), spacing=5)
    save(im, "figure_1_primary_scatter")

    sensitivity = pd.read_csv(TABLES / "table_sensitivity_correlations.csv")
    show = sensitivity[~sensitivity.analysis.str.startswith("leave_out_")].copy()
    im, dr = canvas("Primary association across prespecified city subsets", 1400, 760)
    x0, x1, y0, step = 440, 1280, 130, 82
    dr.line((x0 + (0 + 1) / 2 * (x1 - x0), 100, x0 + (0 + 1) / 2 * (x1 - x0), 650), fill=GRAY, width=2)
    for i, row in enumerate(show.itertuples()):
        y = y0 + i * step; x = x0 + (row.estimate + 1) / 2 * (x1 - x0)
        label = row.analysis.replace("_", " ").title()
        dr.text((x0 - 20, y), label, fill="#25313b", font=font(21), anchor="rm")
        dr.line((x0, y, x1, y), fill=GRID, width=1)
        dr.ellipse((x - 8, y - 8, x + 8, y + 8), fill=BLUE)
        dr.text((x + 15, y), f"{row.estimate:.2f} (n={row.n})", fill=BLUE, font=font(19), anchor="lm")
    for val in [-1, -0.5, 0, 0.5, 1]:
        x = x0 + (val + 1) / 2 * (x1 - x0); dr.text((x, 675), f"{val:.1f}", fill=GRAY, font=font(19), anchor="ma")
    dr.text(((x0 + x1) / 2, 715), "Spearman rho", fill="#25313b", font=font(22), anchor="ma")
    save(im, "figure_2_subset_sensitivity")

    rep = pd.read_csv(TABLES / "table_structural_replication.csv")
    im, dr = canvas("Round-specific associations with sex-work structure", 1800, 1120)
    rounds = ["2006_07", "2011", "2014"]
    outcomes = [("home_share_pct", "Home share", GREEN), ("street_share_pct", "Street share", ORANGE)]
    for ri, (outcome, label, color) in enumerate(outcomes):
        for ci, round_id in enumerate(rounds):
            part = df[df.round_id == round_id]
            left, top = 110 + ci * 565, 115 + ri * 500
            box = (left, top + 50, left + 490, top + 400)
            xlim, ylim = bounds(part.economic_distress_urban_pct), bounds(part[outcome])
            axes(dr, box, xlim, ylim, "Distress (%)" if ri else "", label if ci == 0 else "")
            if ci == 0:
                vertical_text(im, label + " (%)", 32, (box[1] + box[3]) // 2, 18)
            rr = rep[(rep.round_id == round_id) & (rep.outcome == outcome)].iloc[0]
            dr.text((left + 245, top), f"{round_id.replace('_', '-')} | rho={rr.estimate_rho:.2f}, n={rr.n}", fill="#18232d", font=font(20, True), anchor="ma")
            for row in part.itertuples():
                x, y = xy(row.economic_distress_urban_pct, getattr(row, outcome), box, xlim, ylim)
                dr.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
                dr.text((x + 7, y - 13), row.city, fill="#303b44", font=font(11))
    save(im, "figure_3_structural_replication")

    loo = sensitivity[sensitivity.analysis.str.startswith("leave_out_")].sort_values("estimate")
    im, dr = canvas("Leave-one-city-out stability of the primary association", 1400, 1000)
    x0, x1, y0, step = 400, 1290, 115, 52
    all_est = float(primary.estimate_rho); all_x = x0 + (all_est + 1) / 2 * (x1 - x0)
    dr.line((all_x, 90, all_x, 890), fill=ORANGE, width=4)
    zero_x = x0 + 0.5 * (x1 - x0); dr.line((zero_x, 90, zero_x, 890), fill=GRAY, width=2)
    for i, row in enumerate(loo.itertuples()):
        y = y0 + i * step; x = x0 + (row.estimate + 1) / 2 * (x1 - x0)
        dr.text((x0 - 20, y), row.omitted_city, fill="#25313b", font=font(19), anchor="rm")
        dr.line((x0, y, x1, y), fill=GRID, width=1)
        dr.ellipse((x - 7, y - 7, x + 7, y + 7), fill=BLUE)
    for val in [-1, -0.5, 0, 0.5, 1]:
        x = x0 + (val + 1) / 2 * (x1 - x0)
        dr.text((x, 905), f"{val:.1f}", fill=GRAY, font=font(18), anchor="ma")
    dr.text((all_x + 8, 895), f"All cities: {all_est:.2f}", fill=ORANGE, font=font(18))
    dr.text(((x0 + x1) / 2, 955), "Spearman rho after omitting city", fill="#25313b", font=font(22), anchor="ma")
    save(im, "figure_4_leave_one_out")


def build_summary(df: pd.DataFrame):
    p = pd.read_csv(TABLES / "table_primary_result.csv").iloc[0]
    secondary = pd.read_csv(TABLES / "table_secondary_correlations.csv")
    sensitivity = pd.read_csv(TABLES / "table_sensitivity_correlations.csv")
    replication = pd.read_csv(TABLES / "table_structural_replication.csv")
    change = pd.read_csv(TABLES / "table_cross_round_change_tests.csv")
    ols = pd.read_csv(TABLES / "table_ols_models.csv")
    influence = pd.read_csv(ROOT / "results" / "diagnostics" / "influence_diagnostics_2011.csv")
    comparability = pd.read_csv(ROOT / "data" / "processed" / "round_comparability.csv")
    subset = sensitivity[~sensitivity.analysis.str.startswith("leave_out_")]
    loo = sensitivity[sensitivity.analysis.str.startswith("leave_out_")]
    slope = ols[(ols.model == "unadjusted_density") & (ols.term == "economic_distress_urban_pct")].iloc[0]
    influential = influence.loc[influence.cooks_distance.idxmax()]
    direction = "a moderate positive rank association" if p.estimate_rho > .3 else ("a weak positive rank association" if p.estimate_rho > 0 else ("a moderate inverse rank association" if p.estimate_rho < -.3 else "a weak inverse rank association"))
    lines = [
        "# Analysis summary", "", "## Executive result", "",
        f"Across the 15 mapped cities in 2011, urban household economic distress and mapped FSW density showed {direction} (Spearman rho = {p.estimate_rho:.3f}; bootstrap 95% CI {p.ci_95_low_bootstrap:.3f} to {p.ci_95_high_bootstrap:.3f}; two-sided permutation p = {p.p_permutation_two_sided:.4f}). The interval is wide and includes associations in both directions. The evidence therefore does not support a precise claim that more distressed urban districts had higher mapped FSW density in 2011.", "",
        "This is an ecological, small-sample association among surveillance-selected cities. It neither tests individual entry into sex work nor establishes a causal effect of economic distress.", "", "## Data assembled", "",
        markdown_table(comparability, ["round_id", "mapping_period", "cities", "density_available", "typology_available", "economic_period", "status"]), "",
        "The 2011 round is the only acquired source reporting city density per 1,000 adult men. The 2006-07 and 2014 sources support structural replication using typology shares. Round 5 is count context only: its printed city rows sum to 71,315 while its printed Grand Total is 64,829, and neither city density nor city typology composition is published in the acquired report.", "", "## Primary and secondary associations", "",
        markdown_table(secondary, ["analysis", "method", "n", "estimate", "p_value"], {"estimate": "{:.3f}", "p_value": "{:.4f}"}), "",
        f"The unadjusted OLS visual-scale slope was {slope.coefficient:.3f} additional mapped FSWs per 1,000 adult men for a one-percentage-point difference in urban distress (HC3 95% CI {slope.ci_95_low:.3f} to {slope.ci_95_high:.3f}). OLS is secondary because the sample is small and the primary estimand is rank-based.", "", "## Robustness and influence", "",
        f"Across six prespecified city subsets, Spearman estimates ranged from {subset.estimate.min():.3f} to {subset.estimate.max():.3f}. Across leave-one-city-out analyses they ranged from {loo.estimate.min():.3f} to {loo.estimate.max():.3f}. The largest Cook's distance belonged to {influential.city} ({influential.cooks_distance:.3f}); this identifies influence on the linear fit, not an invalid observation.", "",
        markdown_table(subset, ["analysis", "n", "estimate", "p_value"], {"estimate": "{:.3f}", "p_value": "{:.4f}"}), "", "## Structural replication", "",
        markdown_table(replication, ["round_id", "outcome", "n", "estimate_rho", "p_value", "p_fdr_bh"], {"estimate_rho": "{:.3f}", "p_value": "{:.4f}", "p_fdr_bh": "{:.4f}"}), "",
        "These round-specific tests ask whether distress covaries with mapped sex-work organization, not whether national composition changed. FDR values address the six prespecified home/street tests. Differences may reflect structural change, survey coverage, mapping intensity, or category practice.", "", "## Exploratory 2006-07 to 2011 change analysis", "",
        markdown_table(change, ["outcome", "n", "estimate_rho", "p_value", "status"], {"estimate_rho": "{:.3f}", "p_value": "{:.4f}"}), "",
        "Distress change is the change in each city's within-round percentile rank, not a raw percentage-point difference, because the response distribution shifted substantially. With only overlapping cities, these estimates are descriptive and fragile.", "", "## Interpretation", "",
        "The primary result is compatible with no stable monotonic relationship, a modest relationship obscured by measurement error, or heterogeneous city-specific processes. Secondary poverty, literacy, and sanitation measures test adjacent constructs rather than interchangeable versions of one exposure.", "",
        "The structural analyses are the more defensible multi-period comparison because named typology counts are present in 2006-07, 2011, and 2014. Even there, results are replication across snapshots, not a pooled panel effect.", "", "## Main limitations", "",
        "- Mapping estimates may undercount less visible workers and vary with program intensity.", "- City outcomes are paired to district urban strata, with explicit but imperfect matches.", "- Cities were surveillance-selected rather than sampled from all Pakistani cities.", "- Fifteen observations sharply limit precision and adjustment.", "- Ecological associations cannot establish individual mechanisms or causality.", "- Adult-male density was unavailable for other acquired rounds, so cross-round density replication was not attempted.", "", "## Reproducibility status", "",
        "Cached sources are checksummed, joins use an explicit crosswalk, typology components reconcile to published totals, and missing values are never converted to zero. `results/diagnostics/validation_report.md` records executable checks. The manuscript remains reserved until this summary is reviewed.", "",
    ]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    data = pd.read_csv(DATA)
    sample = ["city", "province", "fsw_total", "fsw_density_per_1000_adult_men", "economic_distress_urban_pct", "poverty_headcount_urban_pct", "female_illiteracy_urban_pct", "sanitation_deprivation_urban_pct", "geographic_match_quality"]
    data[data.round_id == "2011"][sample].sort_values("city").to_csv(TABLES / "table_primary_city_data.csv", index=False, float_format="%.3f")
    build_figures(data); build_summary(data)
    print(f"Wrote figures to {FIGURES} and summary to {SUMMARY}")
