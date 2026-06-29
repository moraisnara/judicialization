# GPS (2020) Balance Tests on Topic Shares

Tests share exogeneity for the adversarial-only instrument (no-RRC, no-DRAP).
DRAP (12044) is included as a diagnostic even though excluded from the main spec.

## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)

High R² indicates the share correlates with observables (endogeneity concern).

| Rank | Code | Topic | alpha | R² | F | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11665 | Propaganda Política - Propaganda Eleitor | +0.139 | 0.021 | 3.7 | 0.000 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitor | +0.136 | 0.055 | 10.1 | 0.000 |
| 3 | 11667 | Propaganda Política - Propaganda Eleitor | +0.121 | 0.046 | 8.4 | 0.000 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitor | +0.089 | 0.059 | 10.8 | 0.000 |
| 5 | 11678 | Propaganda Política - Propaganda Eleitor | +0.070 | 0.027 | 4.8 | 0.000 |
| 6 | 11653 | Propaganda Política - Propaganda Eleitor | +0.069 | 0.020 | 3.5 | 0.000 |
| 7 | 11642 | Eleições - 1° Turno | +0.066 | 0.021 | 3.8 | 0.000 |
| 8 | 11654 | Propaganda Política - Propaganda Eleitor | +0.060 | 0.039 | 7.0 | 0.000 |
| 9 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.050 | 0.068 | 12.6 | 0.000 |
| 10 | 12637 | Propaganda Política - Propaganda Eleitor | +0.048 | 0.021 | 3.7 | 0.000 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.035 | 0.020 | 3.6 | 0.000 |
| 12 | 12635 | Propaganda Política - Propaganda Eleitor | -0.027 | 0.028 | 5.0 | 0.000 |
| 13 | 11484 | Calúnia na Propaganda Eleitoral | +0.011 | 0.014 | 2.4 | 0.000 |
| 14 | 12638 | Propaganda Política - Propaganda Eleitor | +0.003 | 0.026 | 4.6 | 0.000 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | 0.005 | 0.9 | 0.686 |

## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)

Under share exogeneity, topic shares should not predict 2016→2020 electoral trends.

### Outcome: delta_margin_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11665 | Propaganda Política - Propaganda Eleitor | +0.139 | -0.0000 | 0.0000 | 0.913 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitor | +0.136 | -0.0000 | 0.0000 | 0.195 |
| 3 | 11667 | Propaganda Política - Propaganda Eleitor | +0.121 | -0.0000 | 0.0000 | 0.598 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitor | +0.089 | +0.0000 | 0.0000 | 0.933 |
| 5 | 11678 | Propaganda Política - Propaganda Eleitor | +0.070 | +0.0000 | 0.0000 | 0.886 |
| 6 | 11653 | Propaganda Política - Propaganda Eleitor | +0.069 | -0.0000 | 0.0000 | 0.374 |
| 7 | 11642 | Eleições - 1° Turno | +0.066 | -0.0000 | 0.0000 | 0.997 |
| 8 | 11654 | Propaganda Política - Propaganda Eleitor | +0.060 | -0.0000 | 0.0000 | 0.709 |
| 9 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.050 | +0.0000 | 0.0000 | 0.757 |
| 10 | 12637 | Propaganda Política - Propaganda Eleitor | +0.048 | -0.0000 | 0.0000 | 0.400 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.035 | -0.0000 | 0.0000 | 0.895 |
| 12 | 12635 | Propaganda Política - Propaganda Eleitor | -0.027 | -0.0000 | 0.0000 | 0.211 |
| 13 | 11484 | Calúnia na Propaganda Eleitoral | +0.011 | -0.0000 | 0.0000 | 0.925 |
| 14 | 12638 | Propaganda Política - Propaganda Eleitor | +0.003 | -0.0000 | 0.0000 | 0.166 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | -0.0000 | 0.0000 | 0.770 |

### Outcome: delta_top1_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11665 | Propaganda Política - Propaganda Eleitor | +0.139 | +0.0052 | 0.0151 | 0.730 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitor | +0.136 | +0.0036 | 0.0065 | 0.583 |
| 3 | 11667 | Propaganda Política - Propaganda Eleitor | +0.121 | +0.0006 | 0.0059 | 0.925 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitor | +0.089 | -0.0122 | 0.0071 | 0.083 |
| 5 | 11678 | Propaganda Política - Propaganda Eleitor | +0.070 | -0.0151 | 0.0136 | 0.264 |
| 6 | 11653 | Propaganda Política - Propaganda Eleitor | +0.069 | -0.0010 | 0.0099 | 0.916 |
| 7 | 11642 | Eleições - 1° Turno | +0.066 | -0.0058 | 0.0108 | 0.592 |
| 8 | 11654 | Propaganda Política - Propaganda Eleitor | +0.060 | -0.0056 | 0.0068 | 0.412 |
| 9 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.050 | -0.0088 | 0.0056 | 0.121 |
| 10 | 12637 | Propaganda Política - Propaganda Eleitor | +0.048 | +0.0079 | 0.0063 | 0.210 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.035 | -0.0014 | 0.0101 | 0.892 |
| 12 | 12635 | Propaganda Política - Propaganda Eleitor | -0.027 | -0.0041 | 0.0058 | 0.478 |
| 13 | 11484 | Calúnia na Propaganda Eleitoral | +0.011 | +0.0083 | 0.0164 | 0.615 |
| 14 | 12638 | Propaganda Política - Propaganda Eleitor | +0.003 | +0.0152 | 0.0252 | 0.547 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | -0.0847 | 0.0658 | 0.198 |

