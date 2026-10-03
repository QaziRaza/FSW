"""Build the Vancouver-cited Markdown and submission-ready DOCX manuscript."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "full_manuscript_source.md"
MARKDOWN_OUT = ROOT / "manuscript" / "paper1_full_manuscript_vancouver.md"
DOCX_OUT = ROOT / "manuscript" / "paper1_full_manuscript_vancouver.docx"

TITLE = "Economic conditions and the changing scale and organisation of female sex work in Pakistan: a multi-period ecological study"
AFFILIATION = "Health Services Academy, NIH Complex, Park Road, Chak Shahzad, Islamabad, 44000, Pakistan"
AUTHOR_RECORDS = [
    {
        "name": "Qazi Raza",
        "degree": "MPH",
        "email": "qaziraza.rq@gmail.com",
        "orcid": "https://orcid.org/0000-0003-4303-3390",
        "ssrn": "12309708",
        "corresponding": True,
    },
    {
        "name": "Amna Khan",
        "degree": "MPH",
        "email": "amnaathar045@gmail.com",
        "orcid": "https://orcid.org/0009-0000-9152-3912",
        "corresponding": False,
    },
    {
        "name": "Maham Qazi",
        "degree": "BS Public Health",
        "email": "qazimaham.mq@gmail.com",
        "orcid": "https://orcid.org/0009-0002-1199-7240",
        "corresponding": False,
    },
]


REFERENCES = {
    "WHO2025Pakistan": "World Health Organization Regional Office for the Eastern Mediterranean. HIV infections rise in Pakistan; WHO and UNAIDS call to action [Internet]. Cairo: WHO EMRO; 2025 Dec 1 [cited 2026 Oct 3]. Available from: https://www.emro.who.int/pak/pakistan-news/hiv-infections-rise-in-pakistan-who-and-unaids-call-to-action.html",
    "PakistanStrategy2021": "Government of Pakistan, Ministry of National Health Services, Regulations and Coordination. Pakistan AIDS Strategy IV 2021-2025 [Internet]. Islamabad: Government of Pakistan; 2021 [cited 2026 Oct 3]. Available from: https://extranet.who.int/cpcd/sites/default/files/public_file_repository/PAK_Pakistan_National-Strategic-Plan-HIV_2021-2025.pdf",
    "NASAPakistan2024": "Government of Pakistan, Common Management Unit for AIDS, TB and Malaria. Pakistan National AIDS Spending Assessment report 2021-2023 [Internet]. Islamabad: Ministry of National Health Services, Regulations and Coordination; 2024 [cited 2026 Oct 3]. Available from: https://www.unaids.org/sites/default/files/NASAreport_pakistan_2020-2022_en.pdf",
    "NACP2017RoundV": "National AIDS Control Programme. Integrated Biological and Behavioral Surveillance in Pakistan: Round 5 [Internet]. Islamabad: National AIDS Control Programme; 2017 [cited 2026 Oct 3]. Available from: https://www.nacp.gov.pk/repository/howwework/pdf/IBBS%20Report%20Round%205.pdf",
    "WHOPrEP2025": "Chikoko T, Fatima H, Saeed N. Expanding community-delivered HIV pre-exposure prophylaxis models in Pakistan. East Mediterr Health J. 2025;31(8):484-5.",
    "Emmanuel2013Organisation": "Emmanuel F, Thompson LH, Athar U, Salim M, Sonia A, Akhtar N, et al. The organisation, operational dynamics and structure of female sex work in Pakistan. Sex Transm Infect. 2013;89 Suppl 2:ii29-33. doi:10.1136/sextrans-2013-051062.",
    "Blanchard2008Variation": "Blanchard JF, Khan A, Bokhari A. Variations in the population size, distribution and client volume among female sex workers in seven cities of Pakistan. Sex Transm Infect. 2008;84 Suppl 2:ii24-27. doi:10.1136/sti.2008.033167.",
    "Emmanuel2013Allocation": "Emmanuel F, Thompson LH, Salim M, Akhtar N, Reza TE, Hafeez H, et al. The size and distribution of key populations at greater risk of HIV in Pakistan: implications for resource allocation for scaling up HIV prevention programmes. Sex Transm Infect. 2013;89 Suppl 2:ii11-17. doi:10.1136/sextrans-2013-051017.",
    "Mishra2013Vulnerabilities": "Mishra S, Thompson LH, Sonia A, Khalid N, Emmanuel F, Blanchard JF. Sexual behaviour, structural vulnerabilities and HIV prevalence among female sex workers in Pakistan. Sex Transm Infect. 2013;89 Suppl 2:ii34-42. doi:10.1136/sextrans-2012-050776.",
    "Khan2011Lahore": "Khan MS, Unemo M, Zaman S, Lundborg CS. HIV, STI prevalence and risk behaviours among women selling sex in Lahore, Pakistan. BMC Infect Dis. 2011;11:119. doi:10.1186/1471-2334-11-119.",
    "RobinsonYeh2011Risk": "Robinson J, Yeh E. Transactional sex as a response to risk in western Kenya. Am Econ J Appl Econ. 2011;3(1):35-64. doi:10.1257/app.3.1.35.",
    "Treibich2022Drought": "Treibich C, Bell E, Lepine A, Blanc E. From a drought to HIV: an analysis of the effect of droughts on transactional sex and sexually transmitted infections in Malawi. SSM Popul Health. 2022;19:101221. doi:10.1016/j.ssmph.2022.101221.",
    "Goehring2025FallenWomen": "Goehring G. Fallen women: recessions and the supply of sex work. J Public Econ. 2025;247:105405. doi:10.1016/j.jpubeco.2025.105405.",
    "Wilson2012Booms": "Wilson N. Economic booms and risky sexual behavior: evidence from Zambian copper mining cities. J Health Econ. 2012;31(6):797-812. doi:10.1016/j.jhealeco.2012.07.007.",
    "MahadeshwarZhou2024Outside": "Mahadeshwar R, Zhou A. Outside options and the supply of sex work [working paper on the Internet]. 2024 Nov 14 [cited 2026 Oct 3]. Available from: https://www.isid.ac.in/~acegd/acegd2024/papers/RuchiMahadeshwar.pdf",
    "Elmes2017Reconfiguration": "Elmes J, Skovdal M, Nhongo K, Ward H, Campbell C, Hallett TB, et al. A reconfiguration of the sex trade: how social and structural changes in eastern Zimbabwe left women involved in sex work and transactional sex more vulnerable. PLoS One. 2017;12(2):e0171916. doi:10.1371/journal.pone.0171916.",
    "Steen2019Economy": "Steen R, Hontelez JAC, Mugurungi O, Mpofu A, Matthijsse SM, de Vlas SJ, et al. Economy, migrant labour and sex work: interplay of HIV epidemic drivers in Zimbabwe over three decades. AIDS. 2019;33(1):123-31. doi:10.1097/QAD.0000000000002066.",
    "Manopaiboon2003Leaving": "Manopaiboon C, Bunnell RE, Kilmarx PH, Chaikummao S, Limpakarnjanarat K, Supawitkul S, et al. Leaving sex work: barriers, facilitating factors and consequences for female sex workers in northern Thailand. AIDS Care. 2003;15(1):39-52. doi:10.1080/012021000039743.",
    "WardDay2006Cohort": "Ward H, Day S. What happens to women who sell sex? Report of a unique occupational cohort. Sex Transm Infect. 2006;82(5):413-7. doi:10.1136/sti.2006.020982.",
    "Ingabire2012Kigali": "Ingabire MC, Mitchell K, Veldhuijzen N, Umulisa MM, Nyinawabega J, Kestelyn E, et al. Joining and leaving sex work: experiences of women in Kigali, Rwanda. Cult Health Sex. 2012;14(9):1037-47. doi:10.1080/13691058.2012.713120.",
    "Learmonth2015Barriers": "Learmonth D, Hakala S, Keller M. I can't carry on like this: barriers to exiting the street-based sex trade in South Africa. Health Psychol Behav Med. 2015;3(1):348-65. doi:10.1080/21642850.2015.1095098.",
    "White2020Interruptions": "White RH, Park JN, Galai N, Decker MR, Allen ST, Footer KHA, et al. Short-term interruptions to sex work among a prospective cohort of street-based cisgender female sex workers in Baltimore. Int J Drug Policy. 2020;84:102858. doi:10.1016/j.drugpo.2020.102858.",
    "Lora2025LifeCourse": "Lora WS, Sakala D, Saidi A, Nyapigoti W, Sanudi E, Shahmanesh M, et al. Exploring the interplay of social and physical factors in risk dynamics and transitions across the life-course of female sex workers in Blantyre, Malawi: a longitudinal narrative study. AIDS Behav. 2025;29:3444-56. doi:10.1007/s10461-025-04790-z.",
    "Emmanuel2013SGS": "Emmanuel F, Salim M, Akhtar N, Arshad S, Reza TE. Second-generation surveillance for HIV/AIDS in Pakistan: results from the 4th round of Integrated Behavior and Biological Survey 2011-2012. Sex Transm Infect. 2013;89 Suppl 3:iii23-28. doi:10.1136/sextrans-2013-051161.",
    "Reza2013Patterns": "Reza T, Melesse DY, Shafer LA, Salim M, Altaf A, Sonia A, et al. Patterns and trends in Pakistan's heterogeneous HIV epidemic. Sex Transm Infect. 2013;89 Suppl 2:ii4-10. doi:10.1136/sextrans-2012-050872.",
    "Melesse2018Heterogeneity": "Melesse DY, Shafer LA, Emmanuel F, Reza T, Achakzai BK, Furqan S, et al. Heterogeneity in geographical trends of HIV epidemics among key populations in Pakistan: a mathematical modeling study of survey data. J Glob Health. 2018;8(1):010412. doi:10.7189/jogh.08.010412.",
    "vonElm2007STROBE": "von Elm E, Altman DG, Egger M, Pocock SJ, Gotzsche PC, Vandenbroucke JP; STROBE Initiative. The Strengthening the Reporting of Observational Studies in Epidemiology statement: guidelines for reporting observational studies. Lancet. 2007;370(9596):1453-7. doi:10.1016/S0140-6736(07)61602-X.",
    "NACP2007RoundII": "National AIDS Control Programme. HIV second generation surveillance in Pakistan: national report round II [Internet]. Islamabad: National AIDS Control Programme; 2007 [cited 2026 Oct 3]. Available from: https://www.nacp.gov.pk/repository/howwework/pdf/SGS%20Round%202%20Report%202006-07.pdf",
    "NACP2011RoundIV": "National AIDS Control Programme. HIV second generation surveillance in Pakistan: national report round IV [Internet]. Islamabad: National AIDS Control Programme; 2011 [cited 2026 Oct 3]. Available from: https://www.anf.gov.pk/library/report-round4-2011.pdf",
    "PACP2014Punjab": "Punjab AIDS Control Program. Integrated biological and behavioral surveillance in Punjab 2014 [Internet]. Lahore: Punjab AIDS Control Program; 2014 [cited 2026 Oct 3]. Available from: https://phkh.nhsrc.pk/sites/default/files/2021-01/IBBS%20Punjab%202014.pdf",
    "NACP2015Mapping": "National AIDS Control Programme. Mapping of key populations in Pakistan 2015 [Internet]. Islamabad: National AIDS Control Programme; 2015 [cited 2026 Oct 3]. Available from: https://medbox.org/document/mapping-of-key-populations-in-pakistan-2015",
    "PSLM2007": "Pakistan Bureau of Statistics. Pakistan Social and Living Standards Measurement Survey 2006-07: district level report [Internet]. Islamabad: Pakistan Bureau of Statistics; 2008 [cited 2026 Oct 3]. Available from: https://www.pbs.gov.pk/sites/default/files/pslm/publications/pslm2006_07/pslm2006_07.pdf",
    "PSLM2011": "Pakistan Bureau of Statistics. Pakistan Social and Living Standards Measurement Survey 2010-11: district level report [Internet]. Islamabad: Pakistan Bureau of Statistics; 2012 [cited 2026 Oct 3]. Available from: https://www.pbs.gov.pk/sites/default/files/pslm/publications/pslm2010_11/pslm2010_11.pdf",
    "PSLM2015": "Pakistan Bureau of Statistics. Pakistan Social and Living Standards Measurement Survey 2014-15: national, provincial and district report [Internet]. Islamabad: Pakistan Bureau of Statistics; 2016 [cited 2026 Oct 3]. Available from: https://www.pbs.gov.pk/sites/default/files/pslm/publications/pslm2014_15/pslm_2014-15_national-provincial-district_report.pdf",
    "Jamal2013Poverty": "Jamal H. Estimating sub-national poverty and inequality in Pakistan. Karachi: Social Policy and Development Centre; 2013. Research Report No. 85.",
    "PES2007": "Government of Pakistan, Finance Division. Pakistan Economic Survey 2006-07: overview [Internet]. Islamabad: Ministry of Finance; 2007 [cited 2026 Oct 3]. Available from: https://www.finance.gov.pk/survey_0607.html",
    "PES2011": "Government of Pakistan, Finance Division. Pakistan Economic Survey 2010-11: overview [Internet]. Islamabad: Ministry of Finance; 2011 [cited 2026 Oct 3]. Available from: https://www.finance.gov.pk/survey_1011.html",
    "PES2015": "Government of Pakistan, Finance Division. Pakistan Economic Survey 2014-15: overview [Internet]. Islamabad: Ministry of Finance; 2015 [cited 2026 Oct 3]. Available from: https://www.finance.gov.pk/survey_1415.html",
    "PES2017": "Government of Pakistan, Finance Division. Pakistan Economic Survey 2016-17: overview [Internet]. Islamabad: Ministry of Finance; 2017 [cited 2026 Oct 3]. Available from: https://www.finance.gov.pk/survey_1617.html",
    "Fearon2020ZimbabwePSE": "Fearon E, Chabata ST, Magutshwa S, et al. Estimating the population size of female sex workers in Zimbabwe: comparison of estimates obtained using different methods in twenty sites and development of a national-level estimate. J Acquir Immune Defic Syndr. 2020;85(1):30-8. doi:10.1097/QAI.0000000000002393.",
    "Davey2019Mobility": "Davey C, Dirawo J, Mushati P, Magutshwa S, Hargreaves JR, Cowan FM. Mobility and sex work: why, where, when? A typology of female-sex-worker mobility in Zimbabwe. Soc Sci Med. 2019;220:322-30. doi:10.1016/j.socscimed.2018.11.027.",
    "Shannon2015Structural": "Shannon K, Strathdee SA, Goldenberg SM, Duff P, Mwangi P, Rusakova M, et al. Global epidemiology of HIV among female sex workers: influence of structural determinants. Lancet. 2015;385(9962):55-71. doi:10.1016/S0140-6736(14)60931-4.",
    "JarvisKing2024Trajectories": "Jarvis-King L. Trajectories of vulnerability and resistance among independent indoor sex workers during economic decline. Sociol Res Online. 2024;29(1):137-53. doi:10.1177/13607804231162757.",
    "Wamoyi2016Transactional": "Wamoyi J, Stobeanau K, Bobrova N, Abramsky T, Watts C. Transactional sex and risk for HIV infection in sub-Saharan Africa: a systematic review and meta-analysis. J Int AIDS Soc. 2016;19(1):20992. doi:10.7448/IAS.19.1.20992.",
    "Mihretie2023Prevalence": "Mihretie GN, Kassa BG, Ayele AD, Liyeh TM, Belay HG, Miskr AD, et al. Transactional sex among women in sub-Saharan Africa: a systematic review and meta-analysis. PLoS One. 2023;18(6):e0286850. doi:10.1371/journal.pone.0286850.",
}


TABLES = {
    "TABLE_1": {
        "caption": "Table 1. Surveillance rounds, available measures, and analytical use",
        "headers": ["Round", "Cities", "Available FSW measures", "Economic pairing", "Analytical use"],
        "widths": [0.8, 0.6, 2.1, 1.5, 1.5],
        "rows": [
            ["2006-07", "12", "Mapped total and typology", "PSLM 2006-07; PES 2006-07", "Structural replication and common-city change"],
            ["2011", "15", "Mapped total, density, typology, and network structure", "PSLM 2010-11; model-based poverty; PES 2010-11", "Primary cross-section and multi-marker analysis"],
            ["2014", "4", "Mapped total and typology in Punjab", "PSLM 2014-15; PES 2014-15", "Regional structural replication and recovery comparison"],
            ["2016-17", "18", "Printed city totals only", "PES 2016-17; local district exposure not forced", "Context and common-city count comparison"],
        ],
    },
    "TABLE_2": {
        "caption": "Table 2. Primary density result and principal sensitivity analyses in 2011",
        "headers": ["Analysis", "n", "Estimate", "95% CI", "p value"],
        "widths": [2.8, 0.45, 0.85, 1.35, 0.7],
        "rows": [
            ["Recent deterioration vs density, Spearman", "15", "rho -0.138", "-0.597 to 0.372", "0.620*"],
            ["Recent deterioration vs density, Pearson", "15", "r -0.196", "-", "0.484"],
            ["Urban poverty vs density, Spearman", "15", "rho 0.281", "-", "0.311"],
            ["Female illiteracy vs density, Spearman", "15", "rho 0.316", "-", "0.251"],
            ["Sanitation deprivation vs density, Spearman", "15", "rho -0.061", "-", "0.829"],
            ["All-area deterioration vs density, Spearman", "15", "rho -0.091", "-", "0.747"],
            ["Close geographic matches only", "9", "rho 0.183", "-", "0.637"],
            ["Unadjusted OLS with HC3 SE", "15", "beta -0.055", "-0.211 to 0.101", "0.462"],
            ["OLS adjusted for log mapped total", "15", "beta -0.029", "-0.269 to 0.210", "0.794"],
            ["Log-density OLS with HC3 SE", "15", "beta -0.007", "-0.025 to 0.010", "0.394"],
        ],
        "note": "*Two-sided permutation p value; the confidence interval is a percentile bootstrap interval. CI, confidence interval; HC3 SE, heteroskedasticity-robust standard error; OLS, ordinary least squares.",
    },
    "TABLE_3": {
        "caption": "Table 3. Acute deterioration and chronic deprivation across selected 2011 FSW markers",
        "headers": ["Economic dimension", "Mapped density rho", "Mapped total rho", "Implied city scale rho", "Kothikhana share rho", "Cellphone share rho"],
        "widths": [1.45, 0.95, 0.95, 1.05, 1.05, 1.05],
        "rows": [
            ["Recent urban deterioration", "-0.138", "0.657", "0.625", "0.618", "-0.515"],
            ["Chronic deprivation", "0.315", "-0.700", "-0.718", "-0.409", "0.552"],
        ],
        "note": "Values are Spearman rank correlations across 15 cities. The implied scale is derived from mapped count and source-reported density and is used only to diagnose city scale.",
    },
    "TABLE_4": {
        "caption": "Table 4. Common-city mapped population and organisational change across economic periods",
        "headers": ["Comparison", "Cities", "Mapped total change", "Annualised change", "Median home change", "Median street change", "Sign-test p"],
        "widths": [1.35, 0.55, 1.0, 1.0, 1.05, 1.05, 0.75],
        "rows": [
            ["2006-07 to 2011", "10", "+66.25%", "+11.96%", "+18.32 pp", "-24.16 pp", "0.109"],
            ["2011 to 2014", "4", "+16.77%", "+5.30%", "-26.10 pp", "+17.11 pp", "0.125"],
            ["2011 to 2016-17", "10", "+3.36%", "+0.60%", "Not available", "Not available", "0.754"],
        ],
        "note": "Annualised changes use approximate intervals of 4.5, 3.0, and 5.5 years. pp, percentage points.",
    },
    "TABLE_5": {
        "caption": "Table 5. Selected round-level economic-marker correlations",
        "headers": ["Economic indicator", "FSW marker", "Rounds", "Spearman rho", "Exact p", "FDR q"],
        "widths": [1.4, 2.0, 0.65, 0.9, 0.75, 0.75],
        "rows": [
            ["GDP growth", "Median city mapped total", "4", "-0.600", "0.417", "1.000"],
            ["CPI inflation", "Median city mapped total", "4", "0.400", "0.750", "1.000"],
            ["CPI inflation", "Home share", "3", "1.000", "0.333", "1.000"],
            ["CPI inflation", "Home minus street balance", "3", "1.000", "0.333", "1.000"],
            ["GDP growth", "Street share", "3", "1.000", "0.333", "1.000"],
            ["GDP growth", "Reported household deterioration", "4", "-0.800", "0.333", "1.000"],
            ["Per-capita income", "Kothikhana share", "3", "1.000", "0.333", "1.000"],
        ],
        "note": "All 32 macro-marker tests used exact permutation inference and Benjamini-Hochberg adjustment. Directional coefficients with three or four rounds are descriptive.",
    },
}


FIGURES = {
    "FIGURE_1": {
        "path": ROOT / "results" / "figures" / "figure_1_primary_scatter.png",
        "caption": "Figure 1. Recent urban economic deterioration and mapped female sex worker density across 15 Pakistani cities in 2011. The labelled scatterplot shows the weak inverse rank association and the broad dispersion of density at similar levels of deterioration.",
    },
    "FIGURE_2": {
        "path": ROOT / "results" / "figures" / "exploratory_figure_3_scale_contrast.png",
        "caption": "Figure 2. The count, city-scale, and density contrast in 2011. Recent deterioration aligned with larger mapped totals and larger implied population scale, while chronic deprivation showed the opposite scale pattern and a weakly positive density association.",
    },
    "FIGURE_3": {
        "path": ROOT / "results" / "figures" / "exploratory_figure_6_better_economy_test.png",
        "caption": "Figure 3. Common-city mapped population change during deterioration and recovery. The combined population expanded rapidly before 2011 and then grew more slowly, approaching a plateau through 2016-17.",
    },
}


def compact_numbers(numbers: list[int]) -> str:
    numbers = sorted(set(numbers))
    parts: list[str] = []
    start = previous = numbers[0]
    for value in numbers[1:] + [None]:
        if value is not None and value == previous + 1:
            previous = value
            continue
        if previous - start >= 2:
            parts.append(f"{start}-{previous}")
        elif previous == start:
            parts.append(str(start))
        else:
            parts.extend([str(start), str(previous)])
        if value is not None:
            start = previous = value
    return ",".join(parts)


def resolve_citations(text: str) -> tuple[str, list[str]]:
    order: list[str] = []

    def replace(match: re.Match[str]) -> str:
        keys = [part.strip().lstrip("@") for part in match.group(1).split(";")]
        for key in keys:
            if key not in REFERENCES:
                raise KeyError(f"No Vancouver reference string for {key}")
            if key not in order:
                order.append(key)
        numbers = [order.index(key) + 1 for key in keys]
        return f"[{compact_numbers(numbers)}]"

    resolved = re.sub(r"\[@([^\]]+)\]", replace, text)
    if "[@" in resolved:
        raise AssertionError("Unresolved citation marker")
    return resolved, order


def markdown_table(table: dict) -> str:
    headers = table["headers"]
    lines = [table["caption"], "", "| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in table["rows"])
    if table.get("note"):
        lines.extend(["", table["note"]])
    return "\n".join(lines)


def produce_markdown(resolved: str, order: list[str]) -> str:
    output = resolved
    for marker, table in TABLES.items():
        output = output.replace(f"[[{marker}]]", markdown_table(table))
    for marker, figure in FIGURES.items():
        rel = figure["path"].relative_to(ROOT).as_posix()
        output = output.replace(f"[[{marker}]]", f"![{figure['caption']}]({rel})\n\n{figure['caption']}")
    references = "\n\n".join(f"{i}. {REFERENCES[key]}" for i, key in enumerate(order, start=1))
    output = output.replace("[[REFERENCES]]", references)
    MARKDOWN_OUT.write_text(output.rstrip() + "\n", encoding="utf-8")
    return output


def set_run_font(run, name: str = "Times New Roman", size: float = 12, bold: bool | None = None, italic: bool | None = None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_inline_runs(paragraph, text: str, size: float = 12):
    parts = re.split(r"(\^[^\^]+\^|\*[^\*]+\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("^") and part.endswith("^"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=size)
            run.font.superscript = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=size, italic=True)
        else:
            run = paragraph.add_run(part)
            set_run_font(run, size=size)


def add_author_block(
    doc: Document,
    font_size: float = 11,
    include_ssrn: bool = True,
    wrap_corresponding: bool = False,
) -> None:
    """Add the numbered author/contact layout approved by the authors."""
    for number, author in enumerate(AUTHOR_RECORDS, start=1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(8 if number == 1 else 5)
        p.paragraph_format.space_after = Pt(2)
        author_line = f"{number}. {author['name']}, {author['degree']}, {AFFILIATION}"
        if wrap_corresponding and author.get("corresponding"):
            first, second = author_line.split(", Islamabad", 1)
            run = p.add_run(first + ",")
            set_run_font(run, size=font_size)
            p.add_run().add_break()
            run = p.add_run("Islamabad" + second)
        else:
            run = p.add_run(author_line)
        set_run_font(run, size=font_size)
        if author.get("corresponding"):
            marker = p.add_run(" [Corresponding Author]")
            set_run_font(marker, size=font_size, bold=True)
            marker.font.highlight_color = WD_COLOR_INDEX.YELLOW

        details = [("Email ID", author["email"]), ("ORCID", author["orcid"])]
        if include_ssrn and author.get("ssrn"):
            details.append(("SSRN Author ID", author["ssrn"]))
        for label, value in details:
            detail = doc.add_paragraph(style="List Bullet")
            detail.alignment = WD_ALIGN_PARAGRAPH.LEFT
            detail.paragraph_format.left_indent = Inches(0.55)
            detail.paragraph_format.first_line_indent = Inches(-0.2)
            detail.paragraph_format.line_spacing = 1.0
            detail.paragraph_format.space_after = Pt(1)
            label_run = detail.add_run(f"{label}: ")
            set_run_font(label_run, size=font_size)
            value_run = detail.add_run(value)
            set_run_font(value_run, size=font_size)
            if label in {"Email ID", "ORCID"}:
                value_run.font.color.rgb = RGBColor(5, 99, 193)
                value_run.font.underline = True


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=100, bottom=90, end=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = borders.find(qn(f"w:{edge}"))
        if tag is None:
            tag = OxmlElement(f"w:{edge}")
            borders.append(tag)
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "4")
        tag.set(qn("w:color"), "D9D9D9")


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_table(doc: Document, spec: dict):
    caption = doc.add_paragraph()
    caption.style = doc.styles["Caption"]
    caption.paragraph_format.keep_with_next = True
    add_inline_runs(caption, spec["caption"], size=10)
    caption.runs[0].bold = True

    table = doc.add_table(rows=1, cols=len(spec["headers"]))
    table.autofit = False
    set_table_borders(table)
    repeat_header(table.rows[0])
    for index, (cell, header, width) in enumerate(zip(table.rows[0].cells, spec["headers"], spec["widths"])):
        cell.width = Inches(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "1F4E78")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(header)
        set_run_font(r, size=8.5, bold=True)
        r.font.color.rgb = RGBColor(255, 255, 255)
    for row_index, values in enumerate(spec["rows"]):
        cells = table.add_row().cells
        for index, (cell, value, width) in enumerate(zip(cells, values, spec["widths"])):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if row_index % 2:
                set_cell_shading(cell, "EAF2F8")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if index in (0, 2, 3, 4) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            add_inline_runs(p, str(value), size=8.5)
    if spec.get("note"):
        note = doc.add_paragraph()
        note.paragraph_format.space_before = Pt(3)
        note.paragraph_format.space_after = Pt(8)
        note.paragraph_format.line_spacing = 1.0
        add_inline_runs(note, spec["note"], size=9)
        note.runs[0].italic = True


def add_figure(doc: Document, spec: dict):
    if not spec["path"].exists():
        raise FileNotFoundError(spec["path"])
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(spec["path"]), width=Inches(6.25))
    caption = doc.add_paragraph()
    caption.style = doc.styles["Caption"]
    caption.alignment = WD_ALIGN_PARAGRAPH.LEFT
    caption.paragraph_format.space_after = Pt(10)
    add_inline_runs(caption, spec["caption"], size=10)
    caption.runs[0].bold = True


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr_text, fld_char2])
    set_run_font(run, size=9)


def configure_document(doc: Document):
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)
    sect_pr = section._sectPr
    line_num = OxmlElement("w:lnNumType")
    line_num.set(qn("w:countBy"), "1")
    line_num.set(qn("w:start"), "1")
    line_num.set(qn("w:restart"), "continuous")
    sect_pr.append(line_num)
    add_page_number(section.footer.paragraphs[0])

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    normal.paragraph_format.space_after = Pt(0)

    for style_name, size in (("Title", 16), ("Subtitle", 13), ("Heading 1", 13), ("Heading 2", 12), ("Heading 3", 12)):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = style_name != "Subtitle"
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.keep_with_next = True
        # Word's built-in Title style can carry a theme border.  Journal
        # manuscripts should keep the title page plain, so remove any inherited
        # paragraph border from the style definition.
        style_ppr = style._element.get_or_add_pPr()
        style_border = style_ppr.find(qn("w:pBdr"))
        if style_border is not None:
            style_ppr.remove(style_border)
    doc.styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles["Subtitle"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption = doc.styles["Caption"]
    caption.font.name = "Times New Roman"
    caption._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    caption._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    caption.font.size = Pt(10)
    caption.font.color.rgb = RGBColor(0, 0, 0)


def add_body_paragraph(doc: Document, text: str, first_line: bool = True):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    p.paragraph_format.space_after = Pt(0)
    if first_line:
        p.paragraph_format.first_line_indent = Inches(0.3)
    add_inline_runs(p, text, size=12)
    return p


def build_docx(resolved: str, order: list[str]):
    doc = Document()
    configure_document(doc)
    lines = resolved.splitlines()
    abstract_index = next(i for i, line in enumerate(lines) if line == "## Abstract")

    p = doc.add_paragraph(style="Title")
    add_inline_runs(p, TITLE, size=16)
    add_author_block(doc)
    for line in lines[:abstract_index]:
        if not line.startswith(("Running title:", "Article type:")):
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        add_inline_runs(p, line, size=11)
    doc.add_page_break()

    paragraph_lines: list[str] = []

    def flush_paragraph():
        if paragraph_lines:
            text = " ".join(item.strip() for item in paragraph_lines)
            add_body_paragraph(doc, text)
            paragraph_lines.clear()

    for line in lines[abstract_index:]:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped == "[[REFERENCES]]":
            flush_paragraph()
            for number, key in enumerate(order, start=1):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(5)
                add_inline_runs(p, f"{number}. {REFERENCES[key]}", size=10)
            continue
        marker_match = re.fullmatch(r"\[\[(TABLE_\d+|FIGURE_\d+)\]\]", stripped)
        if marker_match:
            flush_paragraph()
            marker = marker_match.group(1)
            if marker.startswith("TABLE"):
                add_table(doc, TABLES[marker])
            else:
                add_figure(doc, FIGURES[marker])
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            p = doc.add_paragraph(style="Heading 2")
            add_inline_runs(p, stripped[4:], size=12)
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            heading = stripped[3:]
            p = doc.add_paragraph(style="Heading 1")
            add_inline_runs(p, heading, size=13)
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            p = doc.add_paragraph(style="Title")
            add_inline_runs(p, stripped[2:], size=16)
            continue
        paragraph_lines.append(stripped)
    flush_paragraph()

    props = doc.core_properties
    props.title = TITLE
    props.subject = "Multi-period ecological study using HIV surveillance and socioeconomic surveys"
    props.author = "Qazi Raza; Amna Khan; Maham Qazi"
    props.keywords = "female sex workers, HIV surveillance, economic distress, Pakistan, ecological study"
    props.comments = "Vancouver citation style manuscript"
    doc.save(DOCX_OUT)


def main():
    source = SOURCE.read_text(encoding="utf-8")
    resolved, order = resolve_citations(source)
    produce_markdown(resolved, order)
    build_docx(resolved, order)
    print(f"Built {MARKDOWN_OUT}")
    print(f"Built {DOCX_OUT}")
    print(f"References: {len(order)}")


if __name__ == "__main__":
    main()
