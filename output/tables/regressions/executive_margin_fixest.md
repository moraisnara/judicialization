# Executive Margin Analysis — fixest 2SLS (R)

Benchmark: Ash, Morelli & Vannoni (2025, JPE) — `ivreghdfe` → `feols()` in fixest.
Formula: `y ~ controls | FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## Instrument
- **adversarial** : bartik_iv_2020_2024 / delta_log1p_competition_lawsuits_2024_2020
  (adversarial class/subject filter applied at build stage in 02_bartik_inputs.py)

## Specifications
1. **baseline_state_fe** — 7 baseline controls + state FE
2. **baseline_state_fe_sz** — same, single-zone municipalities only
3. **robustness_full_controls** — 14 controls + state FE
4. **robustness_microregion_fe** — 7 baseline controls + microregion FE
5. **subsample_le200k** — baseline + state FE, ≤200k registered voters
6. **robustness_topic_shares** — baseline + top-4 Rotemberg topic shares
7. **robustness_broader_lawsuits** — baseline + log1p_lawsuits_no_rrc_2020

## First Stage

| variant | spec | coef | se | t | p | first_stage_F | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | 1.7918 | 0.4049 | 4.43 | 0.0000 | 19.58 | 5560 | 2187 |
| adversarial | baseline_state_fe_sz | 1.8008 | 0.4217 | 4.27 | 0.0000 | 18.24 | 5371 | 2049 |
| adversarial | robustness_full_controls | 1.7998 | 0.4058 | 4.44 | 0.0000 | 19.68 | 5560 | 2187 |
| adversarial | subsample_le200k | 1.8693 | 0.4260 | 4.39 | 0.0000 | 19.25 | 5338 | 2017 |
| adversarial | subsample_open_seat | 1.3302 | 0.4083 | 3.26 | 0.0011 | 10.62 | 2571 | 1563 |
| adversarial | subsample_contested_seat | 2.1895 | 0.5595 | 3.91 | 0.0001 | 15.31 | 2989 | 1756 |
| adversarial | robustness_topic_shares | -0.6564 | 0.9256 | -0.71 | 0.4784 | 0.50 | 2824 | 1093 |
| adversarial | robustness_broader_lawsuits | 1.7918 | 0.4049 | 4.43 | 0.0000 | 19.58 | 5560 | 2187 |

## IV Results

| variant | spec | estimator | family | outcome | coef | se | t | p | ivf | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0307 | 0.0217 | -1.42 | 0.1572 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0619 | 0.0431 | 1.44 | 0.1508 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0312 | 0.0251 | 1.25 | 0.2132 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1398 | 0.0903 | 1.55 | 0.1218 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0048 | 0.0186 | -0.26 | 0.7983 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0664 | 0.0393 | -1.69 | 0.0917 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0929 | 0.0479 | -1.94 | 0.0524 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0394 | 0.0420 | -0.94 | 0.3482 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0095 | 0.0499 | -0.19 | 0.8484 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0096 | 0.0490 | 0.20 | 0.8443 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_winner_is_female_2024_2020 | -0.1229 | 0.0632 | -1.94 | 0.0521 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0016 | 0.0733 | -0.02 | 0.9823 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0063 | 0.0048 | -1.33 | 0.1848 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0073 | 0.0059 | 1.23 | 0.2197 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0126 | 0.0053 | 2.36 | 0.0184 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0263 | 0.0127 | -2.07 | 0.0381 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0114 | 0.0433 | -0.26 | 0.7928 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0066 | 0.0261 | 0.25 | 0.8019 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0045 | 0.0254 | 0.18 | 0.8610 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe_sz | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0247 | 0.0220 | -1.12 | 0.2629 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0533 | 0.0439 | 1.21 | 0.2249 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0286 | 0.0257 | 1.11 | 0.2662 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1400 | 0.0932 | 1.50 | 0.1330 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0069 | 0.0193 | -0.36 | 0.7192 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0561 | 0.0395 | -1.42 | 0.1557 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0890 | 0.0486 | -1.83 | 0.0673 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0436 | 0.0440 | -0.99 | 0.3214 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0093 | 0.0521 | -0.18 | 0.8586 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0050 | 0.0505 | 0.10 | 0.9206 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_winner_is_female_2024_2020 | -0.1281 | 0.0659 | -1.94 | 0.0521 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0115 | 0.0766 | -0.15 | 0.8805 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0051 | 0.0048 | -1.06 | 0.2908 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0071 | 0.0063 | 1.13 | 0.2566 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0130 | 0.0056 | 2.30 | 0.0215 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0253 | 0.0132 | -1.92 | 0.0548 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | entry | delta_share_first_time_candidates_2024_2020 | 0.0036 | 0.0455 | 0.08 | 0.9373 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0080 | 0.0272 | 0.29 | 0.7700 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0014 | 0.0268 | 0.05 | 0.9583 | 232.87 | 5371 | 2049 |
| adversarial | robustness_full_controls | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0269 | 0.0209 | -1.29 | 0.1979 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0558 | 0.0419 | 1.33 | 0.1834 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0289 | 0.0246 | 1.17 | 0.2410 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1477 | 0.0897 | 1.65 | 0.0997 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0065 | 0.0183 | -0.36 | 0.7219 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0639 | 0.0385 | -1.66 | 0.0970 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_female_vote_share_2024_2020 | -0.1262 | 0.0490 | -2.58 | 0.0101 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0021 | 0.0367 | 0.06 | 0.9545 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0033 | 0.0497 | -0.07 | 0.9467 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0007 | 0.0475 | 0.01 | 0.9885 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_winner_is_female_2024_2020 | -0.1562 | 0.0640 | -2.44 | 0.0147 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0061 | 0.0722 | 0.08 | 0.9326 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0028 | 0.0040 | -0.71 | 0.4783 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0059 | 0.0047 | 1.27 | 0.2041 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0119 | 0.0051 | 2.35 | 0.0187 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0208 | 0.0104 | -2.00 | 0.0457 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0048 | 0.0333 | -0.14 | 0.8852 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0064 | 0.0254 | 0.25 | 0.8020 | 241.31 | 5560 | 2187 |
| adversarial | robustness_full_controls | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0053 | 0.0246 | 0.22 | 0.8280 | 241.31 | 5560 | 2187 |
| adversarial | subsample_le200k | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0247 | 0.0212 | -1.16 | 0.2456 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0521 | 0.0423 | 1.23 | 0.2173 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0275 | 0.0247 | 1.11 | 0.2661 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1240 | 0.0886 | 1.40 | 0.1618 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0063 | 0.0185 | -0.34 | 0.7351 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0519 | 0.0378 | -1.37 | 0.1697 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0858 | 0.0466 | -1.84 | 0.0658 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0466 | 0.0424 | -1.10 | 0.2726 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0088 | 0.0507 | -0.17 | 0.8618 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0026 | 0.0488 | 0.05 | 0.9579 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_winner_is_female_2024_2020 | -0.1223 | 0.0630 | -1.94 | 0.0525 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0156 | 0.0746 | -0.21 | 0.8344 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0038 | 0.0045 | -0.84 | 0.4027 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0075 | 0.0061 | 1.24 | 0.2158 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0125 | 0.0054 | 2.31 | 0.0210 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0239 | 0.0126 | -1.90 | 0.0576 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | entry | delta_share_first_time_candidates_2024_2020 | 0.0050 | 0.0442 | 0.11 | 0.9105 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0041 | 0.0262 | 0.16 | 0.8760 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0053 | 0.0260 | 0.20 | 0.8384 | 247.49 | 5338 | 2017 |
| adversarial | subsample_open_seat | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0410 | 0.0404 | -1.01 | 0.3112 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0610 | 0.0791 | 0.77 | 0.4405 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0201 | 0.0459 | 0.44 | 0.6619 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0926 | 0.1693 | 0.55 | 0.5846 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | secondary | delta_others_vote_share_2024_2020 | 0.0141 | 0.0350 | 0.40 | 0.6869 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | 0.0046 | 0.0714 | 0.06 | 0.9486 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_female_vote_share_2024_2020 | -0.1377 | 0.1111 | -1.24 | 0.2152 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.1263 | 0.1078 | -1.17 | 0.2412 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0845 | 0.0832 | -1.02 | 0.3100 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | -0.0241 | 0.0683 | -0.35 | 0.7240 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_winner_is_female_2024_2020 | -0.2361 | 0.1460 | -1.62 | 0.1061 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.1066 | 0.1287 | -0.83 | 0.4074 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | 0.0020 | 0.0080 | 0.25 | 0.8037 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0043 | 0.0115 | 0.37 | 0.7091 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0298 | 0.0135 | 2.20 | 0.0278 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0320 | 0.0246 | -1.30 | 0.1924 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0689 | 0.0851 | -0.81 | 0.4183 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0910 | 0.0566 | 1.61 | 0.1080 | 71.60 | 2571 | 1563 |
| adversarial | subsample_open_seat | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0056 | 0.0528 | -0.11 | 0.9157 | 71.60 | 2571 | 1563 |
| adversarial | subsample_contested_seat | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0207 | 0.0232 | -0.89 | 0.3725 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0527 | 0.0476 | 1.11 | 0.2688 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0320 | 0.0287 | 1.12 | 0.2642 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1667 | 0.1062 | 1.57 | 0.1167 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0152 | 0.0211 | -0.72 | 0.4696 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.1051 | 0.0477 | -2.20 | 0.0278 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0699 | 0.0446 | -1.57 | 0.1173 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0004 | 0.0422 | 0.01 | 0.9929 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | 0.0488 | 0.0516 | 0.95 | 0.3439 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0062 | 0.0515 | 0.12 | 0.9042 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0686 | 0.0649 | -1.06 | 0.2903 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0814 | 0.0771 | 1.06 | 0.2916 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0100 | 0.0057 | -1.74 | 0.0821 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0082 | 0.0063 | 1.30 | 0.1953 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0028 | 0.0046 | 0.60 | 0.5455 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0211 | 0.0130 | -1.63 | 0.1036 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | entry | delta_share_first_time_candidates_2024_2020 | 0.0395 | 0.0459 | 0.86 | 0.3896 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0338 | 0.0317 | -1.07 | 0.2868 | 170.03 | 2989 | 1756 |
| adversarial | subsample_contested_seat | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0097 | 0.0263 | 0.37 | 0.7137 | 170.03 | 2989 | 1756 |
| adversarial | robustness_topic_shares | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.1980 | 0.3593 | -0.55 | 0.5818 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.1256 | 0.4329 | 0.29 | 0.7718 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | secondary | delta_winner_vote_share_2024_2020 | -0.0724 | 0.2325 | -0.31 | 0.7556 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | secondary | delta_winner_majority_2024_2020 | -1.3230 | 2.1385 | -0.62 | 0.5363 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | secondary | delta_others_vote_share_2024_2020 | 0.2948 | 0.4552 | 0.65 | 0.5173 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | 0.4380 | 0.6775 | 0.65 | 0.5181 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_female_vote_share_2024_2020 | 0.1311 | 0.4482 | 0.29 | 0.7699 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0015 | 0.5175 | 0.00 | 0.9977 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | 0.1704 | 0.4673 | 0.36 | 0.7154 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.1279 | 0.4717 | 0.27 | 0.7863 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_winner_is_female_2024_2020 | 0.6837 | 1.0314 | 0.66 | 0.5076 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.7061 | 1.2181 | 0.58 | 0.5622 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0711 | 0.1194 | -0.60 | 0.5516 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0387 | 0.0679 | 0.57 | 0.5687 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0094 | 0.0255 | 0.37 | 0.7123 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.1157 | 0.1964 | -0.59 | 0.5560 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | entry | delta_share_first_time_candidates_2024_2020 | 0.1350 | 0.4461 | 0.30 | 0.7622 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.1026 | 0.2686 | 0.38 | 0.7025 | 6.50 | 2824 | 1093 |
| adversarial | robustness_topic_shares | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.1669 | 0.3422 | -0.49 | 0.6258 | 6.50 | 2824 | 1093 |
| adversarial | robustness_broader_lawsuits | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0307 | 0.0217 | -1.42 | 0.1572 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0619 | 0.0431 | 1.44 | 0.1508 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0312 | 0.0251 | 1.25 | 0.2132 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1398 | 0.0903 | 1.55 | 0.1218 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0048 | 0.0186 | -0.26 | 0.7983 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0664 | 0.0393 | -1.69 | 0.0917 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0929 | 0.0479 | -1.94 | 0.0524 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0394 | 0.0420 | -0.94 | 0.3482 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0095 | 0.0499 | -0.19 | 0.8484 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0096 | 0.0490 | 0.20 | 0.8443 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_winner_is_female_2024_2020 | -0.1229 | 0.0632 | -1.94 | 0.0521 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0016 | 0.0733 | -0.02 | 0.9823 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0063 | 0.0048 | -1.33 | 0.1848 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0073 | 0.0059 | 1.23 | 0.2197 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0126 | 0.0053 | 2.36 | 0.0184 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0263 | 0.0127 | -2.07 | 0.0381 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0114 | 0.0433 | -0.26 | 0.7928 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0066 | 0.0261 | 0.25 | 0.8019 | 238.94 | 5560 | 2187 |
| adversarial | robustness_broader_lawsuits | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0045 | 0.0254 | 0.18 | 0.8610 | 238.94 | 5560 | 2187 |