### Outcome: delta_ncand_2020_2016

| Rank | Code | Topic | alpha | beta | SE | p |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 11665 | Propaganda Política - Propaganda Eleitor | +0.139 | -0.1248 | 0.2567 | 0.627 |
| 2 | 11679 | Propaganda Política - Propaganda Eleitor | +0.136 | -0.0721 | 0.1102 | 0.513 |
| 3 | 11667 | Propaganda Política - Propaganda Eleitor | +0.121 | +0.0939 | 0.1003 | 0.349 |
| 4 | 11662 | Propaganda Política - Propaganda Eleitor | +0.089 | +0.1281 | 0.1201 | 0.286 |
| 5 | 11678 | Propaganda Política - Propaganda Eleitor | +0.070 | +0.2246 | 0.2307 | 0.330 |
| 6 | 11653 | Propaganda Política - Propaganda Eleitor | +0.069 | -0.0250 | 0.1688 | 0.882 |
| 7 | 11642 | Eleições - 1° Turno | +0.066 | +0.0733 | 0.1831 | 0.689 |
| 8 | 11654 | Propaganda Política - Propaganda Eleitor | +0.060 | +0.0471 | 0.1163 | 0.686 |
| 9 | 11649 | Pesquisa Eleitoral - Divulgação de Pesqu | -0.050 | +0.1248 | 0.0961 | 0.194 |
| 10 | 12637 | Propaganda Política - Propaganda Eleitor | +0.048 | -0.0702 | 0.1072 | 0.512 |
| 11 | 12639 | Propaganda Política - Propaganda Eleitor | +0.035 | +0.1044 | 0.1716 | 0.543 |
| 12 | 12635 | Propaganda Política - Propaganda Eleitor | -0.027 | -0.0191 | 0.0980 | 0.845 |
| 13 | 11484 | Calúnia na Propaganda Eleitoral | +0.011 | +0.0218 | 0.2795 | 0.938 |
| 14 | 12638 | Propaganda Política - Propaganda Eleitor | +0.003 | +0.0337 | 0.4293 | 0.937 |
| 15 | 12044 *(DRAP)* | Registro de Candidatura - DRAP Partido/C | -0.000 | +1.3106 | 1.1197 | 0.242 |

## Information Environment Focus (all 6 topics)

The preferred instrument (`bartik_iv_information_environment`) is built from these 6 topics.
Share exogeneity must hold for each individual topic for the family IV to be valid.

| Code | Topic | alpha | Family | R²(cov) | p(cov) | p(margin) | p(top1) | p(ncand) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11679 | Propaganda Política - Propaganda Eleitoral -  | +0.136 | information_environment | 0.055 | 0.000 * | 0.195 | 0.583 | 0.513 |
| 12637 | Propaganda Política - Propaganda Eleitoral -  | +0.048 | information_environment | 0.021 | 0.000 * | 0.400 | 0.210 | 0.512 |
| 12639 | Propaganda Política - Propaganda Eleitoral -  | +0.035 | information_environment | 0.020 | 0.000 * | 0.895 | 0.892 | 0.543 |
| 12635 | Propaganda Política - Propaganda Eleitoral -  | -0.027 | information_environment | 0.028 | 0.000 * | 0.211 | 0.478 | 0.845 |
| 11484 | Calúnia na Propaganda Eleitoral | +0.011 | information_environment | 0.014 | 0.000 * | 0.925 | 0.615 | 0.938 |
| 12638 | Propaganda Política - Propaganda Eleitoral -  | +0.003 | information_environment | 0.026 | 0.000 * | 0.166 | 0.547 | 0.937 |

(*) significant at 5% — signals potential share endogeneity.

## Notes
- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.
- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.
- DRAP (12044) is excluded from the adversarial-only instrument but shown here to evaluate its share exogeneity.
  Low R² and non-significant pre-trend coefficients for DRAP would support its inclusion as an instrument.