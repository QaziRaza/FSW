"""Build journal submission support files and reproducibility archives for Paper 1."""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from build_manuscript import FIGURES, REFERENCES, TABLES, TITLE, add_author_block, resolve_citations


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission_packages"
FILES = OUT / "files"

def safe_reset(directory: Path) -> None:
    resolved = directory.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != "submission_packages":
        raise RuntimeError(f"Refusing to reset unexpected path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=90, bottom=90, end=90) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def configure_doc(doc: Document, landscape: bool = False) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    if landscape:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = section.page_height, section.page_width

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(4)

    for style_name, size in (("Title", 16), ("Subtitle", 12), ("Heading 1", 13), ("Heading 2", 11)):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = style_name != "Subtitle"
        style.paragraph_format.space_before = Pt(8)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER if style_name in {"Title", "Subtitle"} else WD_ALIGN_PARAGRAPH.LEFT
        )
        ppr = style._element.get_or_add_pPr()
        border = ppr.find(qn("w:pBdr"))
        if border is not None:
            ppr.remove(border)


def add_title(doc: Document, title: str, subtitle: str | None = None) -> None:
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    if subtitle:
        p = doc.add_paragraph(style="Subtitle")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(subtitle)
        run.font.name = "Times New Roman"
        run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
        run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
        run.font.size = Pt(11)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0, 0, 0)


def add_page_number(section) -> None:
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_end])


def add_table(doc: Document, headers: list[str], rows: list[list[str]], font_size: float = 8.5) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    set_repeat_header(table.rows[0])
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        set_cell_shading(cell, "245681")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(str(value))
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(font_size)
    for row_index, row_values in enumerate(rows):
        cells = table.add_row().cells
        for col_index, value in enumerate(row_values):
            cell = cells[col_index]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if row_index % 2:
                set_cell_shading(cell, "EAF1F7")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if col_index > 0 and len(str(value)) < 18:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(value))
            run.font.size = Pt(font_size)


def create_title_page(path: Path) -> None:
    doc = Document()
    configure_doc(doc)
    add_title(doc, TITLE)
    add_author_block(doc, font_size=10.5, wrap_corresponding=True)
    for text in (
        "Article type: Original research",
        "Main-text word count: 7,582",
        "Tables: 5; Figures: 3; References: 45",
        "Funding: No specific grant was received.",
        "Competing interests: The authors declare no competing interests.",
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(4)
        p.add_run(text)
    doc.save(path)


def create_tables_docx(path: Path, csv_dir: Path) -> None:
    doc = Document()
    configure_doc(doc, landscape=True)
    add_title(doc, "Manuscript Tables", TITLE)
    doc.add_paragraph("Editable copies of the five tables, with titles and notes exactly matching the manuscript.")
    for index, table_spec in enumerate(TABLES.values(), start=1):
        if index > 1:
            doc.add_page_break()
        p = doc.add_paragraph(style="Heading 1")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0)
        p.paragraph_format.right_indent = Inches(0)
        p.paragraph_format.first_line_indent = Inches(0)
        heading_run = p.add_run(table_spec["caption"])
        # Long manuscript titles must remain inside the printable landscape width.
        if len(table_spec["caption"]) > 80:
            heading_run.font.size = Pt(11)
        add_table(doc, table_spec["headers"], table_spec["rows"], font_size=8.5)
        if table_spec.get("note"):
            p = doc.add_paragraph()
            run = p.add_run(table_spec["note"])
            run.italic = True
            run.font.size = Pt(9)

        csv_name = re.sub(r"[^A-Za-z0-9]+", "_", table_spec["caption"]).strip("_") + ".csv"
        with (csv_dir / csv_name).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(table_spec["headers"])
            writer.writerows(table_spec["rows"])
    doc.save(path)


SUPPLEMENT_TABLES = [
    ("Supplementary Table S1", "Geographic and temporal crosswalk", "data/processed/geographic_crosswalk.csv"),
    ("Supplementary Table S2", "Round comparability decisions", "data/processed/round_comparability.csv"),
    ("Supplementary Table S3", "Full 2011 economic exposure and FSW marker association atlas", "results/tables/exploratory_2011_association_atlas.csv"),
    ("Supplementary Table S4", "2011 network-structure associations", "results/tables/exploratory_2011_network_associations.csv"),
    ("Supplementary Table S5", "Standardised two-exposure models", "results/tables/exploratory_two_exposure_models.csv"),
    ("Supplementary Table S6", "Nonlinear leave-one-city-out prediction comparison", "results/tables/exploratory_nonlinear_loocv.csv"),
    ("Supplementary Table S7", "Common-city mapped-count comparisons", "results/tables/exploratory_paired_count_tests.csv"),
    ("Supplementary Table S8", "Cross-round typology transition summary", "results/tables/exploratory_cross_round_transition_summary.csv"),
    ("Supplementary Table S9", "Complete round-level macroeconomic marker atlas", "results/tables/macro_marker_correlations.csv"),
]


