# GPS (2020) Balance Tests on Topic Shares

Tests share exogeneity for the adversarial-only instrument (no-RRC, no-DRAP).
DRAP (12044) is included as a diagnostic even though excluded from the main spec.

## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)

High R² indicates the share correlates with observables (endogeneity concern).

| Rank | Code | Topic | alpha | R² | F | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11616 | Impugnação ao Registro de Candidatura | +0.403 | 0.179 | 37.7 | 0.000 |
| 2 | 11617 | Registro de Candidatura - Preenchimento  | -0.297 | 0.199 | 42.9 | 0.000 |
| 3 | 11679 | Propaganda Política - Propaganda Eleitor | +0.194 | 0.091 | 17.3 | 0.000 |
| 4 | 11619 | Registro de Candidatura - RRCI - Candida | +0.160 | 0.083 | 15.7 | 0.000 |
| 5 | 11662 | Propaganda Política - Propaganda Eleitor | +0.134 | 0.239 | 54.1 | 0.000 |
| 6 | 11596 | Inelegibilidade - Abuso do Poder Econômi | -0.116 | 0.062 | 11.5 | 0.000 |
| 7 | 11653 | Propaganda Política - Propaganda Eleitor | +0.095 | 0.069 | 12.8 | 0.000 |
| 8 | 12063 | Conduta Vedada ao Agente Público | +0.078 | 0.053 | 9.7 | 0.000 |
| 9 | 12362 | Autorização de Divulgação de Publicidade | +0.068 | 0.047 | 8.5 | 0.000 |
| 10 | 12635 | Propaganda Política - Propaganda Eleitor | +0.062 | 0.130 | 25.7 | 0.000 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.024 | 0.072 | 13.4 | 0.000 |
| 12 | 12637 | Propaganda Política - Propaganda Eleitor | +0.023 | 0.104 | 20.1 | 0.000 |
| 13 | 12638 | Propaganda Política - Propaganda Eleitor | +0.016 | 0.060 | 11.0 | 0.000 |
| 14 | 11484 | Calúnia na Propaganda Eleitoral | +0.001 | 0.026 | 4.6 | 0.000 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | — | 0.475 | 156.5 | 0.000 |

## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)

Under share exogeneity, topic shares should not predict 2016→2020 electoral trends.

### Outcome: delta_margin_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11616 | Impugnação ao Registro de Candidatura | +0.403 | +0.0000 | 0.0000 | 0.852 |
| 2 | 11617 | Registro de Candidatura - Preenchimento  | -0.297 | -0.0000 | 0.0000 | 0.429 |
| 3 | 11679 | Propaganda Política - Propaganda Eleitor | +0.194 | -0.0000 | 0.0000 | 0.729 |
| 4 | 11619 | Registro de Candidatura - RRCI - Candida | +0.160 | -0.0000 | 0.0000 | 0.748 |
| 5 | 11662 | Propaganda Política - Propaganda Eleitor | +0.134 | -0.0000 | 0.0000 | 0.893 |
| 6 | 11596 | Inelegibilidade - Abuso do Poder Econômi | -0.116 | -0.0000 | 0.0000 | 0.619 |
| 7 | 11653 | Propaganda Política - Propaganda Eleitor | +0.095 | -0.0000 | 0.0000 | 0.663 |
| 8 | 12063 | Conduta Vedada ao Agente Público | +0.078 | -0.0000 | 0.0000 | 0.986 |
| 9 | 12362 | Autorização de Divulgação de Publicidade | +0.068 | -0.0000 | 0.0000 | 0.804 |
| 10 | 12635 | Propaganda Política - Propaganda Eleitor | +0.062 | -0.0000 | 0.0000 | 0.237 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.024 | -0.0000 | 0.0000 | 0.516 |
| 12 | 12637 | Propaganda Política - Propaganda Eleitor | +0.023 | -0.0000 | 0.0000 | 0.796 |
| 13 | 12638 | Propaganda Política - Propaganda Eleitor | +0.016 | -0.0000 | 0.0000 | 0.691 |
| 14 | 11484 | Calúnia na Propaganda Eleitoral | +0.001 | -0.0000 | 0.0000 | 0.867 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | — | -0.0000 | 0.0000 | 0.828 |

