# Legislative Analysis — fixest 2SLS (R)

Adversarial Bartik shift-share IV. Same instrument as executive analysis.
Formula: `y ~ controls | state FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## First Stage

| spec | coef | se | t | p | first_stage_F | nobs | n_clusters | tF_cv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | 1.7757 | 0.4033 | 4.40 | 0.0000 | 19.38 | 5560 | 2187 |  2.188465 |
| robustness_full_controls | 1.7584 | 0.3997 | 4.40 | 0.0000 | 19.36 | 5560 | 2187 |  2.189239 |
| subsample_le200k | 1.7844 | 0.4069 | 4.38 | 0.0000 | 19.23 | 5509 | 2140 |  2.193166 |
| subsample_gt200k | 1.8797 | 2.5497 | 0.74 | 0.4655 | 0.54 |   51 |   51 | 13.990000 |

## IV Results

| spec | family | outcome | coef | se | t | p | ivf | nobs | n_clusters | first_stage_F_lookup | tF_cv | ci95_low_tF | ci95_high_tF | reject_tF_5pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0752 | 0.0410 | -1.84 | 0.0664 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.16486076 | 1.440528e-02 | FALSE |
| baseline_state_fe | candidate_pool | delta_female_share_2024_2020 | -0.0056 | 0.0063 | -0.90 | 0.3702 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.01929989 | 8.083841e-03 | FALSE |
| baseline_state_fe | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0177 | 0.0187 | -0.94 | 0.3463 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.05868478 | 2.336534e-02 | FALSE |
| baseline_state_fe | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0195 | 0.0158 | -1.24 | 0.2166 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.05407873 | 1.504154e-02 | FALSE |
| baseline_state_fe | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0085 | 0.0104 | -0.82 | 0.4145 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.03110969 | 1.420934e-02 | FALSE |
| baseline_state_fe | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2637 | 0.3011 | -0.88 | 0.3812 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.92264233 | 3.951775e-01 | FALSE |
| baseline_state_fe | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0109 | 0.0115 | 0.95 | 0.3441 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.01433118 | 3.617034e-02 | FALSE |
| baseline_state_fe | elected_comp | delta_elected_female_share_2024_2020 | 0.0131 | 0.0221 | 0.59 | 0.5542 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.03530478 | 6.146626e-02 | FALSE |
| baseline_state_fe | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0274 | 0.0258 | -1.06 | 0.2884 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.08395053 | 2.909497e-02 | FALSE |
| baseline_state_fe | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0065 | 0.0258 | 0.25 | 0.8025 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.05001694 | 6.293017e-02 | FALSE |
| baseline_state_fe | elected_comp | delta_elected_mean_age_2024_2020 | 0.0392 | 0.5761 | 0.07 | 0.9457 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -1.22154407 | 1.299999e+00 | FALSE |
| baseline_state_fe | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0064 | 0.0249 | 0.26 | 0.7975 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.04818877 | 6.099380e-02 | FALSE |
| baseline_state_fe | party_comp | delta_party_count_2024_2020 | -0.2599 | 0.3542 | -0.73 | 0.4632 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -1.03505746 | 5.153170e-01 | FALSE |
| baseline_state_fe | party_comp | delta_coalition_count_2024_2020 | 0.0739 | 0.0665 | 1.11 | 0.2663 | 235.76 | 5560 | 2187 | 19.3844859 |  2.188465 |   -0.07154813 | 2.193207e-01 | FALSE |
| robustness_full_controls | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0734 | 0.0411 | -1.79 | 0.0743 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.16345392 | 1.659206e-02 | FALSE |
| robustness_full_controls | candidate_pool | delta_female_share_2024_2020 | 0.0004 | 0.0049 | 0.08 | 0.9384 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.01031636 | 1.107193e-02 | FALSE |
| robustness_full_controls | candidate_pool | delta_nonwhite_share_2024_2020 | 0.0155 | 0.0192 | 0.81 | 0.4183 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.02648001 | 5.755089e-02 | FALSE |
| robustness_full_controls | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0188 | 0.0159 | -1.18 | 0.2378 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.05360387 | 1.603871e-02 | FALSE |
| robustness_full_controls | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0079 | 0.0105 | -0.75 | 0.4524 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.03088405 | 1.509830e-02 | FALSE |
| robustness_full_controls | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.2441 | 0.3031 | -0.81 | 0.4208 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.90777431 | 4.195546e-01 | FALSE |
| robustness_full_controls | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0087 | 0.0113 | 0.77 | 0.4398 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.01600151 | 3.345729e-02 | FALSE |
| robustness_full_controls | elected_comp | delta_elected_female_share_2024_2020 | 0.0175 | 0.0225 | 0.78 | 0.4357 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.03166802 | 6.669763e-02 | FALSE |
| robustness_full_controls | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.0028 | 0.0252 | 0.11 | 0.9114 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.05239732 | 5.801198e-02 | FALSE |
| robustness_full_controls | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0085 | 0.0261 | 0.32 | 0.7455 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.04857698 | 6.548894e-02 | FALSE |
| robustness_full_controls | elected_comp | delta_elected_mean_age_2024_2020 | -0.0076 | 0.5851 | -0.01 | 0.9896 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -1.28860931 | 1.273362e+00 | FALSE |
| robustness_full_controls | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0052 | 0.0253 | 0.20 | 0.8379 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.05016553 | 6.051132e-02 | FALSE |
| robustness_full_controls | party_comp | delta_party_count_2024_2020 | -0.2279 | 0.3557 | -0.64 | 0.5218 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -1.00667943 | 5.508259e-01 | FALSE |
| robustness_full_controls | party_comp | delta_coalition_count_2024_2020 | 0.0693 | 0.0671 | 1.03 | 0.3021 | 230.93 | 5560 | 2187 | 19.3586869 |  2.189239 |   -0.07766167 | 2.162289e-01 | FALSE |
| subsample_le200k | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0787 | 0.0415 | -1.89 | 0.0584 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.16974061 | 1.242986e-02 | FALSE |
| subsample_le200k | candidate_pool | delta_female_share_2024_2020 | -0.0057 | 0.0063 | -0.89 | 0.3714 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.01951237 | 8.210539e-03 | FALSE |
| subsample_le200k | candidate_pool | delta_nonwhite_share_2024_2020 | -0.0177 | 0.0189 | -0.93 | 0.3505 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.05912423 | 2.381080e-02 | FALSE |
| subsample_le200k | candidate_pool | delta_new_candidate_share_2024_2020 | -0.0200 | 0.0159 | -1.26 | 0.2082 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.05479686 | 1.482886e-02 | FALSE |
| subsample_le200k | candidate_pool | delta_incumbent_candidate_share_2024_2020 | -0.0071 | 0.0104 | -0.69 | 0.4924 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.02981373 | 1.559630e-02 | FALSE |
| subsample_le200k | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -0.3381 | 0.3027 | -1.12 | 0.2643 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -1.00204986 | 3.259071e-01 | FALSE |
| subsample_le200k | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0114 | 0.0117 | 0.98 | 0.3296 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.01423639 | 3.703378e-02 | FALSE |
| subsample_le200k | elected_comp | delta_elected_female_share_2024_2020 | 0.0159 | 0.0224 | 0.71 | 0.4789 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.03332693 | 6.511849e-02 | FALSE |
| subsample_le200k | elected_comp | delta_elected_nonwhite_share_2024_2020 | -0.0268 | 0.0259 | -1.03 | 0.3018 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.08361270 | 3.007332e-02 | FALSE |
| subsample_le200k | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0060 | 0.0260 | 0.23 | 0.8173 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.05102598 | 6.304225e-02 | FALSE |
| subsample_le200k | elected_comp | delta_elected_mean_age_2024_2020 | -0.0137 | 0.5827 | -0.02 | 0.9812 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -1.29164608 | 1.264163e+00 | FALSE |
| subsample_le200k | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0036 | 0.0250 | 0.14 | 0.8865 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.05127208 | 5.841441e-02 | FALSE |
| subsample_le200k | party_comp | delta_party_count_2024_2020 | -0.2913 | 0.3511 | -0.83 | 0.4068 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -1.06140378 | 4.787821e-01 | FALSE |
| subsample_le200k | party_comp | delta_coalition_count_2024_2020 | 0.0702 | 0.0669 | 1.05 | 0.2943 | 237.58 | 5509 | 2140 | 19.2277946 |  2.193166 |   -0.07654612 | 2.168890e-01 | FALSE |
| subsample_gt200k | candidate_pool | delta_log1p_total_candidates_2024_2020 | -0.0797 | 0.3630 | -0.22 | 0.8274 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -5.15803078 | 4.998683e+00 | FALSE |
| subsample_gt200k | candidate_pool | delta_female_share_2024_2020 | -0.0186 | 0.0482 | -0.39 | 0.7019 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -0.69311759 | 6.559309e-01 | FALSE |
| subsample_gt200k | candidate_pool | delta_nonwhite_share_2024_2020 | -0.1083 | 0.2054 | -0.53 | 0.6010 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -2.98140166 | 2.764771e+00 | FALSE |
| subsample_gt200k | candidate_pool | delta_new_candidate_share_2024_2020 | 0.0107 | 0.0828 | 0.13 | 0.8976 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -1.14738935 | 1.168832e+00 | FALSE |
| subsample_gt200k | candidate_pool | delta_incumbent_candidate_share_2024_2020 | 0.0128 | 0.0291 | 0.44 | 0.6630 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -0.39428879 | 4.198440e-01 | FALSE |
| subsample_gt200k | candidate_pool | delta_effective_party_count_candidates_2024_2020 | -3.6880 | 7.4368 | -0.50 | 0.6228 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 | -107.72846766 | 1.003525e+02 | FALSE |
| subsample_gt200k | candidate_pool | delta_candidate_hhi_party_2024_2020 | 0.0109 | 0.0231 | 0.47 | 0.6410 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -0.31231260 | 3.340295e-01 | FALSE |
| subsample_gt200k | elected_comp | delta_elected_female_share_2024_2020 | -0.2300 | 0.4249 | -0.54 | 0.5915 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -6.17492697 | 5.714991e+00 | FALSE |
| subsample_gt200k | elected_comp | delta_elected_nonwhite_share_2024_2020 | 0.5559 | 0.7888 | 0.70 | 0.4853 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |  -10.47975005 | 1.159161e+01 | FALSE |
| subsample_gt200k | elected_comp | delta_elected_higher_ed_share_2024_2020 | 0.0326 | 0.3358 | 0.10 | 0.9231 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -4.66524439 | 4.730527e+00 | FALSE |
| subsample_gt200k | elected_comp | delta_elected_mean_age_2024_2020 | 0.0366 | 10.5710 | 0.00 | 0.9973 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 | -147.85119853 | 1.479243e+02 | FALSE |
| subsample_gt200k | elected_comp | delta_incumbent_reelected_share_2024_2020 | 0.0102 | 0.3276 | 0.03 | 0.9752 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 |   -4.57240540 | 4.592865e+00 | FALSE |
| subsample_gt200k | party_comp | delta_party_count_2024_2020 | -2.8886 | 8.9562 | -0.32 | 0.7488 | 0.48 |   51 |   51 |  0.5434747 | 13.990000 | -128.18527775 | 1.224082e+02 | FALSE |