def display_value(value) -> str:
    if pd.isna(value):
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def create_supplement(path: Path) -> None:
    doc = Document()
    configure_doc(doc, landscape=True)
    add_page_number(doc.sections[0])
    add_title(doc, "Supplementary Appendix", TITLE)
    add_author_block(doc, font_size=9.5)
    doc.add_paragraph(
        "This appendix provides the full crosswalks and exploratory output tables supporting the manuscript. "
        "The primary result remains the prespecified 2011 density analysis; the additional tables are explicitly hypothesis-generating."
    )
    for index, (label, title, relative_path) in enumerate(SUPPLEMENT_TABLES):
        doc.add_page_break()
        p = doc.add_paragraph(style="Heading 1")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0)
        p.paragraph_format.right_indent = Inches(0)
        p.paragraph_format.first_line_indent = Inches(0)
        heading_run = p.add_run(f"{label}. {title}")
        if len(f"{label}. {title}") > 80:
            heading_run.font.size = Pt(11)
        frame = pd.read_csv(ROOT / relative_path)
        headers = [str(column) for column in frame.columns]
        rows = [[display_value(value) for value in row] for row in frame.itertuples(index=False, name=None)]
        font_size = 6.3 if len(headers) >= 9 else 7.2 if len(headers) >= 7 else 8.0
        add_table(doc, headers, rows, font_size=font_size)
        p = doc.add_paragraph()
        r = p.add_run(f"Source file: {relative_path.replace('/', chr(92))}")
        r.italic = True
        r.font.size = Pt(8)
    doc.save(path)


STROBE_ROWS = [
    ("1", "Identify the study design in the title or abstract", "Title and subtitle; Abstract, page 2"),
    ("2", "Provide a balanced summary", "Structured Abstract, pages 2-3"),
    ("3", "Explain the scientific background and rationale", "Introduction, pages 3-5"),
    ("4", "State the objectives", "Introduction, final paragraph, page 5"),
    ("5", "Present the study design early", "Methods: Study design and analytical architecture, pages 6-7"),
    ("6", "Describe setting, locations and relevant periods", "Methods: Data sources and eligibility; Geographic and temporal matching, pages 7-9"),
    ("7", "Define observational units and eligibility criteria", "Methods: Study design and analytical architecture; Data sources and eligibility, pages 6-8"),
    ("8", "Define outcomes, exposures and other variables", "Methods: Economic exposures; Outcomes and derived measures, pages 8-10"),
    ("9", "Describe data sources and measurement", "Methods: Data sources and eligibility; Geographic and temporal matching, pages 7-9"),
    ("10", "Describe efforts to address bias", "Methods: Bias handling, quality assurance, and software, page 13"),
    ("11", "Explain the study size", "Methods, pages 6-7; Results: Data coverage and analytical sample, page 14"),
    ("12", "Explain handling of quantitative variables", "Methods: Outcomes and derived measures; analysis subsections, pages 9-13"),
    ("13", "Describe all statistical methods and sensitivity analyses", "Methods: Primary and sensitivity analyses through Round-level macroeconomic marker analysis, pages 10-13"),
    ("14", "Report numbers at each analytical stage", "Results: Data coverage and analytical sample; Tables 1-5, pages 14-22"),
    ("15", "Give descriptive characteristics", "Results: Data coverage and analytical sample; Table 1, pages 6 and 14"),
    ("16", "Report outcome data", "Results, pages 14-22; Tables 1-5; Figures 1-3"),
    ("17", "Give unadjusted, adjusted and sensitivity estimates", "Results: density, scale and organisation subsections; Tables 2-3, pages 14-19"),
    ("18", "Report other analyses", "Results: common-city panels, nonlinear checks and macro-marker analysis, pages 16-22"),
    ("19", "Summarise key results", "Discussion: Principal findings, pages 22-23"),
    ("20", "Discuss limitations and potential bias", "Discussion: Strengths and limitations, pages 27-28"),
    ("21", "Provide a cautious overall interpretation", "Discussion, pages 22-28; Conclusion, pages 28-29"),
    ("22", "Discuss generalisability", "Discussion: Public-health implications and Strengths and limitations, pages 26-28"),
    ("23", "State funding and the funder's role", "Declarations: Funding, page 29"),
]


