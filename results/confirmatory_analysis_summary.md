# Analysis summary

## Executive result

Across the 15 mapped cities in 2011, urban household economic distress and mapped FSW density showed a weak inverse rank association (Spearman rho = -0.138; bootstrap 95% CI -0.597 to 0.372; two-sided permutation p = 0.6195). The interval is wide and includes associations in both directions. The evidence therefore does not support a precise claim that more distressed urban districts had higher mapped FSW density in 2011.

This is an ecological, small-sample association among surveillance-selected cities. It neither tests individual entry into sex work nor establishes a causal effect of economic distress.

## Data assembled

| round_id | mapping_period | cities | density_available | typology_available | economic_period | status |
|---|---|---|---|---|---|---|
| 2006_07 | 2006-07 | 12 | False | True | 2006-07 | structural replication |
| 2011 | 2011 | 15 | True | True | 2010-11 | primary |
| 2014 | 2014 | 4 | False | True | 2014-15 | structural replication |
| 2016_17 | 2015-17 | 18 | False | False | 2014-15 | context only |

The 2011 round is the only acquired source reporting city density per 1,000 adult men. The 2006-07 and 2014 sources support structural replication using typology shares. Round 5 is count context only: its printed city rows sum to 71,315 while its printed Grand Total is 64,829, and neither city density nor city typology composition is published in the acquired report.

## Primary and secondary associations

| analysis | method | n | estimate | p_value |
|---|---|---|---|---|
| primary_pair_pearson | pearson | 15 | -0.196 | 0.4845 |
| urban_poverty | spearman | 15 | 0.281 | 0.3110 |
| urban_female_illiteracy | spearman | 15 | 0.316 | 0.2512 |
| urban_sanitation_deprivation | spearman | 15 | -0.061 | 0.8288 |
| all_area_economic_distress | spearman | 15 | -0.091 | 0.7466 |
| log_density_pearson | pearson | 15 | -0.227 | 0.4149 |

The unadjusted OLS visual-scale slope was -0.055 additional mapped FSWs per 1,000 adult men for a one-percentage-point difference in urban distress (HC3 95% CI -0.211 to 0.101). OLS is secondary because the sample is small and the primary estimand is rank-based.

## Robustness and influence

Across six prespecified city subsets, Spearman estimates ranged from -0.150 to 0.183. Across leave-one-city-out analyses they ranged from -0.264 to -0.031. The largest Cook's distance belonged to Quetta (0.174); this identifies influence on the linear fit, not an invalid observation.

| analysis | n | estimate | p_value |
|---|---|---|---|
| all_cities | 15 | -0.138 | 0.6248 |
| exclude_karachi | 14 | -0.031 | 0.9167 |
| exclude_lahore | 14 | -0.150 | 0.6097 |
| exclude_karachi_lahore | 13 | -0.047 | 0.8794 |
| close_matches_only | 9 | 0.183 | 0.6368 |
| close_or_composite | 10 | 0.079 | 0.8287 |

## Structural replication

| round_id | outcome | n | estimate_rho | p_value | p_fdr_bh |
|---|---|---|---|---|---|
| 2006_07 | home_share_pct | 12 | 0.161 | 0.6169 | 0.7292 |
| 2006_07 | street_share_pct | 12 | 0.112 | 0.7292 | 0.7292 |
| 2011 | home_share_pct | 15 | -0.146 | 0.6026 | 0.7292 |
| 2011 | street_share_pct | 15 | 0.268 | 0.3344 | 0.6689 |
| 2014 | home_share_pct | 4 | -0.800 | 0.2000 | 0.6000 |
| 2014 | street_share_pct | 4 | 0.800 | 0.2000 | 0.6000 |

These round-specific tests ask whether distress covaries with mapped sex-work organization, not whether national composition changed. FDR values address the six prespecified home/street tests. Differences may reflect structural change, survey coverage, mapping intensity, or category practice.

## Exploratory 2006-07 to 2011 change analysis

| outcome | n | estimate_rho | p_value | status |
|---|---|---|---|---|
| delta_home_share_pct | 10 | 0.073 | 0.8413 | exploratory_small_paired_sample |
| delta_street_share_pct | 10 | -0.225 | 0.5321 | exploratory_small_paired_sample |

Distress change is the change in each city's within-round percentile rank, not a raw percentage-point difference, because the response distribution shifted substantially. With only overlapping cities, these estimates are descriptive and fragile.

## Interpretation

The primary result is compatible with no stable monotonic relationship, a modest relationship obscured by measurement error, or heterogeneous city-specific processes. Secondary poverty, literacy, and sanitation measures test adjacent constructs rather than interchangeable versions of one exposure.

The structural analyses are the more defensible multi-period comparison because named typology counts are present in 2006-07, 2011, and 2014. Even there, results are replication across snapshots, not a pooled panel effect.

## Main limitations

- Mapping estimates may undercount less visible workers and vary with program intensity.
- City outcomes are paired to district urban strata, with explicit but imperfect matches.
- Cities were surveillance-selected rather than sampled from all Pakistani cities.
- Fifteen observations sharply limit precision and adjustment.
- Ecological associations cannot establish individual mechanisms or causality.
- Adult-male density was unavailable for other acquired rounds, so cross-round density replication was not attempted.

## Reproducibility status

Cached sources are checksummed, joins use an explicit crosswalk, typology components reconcile to published totals, and missing values are never converted to zero. `results/diagnostics/validation_report.md` records executable checks. The manuscript remains reserved until this summary is reviewed.
