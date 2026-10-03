# What we know

This repository contains the current reproducible evidence on relationships between socioeconomic conditions and mapped female sex work across available Pakistani surveillance rounds.

## Current answer

**Yes. The complete available Pakistani survey series shows an economic signal.** The central pattern is not that recovery makes the existing FSW population disappear. It is that deterioration coincides with rapid expansion, while recovery coincides with a sharp slowdown toward a plateau:

- in four cities observed continuously through 2014, annualized mapped-population growth slowed from 9.65% during deterioration to 5.30% during recovery;
- in six cities observed continuously through 2016-17, growth slowed from 14.39% to 0.87%;
- the plateau is consistent with fewer net newcomers after economic improvement while people already in sex work remain because leaving for other work is difficult;
- the surveys measure the population stock, not individual entries and exits, so the newcomer mechanism is consistent with the data but not separately counted;
- recent economic deterioration is also associated with larger absolute mapped markets and a shift from street toward home-based work, not with higher per-capita density;
- chronic deprivation is associated with smaller absolute markets but somewhat higher density;
- kothikhana/intermediary organisation and cellphone-based work show opposing economic patterns;
- the 2006-07 to 2011 deterioration coincides with rapid common-city expansion;
- later economic improvement does not reverse mapped counts, although growth slows and visible organisation changes;
- across the three rounds with typology data, inflation is most strongly aligned with a shift from street toward home-based work, while higher GDP growth aligns with street share;
- kothikhana share is informative within 2011 but is not a clean longitudinal macro marker because it rises during both deterioration and recovery;
- density and cellphone share cannot be tested across multiple rounds with the currently published measures.

The best available marker is therefore not a single density statistic. The evidence supports a **marker set**: the rate of change in comparable-city counts, whether that growth accelerates or plateaus, home-versus-street composition, kothikhana/intermediation as a cross-sectional organisation measure, and density only when a valid denominator is published. The complete series is the evidence base for this question; there is no other Pakistani longitudinal FSW dataset against which to defer the answer.

The authoritative numerical synthesis is [`results/analysis_summary.md`](results/analysis_summary.md).
The literature-integrated manuscript interpretation is [`manuscript/discussion_draft.md`](manuscript/discussion_draft.md).

## Repository map

- `docs/analysis_plan.md` — frozen confirmatory plan.
- `data/source_manifest.csv` — source provenance and checksums.
- `data/processed/paper1_city_round_master.csv` — 49-row master city-round dataset.
- `data/processed/paper1_2011_exploratory_features.csv` — acute/chronic, scale and network features.
- `results/analysis_summary.md` — complete current analysis.
- `results/confirmatory_analysis_summary.md` — primary and prespecified analysis only.
- `results/exploratory_report.md` — expanded hypothesis-generating analysis.
- `results/tables/` — all inspectable numerical outputs.
- `results/tables/current_findings.csv` — machine-readable ledger of current conclusions and evidence files.
- `results/tables/macro_marker_round_panel.csv` — survey-round economic indicators and multiple FSW markers.
- `results/tables/macro_marker_correlations.csv` — exact round-level correlation atlas.
- `results/tables/macro_marker_assumption_tests.csv` — explicit assumption-by-assumption verdicts.
- `results/tables/stock_persistence_signal.csv` — identical-city expansion, recovery and plateau comparison.
- `results/figures/` — primary, robustness and exploratory figures.
- `results/diagnostics/complete_validation.md` — end-to-end validation status.
- `literature/` — Pakistan-first literature review, Zimbabwe comparison, source summaries, evidence matrix, discussion map, and BibTeX library.
- `manuscript/discussion_draft.md` — manuscript-ready comparative Discussion with traceable citation keys.

## Reproduce

From PowerShell in the repository root:

```powershell
./scripts/run_full_analysis.ps1
```

The script rebuilds the dataset and all analyses, reruns base and exploratory validation, regenerates the complete synthesis, and runs final cross-output checks.

## Analysis boundary

The primary 2011 density analysis is confirmatory relative to the frozen plan. Acute-versus-chronic, network, count-versus-scale, nonlinear and economic-recovery analyses are exploratory and retained to define the next test. The repository now contains a Discussion draft; other manuscript sections remain unwritten.
