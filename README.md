# Economic conditions and the changing scale and organisation of female sex work in Pakistan: a multi-period ecological study

This repository contains the data, code, validation evidence, manuscript, and submission materials for a multi-period ecological study of economic conditions and female sex work in Pakistan. The analytical design is documented in `docs/analysis_plan.md`. The primary analysis asks whether district-level urban economic distress is associated with the mapped density of female sex workers (FSWs) across 15 Pakistani cities in 2011. Earlier and later mapping rounds are retained only for measures that are actually comparable.

## Public repository contents

The repository publishes the processed analytical datasets, complete analysis code, statistical outputs, figures, literature evidence files, manuscript, supplementary appendix, reporting checklist, and journal-submission packages. Downloaded third-party source reports are not redistributed. Their publisher URLs, expected filenames, file sizes, and SHA-256 checksums are recorded in `data/source_manifest.csv`; placement instructions are provided in `data/raw/README.md`.

## Design in one paragraph

The primary outcome is the 2011 mapping estimate of FSWs per 1,000 adult men. The prespecified primary exposure is the percentage of urban households in the matching PSLM district reporting that their economic situation was “much worse” or “worse” than one year earlier. Spearman correlation is primary. Poverty, female illiteracy, sanitation deprivation, Pearson correlation, leave-one-out estimates, influential-city exclusions, geographic-match restrictions, log outcome, and small-sample regression are sensitivity or exploratory analyses. Mapping rounds in 2006–07 and 2014 support typology-share replication. Round 5 (2016–17) provides city counts but no published adult-male density or city typology table in the acquired report, so it is context-only.

## Reproduce

From PowerShell in this directory:

```powershell
python -m pip install -r requirements.txt
python src/build_dataset.py
python src/validate_data.py
python src/analyse_primary.py
python src/analyse_replication.py
python src/make_outputs.py
```

The build is deterministic. It reads locally acquired primary-source files under `data/raw/`, writes tidy data to `data/processed/`, analytical results to `results/tables/`, figures to `results/figures/`, validation evidence to `results/diagnostics/`, and the integrated interpretation to `results/analysis_summary.md`. The processed data and generated results are included, so the analytical outputs remain inspectable even when the source reports have not yet been downloaded.

## Exploratory extension

After reproducing the frozen analysis, run the separate hypothesis-generating layer:

```powershell
python src/analyse_exploratory.py
python src/analyse_macro_markers.py
python src/make_exploratory_outputs.py
python src/validate_exploratory.py
python src/make_complete_analysis.py
python src/validate_complete_analysis.py
```

This extension pairs acute reported deterioration, chronic deprivation, absolute market size, mapped density, typology composition, network structure, national macroeconomic context, and deterioration-versus-recovery contrasts. The macro-marker layer tests GDP growth, inflation, per-capita income and unemployment against multiple count, typology and reported-distress markers at the survey-round level with exact permutation inference. It also constructs identical-city panels spanning deterioration and recovery to test whether mapped-population growth accelerates, slows or plateaus without incorrectly expecting the accumulated population stock to disappear. The authoritative integrated output is `results/analysis_summary.md`; the prespecified-only and expanded exploratory narratives are retained separately. All underlying correlations, models, paired tests, transitions, assumption verdicts, and proposed later tests are exported as inspectable CSV files. It does not modify the frozen primary result or treat post-hoc associations as confirmatory.

To rebuild and validate everything in the required order:

```powershell
.\scripts\run_full_analysis.ps1
```

Start with `WHAT_WE_KNOW.md` for the repository map and current answer.
The runner uses `PAPER1_PYTHON` when set, otherwise the bundled Codex Python runtime when present, and otherwise `python` on `PATH`.

## Literature repository

`literature/` contains the targeted comprehensive review prepared for the Discussion: a source-by-source evidence matrix, original abstract-style summaries, a finding-to-citation comparison map, a narrative synthesis, search documentation, and a BibTeX library. It prioritises Pakistan, treats the Zimbabwe economic-collapse literature as the closest comparison, and separately covers economic shocks, market reorganisation, demand, entry, exit, re-entry, and population-size measurement.

Validate its internal consistency with:

```powershell
python scripts/validate_literature_repository.py
```

## Manuscript

The analysis gate has been met and the complete journal manuscript is available in two forms:

- `manuscript/paper1_full_manuscript_vancouver.docx` — submission-format A4 Word manuscript with continuous line numbering, five tables, three figures, and Vancouver citations.
- `manuscript/paper1_full_manuscript_vancouver.md` — inspectable text equivalent.

`manuscript/full_manuscript_source.md` is the editable source, `scripts/build_manuscript.py` regenerates both outputs, and `manuscript/STROBE_reporting_map.md` maps the manuscript to the observational-reporting checklist. Rebuild and validate with:

```powershell
python scripts/build_manuscript.py
python scripts/validate_manuscript.py
```

The manuscript declarations are complete. The submission package supplies the derived analytical data, code, source manifest, statistical outputs, and validation reports cited in the data-availability statement.

### Sexually Transmitted Infections submission version

`journal_submissions/STI/` contains the separate journal-specific submission package. Its Original Research manuscript has 1,996 main-text words, a 281-word structured abstract, 30 references, two tables, two figures, the required three-part key-messages box, a title page, cover letter, supplementary appendix, reproducibility archive, and completed STROBE checklist. Run `python scripts/build_sti_submission.py` and `python scripts/validate_sti_submission.py` to rebuild and verify it.

## Boundaries

- This is an ecological analysis of city mapping estimates and district/urban-stratum indicators; it cannot identify individual-level causes.
- Mapping estimates are programmatic enumeration estimates, not a census of all FSWs.
- City-to-district matches are explicit and graded in `data/processed/geographic_crosswalk.csv`.
- No unavailable denominator is reconstructed. A density outcome is used only where the source reports it.
- LFS reports and Pakistan Economic Survey overviews provide period context only; they are not city predictors.
- National macro indicators are tested only at their true round-level grain (three or four observations), never duplicated across cities to inflate the sample size.
- The manuscript distinguishes observed results from literature-supported interpretation and labels unmeasured entry, exit, demand, and survey-visibility mechanisms accordingly.

