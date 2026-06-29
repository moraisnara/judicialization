# Rotemberg Weights — Adversarial Bartik IV

GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.

**HHI** = 0.0988 | **Positive-weight topics** = 101 / 223

## Top 10 Topics by Rotemberg Weight

| Rank | Code | Topic | alpha (%) | Cum. | F_k | winner_majority | margin_top1_top2 | winner_vote_share | blank_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11665 | Propaganda Política - Propaganda Eleitoral -  | +13.9% | 0.14 | 10.2 | -0.038 | -0.007 | -0.014 | 0.005 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitoral -  | +13.6% | 0.27 | 32.4 | 0.069 | 0.030 | 0.022 | -0.000 |
| 3 | 11667 | Propaganda Política - Propaganda Eleitoral -  | +12.1% | 0.40 | 45.9 | 0.061 | -0.023 | -0.001 | -0.002 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitoral -  | +8.9% | 0.48 | 12.8 | -0.044 | 0.039 | -0.007 | 0.006 |
| 5 | 11678 | Propaganda Política - Propaganda Eleitoral -  | +7.0% | 0.55 | 12.1 | -0.097 | -0.013 | -0.023 | 0.004 |
| 6 | 11653 | Propaganda Política - Propaganda Eleitoral -  | +6.9% | 0.62 | 30.2 | -0.042 | -0.042 | -0.033 | -0.002 |
| 7 | 11642 | Eleições - 1° Turno | +6.6% | 0.69 | 3.4 | -0.128 | 0.181 | 0.064 | 0.009 |
| 8 | 11654 | Propaganda Política - Propaganda Eleitoral -  | +6.0% | 0.75 | 24.5 | 0.041 | 0.029 | 0.007 | -0.001 |
| 9 | 12637 | Propaganda Política - Propaganda Eleitoral -  | +4.8% | 0.80 | 30.0 | 0.056 | -0.028 | -0.008 | -0.001 |
| 10 | 12588 | Crimes Conexos | +4.2% | 0.84 | 1.6 | 0.446 | 0.328 | 0.195 | 0.010 |

## Notes
- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.
- `tau_k` = just-identified IV using topic k alone as instrument.
- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).
- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).