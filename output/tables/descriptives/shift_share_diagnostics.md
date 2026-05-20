# Shift-Share Diagnostics

## Construction checks

- Full-variant share sums are exact within municipality: mean = 1.000000, min = 1.000000, max = 1.000000.
- No-RRC share sums are exact within municipality: mean = 1.000000, min = 1.000000, max = 1.000000.
- Municipalities with any 2020 competition-topic baseline in the full components file: 4,045.
- Municipalities with any non-RRC baseline support: 4,045.
- Municipalities in the estimation design: 5,571.
- Rebuilt no-RRC Bartik matches the estimation design with max absolute difference = 0.0000000000.

## Interpretation notes

- The shift-share support is sparse: many municipalities have no baseline litigation topics and therefore receive a zero no-RRC Bartik by construction.
- The no-RRC instrument is still mostly negative in this sample because aggregate topic shocks from 2020 to 2024 are predominantly negative.
- The share side should be read as a municipality-specific topic portfolio, not a single scalar. For mapping, a scalar concentration summary is more interpretable than plotting all topic shares separately.

## Municipality-level summary (no-RRC variant)

       baseline_lawsuits_no_rrc_2020  n_topics_no_rrc  dominant_topic_share_no_rrc  share_hhi_no_rrc  avg_shock_equal_weight  bartik_iv_no_rrc
count                      5571.0000        5571.0000                    5571.0000         5571.0000               5571.0000         5571.0000
mean                         43.1149           7.7819                       0.4063            0.2737                 -0.1041           -0.0947
std                          41.1757           5.8746                       0.2818            0.2156                  0.1286            0.0843
min                           0.0000           0.0000                       0.0000            0.0000                 -1.8010           -0.7548
25%                           0.0000           0.0000                       0.0000            0.0000                 -0.1700           -0.1528
50%                          43.0000           9.0000                       0.4754            0.2795                 -0.0982           -0.0936
75%                          62.0000          12.0000                       0.6207            0.4181                  0.0000            0.0000
max                         788.0000          25.0000                       1.0000            1.0000                  0.2471            0.1422

## Top non-RRC topics by national baseline weight

| CD_ASSUNTO_PRINCIPAL | DS_ASSUNTO_PRINCIPAL | topic_family | national_share_no_rrc_2020 | mean_shift |
| --- | --- | --- | --- | --- |
| 12044 | Registro de Candidatura - DRAP Partido/Coligação | eligibility_ballot_access | 0.502 | -0.084 |
| 11617 | Registro de Candidatura - Preenchimento de Vaga Remanescente | eligibility_ballot_access | 0.0523 | -0.4973 |
| 11667 | Propaganda Política - Propaganda Eleitoral - Extemporânea/Antecipada | campaign_conduct | 0.0486 | -0.0854 |
| 11616 | Impugnação ao Registro de Candidatura | eligibility_ballot_access | 0.0458 | -0.5435 |
| 11679 | Propaganda Política - Propaganda Eleitoral - Internet | information_environment | 0.0362 | -0.4112 |
| 12635 | Propaganda Política - Propaganda Eleitoral - Divulgação de Notícia  Sabidamente Falsa | information_environment | 0.0332 | 0.3734 |
| 12637 | Propaganda Política - Propaganda Eleitoral - Redes Sociais | information_environment | 0.03 | -0.0772 |
| 11621 | Registro de Candidatura - Substituição de Candidato - Por Cancelamento de Registro | eligibility_ballot_access | 0.0291 | 0.1005 |
| 11619 | Registro de Candidatura - RRCI - Candidato Individual | eligibility_ballot_access | 0.0264 | -0.6181 |
| 11654 | Propaganda Política - Propaganda Eleitoral - Alto-falante/Amplificador de Som | campaign_conduct | 0.0229 | -0.2763 |

## State-level shift summary

| SG_UF | weighted_mean_shift | min_shift | max_shift |
| --- | --- | --- | --- |
| SC | -0.4052 | -8.509 | 0.497 |
| AP | -0.2203 | -7.9512 | 0.5961 |
| RJ | -0.2012 | -7.2626 | 1.0986 |
| AM | -0.1727 | -7.3172 | 0.5899 |
| AC | -0.1708 | -7.3324 | 0.5956 |
| MG | -0.1637 | -1.7918 | 1.0087 |
| BA | -0.1448 | -0.9568 | 0.7928 |
| SP | -0.1434 | -4.2195 | 0.7861 |
| CE | -0.1428 | -0.9441 | 1.0829 |
| TO | -0.1422 | -0.9113 | 0.5509 |
| ES | -0.1417 | -0.9186 | 0.7808 |
| GO | -0.1413 | -0.9033 | 0.6641 |
| PA | -0.1399 | -3.6109 | 0.7889 |
| PE | -0.1396 | -0.909 | 1.2379 |
| AL | -0.1396 | -4.1109 | 0.8802 |
| MA | -0.1393 | -0.913 | 1.1382 |
| MS | -0.1389 | -0.8982 | 0.5575 |
| RR | -0.1383 | -0.9017 | 0.6102 |
| SE | -0.1379 | -0.8824 | 0.7948 |
| PR | -0.1371 | -0.9089 | 0.5973 |
| RO | -0.1357 | -0.9048 | 0.5936 |
| RS | -0.1304 | -0.8992 | 0.6073 |
| PI | -0.1303 | -0.9149 | 1.1036 |
| PB | -0.1302 | -0.7457 | 1.0484 |
| MT | -0.1268 | -0.9079 | 1.109 |
| RN | -0.1141 | -0.9127 | 0.7606 |