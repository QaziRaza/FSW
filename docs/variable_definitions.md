# Variable definitions

| Variable | Definition | Source / transformation | Role |
|---|---|---|---|
| `round_id` | Harmonized surveillance round (`2006_07`, `2011`, `2014`, `2016_17`) | Source report | Key |
| `city_id` | Stable lower-snake-case city identifier | Explicit crosswalk | Key |
| `city` | Display city name used by the surveillance source | Source report, harmonized spelling | Descriptor |
| `province` | Province at the time of the round | Source report | Descriptor |
| `fsw_total` | Estimated mapped FSW population | Mapping table | Outcome descriptor |
| `fsw_density_per_1000_adult_men` | Mapped FSW estimate per 1,000 adult men | Published only for 2011 | Primary outcome |
| `brothel_count`, `street_count`, `home_count`, `kothikhana_count`, `cellphone_count`, `other_count` | Mapped FSW counts by operational typology | Mapping tables; unavailable cells remain missing | Components |
| `*_share_pct` | Named typology count divided by `fsw_total`, times 100 | Derived without renormalizing away `other` | Structural outcomes |
| `economic_distress_urban_pct` | Urban households saying economic situation is much worse or worse than one year earlier | PSLM Table 5.1, sum of two response columns | Primary exposure |
| `economic_distress_all_pct` | All-area district equivalent | PSLM Table 5.1 | Sensitivity exposure |
| `female_illiteracy_urban_pct` | 100 minus urban female literacy rate, age 10+ | PSLM literacy table | Secondary exposure |
| `female_illiteracy_all_pct` | 100 minus all-area female literacy rate, age 10+ | PSLM literacy table | Sensitivity |
| `sanitation_deprivation_urban_pct` | 100 minus urban household flush-toilet share | PSLM toilet table | Secondary exposure |
| `sanitation_deprivation_all_pct` | 100 minus all-area household flush-toilet share | PSLM toilet table | Sensitivity |
| `poverty_headcount_urban_pct` | Model-based urban district poverty headcount | SPDC Research Report 85 | Secondary exposure, 2011 |
| `poverty_headcount_all_pct` | Model-based district poverty headcount | SPDC Research Report 85 | Sensitivity, 2011 |
| `geographic_match_quality` | `close`, `composite`, `district_proxy`, or `problematic` | Prespecified crosswalk review | Sensitivity flag |
| `analysis_status` | `primary`, `replication`, or `context_only` | Comparability assessment | Scope flag |

Percentages are stored on a 0–100 scale. Missing means unavailable or not comparable, never zero.

