# Frozen analysis plan

Status: **prespecified before any correlation or regression was run**. The Git commit containing this file is the analysis-plan freeze point.

## Research question

Across Pakistani cities mapped in the 2011 HIV second-generation surveillance round, is greater local economic distress associated with a higher mapped density of female sex workers? A secondary question asks whether economic distress is associated with the organization of sex work—especially home-based versus street-based shares—and whether those structural associations recur in 2006–07 and 2014.

## Units and populations

- Unit of analysis: a mapped city-round.
- Primary sample: all 15 cities with a source-reported 2011 FSW density per 1,000 adult men and a matched PSLM 2010–11 district urban stratum.
- Replication samples: 2006–07 cities with published typology counts and matched PSLM 2006–07 indicators; 2014 Punjab cities with published typology counts and matched PSLM 2014–15 indicators.
- Round 5 (2016–17): context-only. The acquired report publishes city FSW counts but not city-specific adult-male density or city typology composition.

## Primary outcome

`fsw_density_per_1000_adult_men`, as reported in the 2011 mapping table. No denominator will be back-calculated for other rounds. The implied adult-male population calculated from 2011 count and density is diagnostic only and will not be treated as an independently observed covariate.

## Primary exposure

`economic_distress_urban_pct`: the percentage of households in the matched PSLM district's urban stratum reporting that their household economic situation was “much worse” or “worse” than one year earlier. It is the sum of the first two Table 5.1 response percentages. This is chosen before analysis because it is contemporaneous, repeated across PSLM rounds, district-representative, and conceptually closest to short-run household economic pressure.

The urban stratum is primary because the outcome is city-based. It still includes all urban areas in the district and therefore does not perfectly match city boundaries. The all-area district percentage is a geographic sensitivity analysis.

## Secondary exposures

- `poverty_headcount_urban_pct`: model-based urban district poverty estimate for 2010–11 from SPDC Research Report 85; 2011 only.
- `female_illiteracy_urban_pct`: 100 minus the PSLM urban female literacy rate (age 10+).
- `sanitation_deprivation_urban_pct`: 100 minus the PSLM urban household flush-toilet share.

No composite deprivation index will be created. Published LFS estimates are not district-representative for these rounds and will not be used as city-level predictors.

## Primary estimand and inference

- Spearman rank correlation between 2011 FSW density and urban economic distress.
- Report rho, a two-sided asymptotic p-value, a deterministic Monte Carlo permutation p-value (100,000 permutations), and a percentile bootstrap 95% confidence interval (20,000 city resamples).
- Random seed: 20261002.
- Emphasize effect size and uncertainty; do not use a binary significance label as the conclusion.

## Secondary and sensitivity analyses

1. Pearson correlation for the primary exposure/outcome pair.
2. Spearman correlations for the three secondary exposures.
3. Leave-one-city-out Spearman estimates.
4. Exclude Karachi, exclude Lahore, and exclude both.
5. Restrict to `close` geographic matches; a second restriction may include `composite` matches if explicitly labeled.
6. Substitute all-area district economic distress for the urban-stratum measure.
7. Use `log1p(fsw_density_per_1000_adult_men)` with Pearson correlation and OLS.
8. OLS of density on urban distress with HC3 robust standard errors; a second model adds `log(fsw_total)` as a pragmatic scale control. Because mapped count is part of the density numerator, the adjusted model is sensitivity-only and will be interpreted cautiously.
9. Influence diagnostics: studentized residuals, leverage, and Cook's distance.

## Structural and cross-round analyses

- For 2006–07, 2011, and 2014 separately, correlate urban economic distress with `home_share_pct` and `street_share_pct` using Spearman rho.
- Brothel and kothikhana shares are descriptive/exploratory because their distributions contain many zeros or are sensitive to local category practice.
- Apply Benjamini–Hochberg false-discovery-rate correction across the six prespecified home/street replication tests.
- As an exploratory change analysis, compare 2006–07 to 2011 changes in home and street share among overlapping cities. Use within-round percentile ranks for distress before differencing because the national response distribution shifted sharply between PSLM rounds. Report Spearman correlations and clearly mark the small paired sample.
- Do not pool raw levels across rounds as if survey coverage, definitions, and mapping intensity were invariant.

## Geography rules

- Join through the explicit crosswalk only; never join raw city strings.
- `close`: city is a separately identified urban PSLM stratum or the district/city correspondence is otherwise close.
- `composite`: metropolitan city spans or aggregates multiple administrative units.
- `district_proxy`: the district urban stratum is used for a city without a separately identified large-city stratum.
- `problematic`: boundary or identity ambiguity is material enough to exclude from restricted analyses.

The primary analysis includes all documented matches. Sensitivity analyses restrict by match quality.

## Missingness and exclusions

- No imputation.
- Pairwise complete observations for explicitly named analyses.
- Missing density in non-2011 rounds is structural non-availability, not zero.
- Other/undefined typology counts remain in the denominator when computing named typology shares because the source total includes them.
- If a row fails count-total reconciliation by more than one worker or typology shares fail to sum to 100% within 0.15 percentage points, halt the pipeline.

## Multiplicity and interpretation

The 2011 density–distress Spearman test is the single primary test. All other associations are secondary or exploratory. FDR-adjusted values are reported for the six cross-round structural tests. Results will be described as ecological associations compatible with several mechanisms, not as evidence that economic distress causes entry into sex work.