def create_strobe(path: Path) -> None:
    doc = Document()
    configure_doc(doc, landscape=True)
    add_title(doc, "STROBE Cross Sectional Reporting Checklist", TITLE)
    doc.add_paragraph(
        "Completed reporting checklist for the multi-period ecological study. Page numbers refer to the 33-page author manuscript dated 3 October 2026."
    )
    add_table(doc, ["Item", "Reporting recommendation", "Where reported"], [list(row) for row in STROBE_ROWS], font_size=8.5)
    doc.save(path)


def parse_bib_entries(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    cursor = 0
    while True:
        match = re.search(r"@[A-Za-z]+\{([^,]+),", text[cursor:])
        if not match:
            break
        start = cursor + match.start()
        key = match.group(1)
        depth = 0
        end = None
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            raise ValueError(f"Unbalanced BibTeX entry: {key}")
        entries[key] = text[start:end].strip()
        cursor = end
    return entries


EXTRA_BIB = {
    "WHO2025Pakistan": """@misc{WHO2025Pakistan,
  author = {{World Health Organization Regional Office for the Eastern Mediterranean}},
  title = {HIV infections rise in Pakistan: WHO and UNAIDS call to action},
  year = {2025},
  month = dec,
  url = {https://www.emro.who.int/pak/pakistan-news/hiv-infections-rise-in-pakistan-who-and-unaids-call-to-action.html},
  note = {Accessed 3 October 2026}
}""",
    "PakistanStrategy2021": """@techreport{PakistanStrategy2021,
  author = {{Government of Pakistan, Ministry of National Health Services, Regulations and Coordination}},
  title = {Pakistan AIDS Strategy IV 2021--2025},
  institution = {Government of Pakistan},
  address = {Islamabad},
  year = {2021},
  url = {https://extranet.who.int/cpcd/sites/default/files/public_file_repository/PAK_Pakistan_National-Strategic-Plan-HIV_2021-2025.pdf}
}""",
    "NASAPakistan2024": """@techreport{NASAPakistan2024,
  author = {{Government of Pakistan, Common Management Unit for AIDS, TB and Malaria}},
  title = {Pakistan National AIDS Spending Assessment report 2021--2023},
  institution = {Ministry of National Health Services, Regulations and Coordination},
  address = {Islamabad},
  year = {2024},
  url = {https://www.unaids.org/sites/default/files/NASAreport_pakistan_2020-2022_en.pdf}
}""",
    "WHOPrEP2025": """@article{WHOPrEP2025,
  author = {Chikoko, T and Fatima, H and Saeed, N},
  title = {Expanding community-delivered HIV pre-exposure prophylaxis models in Pakistan},
  journal = {Eastern Mediterranean Health Journal},
  year = {2025},
  volume = {31},
  number = {8},
  pages = {484--485}
}""",
    "vonElm2007STROBE": """@article{vonElm2007STROBE,
  author = {von Elm, E and Altman, DG and Egger, M and Pocock, SJ and Gotzsche, PC and Vandenbroucke, JP},
  title = {The Strengthening the Reporting of Observational Studies in Epidemiology statement: guidelines for reporting observational studies},
  journal = {Lancet},
  year = {2007},
  volume = {370},
  number = {9596},
  pages = {1453--1457},
  doi = {10.1016/S0140-6736(07)61602-X}
}""",
    "PSLM2007": """@techreport{PSLM2007,
  author = {{Pakistan Bureau of Statistics}},
  title = {Pakistan Social and Living Standards Measurement Survey 2006--07: district level report},
  institution = {Pakistan Bureau of Statistics},
  address = {Islamabad},
  year = {2008}
}""",
    "PSLM2011": """@techreport{PSLM2011,
  author = {{Pakistan Bureau of Statistics}},
  title = {Pakistan Social and Living Standards Measurement Survey 2010--11: district level report},
  institution = {Pakistan Bureau of Statistics},
  address = {Islamabad},
  year = {2012}
}""",
    "PSLM2015": """@techreport{PSLM2015,
  author = {{Pakistan Bureau of Statistics}},
  title = {Pakistan Social and Living Standards Measurement Survey 2014--15: national, provincial and district report},
  institution = {Pakistan Bureau of Statistics},
  address = {Islamabad},
  year = {2016}
}""",
    "Jamal2013Poverty": """@techreport{Jamal2013Poverty,
  author = {Jamal, H},
  title = {Estimating sub-national poverty and inequality in Pakistan},
  institution = {Social Policy and Development Centre},
  address = {Karachi},
  year = {2013},
  number = {Research Report 85}
}""",
    "PES2007": """@techreport{PES2007,
  author = {{Government of Pakistan, Finance Division}},
  title = {Pakistan Economic Survey 2006--07: overview},
  institution = {Ministry of Finance},
  address = {Islamabad},
  year = {2007},
  url = {https://www.finance.gov.pk/survey_0607.html}
}""",
    "PES2011": """@techreport{PES2011,
  author = {{Government of Pakistan, Finance Division}},
  title = {Pakistan Economic Survey 2010--11: overview},
  institution = {Ministry of Finance},
  address = {Islamabad},
  year = {2011},
  url = {https://www.finance.gov.pk/survey_1011.html}
}""",
    "PES2015": """@techreport{PES2015,
  author = {{Government of Pakistan, Finance Division}},
  title = {Pakistan Economic Survey 2014--15: overview},
  institution = {Ministry of Finance},
  address = {Islamabad},
  year = {2015},
  url = {https://www.finance.gov.pk/survey_1415.html}
}""",
    "PES2017": """@techreport{PES2017,
  author = {{Government of Pakistan, Finance Division}},
  title = {Pakistan Economic Survey 2016--17: overview},
  institution = {Ministry of Finance},
  address = {Islamabad},
  year = {2017},
  url = {https://www.finance.gov.pk/survey_1617.html}
}""",
}


def create_bibtex(path: Path) -> list[str]:
    source = (ROOT / "literature" / "references.bib").read_text(encoding="utf-8")
    entries = parse_bib_entries(source)
    entries.update(EXTRA_BIB)
    manuscript_source = (ROOT / "manuscript" / "full_manuscript_source.md").read_text(encoding="utf-8")
    _, order = resolve_citations(manuscript_source)
    missing = [key for key in order if key not in entries]
    if missing:
        raise RuntimeError(f"Missing BibTeX records: {missing}")
    path.write_text("\n\n".join(entries[key] for key in order) + "\n", encoding="utf-8")
    return order


def copy_figures(figure_dir: Path) -> None:
    safe_stems = {
        1: "Recent_economic_deterioration_and_mapped_FSW_density",
        2: "Count_city_scale_and_density_contrast",
        3: "Mapped_population_change_during_deterioration_and_recovery",
    }
    for number, spec in enumerate(FIGURES.values(), start=1):
        stem = safe_stems[number]
        png_path = figure_dir / f"Figure_{number}_{stem}.png"
        shutil.copy2(spec["path"], png_path)
        with Image.open(spec["path"]) as image:
            scale = max(1, round(3600 / image.width))
            resized = image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)
            resized.convert("RGB").save(figure_dir / f"Figure_{number}_{stem}_600dpi.tiff", dpi=(600, 600), compression="tiff_lzw")

    captions = "\n\n".join(spec["caption"] for spec in FIGURES.values()) + "\n"
    (figure_dir / "Figure_captions.txt").write_text(captions, encoding="utf-8")
    shutil.copy2(ROOT / "results" / "tables" / "table_primary_city_data.csv", figure_dir / "Figure_1_source_data.csv")
    shutil.copy2(ROOT / "data" / "processed" / "paper1_2011_exploratory_features.csv", figure_dir / "Figure_2_source_data.csv")
    shutil.copy2(ROOT / "results" / "tables" / "exploratory_macro_improvement_contrasts.csv", figure_dir / "Figure_3_source_data_period_contrasts.csv")
    shutil.copy2(ROOT / "results" / "tables" / "exploratory_macro_improvement_city_counts.csv", figure_dir / "Figure_3_source_data_city_counts.csv")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    rows = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "MANIFEST_SHA256.csv"):
        rows.append((str(path.relative_to(directory)).replace("\\", "/"), path.stat().st_size, sha256(path)))
    with (directory / "MANIFEST_SHA256.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "bytes", "sha256"])
        writer.writerows(rows)


def make_zip(source_dir: Path, output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(source_dir))


def build() -> None:
    safe_reset(OUT)
    manuscript_dir = FILES / "01_Manuscript"
    title_dir = FILES / "02_Title_Page"
    tables_dir = FILES / "03_Tables"
    table_csv_dir = tables_dir / "CSV"
    figures_dir = FILES / "04_Figures"
    supplement_dir = FILES / "05_Supplementary_Material"
    reporting_dir = FILES / "06_Reporting_Checklist"
    reference_dir = FILES / "07_References"
    reproducibility_dir = FILES / "08_Reproducibility"
    journal_dir = FILES / "09_Journal_Target"
    for directory in (manuscript_dir, title_dir, table_csv_dir, figures_dir, supplement_dir, reporting_dir, reference_dir, reproducibility_dir, journal_dir):
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ROOT / "manuscript" / "paper1_full_manuscript_vancouver.docx", manuscript_dir / "Paper1_Main_Manuscript.docx")
    shutil.copy2(ROOT / "manuscript" / "paper1_full_manuscript_vancouver.md", manuscript_dir / "Paper1_Main_Manuscript.md")

    create_title_page(title_dir / "Paper1_Title_Page.docx")
    create_tables_docx(tables_dir / "Paper1_Manuscript_Tables.docx", table_csv_dir)
    copy_figures(figures_dir)
    create_supplement(supplement_dir / "Paper1_Supplementary_Appendix.docx")
    create_strobe(reporting_dir / "Paper1_STROBE_Cross_Sectional_Checklist.docx")
    order = create_bibtex(reference_dir / "Paper1_References_45.bib")
    (reference_dir / "Paper1_Vancouver_Reference_List.txt").write_text(
        "\n".join(f"{index}. {REFERENCES[key]}" for index, key in enumerate(order, start=1)) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(ROOT / "journal_selection" / "JOURNAL_TARGET_RECOMMENDATION.md", journal_dir / "JOURNAL_TARGET_RECOMMENDATION.md")

    for relative in (
        "README.md",
        "requirements.txt",
        "data/source_manifest.csv",
        "data/processed",
        "src",
        "scripts/run_full_analysis.ps1",
        "scripts/validate_literature_repository.py",
        "scripts/validate_manuscript.py",
        "results/diagnostics",
        "results/tables",
        "results/analysis_summary.md",
        "results/confirmatory_analysis_summary.md",
    ):
        source = ROOT / relative
        target = reproducibility_dir / relative
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    readme = f"""# Paper 1 journal submission files

Study: {TITLE}

This directory contains the author manuscript, separate title page, editable tables, publication figures, supplementary appendix, STROBE checklist, references, and a de-identified reproducibility package. Raw source PDFs are intentionally excluded because they remain third-party publications; their URLs and checksums are recorded in `08_Reproducibility/data/source_manifest.csv`.

## Submission status

The manuscript and declarations are complete. The package supplies the derived analytical data, code, source manifest, statistical outputs, and validation reports cited in the data-availability statement. Raw source PDFs are excluded because they are third-party publications; their publisher URLs and checksums are recorded in the source manifest.
"""
    (FILES / "README.md").write_text(readme, encoding="utf-8")

    write_manifest(FILES)

    components = {
        "Paper1_Tables_and_Figures.zip": [tables_dir, figures_dir],
        "Paper1_Supplementary_Materials.zip": [supplement_dir, reporting_dir],
        "Paper1_Reproducibility_Data_and_Code.zip": [reproducibility_dir],
        "Paper1_References.zip": [reference_dir],
    }
    for zip_name, directories in components.items():
        staging = OUT / f"_{Path(zip_name).stem}"
        staging.mkdir()
        for directory in directories:
            shutil.copytree(directory, staging / directory.name)
        write_manifest(staging)
        make_zip(staging, OUT / zip_name)
        shutil.rmtree(staging)

    make_zip(FILES, OUT / "Paper1_Complete_Submission_Materials.zip")

    print(f"Built submission package in {OUT}")
    print(f"BibTeX records: {len(order)}")
    print(f"Manuscript tables: {len(TABLES)}")
    print(f"Manuscript figures: {len(FIGURES)}")
    print(f"Supplementary tables: {len(SUPPLEMENT_TABLES)}")


if __name__ == "__main__":
    build()
