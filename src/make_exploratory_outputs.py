"""Render static exploratory figures and an integrated hypothesis report."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from analyse_primary import spearman_values

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
REPORT = ROOT / "results" / "exploratory_report.md"
FIGURES.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#17242f", "#566573", "#dfe5e8"
BLUE, ORANGE, TEAL, PURPLE = "#23678a", "#c65f2f", "#36877a", "#74548f"


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def canvas(title: str, subtitle: str, width: int = 1800, height: int = 1120):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 28), title, fill=INK, font=font(34, True), anchor="ma")
    draw.text((width // 2, 72), subtitle, fill=MUTED, font=font(20), anchor="ma")
    return image, draw


def bounds(values, pad: float = 0.08):
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    span = hi - lo or 1.0
    return lo - pad * span, hi + pad * span


def axes(draw, box, xlim, ylim, xlabel, ylabel):
    x0, y0, x1, y1 = box
    for i in range(5):
        xp, yp = x0 + (x1 - x0) * i / 4, y1 - (y1 - y0) * i / 4
        draw.line((xp, y0, xp, y1), fill=GRID, width=1)
        draw.line((x0, yp, x1, yp), fill=GRID, width=1)
        xv, yv = xlim[0] + (xlim[1] - xlim[0]) * i / 4, ylim[0] + (ylim[1] - ylim[0]) * i / 4
        draw.text((xp, y1 + 10), f"{xv:.1f}", fill=MUTED, font=font(15), anchor="ma")
        draw.text((x0 - 10, yp), f"{yv:.1f}", fill=MUTED, font=font(15), anchor="rm")
    draw.line((x0, y1, x1, y1), fill=MUTED, width=2)
    draw.line((x0, y0, x0, y1), fill=MUTED, width=2)
    draw.text(((x0 + x1) / 2, y1 + 46), xlabel, fill=INK, font=font(18), anchor="ma")
    draw.text((x0, y0 - 26), ylabel, fill=INK, font=font(17, True), anchor="la")


def xy(x, y, box, xlim, ylim):
    x0, y0, x1, y1 = box
    return (
        x0 + (x - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0),
        y1 - (y - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0),
    )


def color_for_rho(value: float):
    value = max(-1.0, min(1.0, value))
    if value < 0:
        t = abs(value)
        return tuple(int(246 * (1 - t) + c * t) for c in (43, 105, 139))
    t = value
    return tuple(int(246 * (1 - t) + c * t) for c in (198, 95, 47))


def save(image: Image.Image, name: str):
    image.save(FIGURES / f"{name}.png", dpi=(220, 220), optimize=True)


def association_heatmap(atlas: pd.DataFrame):
    exposures = atlas.exposure_label.drop_duplicates().tolist()
    outcomes = atlas.outcome_label.drop_duplicates().tolist()
    im, dr = canvas(
        "What correlates with what in the 2011 city cross-section?",
        "Spearman rho; blue = inverse, orange = positive. All results are exploratory (15 cities).",
        2050, 1080,
    )
    left, top, cell_w, cell_h = 510, 205, 160, 112
    for j, label in enumerate(outcomes):
        x = left + j * cell_w + cell_w / 2
        dr.text((x, top - 18), label.replace(" ", "\n"), fill=INK, font=font(17, True), anchor="ms", align="center", spacing=3)
    for i, exposure in enumerate(exposures):
        y = top + i * cell_h
        dr.text((left - 20, y + cell_h / 2), exposure, fill=INK, font=font(20, True), anchor="rm")
        for j, outcome in enumerate(outcomes):
            row = atlas[(atlas.exposure_label == exposure) & (atlas.outcome_label == outcome)].iloc[0]
            x0 = left + j * cell_w
            dr.rounded_rectangle((x0 + 4, y + 4, x0 + cell_w - 4, y + cell_h - 4), radius=8, fill=color_for_rho(row.estimate_rho))
            dr.text((x0 + cell_w / 2, y + 43), f"{row.estimate_rho:+.2f}", fill="white" if abs(row.estimate_rho) > .35 else INK, font=font(24, True), anchor="mm")
            dr.text((x0 + cell_w / 2, y + 78), f"p={row.p_value_exploratory:.3f}", fill="white" if abs(row.estimate_rho) > .50 else INK, font=font(14), anchor="mm")
    legend_y = top + len(exposures) * cell_h + 55
    for k in range(101):
        value = -1 + 2 * k / 100
        x0 = left + 400 + 5 * k
        dr.rectangle((x0, legend_y, x0 + 6, legend_y + 25), fill=color_for_rho(value))
    dr.text((left + 380, legend_y + 12), "-1", fill=INK, font=font(16), anchor="rm")
    dr.text((left + 660, legend_y + 12), "0", fill=INK, font=font(16), anchor="mm")
    dr.text((left + 925, legend_y + 12), "+1", fill=INK, font=font(16), anchor="lm")
    save(im, "exploratory_figure_1_association_atlas")


def acute_chronic_map(features: pd.DataFrame):
    im, dr = canvas(
        "Acute deterioration and chronic deprivation are different axes",
        "Quadrants use sample medians; point size is mapped total; label suffix is density per 1,000 adult men.",
        1800, 1120,
    )
    box = (150, 145, 1660, 955)
    xlim = bounds(features.economic_distress_urban_pct, .05)
    ylim = bounds(features.chronic_deprivation_index, .10)
    axes(dr, box, xlim, ylim, "Households reporting worse/much worse economic situation (%)", "Chronic deprivation index (z-score mean)")
    xmid, ymid = features.economic_distress_urban_pct.median(), features.chronic_deprivation_index.median()
    xv, _ = xy(xmid, ylim[0], box, xlim, ylim)
    _, yv = xy(xlim[0], ymid, box, xlim, ylim)
    dr.line((xv, box[1], xv, box[3]), fill="#83919b", width=3)
    dr.line((box[0], yv, box[2], yv), fill="#83919b", width=3)
    dr.text((box[2] - 12, box[1] + 120), "more acute / more chronic", fill=MUTED, font=font(18), anchor="ra")
    dr.text((box[2] - 12, box[3] - 12), "more acute / less chronic", fill=MUTED, font=font(18), anchor="rd")
    for row in features.itertuples():
        x, y = xy(row.economic_distress_urban_pct, row.chronic_deprivation_index, box, xlim, ylim)
        radius = 6 + 6 * (math_log(row.fsw_total) - math_log(features.fsw_total.min())) / (math_log(features.fsw_total.max()) - math_log(features.fsw_total.min()))
        dr.ellipse((x - radius, y - radius, x + radius, y + radius), fill=TEAL, outline="white", width=2)
        dr.text((x + 10, y - 10), f"{row.city} ({row.fsw_density_per_1000_adult_men:g})", fill=INK, font=font(15))
    rho, p = spearman_values(features.economic_distress_urban_pct.to_numpy(float), features.chronic_deprivation_index.to_numpy(float))
    dr.rounded_rectangle((1165, 170, 1605, 250), radius=9, fill="white", outline="#aeb9c0", width=2)
    dr.text((1185, 188), f"Acute vs chronic: rho={rho:+.2f}, p={p:.3f}", fill=INK, font=font(21, True))
    save(im, "exploratory_figure_2_acute_vs_chronic")


def math_log(value):
    return float(np.log(value))


def scale_contrast(features: pd.DataFrame):
    panels = [
        ("fsw_total", "Mapped FSW total", True),
        ("adult_male_population_implied", "Implied adult-male population", True),
        ("fsw_density_per_1000_adult_men", "Mapped density per 1,000 men", False),
    ]
    im, dr = canvas(
        "The count association appears tied to city scale",
        "Acute deterioration is positive with total market size and population scale, but not with density.",
        1900, 760,
    )
    for i, (outcome, label, log_y) in enumerate(panels):
        left = 90 + i * 610
        box = (left + 70, 155, left + 560, 610)
        x = features.economic_distress_urban_pct.to_numpy(float)
        raw_y = features[outcome].to_numpy(float)
        y = np.log(raw_y) if log_y else raw_y
        xlim, ylim = bounds(x), bounds(y)
        axes(dr, box, xlim, ylim, "Acute deterioration (%)", ("log " if log_y else "") + label)
        rho, p = spearman_values(x, raw_y)
        dr.text((left + 315, 115), f"rho={rho:+.2f}, p={p:.3f}", fill=INK, font=font(20, True), anchor="ma")
        for city, xv, yv in zip(features.city, x, y):
            px, py = xy(xv, yv, box, xlim, ylim)
            dr.ellipse((px - 6, py - 6, px + 6, py + 6), fill=[ORANGE, PURPLE, BLUE][i])
            dr.text((px + 7, py - 10), city, fill=INK, font=font(11))
    dr.text((950, 715), "Same 15 cities; Spearman correlations are descriptive and do not identify a causal channel.", fill=MUTED, font=font(17), anchor="ma")
    save(im, "exploratory_figure_3_scale_contrast")


def organisation_panels(features: pd.DataFrame):
    panels = [
        ("kothikhana_share_pct", "Kothikhana share (%)"),
        ("cellphone_share_pct", "Cellphone share (%)"),
        ("avg_kothikhana_fsw_per_operator", "Kothikhana FSWs per operator"),
        ("street_share_pct", "Street share (%)"),
    ]
    im, dr = canvas(
        "Acute deterioration may align with how sex work is organised",
        "The strongest directional pattern is toward kothikhana organisation and away from cellphone-based work.",
        1850, 1100,
    )
    for i, (outcome, label) in enumerate(panels):
        col, row = i % 2, i // 2
        left, top = 80 + col * 900, 125 + row * 475
        box = (left + 90, top + 70, left + 820, top + 405)
        x = features.economic_distress_urban_pct.to_numpy(float)
        y = features[outcome].to_numpy(float)
        xlim, ylim = bounds(x), bounds(y)
        axes(dr, box, xlim, ylim, "Acute deterioration (%)", label)
        rho, p = spearman_values(x, y)
        dr.text((left + 450, top + 22), f"{label}: rho={rho:+.2f}, p={p:.3f}", fill=INK, font=font(20, True), anchor="ma")
        for city, xv, yv in zip(features.city, x, y):
            px, py = xy(xv, yv, box, xlim, ylim)
            dr.ellipse((px - 5, py - 5, px + 5, py + 5), fill=[ORANGE, BLUE, PURPLE, TEAL][i])
            if city in {"Karachi", "Lahore", "Sukkur", "Peshawar", "Quetta", "Sargodha"}:
                dr.text((px + 7, py - 9), city, fill=INK, font=font(12))
    save(im, "exploratory_figure_4_organisation")


def round_context_figure(rounds: pd.DataFrame):
    rounds = rounds.set_index("round_id").loc[["2006_07", "2011", "2014"]].reset_index()
    xlabels = ["2006-07\n12 cities", "2011\n15 cities", "2014\n4 Punjab cities"]
    panels = [
        ("median_acute_distress_pct", "Median acute distress (%)", ORANGE),
        ("median_home_share_pct", "Median home share (%)", TEAL),
        ("median_street_share_pct", "Median street share (%)", BLUE),
        ("median_kothikhana_share_pct", "Median kothikhana share (%)", PURPLE),
    ]
    im, dr = canvas(
        "Round snapshots: economic context and mapped typology composition",
        "Coverage changes across rounds, so these are not national time trends.",
        1900, 1040,
    )
    xs = [420, 1030, 1640]
    for i, (column, label, color) in enumerate(panels):
        top = 145 + i * 185
        values = rounds[column].to_numpy(float)
        ylim = (0, max(values) * 1.18)
        dr.text((70, top + 55), label, fill=INK, font=font(19, True), anchor="lm")
        points = []
        for j, value in enumerate(values):
            y = top + 110 - value / ylim[1] * 110
            points.append((xs[j], y))
            dr.ellipse((xs[j] - 7, y - 7, xs[j] + 7, y + 7), fill=color)
            dr.text((xs[j], y - 15), f"{value:.1f}", fill=color, font=font(17, True), anchor="ms")
        dr.line([coordinate for point in points for coordinate in point], fill=color, width=4)
        dr.line((220, top + 110, 1680, top + 110), fill=GRID, width=1)
    for x, label in zip(xs, xlabels):
        dr.text((x, 905), label, fill=INK, font=font(19, True), anchor="ma", align="center")
    macro = rounds[["round_id", "real_gdp_growth_pct", "cpi_inflation_pct"]]
    for x, row in zip(xs, macro.itertuples()):
        dr.text((x, 970), f"GDP growth {row.real_gdp_growth_pct:.1f}% | CPI {row.cpi_inflation_pct:.1f}%", fill=MUTED, font=font(16), anchor="ma")
    save(im, "exploratory_figure_5_round_context")


def improvement_test_figure(contrasts: pd.DataFrame):
    im, dr = canvas(
        "Testing the opposite: what happened when economic conditions improved?",
        "Common-city mapped counts are compared so changing survey coverage does not create the result.",
        1900, 940,
    )
    titles = {
        "2006_07_to_2011": "Deterioration: 2006-07 to 2011",
        "2011_to_2014": "Improvement: 2011 to 2014",
        "2011_to_2016_17": "Improvement: 2011 to 2016-17",
    }
    conclusions = {
        "2006_07_to_2011": "Mapped totals expanded sharply",
        "2011_to_2014": "Mapped totals still increased",
        "2011_to_2016_17": "Mapped totals were broadly stable",
    }
    for i, row in enumerate(contrasts.itertuples()):
        x0, x1 = 70 + i * 610, 630 + i * 610
        dr.rounded_rectangle((x0, 135, x1, 820), radius=18, fill="#f7f9fa", outline="#cbd4d9", width=2)
        dr.text(((x0 + x1) / 2, 175), titles[row.comparison], fill=INK, font=font(23, True), anchor="ma")
        macro_color = ORANGE if row.delta_real_gdp_growth_pp < 0 else TEAL
        dr.text((x0 + 35, 245), "National economy", fill=MUTED, font=font(18, True))
        dr.text((x0 + 35, 287), f"GDP growth: {row.real_gdp_growth_start_pct:.2f}% → {row.real_gdp_growth_end_pct:.2f}%", fill=macro_color, font=font(22, True))
        dr.text((x0 + 35, 330), f"CPI inflation: {row.cpi_inflation_start_pct:.2f}% → {row.cpi_inflation_end_pct:.2f}%", fill=macro_color, font=font(22, True))
        dr.text((x0 + 35, 373), f"Per-capita income: ${row.per_capita_income_start_usd:,.0f} → ${row.per_capita_income_end_usd:,.0f}", fill=INK, font=font(20))
        dr.line((x0 + 30, 420, x1 - 30, 420), fill=GRID, width=2)
        dr.text((x0 + 35, 465), f"Same {row.common_cities} cities", fill=MUTED, font=font(18, True))
        dr.text((x0 + 35, 510), f"Combined mapped total: {row.aggregate_fsw_total_pct_change:+.1f}%", fill=BLUE, font=font(25, True))
        dr.text((x0 + 35, 555), f"Median city change: {row.median_city_fsw_pct_change:+.1f}%", fill=BLUE, font=font(21))
        dr.text((x0 + 35, 600), f"Cities up/down: {row.cities_with_count_increase}/{row.cities_with_count_decrease}", fill=INK, font=font(20))
        if not pd.isna(row.median_delta_economic_distress_urban_pct):
            dr.text((x0 + 35, 645), f"District distress ({row.local_economic_period_end}, n={row.paired_n_economic_distress_urban_pct}): {row.median_delta_economic_distress_urban_pct:+.1f}", fill=INK, font=font(17))
        dr.rounded_rectangle((x0 + 28, 710, x1 - 28, 780), radius=10, fill="white", outline=macro_color, width=3)
        dr.text(((x0 + x1) / 2, 745), conclusions[row.comparison], fill=macro_color, font=font(22, True), anchor="mm")
    dr.text((950, 885), "Better macro conditions did not produce a fall in mapped FSW totals across the common cities.", fill=INK, font=font(23, True), anchor="ma")
    save(im, "exploratory_figure_6_better_economy_test")


def md_table(df: pd.DataFrame, columns: list[str], digits: dict[str, int] | None = None):
    digits = digits or {}
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in df[columns].iterrows():
        values = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                values.append("NA")
            elif column in digits:
                values.append(f"{value:.{digits[column]}f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_report(features, atlas, economic, networks, models, cv, transitions, rounds, improvement):
    def atlas_row(exposure, outcome):
        return atlas[(atlas.exposure_label == exposure) & (atlas.outcome_label == outcome)].iloc[0]

    acute_density = atlas_row("acute urban deterioration", "mapped density")
    acute_total = atlas_row("acute urban deterioration", "mapped total")
    acute_scale = atlas_row("acute urban deterioration", "implied adult-male population")
    chronic_density = atlas_row("chronic deprivation index", "mapped density")
    chronic_total = atlas_row("chronic deprivation index", "mapped total")
    chronic_scale = atlas_row("chronic deprivation index", "implied adult-male population")
    kk = atlas_row("acute urban deterioration", "kothikhana share")
    phone = atlas_row("acute urban deterioration", "cellphone share")
    econ_show = economic[(economic.variable_1 == "economic_distress_urban_pct") | (economic.variable_1 == "poverty_headcount_urban_pct")][["variable_1", "variable_2", "estimate_rho", "p_value_exploratory", "p_fdr_bh_within_family"]]
    model_show = models[(models.term != "const") & models.model.isin(["mapped_density", "log_mapped_total", "log_implied_population_scale", "kothikhana_share", "cellphone_share"])][["model", "term", "coefficient", "ci_95_low", "ci_95_high", "p_value", "r_squared"]]
    net_show = networks[
        ((networks.exposure_label == "acute urban deterioration") & (networks.network_outcome == "avg_kothikhana_fsw_per_operator")) |
        ((networks.exposure_label == "mapped density") & networks.network_outcome.isin(["avg_home_fsw_per_operator", "avg_networked_fsw_per_operator"]))
    ][["exposure_label", "network_outcome", "estimate_rho", "p_value_exploratory", "p_fdr_bh_within_family"]]
    round_show = rounds[["round_id", "cities", "median_acute_distress_pct", "median_female_illiteracy_pct", "median_sanitation_deprivation_pct", "median_home_share_pct", "median_street_share_pct", "median_kothikhana_share_pct", "real_gdp_growth_pct", "cpi_inflation_pct"]]
    transition_show = transitions[[c for c in transitions.columns if c in {
        "comparison", "paired_cities", "median_delta_economic_distress_urban_pct", "median_delta_home_share_pct", "median_delta_street_share_pct", "median_delta_kothikhana_share_pct"
    }]]
    improvement_show = improvement[[
        "comparison", "common_cities", "delta_real_gdp_growth_pp", "delta_cpi_inflation_pp",
        "aggregate_fsw_total_pct_change", "median_city_fsw_pct_change",
        "cities_with_count_increase", "cities_with_count_decrease",
        "median_delta_economic_distress_urban_pct", "median_delta_home_share_pct",
        "median_delta_street_share_pct", "median_delta_kothikhana_share_pct",
    ]]
    paired_test_show = improvement[[
        "comparison", "annualized_aggregate_fsw_change_pct", "exact_sign_test_p_two_sided",
        "paired_n_distress_count_change", "rho_distress_change_vs_log_count_change",
        "p_distress_change_vs_log_count_change",
    ]]
    archetype_show = features.groupby("economic_archetype", sort=False).agg(
        cities=("city", lambda values: ", ".join(sorted(values))),
        n=("city", "size"),
        median_density=("fsw_density_per_1000_adult_men", "median"),
        median_mapped_total=("fsw_total", "median"),
    ).reset_index()
    lines = [
        "# Exploratory synthesis: pairing the sex-work mapping and economic surveys", "",
        "> Status: hypothesis-generating. This report broadens interpretation after the frozen primary analysis. It does not convert post-hoc patterns into confirmatory findings.", "",
        "## Bottom line", "",
        "The inverse primary estimate is not the end of the analysis. It is one part of a more coherent two-process pattern:", "",
        f"1. **Acute reported deterioration appears mainly tied to large-city/market scale in these data.** It is positively associated with the absolute mapped FSW total (rho={acute_total.estimate_rho:+.3f}) and implied adult-male population (rho={acute_scale.estimate_rho:+.3f}), but weakly inversely associated with mapped density (rho={acute_density.estimate_rho:+.3f}). Large distressed markets contain more mapped workers, not more workers per 1,000 adult men.", "",
        f"2. **Chronic deprivation points in the opposite scale direction.** The exploratory index is strongly inverse with mapped total (rho={chronic_total.estimate_rho:+.3f}) and implied population scale (rho={chronic_scale.estimate_rho:+.3f}), while its association with density is positive but imprecise (rho={chronic_density.estimate_rho:+.3f}). Smaller, chronically deprived cities can therefore have fewer workers in absolute terms yet somewhat higher mapped density.", "",
        f"3. **Economic conditions may be related more to organisation than prevalence.** Acute deterioration is positively associated with kothikhana share (rho={kk.estimate_rho:+.3f}) and inversely with cellphone share (rho={phone.estimate_rho:+.3f}). The network table adds a parallel signal: more kothikhana-based FSWs per operator where acute deterioration is higher. These patterns suggest an intermediation/venue hypothesis, not a demonstrated transition mechanism.", "",
        "4. **The round snapshots show substantial typology reclassification or restructuring, but city-level economic change does not consistently explain it.** Among ten cities observed in 2006-07 and 2011, median acute distress rose 20.84 points, median home share rose 18.32 points, median street share fell 24.16 points, and median kothikhana share rose 6.99 points. With only four Punjab cities in 2014, the home/street movement partly reverses. Coverage and mapping practice remain serious competing explanations.", "",
        "One association in the 54-cell outcome atlas survives Benjamini-Hochberg correction at 0.05: all-area reported deterioration versus kothikhana share (rho=+0.771; raw p=0.00076; q=0.0409). The next closest are chronic deprivation versus market scale and all-area deterioration versus cellphone share (q=0.0541). The adjusted result strengthens the structural-signal interpretation, while the rest remain hypotheses to test later.", "",
        "## 1. The economic variables are not interchangeable", "",
        "The key measurement fact is that the primary PSLM item asks whether the household economic situation is worse than one year earlier. It measures perceived deterioration. Poverty, female illiteracy, and sanitation deprivation measure longer-run disadvantage. In 2011, the chronic indicators move together, while acute deterioration generally moves against them.", "",
        md_table(econ_show, econ_show.columns.tolist(), {"estimate_rho": 3, "p_value_exploratory": 4, "p_fdr_bh_within_family": 4}), "",
        "This means the primary inverse estimate should not be paraphrased as 'poverty reduces mapped sex work.' A defensible reading is that cities experiencing greater recent deterioration were, in this cross-section, often larger and less chronically deprived. The acute item and the chronic deprivation index describe different economic states.", "",
        "![Association atlas](figures/exploratory_figure_1_association_atlas.png)", "",
        "![Acute versus chronic map](figures/exploratory_figure_2_acute_vs_chronic.png)", "",
        "Using the two sample medians as descriptive cut points produces four city archetypes:", "",
        md_table(archetype_show, archetype_show.columns.tolist(), {"median_density": 2, "median_mapped_total": 0}), "",
        "## 2. Reconciling counts, density, and city scale", "",
        md_table(pd.DataFrame([
            {"economic axis": "acute deterioration", "mapped density rho": acute_density.estimate_rho, "mapped total rho": acute_total.estimate_rho, "population scale rho": acute_scale.estimate_rho},
            {"economic axis": "chronic deprivation", "mapped density rho": chronic_density.estimate_rho, "mapped total rho": chronic_total.estimate_rho, "population scale rho": chronic_scale.estimate_rho},
        ]), ["economic axis", "mapped density rho", "mapped total rho", "population scale rho"], {"mapped density rho": 3, "mapped total rho": 3, "population scale rho": 3}), "",
        "The absolute count and density questions are substantively different. A larger city can have many more mapped workers and a lower rate per adult man. The acute-distress/count correlation is therefore consistent with a scale or demand-market process, while the weak inverse density correlation says the rate is not elevated. Conversely, the chronic-deprivation pattern is consistent with smaller denominators producing higher mapped density without a larger absolute market.", "",
        "The adult-male population variable is algebraically implied by the published count and density; it is a diagnostic of scale, not an independently observed population estimate.", "",
        "![Scale contrast](figures/exploratory_figure_3_scale_contrast.png)", "",
        "The two-exposure models tell the same qualitative story after acute and chronic conditions are entered together, but uncertainty is wide:", "",
        md_table(model_show, model_show.columns.tolist(), {"coefficient": 3, "ci_95_low": 3, "ci_95_high": 3, "p_value": 4, "r_squared": 3}), "",
        "All coefficients are standardized and use HC3 standard errors. With 15 cities and correlated predictors, they are descriptive separation exercises, not stable adjusted effects.", "",
        "## 3. A possible organisation channel", "",
        f"The simple rank association of acute deterioration with kothikhana share is {kk.estimate_rho:+.3f} (unadjusted exploratory p={kk.p_value_exploratory:.4f}); the association with cellphone share is {phone.estimate_rho:+.3f} (p={phone.p_value_exploratory:.4f}). In the separately published network table, acute deterioration is associated with average kothikhana-based FSWs per operator (rho={net_show.iloc[0].estimate_rho:+.3f}).", "",
        md_table(net_show, net_show.columns.tolist(), {"estimate_rho": 3, "p_value_exploratory": 4, "p_fdr_bh_within_family": 4}), "",
        "One hypothesis is that adverse short-run conditions in large urban markets correlate with more venue-mediated or operator-mediated organisation, while direct cellphone solicitation is more visible in different city economies. But the typologies overlap, shares are compositional, and network mapping used snowball procedures. The evidence cannot show that distress moved workers from one category to another.", "",
        "![Organisation panels](figures/exploratory_figure_4_organisation.png)", "",
        "## 4. What the multi-period pairing can and cannot say", "",
        md_table(round_show, round_show.columns.tolist(), {c: 2 for c in round_show.columns if c not in {"round_id", "cities"}}), "",
        md_table(transition_show, transition_show.columns.tolist(), {c: 2 for c in transition_show.columns if c not in {"comparison", "paired_cities"}}), "",
        "### Direct test of better economic conditions", "",
        "Reversing the question produces a clear result: better national economic conditions after 2011 did **not** lead to fewer mapped sex workers in the common cities.", "",
        md_table(improvement_show, improvement_show.columns.tolist(), {c: 2 for c in improvement_show.columns if c not in {"comparison", "common_cities", "cities_with_count_increase", "cities_with_count_decrease"}}), "",
        "Formal paired-city comparisons confirm that the change was much faster during deterioration: the common-city mapped total grew at an approximate annualized rate of 11.96% before 2011, 5.30% from 2011 to 2014, and 0.60% from 2011 to 2016-17. Exact sign tests and city-level distress-change correlations are shown below.", "",
        md_table(paired_test_show, paired_test_show.columns.tolist(), {c: 3 for c in paired_test_show.columns if c not in {"comparison", "paired_n_distress_count_change"}}), "",
        "The city-level distress-change correlations do not have a stable direction (-0.382, -0.400 and +0.417). The macro-period pattern therefore describes expansion followed by persistence; it does not show that the cities with the largest local improvement experienced the largest count reductions.", "",
        "From 2011 to 2014, GDP growth improved by 1.84 points and CPI inflation fell by 9.20 points. Reported distress declined modestly in the four common cities, but every one of those cities had a higher mapped FSW count; their combined total rose 16.77%. The composition changed more clearly: median home-based share fell 26.10 points, street share rose 17.11 points, and kothikhana share rose 7.85 points.", "",
        "Across the longer 2011 to 2016-17 improvement, the ten common cities were essentially stable in aggregate: their mapped total increased 3.36%, while the median city changed -1.94%; four cities increased and six decreased. Thus, improvement is associated with persistence and reorganisation, not a general contraction of the mapped sex-work population. This is an asymmetric, ratchet-like pattern: deterioration coincides with expansion, while recovery does not undo the expansion.", "",
        "![Better-economy test](figures/exploratory_figure_6_better_economy_test.png)", "",
        "The 2011 mapping coincides with a nationally difficult macroeconomic setting: 2.4% real GDP growth and 14.0% CPI inflation in the reviewed Economic Survey overview, following flood and oil-price shocks. That context makes the large jump in reported deterioration plausible. It does not identify a city-level causal effect because the macro values are national and there are only three structurally comparable mapping snapshots.", "",
        "Round totals and medians cannot be read as national trends: the city sets change (12 cities in 2006-07, 15 in 2011, and four Punjab cities in 2014), typology measurement can change, and 2016-17 lacks comparable city density and typology detail.", "",
        "![Round context](figures/exploratory_figure_5_round_context.png)", "",
        "## 5. Nonlinearity does not rescue the density story", "",
        md_table(cv, cv.columns.tolist(), {"loocv_rmse_density": 3, "rmse_relative_to_constant": 3}), "",
        "A constant-only model has the lowest leave-one-city-out prediction error. Linear, quadratic, and cubic specifications all perform worse. The existing data therefore do not support a useful U-shaped or threshold model for mapped density.", "",
        "## 6. Hypotheses worth testing next", "",
        "- **Shock versus level:** acute deterioration and chronic deprivation have distinct associations with market scale and density.",
        "- **Market scale/demand:** short-run urban stress may be concentrated in large labour and client markets, raising absolute numbers without raising per-capita density.",
        "- **Intermediation:** acute stress may correlate with kothikhana/operator-based organisation rather than prevalence.",
        "- **Small-city vulnerability:** chronic deprivation may matter for density because smaller cities have fewer adult men, even when absolute FSW totals are lower.",
        "- **Visibility and mapping effort:** observed organisation shifts may reflect where and how mapping teams could enumerate workers.",
        "- **Asymmetric recovery:** downturn-related expansion may persist after growth and inflation improve, while visible work arrangements change.", "",
        "The corresponding falsification tests and data requirements are in `results/tables/exploratory_hypothesis_ledger.csv`.", "",
        "## 7. Boundaries", "",
        "- All city correlations are ecological and based on 15 observations.",
        "- The chronic deprivation index was constructed after the primary analysis and is exploratory.",
        "- FSW mapping estimates are programmatic enumeration estimates, not a census.",
        "- City outcomes are paired to district urban strata; match quality varies.",
        "- Typology shares are compositional and categories can overlap or change over time.",
        "- The network operator table comes from a supplementary snowball mapping process and is not a denominator for total FSW counts.",
        "- Multiple comparisons are substantial; nominal p-values are navigation aids, not discoveries.",
        "- Mechanisms such as labour displacement, migration, client demand, entry into sex work, or movement across typologies are not directly measured.", "",
        "## Reproducible artifacts", "",
        "- `data/processed/paper1_2011_exploratory_features.csv`: 2011 joined feature table.",
        "- `data/processed/paper1_2011_network_structure.csv`: source-parsed network table.",
        "- `data/processed/paper1_round_macro_context.csv`: reviewed national macro context with locators.",
        "- `results/tables/exploratory_*.csv`: full coefficient, correlation, city-archetype, transition, and hypothesis tables.",
        "- `results/diagnostics/exploratory_validation.md`: executable validation evidence.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def run():
    features = pd.read_csv(PROCESSED / "paper1_2011_exploratory_features.csv")
    atlas = pd.read_csv(TABLES / "exploratory_2011_association_atlas.csv")
    economic = pd.read_csv(TABLES / "exploratory_economic_intercorrelations.csv")
    networks = pd.read_csv(TABLES / "exploratory_2011_network_associations.csv")
    models = pd.read_csv(TABLES / "exploratory_two_exposure_models.csv")
    cv = pd.read_csv(TABLES / "exploratory_nonlinear_loocv.csv")
    transitions = pd.read_csv(TABLES / "exploratory_cross_round_transition_summary.csv")
    rounds = pd.read_csv(TABLES / "exploratory_round_economic_mapping_context.csv")
    improvement = pd.read_csv(TABLES / "exploratory_macro_improvement_contrasts.csv")
    association_heatmap(atlas)
    acute_chronic_map(features)
    scale_contrast(features)
    organisation_panels(features)
    round_context_figure(rounds)
    improvement_test_figure(improvement)
    build_report(features, atlas, economic, networks, models, cv, transitions, rounds, improvement)
    print(f"Wrote 6 exploratory figures and {REPORT}")


if __name__ == "__main__":
    run()
