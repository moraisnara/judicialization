# Legislative Analysis — fixest 2SLS (R)

Adversarial Bartik shift-share IV. Same instrument as executive analysis.
Formula: `y ~ controls | state FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## First Stage

| variant | spec | coef | se | t | p | first_stage_F | nobs | n_clusters | tF_cv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | 1.7757 | 0.4033 | 4.40 | 0.0000 | 19.38 | 5560 | 2187 | 2.188465 |
| adversarial | baseline_state_fe_sz | 1.7893 | 0.4211 | 4.25 | 0.0000 | 18.06 | 5371 | 2049 | 2.237753 |
| adversarial | robustness_full_controls | 1.7584 | 0.3997 | 4.40 | 0.0000 | 19.36 | 5560 | 2187 | 2.189239 |
| adversarial | subsample_le200k | 1.7844 | 0.4069 | 4.38 | 0.0000 | 19.23 | 5509 | 2140 | 2.193166 |
| adversarial | robustness_broader_lawsuits | 1.7757 | 0.4033 | 4.40 | 0.0000 | 19.38 | 5560 | 2187 | 2.188465 |

## IV Results

| variant | spec | family | outcome | coef | se | t | p | ivf | nobs | n_clusters | first_stage_F_lookup | tF_cv | ci95_low_tF | ci95_high_tF | reject_tF_5pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0752 | 0.0410 | -1.84 | 0.0664 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.16486076 | 0.014405283 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_female_share_2024_2020 | -0.0056 | 0.0063 | -0.90 | 0.3702 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.01929989 | 0.008083841 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0177 | 0.0187 | -0.94 | 0.3463 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05868478 | 0.023365338 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0195 | 0.0158 | -1.24 | 0.2166 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05407873 | 0.015041540 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0085 | 0.0104 | -0.82 | 0.4145 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.03110969 | 0.014209336 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2637 | 0.3011 | -0.88 | 0.3812 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.92264233 | 0.395177487 | FALSE |
| adversarial | baseline_state_fe | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0109 | 0.0115 | 0.95 | 0.3441 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.01433118 | 0.036170339 | FALSE |
| adversarial | baseline_state_fe | elected_comp | delta_elected_female_share_2024_2020 | 0.0131 | 0.0221 | 0.59 | 0.5542 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.03530478 | 0.061466260 | FALSE |
| adversarial | baseline_state_fe | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0274 | 0.0258 | -1.06 | 0.2884 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.08395053 | 0.029094967 | FALSE |
| adversarial | baseline_state_fe | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0065 | 0.0258 | 0.25 | 0.8025 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05001694 | 0.062930171 | FALSE |
| adversarial | baseline_state_fe | elected_comp | delta_elected_mean_age_2024_2020 | 0.0392 | 0.5761 | 0.07 | 0.9457 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -1.22154407 | 1.299999347 | FALSE |
| adversarial | baseline_state_fe | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0064 | 0.0249 | 0.26 | 0.7975 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.04818877 | 0.060993800 | FALSE |
| adversarial | baseline_state_fe | party_comp | delta_party_count_2024_2020 | -0.2599 | 0.3542 | -0.73 | 0.4632 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -1.03505746 | 0.515316986 | FALSE |
| adversarial | baseline_state_fe | party_comp | delta_coalition_count_2024_2020 | 0.0739 | 0.0665 | 1.11 | 0.2663 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.07154813 | 0.219320706 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0804 | 0.0428 | -1.88 | 0.0607 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.17623726 | 0.015455916 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_female_share_2024_2020 | -0.0065 | 0.0066 | -0.99 | 0.3206 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.02127662 | 0.008192829 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0179 | 0.0196 | -0.91 | 0.3618 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.06186438 | 0.026035912 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0217 | 0.0166 | -1.30 | 0.1923 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.05882482 | 0.015506067 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0048 | 0.0106 | -0.45 | 0.6531 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.02849035 | 0.018958769 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3797 | 0.3021 | -1.26 | 0.2090 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -1.05578209 | 0.296387463 | FALSE |
| adversarial | baseline_state_fe_sz | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0098 | 0.0121 | 0.81 | 0.4176 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.01724927 | 0.036851420 | FALSE |
| adversarial | baseline_state_fe_sz | elected_comp | delta_elected_female_share_2024_2020 | 0.0132 | 0.0232 | 0.57 | 0.5686 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.03863216 | 0.065050464 | FALSE |
| adversarial | baseline_state_fe_sz | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0276 | 0.0271 | -1.02 | 0.3076 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.08827590 | 0.032976521 | FALSE |
| adversarial | baseline_state_fe_sz | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0039 | 0.0267 | 0.15 | 0.8841 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.05586173 | 0.063648772 | FALSE |
| adversarial | baseline_state_fe_sz | elected_comp | delta_elected_mean_age_2024_2020 | -0.1012 | 0.6219 | -0.16 | 0.8707 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -1.49284870 | 1.290363421 | FALSE |
| adversarial | baseline_state_fe_sz | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0056 | 0.0252 | 0.22 | 0.8231 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.05083290 | 0.062121643 | FALSE |
| adversarial | baseline_state_fe_sz | party_comp | delta_party_count_2024_2020 | -0.3764 | 0.3536 | -1.06 | 0.2873 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -1.16769072 | 0.414949412 | FALSE |
| adversarial | baseline_state_fe_sz | party_comp | delta_coalition_count_2024_2020 | 0.0645 | 0.0701 | 0.92 | 0.3572 | 230.48 | 5371 | 2049 | 18.05617 | 2.237753 | -0.09229414 | 0.221368515 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0734 | 0.0411 | -1.79 | 0.0743 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.16345392 | 0.016592062 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_female_share_2024_2020 | 0.0004 | 0.0049 | 0.08 | 0.9384 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.01031636 | 0.011071932 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0155 | 0.0192 | 0.81 | 0.4183 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.02648001 | 0.057550894 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0188 | 0.0159 | -1.18 | 0.2378 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.05360387 | 0.016038714 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0079 | 0.0105 | -0.75 | 0.4524 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.03088405 | 0.015098304 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2441 | 0.3031 | -0.81 | 0.4208 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.90777431 | 0.419554587 | FALSE |
| adversarial | robustness_full_controls | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0087 | 0.0113 | 0.77 | 0.4398 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.01600151 | 0.033457287 | FALSE |
| adversarial | robustness_full_controls | elected_comp | delta_elected_female_share_2024_2020 | 0.0175 | 0.0225 | 0.78 | 0.4357 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.03166802 | 0.066697629 | FALSE |
| adversarial | robustness_full_controls | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0028 | 0.0252 | 0.11 | 0.9114 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.05239732 | 0.058011978 | FALSE |
| adversarial | robustness_full_controls | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0085 | 0.0261 | 0.32 | 0.7455 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.04857698 | 0.065488942 | FALSE |
| adversarial | robustness_full_controls | elected_comp | delta_elected_mean_age_2024_2020 | -0.0076 | 0.5851 | -0.01 | 0.9896 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -1.28860931 | 1.273362446 | FALSE |
| adversarial | robustness_full_controls | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0052 | 0.0253 | 0.20 | 0.8379 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.05016553 | 0.060511324 | FALSE |
| adversarial | robustness_full_controls | party_comp | delta_party_count_2024_2020 | -0.2279 | 0.3557 | -0.64 | 0.5218 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -1.00667943 | 0.550825901 | FALSE |
| adversarial | robustness_full_controls | party_comp | delta_coalition_count_2024_2020 | 0.0693 | 0.0671 | 1.03 | 0.3021 | 230.93 | 5560 | 2187 | 19.35869 | 2.189239 | -0.07766167 | 0.216228920 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0787 | 0.0415 | -1.89 | 0.0584 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.16974061 | 0.012429864 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_female_share_2024_2020 | -0.0057 | 0.0063 | -0.89 | 0.3714 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.01951237 | 0.008210539 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0177 | 0.0189 | -0.93 | 0.3505 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.05912423 | 0.023810804 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0200 | 0.0159 | -1.26 | 0.2082 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.05479686 | 0.014828860 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0071 | 0.0104 | -0.69 | 0.4924 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.02981373 | 0.015596302 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3381 | 0.3027 | -1.12 | 0.2643 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -1.00204986 | 0.325907118 | FALSE |
| adversarial | subsample_le200k | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0114 | 0.0117 | 0.98 | 0.3296 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.01423639 | 0.037033780 | FALSE |
| adversarial | subsample_le200k | elected_comp | delta_elected_female_share_2024_2020 | 0.0159 | 0.0224 | 0.71 | 0.4789 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.03332693 | 0.065118486 | FALSE |
| adversarial | subsample_le200k | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0268 | 0.0259 | -1.03 | 0.3018 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.08361270 | 0.030073320 | FALSE |
| adversarial | subsample_le200k | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0060 | 0.0260 | 0.23 | 0.8173 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.05102598 | 0.063042249 | FALSE |
| adversarial | subsample_le200k | elected_comp | delta_elected_mean_age_2024_2020 | -0.0137 | 0.5827 | -0.02 | 0.9812 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -1.29164608 | 1.264162688 | FALSE |
| adversarial | subsample_le200k | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0036 | 0.0250 | 0.14 | 0.8865 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.05127208 | 0.058414407 | FALSE |
| adversarial | subsample_le200k | party_comp | delta_party_count_2024_2020 | -0.2913 | 0.3511 | -0.83 | 0.4068 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -1.06140378 | 0.478782071 | FALSE |
| adversarial | subsample_le200k | party_comp | delta_coalition_count_2024_2020 | 0.0702 | 0.0669 | 1.05 | 0.2943 | 237.58 | 5509 | 2140 | 19.22779 | 2.193166 | -0.07654612 | 0.216889030 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0752 | 0.0410 | -1.84 | 0.0664 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.16486076 | 0.014405283 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_female_share_2024_2020 | -0.0056 | 0.0063 | -0.90 | 0.3702 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.01929989 | 0.008083841 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0177 | 0.0187 | -0.94 | 0.3463 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05868478 | 0.023365338 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0195 | 0.0158 | -1.24 | 0.2166 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05407873 | 0.015041540 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0085 | 0.0104 | -0.82 | 0.4145 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.03110969 | 0.014209336 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2637 | 0.3011 | -0.88 | 0.3812 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.92264233 | 0.395177487 | FALSE |
| adversarial | robustness_broader_lawsuits | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0109 | 0.0115 | 0.95 | 0.3441 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.01433118 | 0.036170339 | FALSE |
| adversarial | robustness_broader_lawsuits | elected_comp | delta_elected_female_share_2024_2020 | 0.0131 | 0.0221 | 0.59 | 0.5542 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.03530478 | 0.061466260 | FALSE |
| adversarial | robustness_broader_lawsuits | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0274 | 0.0258 | -1.06 | 0.2884 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.08395053 | 0.029094967 | FALSE |
| adversarial | robustness_broader_lawsuits | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0065 | 0.0258 | 0.25 | 0.8025 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.05001694 | 0.062930171 | FALSE |
| adversarial | robustness_broader_lawsuits | elected_comp | delta_elected_mean_age_2024_2020 | 0.0392 | 0.5761 | 0.07 | 0.9457 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -1.22154407 | 1.299999347 | FALSE |
| adversarial | robustness_broader_lawsuits | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0064 | 0.0249 | 0.26 | 0.7975 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.04818877 | 0.060993800 | FALSE |
| adversarial | robustness_broader_lawsuits | party_comp | delta_party_count_2024_2020 | -0.2599 | 0.3542 | -0.73 | 0.4632 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -1.03505746 | 0.515316986 | FALSE |
| adversarial | robustness_broader_lawsuits | party_comp | delta_coalition_count_2024_2020 | 0.0739 | 0.0665 | 1.11 | 0.2663 | 235.76 | 5560 | 2187 | 19.38449 | 2.188465 | -0.07154813 | 0.219320706 | FALSE |
