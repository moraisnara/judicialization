# Shift Descriptives — Adversarial Bartik IV

BHJ (2024) checklist item 5: distribution of shifts g_k and importance weights s_k_bar.

**K** = 10 topics | **N** = 5,017 municipalities
| HHI (importance) | K_eff | Positive shifts | Negative shifts |
| --- | --- | --- | --- |
| 0.1658 | 6.03 | 6 | 4 |

## Per-Topic Statistics (sorted by importance weight)

| Code | Topic (truncated) | Family | N munis | s̄_k (%) | g_mean | g_sd | g_p10 | g_p50 | g_p90 | HHI contrib |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abuso | abuso | abuso | 3687 | 26.83% | +0.086 | 0.011 | +0.068 | +0.088 | +0.101 | 0.0720 |
| pesquisa_adv | pesquisa_adv | pesquisa_adv | 2945 | 19.26% | +0.163 | 0.030 | +0.132 | +0.155 | +0.217 | 0.0371 |
| vote_buying | vote_buying | vote_buying | 2657 | 18.12% | -0.143 | 0.023 | -0.162 | -0.147 | -0.092 | 0.0328 |
| fraude | fraude | fraude | 2035 | 9.02% | +0.283 | 0.044 | +0.172 | +0.291 | +0.317 | 0.0081 |
| honra | honra | honra | 1797 | 9.00% | -0.115 | 0.013 | -0.137 | -0.110 | -0.104 | 0.0081 |
| finance | finance | finance | 1179 | 6.14% | -0.016 | 0.055 | -0.101 | -0.003 | +0.061 | 0.0038 |
| conduta_vedada | conduta_vedada | conduta_vedada | 1372 | 4.77% | +0.077 | 0.018 | +0.046 | +0.080 | +0.096 | 0.0023 |
| ballot_integrity | ballot_integrity | ballot_integrity | 875 | 2.63% | +0.150 | 0.033 | +0.115 | +0.138 | +0.206 | 0.0007 |
| direito_resposta | direito_resposta | direito_resposta | 701 | 2.56% | -0.325 | 0.026 | -0.369 | -0.320 | -0.294 | 0.0007 |
| inelegib | inelegib | inelegib | 495 | 1.68% | +0.041 | 0.024 | +0.013 | +0.039 | +0.068 | 0.0003 |

## Notes
- `s̄_k` = mean share of topic k across all N municipalities (including zeros), re-normalised to sum to 1.
- `g_k` = leave-state-out log growth 2020→2024 for topic k; values vary by municipality (own-state excluded).
  Statistics above are computed across municipalities that have the topic in 2020.
- **HHI** = Σ_k (s̄_k)² — measures concentration of instrument in few topics.
  K_eff = 1/HHI is the effective number of topics driving the Bartik estimate.
- BHJ (2024) criterion: K_eff >> 1 needed for exposure-robust SE asymptotics.
  Here K_eff = 6.03 → GPS share-exogeneity identification is the primary justification.