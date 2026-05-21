# Rotemberg Weights — Adversarial Bartik IV

GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.

**HHI** = 0.3356 | **Positive-weight topics** = 90 / 215

## Top 10 Topics by Rotemberg Weight

| Rank | Code | Topic | alpha (%) | Cum. | F_k | winner_majority | margin_top1_top2 | winner_vote_share | blank_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11472 | Falsificação ou Alteração de Documento Públic | +23.5% | 0.24 | 50.9 | -0.138 | -0.184 | -0.121 | -0.033 |
| 2 | 11593 | Direito de Resposta | +16.4% | 0.40 | 1.1 | -3.346 | -1.175 | -0.951 | -0.033 |
| 3 | 11642 | Eleições - 1° Turno | +15.8% | 0.56 | 1.9 | -0.325 | -0.726 | -0.432 | -0.079 |
| 4 | 11665 | Propaganda Política - Propaganda Eleitoral -  | +12.7% | 0.68 | 2.3 | 0.570 | 0.103 | 0.051 | 0.033 |
| 5 | 10750 | Injúria | +11.6% | 0.80 | 16.8 | -0.215 | -0.155 | -0.082 | -0.008 |
| 6 | 11662 | Propaganda Política - Propaganda Eleitoral -  | +10.7% | 0.91 | 2.5 | -1.301 | 0.410 | 0.134 | -0.004 |
| 7 | 11596 | Inelegibilidade - Abuso do Poder Econômico ou | +10.3% | 1.01 | 1.3 | -1.520 | -0.056 | -0.132 | 0.004 |
| 8 | 12592 | Direito Líquido e Certo | +8.6% | 1.10 | 0.6 | -1.246 | 0.379 | 0.173 | 0.023 |
| 9 | 11654 | Propaganda Política - Propaganda Eleitoral -  | +8.4% | 1.18 | 21.6 | -0.020 | -0.165 | -0.065 | 0.004 |
| 10 | 11678 | Propaganda Política - Propaganda Eleitoral -  | +7.9% | 1.26 | 2.9 | -0.292 | -0.313 | -0.282 | 0.028 |

## Notes
- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.
- `tau_k` = just-identified IV using topic k alone as instrument.
- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).
- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).