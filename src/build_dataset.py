"""Build the harmonized city-round dataset from cached primary sources.

PDF mapping-table values outside 2011 are transcribed below with page locators;
the script reconciles every component total. The 2011 table and PSLM/SPDC
indicators are extracted directly from machine-readable XML/PDF text.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def num(value: str) -> float:
    return float(value.replace(" ", "").replace(",", ""))


PROVINCE = {
    "DG Khan": "Punjab", "Faisalabad": "Punjab", "Lahore": "Punjab",
    "Multan": "Punjab", "Rawalpindi": "Punjab", "Sargodha": "Punjab",
    "Gujranwala": "Punjab", "Gujrat": "Punjab", "Kasur": "Punjab",
    "Sheikhupura": "Punjab", "Sialkot": "Punjab", "Bahawalpur": "Punjab",
    "Hyderabad": "Sindh", "Karachi": "Sindh", "Larkana": "Sindh",
    "Mirpurkhas": "Sindh", "Nawabshah": "Sindh", "Sukkur": "Sindh",
    "Haripur": "Khyber Pakhtunkhwa", "Peshawar": "Khyber Pakhtunkhwa",
    "Bannu": "Khyber Pakhtunkhwa", "Quetta": "Balochistan",
    "Turbat": "Balochistan",
}


# Manual transcription from the named source tables. Automated checks below
# prevent silent inconsistencies between components and totals.
ROUND_2006 = [
    ("Lahore", 450, 6150, 2200, 5700, 25, 14525),
    ("Multan", 75, 800, 650, 1200, 0, 2725),
    ("Sargodha", 0, 506, 631, 75, 25, 1237),
    ("Gujranwala", 0, 667, 554, 500, 4, 1725),
    ("Faisalabad", 0, 3200, 2700, 600, 0, 6500),
    ("Karachi", 200, 7850, 2600, 2000, 500, 13150),
    ("Hyderabad", 100, 1750, 450, 0, 0, 2300),
    ("Sukkur", 0, 500, 1550, 500, 0, 2550),
    ("Larkana", 125, 100, 150, 0, 0, 375),
    ("Peshawar", 0, 450, 150, 200, 400, 1200),
    ("Bannu", 0, 75, 75, 75, 25, 250),
    ("Quetta", 0, 1450, 1000, 50, 0, 2500),
]

ROUND_2014 = [
    ("Lahore", 187, 11315, 1945, 7320, 2758, 2191, 25716),
    ("Faisalabad", 0, 3147, 1365, 1172, 352, 1520, 7556),
    ("Multan", 53, 1261, 2703, 2418, 126, 0, 6561),
    ("Sargodha", 60, 776, 741, 2698, 26, 26, 4327),
]

ROUND_2016 = [
    ("Bahawalpur", 6201), ("Bannu", 192), ("DG Khan", 1349),
    ("Gujranwala", 4069), ("Gujrat", 317), ("Hyderabad", 4426),
    ("Karachi", 25191), ("Kasur", 1739), ("Larkana", 4593),
    ("Mirpurkhas", 2084), ("Nawabshah", 1690), ("Peshawar", 765),
    ("Quetta", 4121), ("Rawalpindi", 2465), ("Sheikhupura", 6252),
    ("Sialkot", 2031), ("Sukkur", 3307), ("Turbat", 523),
]


def sexwork_rows() -> list[dict]:
    rows: list[dict] = []
    for city, brothel, street, home, kk, other, total in ROUND_2006:
        rows.append({
            "round_id": "2006_07", "city": city, "province": PROVINCE[city],
            "brothel_count": brothel, "street_count": street,
            "home_count": home, "kothikhana_count": kk,
            "cellphone_count": np.nan, "other_count": other,
            "fsw_total": total, "fsw_density_per_1000_adult_men": np.nan,
            "analysis_status": "replication", "sexwork_source_id": "fsw_r2_2006_07",
            "sexwork_locator": "PDF page 30, Table 3.1a",
            "extraction_method": "manual transcription; automated reconciliation",
        })

    root = ET.parse(RAW / "sexwork" / "2011" / "emmanuel_2013_fsw_structure.xml").getroot()
    table = root.findall(".//table-wrap")[0]

    def text(el: ET.Element) -> str:
        return " ".join("".join(el.itertext()).split())

    province = None
    for tr in table.findall(".//tr")[2:]:
        values = [text(x) for x in list(tr)]
        if values[0] == "Total":
            continue
        if len(values) == 16:
            province, city, offset = values[0], values[1], 2
        elif len(values) == 15:
            city, offset = values[0], 1
        else:
            raise ValueError(f"Unexpected 2011 table row: {values}")
        province = {"Sind": "Sindh", "KPK": "Khyber Pakhtunkhwa"}.get(province, province)
        rows.append({
            "round_id": "2011", "city": city, "province": province,
            "brothel_count": int(num(values[offset])),
            "street_count": int(num(values[offset + 2])),
            "home_count": int(num(values[offset + 4])),
            "kothikhana_count": int(num(values[offset + 6])),
            "cellphone_count": int(num(values[offset + 8])),
            "other_count": int(num(values[offset + 10])),
            "fsw_total": int(num(values[offset + 12])),
            "fsw_density_per_1000_adult_men": num(values[offset + 13]),
            "analysis_status": "primary", "sexwork_source_id": "fsw_2011_xml",
            "sexwork_locator": "Table 1",
            "extraction_method": "XML table extraction",
        })

    for city, brothel, street, home, kk, cellphone, other, total in ROUND_2014:
        rows.append({
            "round_id": "2014", "city": city, "province": PROVINCE[city],
            "brothel_count": brothel, "street_count": street,
            "home_count": home, "kothikhana_count": kk,
            "cellphone_count": cellphone, "other_count": other,
            "fsw_total": total, "fsw_density_per_1000_adult_men": np.nan,
            "analysis_status": "replication", "sexwork_source_id": "fsw_punjab_2014",
            "sexwork_locator": "PDF pages 71 and 73, FSW mapping tables",
            "extraction_method": "manual transcription; automated reconciliation",
        })

    for city, total in ROUND_2016:
        rows.append({
            "round_id": "2016_17", "city": city, "province": PROVINCE[city],
            "brothel_count": np.nan, "street_count": np.nan,
            "home_count": np.nan, "kothikhana_count": np.nan,
            "cellphone_count": np.nan, "other_count": np.nan,
            "fsw_total": total, "fsw_density_per_1000_adult_men": np.nan,
            "analysis_status": "context_only", "sexwork_source_id": "fsw_r5_2016_17",
            "sexwork_locator": "PDF pages 99-100, Table 6.1a",
            "extraction_method": "manual transcription; automated total check",
        })
    return rows


ALIASES = {
    "DG Khan": ["D.G.Khan", "D.G.khan", "D. G. Khan", "D.G. Khan"],
    "Mirpurkhas": ["Mir Pur Khas", "Mirpur Khas", "Mirpurkhas"],
    "Nawabshah": ["Nawabshah", "Shaheed Benazirabad"],
    "Sheikhupura": ["Sheikhupura", "Sheikupura"],
    "Sialkot": ["Sialkot", "Sailkot"],
    "Turbat": ["Kech", "Ketch", "Turbat"],
}


def aliases(city: str) -> list[str]:
    return ALIASES.get(city, [city])


PSLM = {
    "2006_07": {
        "path": RAW / "economic" / "pslm" / "pslm_2006_07_district.pdf",
        "source": "pslm_2006_07", "econ_pages": range(370, 375),
        "lit_pages": range(127, 132), "toilet_pages": range(366, 371),
        "year": "2006-07", "econ_locator": "Table 5.1, PDF pages 371-375",
        "lit_locator": "Table 2.14(a), PDF pages 128-132",
        "toilet_locator": "Table 4.8, PDF pages 367-371",
    },
    "2011": {
        "path": RAW / "economic" / "pslm" / "pslm_2010_11_district.pdf",
        "source": "pslm_2010_11", "econ_pages": range(402, 411),
        "lit_pages": range(130, 135), "toilet_pages": range(398, 403),
        "year": "2010-11", "econ_locator": "Table 5.1, PDF pages 403-411",
        "lit_locator": "Table 2.14(a), PDF pages 131-135",
        "toilet_locator": "Table 4.8, PDF pages 399-403",
    },
    "2014": {
        "path": RAW / "economic" / "pslm" / "pslm_2014_15_district.pdf",
        "source": "pslm_2014_15", "econ_pages": range(446, 456),
        "lit_pages": range(125, 134), "toilet_pages": range(415, 424),
        "year": "2014-15", "econ_locator": "Table 5.1, PDF pages 447-456",
        "lit_locator": "Table 2.14(a), PDF pages 126-134",
        "toilet_locator": "Table 4.6, PDF pages 416-424",
    },
    "2016_17": {
        "path": RAW / "economic" / "pslm" / "pslm_2014_15_district.pdf",
        "source": "pslm_2014_15", "econ_pages": range(446, 456),
        "lit_pages": range(125, 134), "toilet_pages": range(415, 424),
        "year": "2014-15", "econ_locator": "Table 5.1, PDF pages 447-456",
        "lit_locator": "Table 2.14(a), PDF pages 126-134",
        "toilet_locator": "Table 4.6, PDF pages 416-424",
    },
}


def page_lines(reader: PdfReader, pages: range) -> list[str]:
    return [line.strip() for p in pages for line in (reader.pages[p].extract_text() or "").splitlines()]


def locate(lines: list[str], candidates: list[str], minimum_numbers: int) -> tuple[str, list[float], int]:
    for candidate in candidates:
        pattern = re.compile(r"(?i)(?:^|\s)" + re.escape(candidate) + r"(?:\s|$)")
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if not match:
                continue
            numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", line[match.end():])]
            if len(numbers) >= minimum_numbers:
                return candidate, numbers, i
    raise KeyError(f"Could not find {candidates}")


def pslm_indicators(readers: dict[str, PdfReader], round_id: str, city: str) -> dict:
    cfg = PSLM[round_id]
    reader = readers[str(cfg["path"])]
    econ_lines = page_lines(reader, cfg["econ_pages"])
    matched, overall, i = locate(econ_lines, aliases(city), 7)
    if i + 1 >= len(econ_lines) or not econ_lines[i + 1].lower().startswith("urban"):
        raise ValueError(f"Urban row did not follow {city} in {round_id}")
    urban = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", econ_lines[i + 1])]
    if len(urban) < 7:
        raise ValueError(f"Incomplete urban row for {city} in {round_id}")

    _, literacy, _ = locate(page_lines(reader, cfg["lit_pages"]), aliases(city), 9)
    _, toilet, _ = locate(page_lines(reader, cfg["toilet_pages"]), aliases(city), 9)
    return {
        "economic_geography": matched,
        "economic_source_id": cfg["source"], "economic_period": cfg["year"],
        "economic_distress_all_pct": round(overall[0] + overall[1], 2),
        "economic_distress_urban_pct": round(urban[0] + urban[1], 2),
        "female_illiteracy_urban_pct": 100 - literacy[1],
        "female_illiteracy_all_pct": 100 - literacy[7],
        "sanitation_deprivation_urban_pct": 100 - toilet[0],
        "sanitation_deprivation_all_pct": 100 - toilet[2],
        "economic_locator": cfg["econ_locator"],
        "literacy_locator": cfg["lit_locator"],
        "sanitation_locator": cfg["toilet_locator"],
    }


def poverty_table() -> dict[str, tuple[float, float]]:
    path = RAW / "economic" / "poverty_estimates" / "jamal_2013_rr85_subnational_poverty.pdf"
    reader = PdfReader(path)
    lines = page_lines(reader, range(15, 19))
    cities = {r["city"] for r in sexwork_rows() if r["round_id"] == "2011"}
    out: dict[str, tuple[float, float]] = {}
    for city in cities:
        _, values, _ = locate(lines, aliases(city), 4)
        # rank, overall, urban, rural
        out[city] = (values[1], values[2])
    return out


def match_quality(city: str) -> tuple[str, str]:
    if city == "Karachi":
        return "composite", "Metropolitan surveillance geography versus changing multi-district administration"
    if city in {"DG Khan", "Mirpurkhas", "Larkana", "Nawabshah", "Haripur", "Bannu", "Bahawalpur", "Gujrat", "Kasur", "Sheikhupura", "Sialkot", "Turbat"}:
        note = "District urban stratum used as city proxy"
        if city == "Nawabshah":
            note += "; later PSLM name is Shaheed Benazirabad"
        if city == "Turbat":
            note += "; matched to Kech district"
        return "district_proxy", note
    return "close", "City has a separately identified large-city stratum or close district-city correspondence"


def build() -> pd.DataFrame:
    base = sexwork_rows()
    readers = {str(cfg["path"]): PdfReader(cfg["path"]) for cfg in PSLM.values()}
    poverty = poverty_table()
    rows = []
    for row in base:
        city = row["city"]
        row["city_id"] = slug(city)
        try:
            row.update(pslm_indicators(readers, row["round_id"], city))
        except KeyError:
            # Context-only rows may lack a defensible district match/table row.
            if row["analysis_status"] != "context_only":
                raise
            row.update({
                "economic_geography": np.nan, "economic_source_id": PSLM[row["round_id"]]["source"],
                "economic_period": PSLM[row["round_id"]]["year"],
                "economic_distress_all_pct": np.nan, "economic_distress_urban_pct": np.nan,
                "female_illiteracy_urban_pct": np.nan, "female_illiteracy_all_pct": np.nan,
                "sanitation_deprivation_urban_pct": np.nan, "sanitation_deprivation_all_pct": np.nan,
                "economic_locator": PSLM[row["round_id"]]["econ_locator"],
                "literacy_locator": PSLM[row["round_id"]]["lit_locator"],
                "sanitation_locator": PSLM[row["round_id"]]["toilet_locator"],
            })
        quality, note = match_quality(city)
        row["geographic_match_quality"] = quality
        row["geographic_match_note"] = note
        if row["round_id"] == "2011":
            row["poverty_headcount_all_pct"], row["poverty_headcount_urban_pct"] = poverty[city]
            row["poverty_source_id"] = "spdc_rr85"
            row["poverty_locator"] = "Tables A.3-A.6, PDF pages 16-19"
        else:
            row["poverty_headcount_all_pct"] = np.nan
            row["poverty_headcount_urban_pct"] = np.nan
            row["poverty_source_id"] = np.nan
            row["poverty_locator"] = np.nan
        rows.append(row)

    df = pd.DataFrame(rows)
    components = ["brothel_count", "street_count", "home_count", "kothikhana_count", "cellphone_count", "other_count"]
    for col in components:
        share = col.replace("_count", "_share_pct")
        df[share] = np.where(df[col].notna(), 100 * df[col] / df["fsw_total"], np.nan)
    df["typology_count_sum"] = df[components].sum(axis=1, min_count=1)
    df["typology_sum_difference"] = df["typology_count_sum"] - df["fsw_total"]
    df["adult_male_population_implied"] = np.where(
        df["fsw_density_per_1000_adult_men"].notna(),
        df["fsw_total"] / df["fsw_density_per_1000_adult_men"] * 1000,
        np.nan,
    )
    order = [
        "round_id", "city_id", "city", "province", "analysis_status",
        "fsw_total", "fsw_density_per_1000_adult_men", "adult_male_population_implied",
        *components,
        *[c.replace("_count", "_share_pct") for c in components],
        "typology_count_sum", "typology_sum_difference",
        "economic_distress_urban_pct", "economic_distress_all_pct",
        "poverty_headcount_urban_pct", "poverty_headcount_all_pct",
        "female_illiteracy_urban_pct", "female_illiteracy_all_pct",
        "sanitation_deprivation_urban_pct", "sanitation_deprivation_all_pct",
        "economic_geography", "geographic_match_quality", "geographic_match_note",
        "economic_period", "sexwork_source_id", "economic_source_id", "poverty_source_id",
        "sexwork_locator", "economic_locator", "literacy_locator", "sanitation_locator",
        "poverty_locator", "extraction_method",
    ]
    df = df[order].sort_values(["round_id", "city_id"]).reset_index(drop=True)
    df.to_csv(OUT / "paper1_city_round_master.csv", index=False, float_format="%.6g")

    crosswalk = df[[
        "round_id", "city_id", "city", "province", "economic_geography",
        "economic_period", "geographic_match_quality", "geographic_match_note",
    ]].drop_duplicates()
    crosswalk.to_csv(OUT / "geographic_crosswalk.csv", index=False)

    comparability = pd.DataFrame([
        {"round_id": "2006_07", "mapping_period": "2006-07", "cities": 12, "density_available": False, "typology_available": True, "economic_period": "2006-07", "status": "structural replication", "reason": "Published typology counts; no city adult-male density"},
        {"round_id": "2011", "mapping_period": "2011", "cities": 15, "density_available": True, "typology_available": True, "economic_period": "2010-11", "status": "primary", "reason": "Published total, typology, and density"},
        {"round_id": "2014", "mapping_period": "2014", "cities": 4, "density_available": False, "typology_available": True, "economic_period": "2014-15", "status": "structural replication", "reason": "Four-city Punjab typology table; no city adult-male density"},
        {"round_id": "2016_17", "mapping_period": "2015-17", "cities": 18, "density_available": False, "typology_available": False, "economic_period": "2014-15", "status": "context only", "reason": "City rows sum to 71,315 versus printed total 64,829; no density or city typology"},
    ])
    comparability.to_csv(OUT / "round_comparability.csv", index=False)

    dictionary = pd.DataFrame([
        (c, str(df[c].dtype), "0-100" if c.endswith("_pct") else ("count" if c.endswith("_count") or c == "fsw_total" else "varies"),
         "Missing is unavailable/not comparable; never zero") for c in df.columns
    ], columns=["variable", "storage_type", "unit", "missing_value_rule"])
    dictionary.to_csv(OUT / "paper1_data_dictionary.csv", index=False)
    return df


if __name__ == "__main__":
    built = build()
    print(f"Wrote {len(built)} city-round rows to {OUT / 'paper1_city_round_master.csv'}")
    print(built.groupby(["round_id", "analysis_status"]).size().to_string())
