# Rotemberg Weights — Adversarial Bartik IV

GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.

**HHI** = 1.0656 | **Positive-weight topics** = 6 / 10

## Top 10 Topics by Rotemberg Weight

| Rank | Code | Topic | alpha (%) | Cum. | F_k | winner_majority | others_vote_share | margin_top1_top2 | winner_vote_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | fraude | fraude | +64.3% | 0.64 | 75.2 | -0.047 | 0.012 | -0.041 | -0.025 |
| 2 | pesquisa_adv | pesquisa_adv | +50.5% | 1.15 | 74.4 | -0.119 | 0.048 | -0.100 | -0.074 |
| 3 | abuso | abuso | +38.1% | 1.53 | 121.9 | 0.101 | -0.041 | 0.001 | 0.021 |
| 4 | ballot_integrity | ballot_integrity | +9.4% | 1.62 | 19.5 | -0.117 | 0.049 | -0.131 | -0.092 |
| 5 | conduta_vedada | conduta_vedada | +7.2% | 1.70 | 23.8 | 0.029 | -0.016 | -0.017 | -0.001 |
| 6 | inelegib | inelegib | +0.9% | 1.70 | 2.2 | -0.085 | -0.015 | 0.139 | 0.072 |
| 7 | finance | finance | -0.9% | 1.70 | 0.5 | 0.025 | -0.188 | -0.478 | -0.158 |
| 8 | direito_resposta | direito_resposta | -7.6% | 1.62 | 3.2 | 0.092 | -0.101 | -0.149 | -0.049 |
| 9 | honra | honra | -17.1% | 1.45 | 37.9 | -0.071 | 0.006 | -0.031 | -0.016 |
| 10 | vote_buying | vote_buying | -44.9% | 1.00 | 87.0 | -0.018 | -0.001 | -0.009 | -0.004 |

## Notes
- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.
- `tau_k` = just-identified IV using topic k alone as instrument.
- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).
- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).