# Executive Margin Analysis — fixest 2SLS (R)

Benchmark: Ash, Morelli & Vannoni (2025, JPE) — `ivreghdfe` → `feols()` in fixest.
Formula: `y ~ controls | FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## Variants
- **all_topics**  : bartik_iv_2020_2024 / delta_log1p_competition_lawsuits_2024_2020
- **no_rrc_drap** : bartik_iv_no_rrc_drap / delta_log1p_lawsuits_no_rrc_drap_2024_2020

## Specifications
1. **baseline_state_fe** — 7 baseline controls + state FE, all municipalities
2. **baseline_state_fe_sz** — same, single-zone municipalities only
3. **robustness_full_controls** — 14 controls + state FE
4. **robustness_microregion_fe** — 7 baseline controls + microregion FE (~558 cells)
5. **subsample_le200k** — baseline + state FE, ≤200k registered voters
6. **subsample_gt200k** — baseline + state FE, >200k registered voters

## First Stage

| variant | spec | coef | se | t | p | first_stage_F | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | 1.7918 | 0.4049 | 4.43 | 0.0000 | 19.58 | 5560 | 2187 |
| adversarial | baseline_state_fe_sz | 1.8008 | 0.4217 | 4.27 | 0.0000 | 18.24 | 5371 | 2049 |
| adversarial | robustness_full_controls | 1.7993 | 0.4056 | 4.44 | 0.0000 | 19.68 | 5560 | 2187 |
| adversarial | subsample_le200k | 1.8693 | 0.4260 | 4.39 | 0.0000 | 19.25 | 5338 | 2017 |

## IV Results

| variant | spec | family | outcome | coef | se | t | p | ivf | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline_state_fe | primary | delta_runnerup_vote_share_2024_2020 | -0.0307 | 0.0217 | -1.42 | 0.1572 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | primary | delta_margin_top1_top2_2024_2020 | 0.0619 | 0.0431 | 1.44 | 0.1508 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | secondary | delta_winner_vote_share_2024_2020 | 0.0312 | 0.0251 | 1.25 | 0.2132 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | secondary | delta_winner_majority_2024_2020 | 0.1398 | 0.0903 | 1.55 | 0.1218 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | secondary | delta_others_vote_share_2024_2020 | -0.0048 | 0.0186 | -0.26 | 0.7983 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0664 | 0.0393 | -1.69 | 0.0917 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_female_vote_share_2024_2020 | -0.0929 | 0.0479 | -1.94 | 0.0524 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_nonwhite_vote_share_2024_2020 | -0.0394 | 0.0420 | -0.94 | 0.3482 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_new_candidate_vote_share_2024_2020 | -0.0095 | 0.0499 | -0.19 | 0.8484 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0096 | 0.0490 | 0.20 | 0.8443 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_winner_is_female_2024_2020 | -0.1229 | 0.0632 | -1.94 | 0.0521 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0016 | 0.0733 | -0.02 | 0.9823 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | voter_behavior | delta_turnout_rate_2024_2020 | -0.0063 | 0.0048 | -1.33 | 0.1848 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | voter_behavior | delta_null_rate_2024_2020 | 0.0073 | 0.0059 | 1.23 | 0.2197 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | voter_behavior | delta_blank_rate_2024_2020 | 0.0126 | 0.0053 | 2.36 | 0.0184 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0263 | 0.0127 | -2.07 | 0.0381 | 238.94 | 5560 | 2187 |
| adversarial | baseline_state_fe_sz | primary | delta_runnerup_vote_share_2024_2020 | -0.0247 | 0.0220 | -1.12 | 0.2629 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | primary | delta_margin_top1_top2_2024_2020 | 0.0533 | 0.0439 | 1.21 | 0.2249 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | secondary | delta_winner_vote_share_2024_2020 | 0.0286 | 0.0257 | 1.11 | 0.2662 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | secondary | delta_winner_majority_2024_2020 | 0.1400 | 0.0932 | 1.50 | 0.1330 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | secondary | delta_others_vote_share_2024_2020 | -0.0069 | 0.0193 | -0.36 | 0.7192 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0561 | 0.0395 | -1.42 | 0.1557 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_female_vote_share_2024_2020 | -0.0890 | 0.0486 | -1.83 | 0.0673 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_nonwhite_vote_share_2024_2020 | -0.0436 | 0.0440 | -0.99 | 0.3214 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_new_candidate_vote_share_2024_2020 | -0.0093 | 0.0521 | -0.18 | 0.8586 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0050 | 0.0505 | 0.10 | 0.9206 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_winner_is_female_2024_2020 | -0.1281 | 0.0659 | -1.94 | 0.0521 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0115 | 0.0766 | -0.15 | 0.8805 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | voter_behavior | delta_turnout_rate_2024_2020 | -0.0051 | 0.0048 | -1.06 | 0.2908 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | voter_behavior | delta_null_rate_2024_2020 | 0.0071 | 0.0063 | 1.13 | 0.2566 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | voter_behavior | delta_blank_rate_2024_2020 | 0.0130 | 0.0056 | 2.30 | 0.0215 | 232.87 | 5371 | 2049 |
| adversarial | baseline_state_fe_sz | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0253 | 0.0132 | -1.92 | 0.0548 | 232.87 | 5371 | 2049 |
| adversarial | robustness_full_controls | primary | delta_runnerup_vote_share_2024_2020 | -0.0274 | 0.0211 | -1.30 | 0.1935 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | primary | delta_margin_top1_top2_2024_2020 | 0.0565 | 0.0421 | 1.34 | 0.1794 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | secondary | delta_winner_vote_share_2024_2020 | 0.0291 | 0.0246 | 1.18 | 0.2369 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | secondary | delta_winner_majority_2024_2020 | 0.1461 | 0.0901 | 1.62 | 0.1049 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | secondary | delta_others_vote_share_2024_2020 | -0.0063 | 0.0183 | -0.34 | 0.7313 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0647 | 0.0384 | -1.69 | 0.0919 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_female_vote_share_2024_2020 | -0.1264 | 0.0490 | -2.58 | 0.0100 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0018 | 0.0367 | 0.05 | 0.9618 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0030 | 0.0498 | -0.06 | 0.9521 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0005 | 0.0475 | 0.01 | 0.9920 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_winner_is_female_2024_2020 | -0.1565 | 0.0640 | -2.44 | 0.0146 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0067 | 0.0723 | 0.09 | 0.9259 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0030 | 0.0040 | -0.73 | 0.4637 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | voter_behavior | delta_null_rate_2024_2020 | 0.0073 | 0.0059 | 1.24 | 0.2157 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | voter_behavior | delta_blank_rate_2024_2020 | 0.0123 | 0.0052 | 2.35 | 0.0188 | 241.19 | 5560 | 2187 |
| adversarial | robustness_full_controls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0226 | 0.0118 | -1.92 | 0.0548 | 241.19 | 5560 | 2187 |
| adversarial | subsample_le200k | primary | delta_runnerup_vote_share_2024_2020 | -0.0247 | 0.0212 | -1.16 | 0.2456 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | primary | delta_margin_top1_top2_2024_2020 | 0.0521 | 0.0423 | 1.23 | 0.2173 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | secondary | delta_winner_vote_share_2024_2020 | 0.0275 | 0.0247 | 1.11 | 0.2661 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | secondary | delta_winner_majority_2024_2020 | 0.1240 | 0.0886 | 1.40 | 0.1618 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | secondary | delta_others_vote_share_2024_2020 | -0.0063 | 0.0185 | -0.34 | 0.7351 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0519 | 0.0378 | -1.37 | 0.1697 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_female_vote_share_2024_2020 | -0.0858 | 0.0466 | -1.84 | 0.0658 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_nonwhite_vote_share_2024_2020 | -0.0466 | 0.0424 | -1.10 | 0.2726 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_new_candidate_vote_share_2024_2020 | -0.0088 | 0.0507 | -0.17 | 0.8618 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0026 | 0.0488 | 0.05 | 0.9579 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_winner_is_female_2024_2020 | -0.1223 | 0.0630 | -1.94 | 0.0525 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0156 | 0.0746 | -0.21 | 0.8344 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | voter_behavior | delta_turnout_rate_2024_2020 | -0.0038 | 0.0045 | -0.84 | 0.4027 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | voter_behavior | delta_null_rate_2024_2020 | 0.0075 | 0.0061 | 1.24 | 0.2158 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | voter_behavior | delta_blank_rate_2024_2020 | 0.0125 | 0.0054 | 2.31 | 0.0210 | 247.49 | 5338 | 2017 |
| adversarial | subsample_le200k | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0239 | 0.0126 | -1.90 | 0.0576 | 247.49 | 5338 | 2017 |
