# Rotemberg Weights — Adversarial-Only (No-RRC, No-DRAP) Bartik IV

GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.

**HHI** = 0.3804 | **Positive-weight topics** = 20 / 29

## Top 10 Topics by Rotemberg Weight

| Rank | Code | Topic | alpha (%) | Cum. | F_k | winner_majority | margin_top1_top2 | winner_vote_share | blank_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11616 | Impugnação ao Registro de Candidatura | +40.3% | 0.40 | 43.4 | 0.213 | 0.078 | 0.068 | 0.002 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitoral -  | +19.4% | 0.60 | 49.0 | 0.126 | 0.109 | 0.058 | 0.005 |
| 3 | 11619 | Registro de Candidatura - RRCI - Candidato In | +16.0% | 0.76 | 9.2 | 0.225 | 0.066 | 0.017 | 0.002 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitoral -  | +13.4% | 0.89 | 6.5 | -0.315 | 0.094 | 0.019 | -0.003 |
| 5 | 11653 | Propaganda Política - Propaganda Eleitoral -  | +9.5% | 0.99 | 23.0 | -0.321 | -0.144 | -0.124 | 0.000 |
| 6 | 12063 | Conduta Vedada ao Agente Público | +7.8% | 1.07 | 18.9 | -0.029 | 0.002 | 0.001 | -0.005 |
| 7 | 12362 | Autorização de Divulgação de Publicidade Inst | +6.8% | 1.13 | 18.0 | 0.179 | -0.074 | -0.009 | -0.002 |
| 8 | 12635 | Propaganda Política - Propaganda Eleitoral -  | +6.2% | 1.20 | 5.6 | 0.271 | -0.182 | -0.059 | -0.032 |
| 9 | 11654 | Propaganda Política - Propaganda Eleitoral -  | +5.6% | 1.25 | 13.8 | -0.045 | -0.034 | -0.002 | 0.013 |
| 10 | 11655 | Propaganda Política - Propaganda Eleitoral -  | +4.9% | 1.30 | 57.7 | 0.056 | -0.053 | -0.024 | 0.004 |

## Notes
- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.
- `tau_k` = just-identified IV using topic k alone as instrument.
- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).
- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).