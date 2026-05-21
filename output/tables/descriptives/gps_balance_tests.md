# GPS (2020) Balance Tests on Topic Shares

Tests share exogeneity for the adversarial-only instrument (no-RRC, no-DRAP).
DRAP (12044) is included as a diagnostic even though excluded from the main spec.

## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)

High R² indicates the share correlates with observables (endogeneity concern).

| Rank | Code | Topic | alpha | R² | F | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11472 | Falsificação ou Alteração de Documento P | +0.235 | 0.007 | 1.2 | 0.190 |
| 2 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.226 | 0.132 | 26.2 | 0.000 |
| 3 | 11593 | Direito de Resposta | +0.164 | 0.072 | 13.4 | 0.000 |
| 4 | 11642 | Eleições - 1° Turno | +0.158 | 0.047 | 8.5 | 0.000 |
| 5 | 11518 | Subscrição de Mais de Uma Ficha de Filia | -0.154 | 0.018 | 3.2 | 0.000 |
| 6 | 11665 | Propaganda Política - Propaganda Eleitor | +0.127 | 0.087 | 16.4 | 0.000 |
| 7 | 11513 | Arregimentação de Eleitor ou Boca de Urn | -0.119 | 0.004 | 0.6 | 0.947 |
| 8 | 10750 | Injúria | +0.116 | 0.022 | 3.8 | 0.000 |
| 9 | 11662 | Propaganda Política - Propaganda Eleitor | +0.107 | 0.176 | 36.9 | 0.000 |
| 10 | 11596 | Inelegibilidade - Abuso do Poder Econômi | +0.103 | 0.052 | 9.5 | 0.000 |
| 11 | 12635 | Propaganda Política - Propaganda Eleitor | -0.016 | 0.133 | 26.5 | 0.000 |
| 12 | 12638 | Propaganda Política - Propaganda Eleitor | -0.011 | 0.049 | 9.0 | 0.000 |
| 13 | 12639 | Propaganda Política - Propaganda Eleitor | +0.009 | 0.070 | 13.0 | 0.000 |
| 14 | 11679 | Propaganda Política - Propaganda Eleitor | -0.009 | 0.080 | 15.0 | 0.000 |
| 15 | 12637 | Propaganda Política - Propaganda Eleitor | -0.001 | 0.098 | 18.8 | 0.000 |
| 16 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | 0.011 | 1.9 | 0.001 |
| 17 | 11484 | Calúnia na Propaganda Eleitoral | -0.000 | 0.027 | 4.7 | 0.000 |

## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)

Under share exogeneity, topic shares should not predict 2016→2020 electoral trends.

### Outcome: delta_margin_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11472 | Falsificação ou Alteração de Documento P | +0.235 | +0.0000 | 0.0000 | 0.936 |
| 2 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.226 | -0.0000 | 0.0000 | 0.858 |
| 3 | 11593 | Direito de Resposta | +0.164 | -0.0000 | 0.0000 | 0.075 |
| 4 | 11642 | Eleições - 1° Turno | +0.158 | -0.0000 | 0.0000 | 0.942 |
| 5 | 11518 | Subscrição de Mais de Uma Ficha de Filia | -0.154 | -0.0000 | 0.0000 | 0.695 |
| 6 | 11665 | Propaganda Política - Propaganda Eleitor | +0.127 | +0.0000 | 0.0000 | 0.972 |
| 7 | 11513 | Arregimentação de Eleitor ou Boca de Urn | -0.119 | -0.0000 | 0.0000 | 0.781 |
| 8 | 10750 | Injúria | +0.116 | -0.0000 | 0.0000 | 0.758 |
| 9 | 11662 | Propaganda Política - Propaganda Eleitor | +0.107 | -0.0000 | 0.0000 | 0.943 |
| 10 | 11596 | Inelegibilidade - Abuso do Poder Econômi | +0.103 | -0.0000 | 0.0000 | 0.771 |
| 11 | 12635 | Propaganda Política - Propaganda Eleitor | -0.016 | -0.0000 | 0.0000 | 0.236 |
| 12 | 12638 | Propaganda Política - Propaganda Eleitor | -0.011 | -0.0000 | 0.0000 | 0.684 |
| 13 | 12639 | Propaganda Política - Propaganda Eleitor | +0.009 | -0.0000 | 0.0000 | 0.762 |
| 14 | 11679 | Propaganda Política - Propaganda Eleitor | -0.009 | -0.0000 | 0.0000 | 0.841 |
| 15 | 12637 | Propaganda Política - Propaganda Eleitor | -0.001 | -0.0000 | 0.0000 | 0.827 |
| 16 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | +0.0000 | 0.0000 | 0.953 |
| 17 | 11484 | Calúnia na Propaganda Eleitoral | -0.000 | -0.0000 | 0.0000 | 0.921 |

