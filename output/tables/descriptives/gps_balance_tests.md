# GPS (2020) Balance Tests on Topic-Family Shares

Tests share exogeneity for the family-level shift-share instrument
(SIG family crosswalk, headline rung theme9 = 9 kept families; mandatory-filing classes dropped at build stage).

## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)

High R² indicates the family share correlates with observables (endogeneity concern).

| Rank | Family | alpha | R² | F | p |
| --- | --- | --- | --- | --- | --- |
| 1 | fraude | +0.643 | 0.020 | 3.5 | 0.000 |
| 2 | pesquisa_adv | +0.505 | 0.114 | 22.2 | 0.000 |
| 3 | vote_buying | -0.449 | 0.057 | 10.5 | 0.000 |
| 4 | abuso | +0.381 | 0.031 | 5.5 | 0.000 |
| 5 | honra | -0.171 | 0.049 | 9.0 | 0.000 |
| 6 | ballot_integrity | +0.094 | 0.019 | 3.3 | 0.000 |
| 7 | direito_resposta | -0.076 | 0.019 | 3.4 | 0.000 |
| 8 | conduta_vedada | +0.072 | 0.030 | 5.3 | 0.000 |
| 9 | finance | -0.009 | 0.073 | 13.5 | 0.000 |
| 10 | inelegib | +0.009 | 0.011 | 1.9 | 0.002 |

## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)

Under share exogeneity, family shares should not predict 2016→2020 electoral trends.

### Outcome: delta_margin_2020_2016

| Rank | Family | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- |
| 1 | fraude | +0.643 | -0.0000 | 0.0000 | 0.305 |
| 2 | pesquisa_adv | +0.505 | -0.0000 | 0.0000 | 0.798 |
| 3 | vote_buying | -0.449 | -0.0000 | 0.0000 | 0.276 |
| 4 | abuso | +0.381 | +0.0000 | 0.0000 | 0.945 |
| 5 | honra | -0.171 | -0.0000 | 0.0000 | 0.100 |
| 6 | ballot_integrity | +0.094 | -0.0000 | 0.0000 | 0.319 |
| 7 | direito_resposta | -0.076 | -0.0000 | 0.0000 | 0.349 |
| 8 | conduta_vedada | +0.072 | -0.0000 | 0.0000 | 0.403 |
| 9 | finance | -0.009 | -0.0000 | 0.0000 | 0.016 * |
| 10 | inelegib | +0.009 | +0.0000 | 0.0000 | 0.943 |

### Outcome: delta_top1_2020_2016

| Rank | Family | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- |
| 1 | fraude | +0.643 | -0.0029 | 0.0047 | 0.537 |
| 2 | pesquisa_adv | +0.505 | -0.0090 | 0.0035 | 0.009 * |
| 3 | vote_buying | -0.449 | -0.0004 | 0.0035 | 0.910 |
| 4 | abuso | +0.381 | +0.0051 | 0.0029 | 0.083 |
| 5 | honra | -0.171 | -0.0000 | 0.0049 | 0.993 |
| 6 | ballot_integrity | +0.094 | -0.0083 | 0.0093 | 0.372 |
| 7 | direito_resposta | -0.076 | +0.0034 | 0.0092 | 0.713 |
| 8 | conduta_vedada | +0.072 | +0.0088 | 0.0069 | 0.201 |
| 9 | finance | -0.009 | +0.0014 | 0.0058 | 0.806 |
| 10 | inelegib | +0.009 | +0.0034 | 0.0106 | 0.749 |

### Outcome: delta_ncand_2020_2016

| Rank | Family | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- |
| 1 | fraude | +0.643 | -0.0322 | 0.0793 | 0.685 |
| 2 | pesquisa_adv | +0.505 | +0.0818 | 0.0593 | 0.168 |
| 3 | vote_buying | -0.449 | +0.0131 | 0.0588 | 0.824 |
| 4 | abuso | +0.381 | -0.1020 | 0.0501 | 0.042 * |
| 5 | honra | -0.171 | +0.1451 | 0.0839 | 0.084 |
| 6 | ballot_integrity | +0.094 | +0.0632 | 0.1578 | 0.689 |
| 7 | direito_resposta | -0.076 | +0.1003 | 0.1563 | 0.521 |
| 8 | conduta_vedada | +0.072 | +0.1269 | 0.1171 | 0.279 |
| 9 | finance | -0.009 | -0.0160 | 0.0980 | 0.870 |
| 10 | inelegib | +0.009 | -0.2237 | 0.1796 | 0.213 |

## Notes
- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.
- Family shares = baseline_share_2020 (municipality 2020 family portfolio).
- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.
- (*) significant at 5% — signals potential share endogeneity.