### Outcome: delta_top1_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11616 | Impugnação ao Registro de Candidatura | +0.403 | +0.0180 | 0.0074 | 0.015 * |
| 2 | 11617 | Registro de Candidatura - Preenchimento  | -0.297 | +0.0035 | 0.0065 | 0.583 |
| 3 | 11679 | Propaganda Política - Propaganda Eleitor | +0.194 | +0.0017 | 0.0119 | 0.890 |
| 4 | 11619 | Registro de Candidatura - RRCI - Candida | +0.160 | -0.0076 | 0.0097 | 0.435 |
| 5 | 11662 | Propaganda Política - Propaganda Eleitor | +0.134 | -0.0149 | 0.0138 | 0.280 |
| 6 | 11596 | Inelegibilidade - Abuso do Poder Econômi | -0.116 | -0.0970 | 0.0294 | 0.001 * |
| 7 | 11653 | Propaganda Política - Propaganda Eleitor | +0.095 | -0.0428 | 0.0182 | 0.019 * |
| 8 | 12063 | Conduta Vedada ao Agente Público | +0.078 | -0.0187 | 0.0257 | 0.466 |
| 9 | 12362 | Autorização de Divulgação de Publicidade | +0.068 | +0.0182 | 0.0310 | 0.557 |
| 10 | 12635 | Propaganda Política - Propaganda Eleitor | +0.062 | -0.0237 | 0.0120 | 0.048 * |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.024 | +0.0181 | 0.0252 | 0.472 |
| 12 | 12637 | Propaganda Política - Propaganda Eleitor | +0.023 | +0.0017 | 0.0120 | 0.885 |
| 13 | 12638 | Propaganda Política - Propaganda Eleitor | +0.016 | +0.0281 | 0.0417 | 0.501 |
| 14 | 11484 | Calúnia na Propaganda Eleitoral | +0.001 | +0.0132 | 0.0233 | 0.570 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | — | -0.0637 | 0.0237 | 0.007 * |

### Outcome: delta_ncand_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11616 | Impugnação ao Registro de Candidatura | +0.403 | -0.3006 | 0.1268 | 0.018 * |
| 2 | 11617 | Registro de Candidatura - Preenchimento  | -0.297 | -0.2390 | 0.1098 | 0.030 * |
| 3 | 11679 | Propaganda Política - Propaganda Eleitor | +0.194 | -0.1702 | 0.2023 | 0.400 |
| 4 | 11619 | Registro de Candidatura - RRCI - Candida | +0.160 | +0.0842 | 0.1659 | 0.612 |
| 5 | 11662 | Propaganda Política - Propaganda Eleitor | +0.134 | +0.3637 | 0.2351 | 0.122 |
| 6 | 11596 | Inelegibilidade - Abuso do Poder Econômi | -0.116 | +1.4336 | 0.5012 | 0.004 * |
| 7 | 11653 | Propaganda Política - Propaganda Eleitor | +0.095 | +0.8860 | 0.3100 | 0.004 * |
| 8 | 12063 | Conduta Vedada ao Agente Público | +0.078 | +0.5049 | 0.4368 | 0.248 |
| 9 | 12362 | Autorização de Divulgação de Publicidade | +0.068 | -0.2276 | 0.5283 | 0.667 |
| 10 | 12635 | Propaganda Política - Propaganda Eleitor | +0.062 | +0.2646 | 0.2037 | 0.194 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.024 | -0.2856 | 0.4290 | 0.506 |
| 12 | 12637 | Propaganda Política - Propaganda Eleitor | +0.023 | -0.0203 | 0.2036 | 0.920 |
| 13 | 12638 | Propaganda Política - Propaganda Eleitor | +0.016 | +0.5276 | 0.7106 | 0.458 |
| 14 | 11484 | Calúnia na Propaganda Eleitoral | +0.001 | -0.2215 | 0.3961 | 0.576 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | — | +0.8759 | 0.4044 | 0.030 * |

## Information Environment Focus (all 6 topics)

The preferred instrument (`bartik_iv_information_environment`) is built from these 6 topics.
Share exogeneity must hold for each individual topic for the family IV to be valid.

| Code | Topic | alpha | Family | R²(cov) | p(cov) | p(margin) | p(top1) | p(ncand) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11679 | Propaganda Política - Propaganda Eleitoral -  | +0.194 | information_environment | 0.091 | 0.000 * | 0.729 | 0.890 | 0.400 |
| 12635 | Propaganda Política - Propaganda Eleitoral -  | +0.062 | information_environment | 0.130 | 0.000 * | 0.237 | 0.048 * | 0.194 |
| 12639 | Propaganda Política - Propaganda Eleitoral -  | +0.024 | information_environment | 0.072 | 0.000 * | 0.516 | 0.472 | 0.506 |
| 12637 | Propaganda Política - Propaganda Eleitoral -  | +0.023 | information_environment | 0.104 | 0.000 * | 0.796 | 0.885 | 0.920 |
| 12638 | Propaganda Política - Propaganda Eleitoral -  | +0.016 | information_environment | 0.060 | 0.000 * | 0.691 | 0.501 | 0.458 |
| 11484 | Calúnia na Propaganda Eleitoral | +0.001 | information_environment | 0.026 | 0.000 * | 0.867 | 0.570 | 0.576 |

(*) significant at 5% — signals potential share endogeneity.

## Notes
- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.
- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.
- DRAP (12044) is excluded from the adversarial-only instrument but shown here to evaluate its share exogeneity.
  Low R² and non-significant pre-trend coefficients for DRAP would support its inclusion as an instrument.