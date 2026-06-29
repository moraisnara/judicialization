# Legislative Analysis — fixest 2SLS (R)

Adversarial Bartik shift-share IV. Same instrument as executive analysis.
Formula: `y ~ controls | state FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## First Stage

| variant | spec | coef | se | t | p | first_stage_F | nobs | n_clusters | tF_cv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline | 0.2125 | 0.0403 | 5.27 | 0.0000 | 27.81 | 5560 | 26 | 1.96 |
| adversarial | single_zone | 0.2146 | 0.0417 | 5.15 | 0.0000 | 26.47 | 5371 | 26 | 1.96 |
| adversarial | extended_controls | 0.2141 | 0.0405 | 5.29 | 0.0000 | 27.97 | 5560 | 26 | 1.96 |
| adversarial | broader_treatment | 0.2125 | 0.0403 | 5.27 | 0.0000 | 27.81 | 5560 | 26 | 1.96 |
| adversarial | ancova_2020lvl | 0.2134 | 0.0402 | 5.31 | 0.0000 | 28.22 | 5560 | 26 | 1.96 |

## IV Results

| variant | spec | family | outcome | coef | se | t | p | ivf | nobs | n_clusters | first_stage_F_lookup | tF_cv | ci95_low_tF | ci95_high_tF | reject_tF_5pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0207 | 0.0429 | -0.48 | 0.6337 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.1046767382 | 0.063324972 | FALSE |
| adversarial | baseline | candidate_pool | delta_female_share_2024_2020 | 0.0052 | 0.0049 | 1.08 | 0.2918 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0043053262 | 0.014805259 | FALSE |
| adversarial | baseline | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0109 | 0.0160 | 0.68 | 0.5036 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0205379421 | 0.042294248 | FALSE |
| adversarial | baseline | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0016 | 0.0108 | -0.14 | 0.8868 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0227408985 | 0.019630704 | FALSE |
| adversarial | baseline | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0012 | 0.0096 | -0.12 | 0.9032 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0199811227 | 0.017623986 | FALSE |
| adversarial | baseline | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3139 | 0.2782 | -1.13 | 0.2699 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.8592266818 | 0.231354233 | FALSE |
| adversarial | baseline | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0017 | 0.0074 | 0.22 | 0.8243 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0128240456 | 0.016139594 | FALSE |
| adversarial | baseline | elected_comp | delta_elected_female_share_2024_2020 | -0.0010 | 0.0151 | -0.06 | 0.9488 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0305330467 | 0.028575811 | FALSE |
| adversarial | baseline | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0177 | 0.0244 | 0.72 | 0.4754 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0302023048 | 0.065638286 | FALSE |
| adversarial | baseline | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0152 | 0.0188 | 0.81 | 0.4266 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0216083395 | 0.051935955 | FALSE |
| adversarial | baseline | elected_comp | delta_elected_mean_age_2024_2020 | 0.0014 | 0.4465 | 0.00 | 0.9975 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.8737401664 | 0.876546010 | FALSE |
| adversarial | baseline | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0374 | 0.0193 | 1.93 | 0.0646 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0005091640 | 0.075211860 | FALSE |
| adversarial | baseline | party_comp | delta_party_count_2024_2020 | -0.2122 | 0.2989 | -0.71 | 0.4843 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.7981023520 | 0.373650740 | FALSE |
| adversarial | baseline | party_comp | delta_coalition_count_2024_2020 | -0.0697 | 0.0562 | -1.24 | 0.2263 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.1797635724 | 0.040407866 | FALSE |
| adversarial | single_zone | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0179 | 0.0421 | -0.43 | 0.6739 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.1003928096 | 0.064554532 | FALSE |
| adversarial | single_zone | candidate_pool | delta_female_share_2024_2020 | 0.0057 | 0.0049 | 1.14 | 0.2636 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0040391789 | 0.015355452 | FALSE |
| adversarial | single_zone | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0121 | 0.0161 | 0.75 | 0.4579 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0193954049 | 0.043650305 | FALSE |
| adversarial | single_zone | candidate_pool | delta_new_candidate_share_2024_2020 | 0.0005 | 0.0107 | 0.04 | 0.9668 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0205582145 | 0.021460454 | FALSE |
| adversarial | single_zone | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0024 | 0.0092 | -0.26 | 0.7946 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0204411453 | 0.015602045 | FALSE |
| adversarial | single_zone | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2373 | 0.2474 | -0.96 | 0.3467 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.7222722051 | 0.247636050 | FALSE |
| adversarial | single_zone | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0013 | 0.0073 | 0.18 | 0.8599 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0130863363 | 0.015706180 | FALSE |
| adversarial | single_zone | elected_comp | delta_elected_female_share_2024_2020 | -0.0013 | 0.0150 | -0.09 | 0.9310 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0307557877 | 0.028128648 | FALSE |
| adversarial | single_zone | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0197 | 0.0243 | 0.81 | 0.4250 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0279280049 | 0.067361760 | FALSE |
| adversarial | single_zone | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0149 | 0.0182 | 0.81 | 0.4231 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0209012773 | 0.050617031 | FALSE |
| adversarial | single_zone | elected_comp | delta_elected_mean_age_2024_2020 | 0.0156 | 0.4550 | 0.03 | 0.9729 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.8761963738 | 0.907375453 | FALSE |
| adversarial | single_zone | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0351 | 0.0188 | 1.87 | 0.0735 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.0017244181 | 0.071962513 | FALSE |
| adversarial | single_zone | party_comp | delta_party_count_2024_2020 | -0.1687 | 0.2588 | -0.65 | 0.5206 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.6759989026 | 0.338660212 | FALSE |
| adversarial | single_zone | party_comp | delta_coalition_count_2024_2020 | -0.0653 | 0.0563 | -1.16 | 0.2573 | 71.58 | 5371 | 26 | 26.47235 | 1.96 | -0.1755817129 | 0.045078305 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0226 | 0.0433 | -0.52 | 0.6072 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.1075104725 | 0.062386659 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_female_share_2024_2020 | 0.0065 | 0.0035 | 1.87 | 0.0735 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0003215505 | 0.013400879 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0024 | 0.0135 | 0.17 | 0.8629 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0240831265 | 0.028790652 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0018 | 0.0109 | -0.17 | 0.8698 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0231804080 | 0.019568623 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0019 | 0.0097 | -0.19 | 0.8489 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0208254465 | 0.017100496 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3199 | 0.2841 | -1.13 | 0.2709 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.8767659093 | 0.236951972 | FALSE |
| adversarial | extended_controls | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0015 | 0.0078 | 0.19 | 0.8510 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0138704542 | 0.016844587 | FALSE |
| adversarial | extended_controls | elected_comp | delta_elected_female_share_2024_2020 | -0.0009 | 0.0148 | -0.06 | 0.9518 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0299898901 | 0.028176969 | FALSE |
| adversarial | extended_controls | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0101 | 0.0216 | 0.47 | 0.6451 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0323132000 | 0.052484398 | FALSE |
| adversarial | extended_controls | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0154 | 0.0185 | 0.83 | 0.4145 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.0209420082 | 0.051691195 | FALSE |
| adversarial | extended_controls | elected_comp | delta_elected_mean_age_2024_2020 | 0.0108 | 0.4445 | 0.02 | 0.9809 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.8604986379 | 0.882012953 | FALSE |
| adversarial | extended_controls | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0377 | 0.0190 | 1.98 | 0.0585 | 72.68 | 5560 | 26 | 27.97153 | 1.96 |  0.0004310761 | 0.074910627 | TRUE |
| adversarial | extended_controls | party_comp | delta_party_count_2024_2020 | -0.2136 | 0.3070 | -0.70 | 0.4929 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.8152157903 | 0.388031241 | FALSE |
| adversarial | extended_controls | party_comp | delta_coalition_count_2024_2020 | -0.0677 | 0.0555 | -1.22 | 0.2335 | 72.68 | 5560 | 26 | 27.97153 | 1.96 | -0.1763994334 | 0.040988755 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0207 | 0.0429 | -0.48 | 0.6337 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.1046767382 | 0.063324972 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_female_share_2024_2020 | 0.0052 | 0.0049 | 1.08 | 0.2918 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0043053262 | 0.014805259 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0109 | 0.0160 | 0.68 | 0.5036 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0205379421 | 0.042294248 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0016 | 0.0108 | -0.14 | 0.8868 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0227408985 | 0.019630704 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0012 | 0.0096 | -0.12 | 0.9032 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0199811227 | 0.017623986 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3139 | 0.2782 | -1.13 | 0.2699 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.8592266818 | 0.231354233 | FALSE |
| adversarial | broader_treatment | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0017 | 0.0074 | 0.22 | 0.8243 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0128240456 | 0.016139594 | FALSE |
| adversarial | broader_treatment | elected_comp | delta_elected_female_share_2024_2020 | -0.0010 | 0.0151 | -0.06 | 0.9488 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0305330467 | 0.028575811 | FALSE |
| adversarial | broader_treatment | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0177 | 0.0244 | 0.72 | 0.4754 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0302023048 | 0.065638286 | FALSE |
| adversarial | broader_treatment | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0152 | 0.0188 | 0.81 | 0.4266 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0216083395 | 0.051935955 | FALSE |
| adversarial | broader_treatment | elected_comp | delta_elected_mean_age_2024_2020 | 0.0014 | 0.4465 | 0.00 | 0.9975 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.8737401664 | 0.876546010 | FALSE |
| adversarial | broader_treatment | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0374 | 0.0193 | 1.93 | 0.0646 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.0005091640 | 0.075211860 | FALSE |
| adversarial | broader_treatment | party_comp | delta_party_count_2024_2020 | -0.2122 | 0.2989 | -0.71 | 0.4843 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.7981023520 | 0.373650740 | FALSE |
| adversarial | broader_treatment | party_comp | delta_coalition_count_2024_2020 | -0.0697 | 0.0562 | -1.24 | 0.2263 | 71.44 | 5560 | 26 | 27.81046 | 1.96 | -0.1797635724 | 0.040407866 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0035 | 0.0362 | -0.10 | 0.9234 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0743885620 | 0.067360214 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_female_share_2024_2020 | 0.0056 | 0.0049 | 1.13 | 0.2684 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0040835172 | 0.015249295 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0113 | 0.0162 | 0.70 | 0.4912 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0203949132 | 0.042992114 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0004 | 0.0104 | -0.04 | 0.9666 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0207672139 | 0.019888826 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0022 | 0.0086 | -0.25 | 0.8026 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0189579775 | 0.014627820 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.0376 | 0.2053 | -0.18 | 0.8561 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.4400065253 | 0.364772025 | FALSE |
| adversarial | ancova_2020lvl | candidate_pool | delta_candidate_hhi_party_2024_2020 | -0.0035 | 0.0060 | -0.59 | 0.5577 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0152028876 | 0.008128797 | FALSE |
| adversarial | ancova_2020lvl | elected_comp | delta_elected_female_share_2024_2020 | -0.0006 | 0.0149 | -0.04 | 0.9679 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0298171086 | 0.028605087 | FALSE |
| adversarial | ancova_2020lvl | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0172 | 0.0242 | 0.71 | 0.4825 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0301538565 | 0.064632737 | FALSE |
| adversarial | ancova_2020lvl | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0136 | 0.0187 | 0.73 | 0.4725 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.0229723130 | 0.050203776 | FALSE |
| adversarial | ancova_2020lvl | elected_comp | delta_elected_mean_age_2024_2020 | 0.0293 | 0.4423 | 0.07 | 0.9477 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.8375546182 | 0.896176180 | FALSE |
| adversarial | ancova_2020lvl | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0373 | 0.0188 | 1.99 | 0.0582 | 71.94 | 5560 | 26 | 28.22276 | 1.96 |  0.0004794295 | 0.074188998 | TRUE |
| adversarial | ancova_2020lvl | party_comp | delta_party_count_2024_2020 | 0.0591 | 0.2280 | 0.26 | 0.7977 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.3878853744 | 0.506067623 | FALSE |
| adversarial | ancova_2020lvl | party_comp | delta_coalition_count_2024_2020 | -0.0709 | 0.0532 | -1.33 | 0.1949 | 71.94 | 5560 | 26 | 28.22276 | 1.96 | -0.1752793503 | 0.033433905 | FALSE |
