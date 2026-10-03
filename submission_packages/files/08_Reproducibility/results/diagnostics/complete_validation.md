# Complete-analysis validation

Status: **PASS** — 72/72 checks passed.

| Check | Result | Detail |
|---|---:|---|
| primary rho independently recomputed | PASS | recomputed=-0.137622933; table=-0.137623000 |
| primary interval ordered | PASS | CI -0.597 to 0.372 |
| primary permutation p bounded | PASS | p=0.619524 |
| paired comparison set | PASS | comparisons=['2006_07_to_2011', '2011_to_2014', '2011_to_2016_17'] |
| 2006_07_to_2011: totals reconcile | PASS | 47062->78241 |
| 2006_07_to_2011: percent change | PASS | recomputed=66.250903 |
| 2006_07_to_2011: annualized change | PASS | recomputed=11.958912 |
| 2006_07_to_2011: exact sign test | PASS | up/down=8/2; p=0.109375 |
| 2011_to_2014: totals reconcile | PASS | 37818->44160 |
| 2011_to_2014: percent change | PASS | recomputed=16.769792 |
| 2011_to_2014: annualized change | PASS | recomputed=5.303669 |
| 2011_to_2014: exact sign test | PASS | up/down=4/0; p=0.125000 |
| 2011_to_2016_17: totals reconcile | PASS | 48366->49991 |
| 2011_to_2016_17: percent change | PASS | recomputed=3.359798 |
| 2011_to_2016_17: annualized change | PASS | recomputed=0.602643 |
| 2011_to_2016_17: exact sign test | PASS | up/down=4/6; p=0.753906 |
| atlas family complete | PASS | 54 cells = 6 exposures x 9 outcomes |
| atlas FDR result | PASS | hits=1; minimum q=0.040871 |
| macro-marker round panel | PASS | rounds=['2006_07', '2011', '2014', '2016_17'] |
| macro-marker atlas complete | PASS | 32 cells = 4 indicators x 8 markers |
| macro-marker sample grain | PASS | n range=3-4 |
| macro-marker exact p bounded | PASS | minimum p=0.333333 |
| macro-marker FDR result | PASS | hits=0; minimum q=1.000000 |
| inflation-composition result independently recomputed | PASS | rho=1.000000; exact p=0.333333 |
| macro assumptions ledger | PASS | rows=8 |
| continuous stock panels | PASS | panels=['continuous_to_2014', 'continuous_to_2016_17']; cities=[4, 6] |
| continuous_to_2014: common cities independently reconstructed | PASS | n=4 |
| continuous_to_2014: stock totals independently reconstructed | PASS | totals=[np.int64(24987), np.int64(37818), np.int64(44160)] |
| continuous_to_2014: recovery growth is slower | PASS | annualized 9.65% -> 5.30% |
| continuous_to_2016_17: common cities independently reconstructed | PASS | n=6 |
| continuous_to_2016_17: stock totals independently reconstructed | PASS | totals=[np.int64(22075), np.int64(40423), np.int64(42403)] |
| continuous_to_2016_17: recovery growth is slower | PASS | annualized 14.39% -> 0.87% |
| base validation current | PASS | status=PASS; checks=67 |
| exploratory validation current | PASS | status=pass; checks=45 |
| report section: Executive summary | PASS | present |
| report section: Evidence assembled and usable | PASS | present |
| report section: Frozen primary result | PASS | present |
| report section: Recent deterioration and chronic deprivation | PASS | present |
| report section: Sex-work structure | PASS | present |
| report section: What changed across economic deterioration and recovery | PASS | present |
| report section: National economic indicators tested against multiple FSW markers | PASS | present |
| report section: Replication and model checks | PASS | present |
| report section: What the evidence supports and contradicts | PASS | present |
| report section: Is Paper 2 justified? | PASS | present |
| report section: Reproducibility and validation status | PASS | present |
| report section: Source traceability | PASS | present |
| report claim: rho=-0.138 | PASS | present |
| report claim: 66.25% | PASS | present |
| report claim: 16.77% | PASS | present |
| report claim: +3.36% | PASS | present |
| report claim: 11.96% | PASS | present |
| report claim: category C | PASS | present |
| report claim: 71,315 | PASS | present |
| report claim: 64,829 | PASS | present |
| report claim: not supported | PASS | present |
| report claim: Paper 2 | PASS | present |
| report claim: minimum exact p-value is 0.333 | PASS | present |
| report claim: home-minus-street balance | PASS | present |
| report claim: Kothikhana share did not behave as a clean temporal macro marker | PASS | present |
| report claim: Simple answer: yes | PASS | present |
| report claim: 9.65% | PASS | present |
| report claim: 14.39% | PASS | present |
| report claim: 0.87% | PASS | present |
| report claim: fewer net newcomers | PASS | present |
| report avoids prohibited certainty | PASS | no prohibited certainty language |
| all report figures exist | PASS | referenced=5; missing=[] |
| knowledge index exists | PASS | WHAT_WE_KNOW.md |
| confirmatory summary preserved | PASS | prespecified-only narrative retained separately |
| source manifest retained | PASS | source provenance available |
| hypothesis ledger retained | PASS | six hypotheses with later tests available |
| current findings ledger | PASS | rows=18; unique IDs=18 |
| findings preserve confirmatory boundary | PASS | one confirmatory result and one FDR-adjusted exploratory result |

This layer independently recomputes the primary rank correlation, every paired-count contrast, both continuous-city stock panels and the key inflation-composition result; checks exact tests and multiplicity results; confirms required synthesis sections and claims; and ensures referenced artifacts exist.