### Outcome: delta_top1_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11472 | Falsificação ou Alteração de Documento P | +0.235 | -0.0511 | 0.0784 | 0.514 |
| 2 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.226 | +0.0026 | 0.0103 | 0.798 |
| 3 | 11593 | Direito de Resposta | +0.164 | -0.0090 | 0.0205 | 0.661 |
| 4 | 11642 | Eleições - 1° Turno | +0.158 | +0.0015 | 0.0192 | 0.939 |
| 5 | 11518 | Subscrição de Mais de Uma Ficha de Filia | -0.154 | +0.1043 | 0.0890 | 0.241 |
| 6 | 11665 | Propaganda Política - Propaganda Eleitor | +0.127 | -0.0077 | 0.0319 | 0.808 |
| 7 | 11513 | Arregimentação de Eleitor ou Boca de Urn | -0.119 | -0.0994 | 0.0446 | 0.026 * |
| 8 | 10750 | Injúria | +0.116 | +0.0065 | 0.1287 | 0.960 |
| 9 | 11662 | Propaganda Política - Propaganda Eleitor | +0.107 | -0.0031 | 0.0120 | 0.799 |
| 10 | 11596 | Inelegibilidade - Abuso do Poder Econômi | +0.103 | -0.0456 | 0.0229 | 0.046 * |
| 11 | 12635 | Propaganda Política - Propaganda Eleitor | -0.016 | -0.0082 | 0.0103 | 0.427 |
| 12 | 12638 | Propaganda Política - Propaganda Eleitor | -0.011 | +0.0193 | 0.0347 | 0.577 |
| 13 | 12639 | Propaganda Política - Propaganda Eleitor | +0.009 | +0.0236 | 0.0195 | 0.225 |
| 14 | 11679 | Propaganda Política - Propaganda Eleitor | -0.009 | +0.0104 | 0.0105 | 0.325 |
| 15 | 12637 | Propaganda Política - Propaganda Eleitor | -0.001 | +0.0148 | 0.0101 | 0.144 |
| 16 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | +0.1812 | 0.5605 | 0.746 |
| 17 | 11484 | Calúnia na Propaganda Eleitoral | -0.000 | +0.0116 | 0.0230 | 0.614 |

### Outcome: delta_ncand_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11472 | Falsificação ou Alteração de Documento P | +0.235 | +0.8619 | 1.3353 | 0.519 |
| 2 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.226 | +0.2072 | 0.1746 | 0.235 |
| 3 | 11593 | Direito de Resposta | +0.164 | -0.1889 | 0.3498 | 0.589 |
| 4 | 11642 | Eleições - 1° Turno | +0.158 | +0.3693 | 0.3261 | 0.258 |
| 5 | 11518 | Subscrição de Mais de Uma Ficha de Filia | -0.154 | -0.7620 | 1.5158 | 0.615 |
| 6 | 11665 | Propaganda Política - Propaganda Eleitor | +0.127 | +0.0350 | 0.5425 | 0.949 |
| 7 | 11513 | Arregimentação de Eleitor ou Boca de Urn | -0.119 | +1.2990 | 0.7595 | 0.087 |
| 8 | 10750 | Injúria | +0.116 | +2.4842 | 2.1904 | 0.257 |
| 9 | 11662 | Propaganda Política - Propaganda Eleitor | +0.107 | +0.1504 | 0.2043 | 0.462 |
| 10 | 11596 | Inelegibilidade - Abuso do Poder Econômi | +0.103 | +0.4212 | 0.3897 | 0.280 |
| 11 | 12635 | Propaganda Política - Propaganda Eleitor | -0.016 | -0.0910 | 0.1761 | 0.605 |
| 12 | 12638 | Propaganda Política - Propaganda Eleitor | -0.011 | +0.2650 | 0.5903 | 0.653 |
| 13 | 12639 | Propaganda Política - Propaganda Eleitor | +0.009 | -0.5681 | 0.3312 | 0.086 |
| 14 | 11679 | Propaganda Política - Propaganda Eleitor | -0.009 | -0.2852 | 0.1792 | 0.112 |
| 15 | 12637 | Propaganda Política - Propaganda Eleitor | -0.001 | -0.2698 | 0.1725 | 0.118 |
| 16 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | -13.8839 | 9.5412 | 0.146 |
| 17 | 11484 | Calúnia na Propaganda Eleitoral | -0.000 | -0.4337 | 0.3908 | 0.267 |

## Information Environment Focus (all 6 topics)

The preferred instrument (`bartik_iv_information_environment`) is built from these 6 topics.
Share exogeneity must hold for each individual topic for the family IV to be valid.

| Code | Topic | alpha | Family | R²(cov) | p(cov) | p(margin) | p(top1) | p(ncand) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12635 | Propaganda Política - Propaganda Eleitoral -  | -0.016 | information_environment | 0.133 | 0.000 * | 0.236 | 0.427 | 0.605 |
| 12638 | Propaganda Política - Propaganda Eleitoral -  | -0.011 | information_environment | 0.049 | 0.000 * | 0.684 | 0.577 | 0.653 |
| 12639 | Propaganda Política - Propaganda Eleitoral -  | +0.009 | information_environment | 0.070 | 0.000 * | 0.762 | 0.225 | 0.086 |
| 11679 | Propaganda Política - Propaganda Eleitoral -  | -0.009 | information_environment | 0.080 | 0.000 * | 0.841 | 0.325 | 0.112 |
| 12637 | Propaganda Política - Propaganda Eleitoral -  | -0.001 | information_environment | 0.098 | 0.000 * | 0.827 | 0.144 | 0.118 |
| 11484 | Calúnia na Propaganda Eleitoral | -0.000 | information_environment | 0.027 | 0.000 * | 0.921 | 0.614 | 0.267 |

(*) significant at 5% — signals potential share endogeneity.

## Notes
- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.
- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.
- DRAP (12044) is excluded from the adversarial-only instrument but shown here to evaluate its share exogeneity.
  Low R² and non-significant pre-trend coefficients for DRAP would support its inclusion as an instrument.