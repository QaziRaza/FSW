# Exploratory validation report

Status: **PASS** — 45/45 checks passed.

| Check | Status | Detail |
|---|---|---|
| feature row count | PASS | observed 15, expected 15 |
| feature city uniqueness | PASS | unique cities 15 |
| network row count | PASS | observed 15, expected 15 |
| network city uniqueness | PASS | unique cities 15 |
| network city coverage | PASS | network and 2011 city sets match |
| network operator total | PASS | observed 12162, published 12162 |
| no missing network values | PASS | all 15x6 numeric network cells present |
| chronic index reconstruction | PASS | index equals mean of three z-scored chronic measures |
| chronic index centering | PASS | mean 1.33e-09 |
| acute z centering | PASS | mean 0 |
| implied population reconstruction | PASS | count*1000/density reproduced |
| archetypes complete | PASS | four archetypes; counts {'low acute / high chronic': 6, 'high acute / low chronic': 6, 'high acute / high chronic': 2, 'low acute / low chronic': 1} |
| archetype table coverage | PASS | dedicated table contains all 15 cities |
| macro context rows | PASS | rounds ['2006_07', '2011', '2014', '2016_17'] |
| 2011 macro values | PASS | 2011 growth 2.4 and CPI 14.0 |
| macro sources and locators | PASS | every macro row has source file and locator |
| association atlas dimensions | PASS | 54 rows, 6x9 |
| association bounds | PASS | all rho and p values within bounds |
| atlas FDR dominates p | PASS | all adjusted p values are at least raw p values |
| economic family dimensions | PASS | observed 10, expected 10 pairwise tests |
| network association dimensions | PASS | observed 24, expected 24 |
| model dimensions | PASS | 21 rows across 7 models |
| model confidence intervals ordered | PASS | all coefficients lie inside own intervals |
| constant wins nonlinear LOOCV | PASS | minimum-RMSE degree 0 |
| paired transition coverage | PASS | counts {'2006_07_to_2011': 10, '2011_to_2014': 4} |
| hypothesis ledger complete | PASS | 6 fully specified hypotheses |
| macro contrast coverage | PASS | common-city counts [10, 4, 10] |
| macro contrast city rows | PASS | observed 24, expected 24 |
| improvement direction encoded | PASS | post-2011 contrasts have higher growth and lower inflation |
| improvement count result | PASS | aggregate changes [16.77, 3.36] |
| paired count tests complete | PASS | rows=3 |
| exact sign tests | PASS | p=[0.109375, 0.125, 0.753906] |
| annualized contrast ordering | PASS | annualized=[11.959, 5.304, 0.603] |
| 2011 source values preserved | PASS | city, total and density unchanged from frozen master |
| figure exploratory_figure_1_association_atlas.png | PASS | dimensions (2050, 1080) |
| figure exploratory_figure_2_acute_vs_chronic.png | PASS | dimensions (1800, 1120) |
| figure exploratory_figure_3_scale_contrast.png | PASS | dimensions (1900, 760) |
| figure exploratory_figure_4_organisation.png | PASS | dimensions (1850, 1100) |
| figure exploratory_figure_5_round_context.png | PASS | dimensions (1900, 1040) |
| figure exploratory_figure_6_better_economy_test.png | PASS | dimensions (1900, 940) |
| report status label | PASS | exploratory status explicitly stated |
| atlas FDR result | PASS | one adjusted association: all-area deterioration versus kothikhana share |
| report multiplicity statement | PASS | correct FDR result stated |
| report scale distinction | PASS | count and density distinction stated |
| report mechanism boundary | PASS | mechanistic limits stated |

This validation covers structure, exact source invariants, derived-feature reconstruction, statistical-output bounds, figure production, and interpretive guardrails. It does not make exploratory associations confirmatory.
