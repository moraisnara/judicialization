# Executive Margin Analysis — fixest 2SLS (R)

Benchmark: Ash, Morelli & Vannoni (2025, JPE) — `ivreghdfe` → `feols()` in fixest.
Formula: `y ~ controls | FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by state (UF); leave-own-state-out shift is constant within state.

## Instrument
- **adversarial** : bartik_iv_2020_2024 / delta_log1p_competition_lawsuits_2024_2020
  (adversarial class/subject filter applied at build stage in 02_bartik_inputs.py)

## Specifications (headline = ANCOVA on the 2016 pre-window baseline)
Baseline (V3) controls: 2010 Census structure (log pop, urban share, log income p.c., higher-ed share),
log valid-vote volume (2020), 2016 victory margin, PLUS each outcome's own 2016 level where one exists
(per-outcome lagged DV). No 2020 levels of competition outcomes (avoids Lord's-paradox bias).

1. **baseline** — ANCOVA-2016: per-outcome 2016 level as free lag + common controls + state FE
2. **single_zone** — baseline, single-zone municipalities only
3. **extended_controls** — baseline + extended 2020 covariates + state FE
4. **open_seat** — baseline, open-seat municipalities (2020 winner term-limited)
5. **contested_seat** — baseline, contested-seat municipalities
6. **broader_treatment** — baseline + log1p_lawsuits_no_rrc_2020 as additional control
7. **fd** — appendix robustness: pure first difference (delta_Y ~ D, persistence pinned to 1)
8. **ancova_2020lvl** — legacy V1 stance check: delta outcome + 2020 competition levels as controls

## First Stage

| variant | spec | coef | se | t | p | first_stage_F | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline | 0.2130 | 0.0402 | 5.30 | 0.0000 | 28.06 | 5560 | 26 |
| adversarial | single_zone | 0.2150 | 0.0416 | 5.17 | 0.0000 | 26.68 | 5371 | 26 |
| adversarial | extended_controls | 0.2072 | 0.0391 | 5.30 | 0.0000 | 28.05 | 5560 | 26 |
| adversarial | open_seat | 0.1772 | 0.0561 | 3.16 | 0.0041 | 9.96 | 1994 | 26 |
| adversarial | contested_seat | 0.2373 | 0.0391 | 6.07 | 0.0000 | 36.81 | 3566 | 26 |
| adversarial | broader_treatment | 0.2130 | 0.0402 | 5.30 | 0.0000 | 28.06 | 5560 | 26 |
| adversarial | fd | 0.2130 | 0.0402 | 5.30 | 0.0000 | 28.06 | 5560 | 26 |
| adversarial | ancova_2020lvl | 0.2068 | 0.0388 | 5.33 | 0.0000 | 28.38 | 5560 | 26 |

## IV Results

| variant | spec | estimator | family | outcome | coef | se | t | p | ivf | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | baseline | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0458 | 0.0148 | -3.10 | 0.0047 | 70.33 | 5560 | 26 |
| adversarial | baseline | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0924 | 0.0280 | 3.30 | 0.0029 | 71.87 | 5560 | 26 |
| adversarial | baseline | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0480 | 0.0149 | 3.22 | 0.0035 | 71.24 | 5560 | 26 |
| adversarial | baseline | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0357 | 0.0362 | 0.98 | 0.3343 | 70.72 | 5560 | 26 |
| adversarial | baseline | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0053 | 0.0088 | -0.61 | 0.5478 | 70.11 | 5560 | 26 |
| adversarial | baseline | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0457 | 0.0265 | -1.72 | 0.0972 | 69.39 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0447 | 0.0287 | -1.55 | 0.1328 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_female_share_2024_2020 | -0.0405 | 0.0366 | -1.11 | 0.2793 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0304 | 0.0387 | -0.79 | 0.4386 | 71.67 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0269 | 0.0366 | -0.74 | 0.4687 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0386 | 0.0422 | 0.91 | 0.3692 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0396 | 0.0445 | -0.89 | 0.3819 | 71.98 | 5560 | 26 |
| adversarial | baseline | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0017 | 0.0497 | 0.03 | 0.9725 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0058 | 0.0035 | -1.63 | 0.1161 | 73.25 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0054 | 0.0023 | 2.36 | 0.0265 | 71.59 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0058 | 0.0017 | 3.38 | 0.0024 | 71.33 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0138 | 0.0058 | -2.38 | 0.0254 | 71.72 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | 0.0001 | 0.0009 | 0.16 | 0.8758 | 71.77 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0005 | 0.0007 | 0.74 | 0.4653 | 71.84 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0059 | 0.0042 | -1.42 | 0.1688 | 72.32 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0034 | 0.0087 | -0.39 | 0.7027 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | 0.0005 | 0.0020 | 0.26 | 0.8002 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0036 | 0.0050 | -0.73 | 0.4745 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0065 | 0.0028 | 2.29 | 0.0310 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0121 | 0.0121 | -1.00 | 0.3282 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0101 | 0.0069 | 1.46 | 0.1567 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0002 | 0.0017 | 0.10 | 0.9185 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0134 | 0.0583 | -0.23 | 0.8205 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0058 | 0.0451 | -0.13 | 0.8992 | 71.76 | 5560 | 26 |
| adversarial | baseline | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0240 | 0.0317 | -0.76 | 0.4546 | 71.76 | 5560 | 26 |
| adversarial | single_zone | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0453 | 0.0146 | -3.09 | 0.0048 | 70.58 | 5371 | 26 |
| adversarial | single_zone | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0935 | 0.0278 | 3.36 | 0.0025 | 71.86 | 5371 | 26 |
| adversarial | single_zone | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0494 | 0.0150 | 3.29 | 0.0029 | 71.38 | 5371 | 26 |
| adversarial | single_zone | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0413 | 0.0377 | 1.09 | 0.2847 | 70.97 | 5371 | 26 |
| adversarial | single_zone | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0068 | 0.0092 | -0.74 | 0.4654 | 70.40 | 5371 | 26 |
| adversarial | single_zone | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0450 | 0.0264 | -1.71 | 0.0998 | 69.19 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0449 | 0.0291 | -1.54 | 0.1352 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_female_share_2024_2020 | -0.0400 | 0.0371 | -1.08 | 0.2906 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0303 | 0.0374 | -0.81 | 0.4255 | 71.69 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0301 | 0.0386 | -0.78 | 0.4439 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0414 | 0.0436 | 0.95 | 0.3509 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0392 | 0.0443 | -0.88 | 0.3848 | 71.92 | 5371 | 26 |
| adversarial | single_zone | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0065 | 0.0507 | -0.13 | 0.8985 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0056 | 0.0034 | -1.67 | 0.1074 | 72.87 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0051 | 0.0023 | 2.27 | 0.0323 | 71.53 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0053 | 0.0017 | 3.10 | 0.0048 | 71.22 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0134 | 0.0055 | -2.42 | 0.0231 | 71.40 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | -0.0002 | 0.0009 | -0.25 | 0.8014 | 71.73 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0004 | 0.0007 | 0.68 | 0.5012 | 71.74 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0055 | 0.0040 | -1.39 | 0.1772 | 72.22 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0018 | 0.0083 | -0.22 | 0.8265 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | 0.0011 | 0.0021 | 0.53 | 0.5999 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0025 | 0.0048 | -0.51 | 0.6115 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0068 | 0.0029 | 2.37 | 0.0257 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0108 | 0.0118 | -0.92 | 0.3663 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0093 | 0.0068 | 1.38 | 0.1810 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0002 | 0.0017 | 0.14 | 0.8860 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0172 | 0.0600 | -0.29 | 0.7768 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0053 | 0.0448 | -0.12 | 0.9061 | 71.77 | 5371 | 26 |
| adversarial | single_zone | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0206 | 0.0323 | -0.64 | 0.5293 | 71.77 | 5371 | 26 |
| adversarial | extended_controls | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0457 | 0.0155 | -2.95 | 0.0068 | 68.82 | 5560 | 26 |
| adversarial | extended_controls | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0957 | 0.0292 | 3.28 | 0.0030 | 69.09 | 5560 | 26 |
| adversarial | extended_controls | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0503 | 0.0149 | 3.38 | 0.0024 | 69.36 | 5560 | 26 |
| adversarial | extended_controls | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0424 | 0.0370 | 1.15 | 0.2625 | 68.83 | 5560 | 26 |
| adversarial | extended_controls | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0067 | 0.0085 | -0.79 | 0.4394 | 69.31 | 5560 | 26 |
| adversarial | extended_controls | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0502 | 0.0271 | -1.85 | 0.0756 | 68.30 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0488 | 0.0290 | -1.69 | 0.1042 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_female_share_2024_2020 | -0.0442 | 0.0301 | -1.47 | 0.1546 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0156 | 0.0437 | -0.36 | 0.7247 | 68.77 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0340 | 0.0378 | -0.90 | 0.3772 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0442 | 0.0438 | 1.01 | 0.3229 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0380 | 0.0476 | -0.80 | 0.4320 | 69.21 | 5560 | 26 |
| adversarial | extended_controls | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0070 | 0.0548 | -0.13 | 0.8994 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0019 | 0.0025 | -0.77 | 0.4505 | 67.64 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0049 | 0.0023 | 2.10 | 0.0458 | 68.75 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0055 | 0.0018 | 3.03 | 0.0056 | 68.22 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0121 | 0.0049 | -2.48 | 0.0203 | 67.28 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | -0.0002 | 0.0009 | -0.25 | 0.8067 | 68.94 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0005 | 0.0006 | 0.72 | 0.4777 | 69.18 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0030 | 0.0034 | -0.88 | 0.3860 | 67.39 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0039 | 0.0067 | -0.58 | 0.5697 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | -0.0001 | 0.0017 | -0.08 | 0.9370 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0037 | 0.0039 | -0.93 | 0.3594 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0054 | 0.0032 | 1.69 | 0.1038 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0119 | 0.0111 | -1.08 | 0.2926 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0090 | 0.0061 | 1.48 | 0.1509 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | -0.0000 | 0.0017 | -0.02 | 0.9831 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | entry | delta_share_first_time_candidates_2024_2020 | 0.0014 | 0.0344 | 0.04 | 0.9668 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0099 | 0.0441 | -0.23 | 0.8232 | 68.98 | 5560 | 26 |
| adversarial | extended_controls | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0333 | 0.0305 | -1.09 | 0.2865 | 68.98 | 5560 | 26 |
| adversarial | open_seat | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0139 | 0.0225 | -0.62 | 0.5404 | 20.87 | 1994 | 26 |
| adversarial | open_seat | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0459 | 0.0400 | 1.15 | 0.2622 | 20.97 | 1994 | 26 |
| adversarial | open_seat | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0321 | 0.0217 | 1.48 | 0.1505 | 20.93 | 1994 | 26 |
| adversarial | open_seat | 2sls | secondary | delta_winner_majority_2024_2020 | 0.1146 | 0.0794 | 1.44 | 0.1617 | 21.22 | 1994 | 26 |
| adversarial | open_seat | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0234 | 0.0195 | -1.20 | 0.2414 | 20.89 | 1994 | 26 |
| adversarial | open_seat | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.1062 | 0.0516 | -2.06 | 0.0501 | 19.86 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0342 | 0.0657 | -0.52 | 0.6076 | 20.98 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_female_share_2024_2020 | -0.0726 | 0.0613 | -1.18 | 0.2476 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0247 | 0.0692 | 0.36 | 0.7241 | 20.89 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | 0.0372 | 0.0520 | 0.71 | 0.4813 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | -0.0030 | 0.0025 | -1.20 | 0.2408 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_winner_is_female_2024_2020 | 0.0026 | 0.0901 | 0.03 | 0.9771 | 21.02 | 1994 | 26 |
| adversarial | open_seat | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0564 | 0.0685 | 0.82 | 0.4181 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | 0.0108 | 0.0061 | 1.76 | 0.0910 | 20.82 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0037 | 0.0038 | 0.99 | 0.3318 | 20.29 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0030 | 0.0018 | 1.63 | 0.1166 | 20.90 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | 0.0060 | 0.0103 | 0.58 | 0.5651 | 19.89 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | -0.0006 | 0.0013 | -0.47 | 0.6391 | 21.06 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0001 | 0.0009 | 0.16 | 0.8773 | 20.96 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | 0.0119 | 0.0077 | 1.54 | 0.1351 | 20.65 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | 0.0008 | 0.0167 | 0.05 | 0.9609 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | 0.0042 | 0.0055 | 0.77 | 0.4512 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0007 | 0.0105 | -0.07 | 0.9441 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0072 | 0.0056 | 1.28 | 0.2125 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0027 | 0.0202 | -0.13 | 0.8960 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0079 | 0.0121 | 0.66 | 0.5184 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0017 | 0.0032 | 0.54 | 0.5953 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0002 | 0.0784 | -0.00 | 0.9980 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.1067 | 0.0826 | -1.29 | 0.2080 | 20.99 | 1994 | 26 |
| adversarial | open_seat | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | 0.0715 | 0.0481 | 1.49 | 0.1499 | 20.99 | 1994 | 26 |
| adversarial | contested_seat | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0618 | 0.0199 | -3.11 | 0.0046 | 51.50 | 3566 | 26 |
| adversarial | contested_seat | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.1142 | 0.0374 | 3.06 | 0.0053 | 53.29 | 3566 | 26 |
| adversarial | contested_seat | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0542 | 0.0196 | 2.76 | 0.0106 | 52.96 | 3566 | 26 |
| adversarial | contested_seat | 2sls | secondary | delta_winner_majority_2024_2020 | -0.0060 | 0.0470 | -0.13 | 0.8995 | 51.77 | 3566 | 26 |
| adversarial | contested_seat | 2sls | secondary | delta_others_vote_share_2024_2020 | 0.0041 | 0.0103 | 0.40 | 0.6944 | 51.29 | 3566 | 26 |
| adversarial | contested_seat | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0162 | 0.0289 | -0.56 | 0.5812 | 51.86 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0496 | 0.0405 | -1.22 | 0.2322 | 53.04 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_female_share_2024_2020 | -0.0159 | 0.0401 | -0.40 | 0.6945 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0587 | 0.0398 | -1.48 | 0.1524 | 53.39 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0747 | 0.0406 | -1.84 | 0.0778 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0732 | 0.0448 | 1.64 | 0.1145 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0644 | 0.0548 | -1.17 | 0.2511 | 53.13 | 3566 | 26 |
| adversarial | contested_seat | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0505 | 0.0547 | -0.92 | 0.3648 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0138 | 0.0045 | -3.08 | 0.0049 | 54.59 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0057 | 0.0026 | 2.22 | 0.0359 | 53.03 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0073 | 0.0024 | 3.07 | 0.0051 | 53.00 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0231 | 0.0073 | -3.18 | 0.0039 | 53.71 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | 0.0005 | 0.0010 | 0.47 | 0.6405 | 53.06 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0007 | 0.0006 | 1.04 | 0.3081 | 52.84 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0148 | 0.0051 | -2.93 | 0.0071 | 53.75 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0059 | 0.0087 | -0.68 | 0.5049 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | -0.0015 | 0.0020 | -0.78 | 0.4442 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0052 | 0.0047 | -1.10 | 0.2802 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0067 | 0.0034 | 1.97 | 0.0604 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0171 | 0.0130 | -1.32 | 0.1983 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0119 | 0.0065 | 1.82 | 0.0808 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | -0.0004 | 0.0021 | -0.21 | 0.8345 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0426 | 0.0596 | -0.71 | 0.4818 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | entry | delta_share_serial_challenger_2024_2020 | 0.0453 | 0.0416 | 1.09 | 0.2862 | 53.08 | 3566 | 26 |
| adversarial | contested_seat | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0810 | 0.0468 | -1.73 | 0.0958 | 53.08 | 3566 | 26 |
| adversarial | broader_treatment | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0458 | 0.0148 | -3.10 | 0.0047 | 70.33 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0924 | 0.0280 | 3.30 | 0.0029 | 71.87 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0480 | 0.0149 | 3.22 | 0.0035 | 71.24 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0357 | 0.0362 | 0.98 | 0.3343 | 70.72 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0053 | 0.0088 | -0.61 | 0.5478 | 70.11 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0457 | 0.0265 | -1.72 | 0.0972 | 69.39 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0447 | 0.0287 | -1.55 | 0.1328 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_female_share_2024_2020 | -0.0405 | 0.0366 | -1.11 | 0.2793 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | -0.0304 | 0.0387 | -0.79 | 0.4386 | 71.67 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0269 | 0.0366 | -0.74 | 0.4687 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0386 | 0.0422 | 0.91 | 0.3692 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0396 | 0.0445 | -0.89 | 0.3819 | 71.98 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0017 | 0.0497 | 0.03 | 0.9725 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0058 | 0.0035 | -1.63 | 0.1161 | 73.25 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_null_rate_2024_2020 | 0.0054 | 0.0023 | 2.36 | 0.0265 | 71.59 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0058 | 0.0017 | 3.38 | 0.0024 | 71.33 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0138 | 0.0058 | -2.38 | 0.0254 | 71.72 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | 0.0001 | 0.0009 | 0.16 | 0.8758 | 71.77 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | 0.0005 | 0.0007 | 0.74 | 0.4653 | 71.84 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0059 | 0.0042 | -1.42 | 0.1688 | 72.32 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0034 | 0.0087 | -0.39 | 0.7027 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | 0.0005 | 0.0020 | 0.26 | 0.8002 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0036 | 0.0050 | -0.73 | 0.4745 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0065 | 0.0028 | 2.29 | 0.0310 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0121 | 0.0121 | -1.00 | 0.3282 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0101 | 0.0069 | 1.46 | 0.1567 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0002 | 0.0017 | 0.10 | 0.9185 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0134 | 0.0583 | -0.23 | 0.8205 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0058 | 0.0451 | -0.13 | 0.8992 | 71.76 | 5560 | 26 |
| adversarial | broader_treatment | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0240 | 0.0317 | -0.76 | 0.4546 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0082 | 0.0132 | -0.62 | 0.5393 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0282 | 0.0272 | 1.04 | 0.3097 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0199 | 0.0176 | 1.13 | 0.2685 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0647 | 0.0585 | 1.11 | 0.2786 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0157 | 0.0156 | -1.01 | 0.3232 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0632 | 0.0397 | -1.59 | 0.1241 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0454 | 0.0373 | -1.22 | 0.2347 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_female_share_2024_2020 | -0.0405 | 0.0366 | -1.11 | 0.2793 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0203 | 0.0601 | 0.34 | 0.7384 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0269 | 0.0366 | -0.74 | 0.4687 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0386 | 0.0422 | 0.91 | 0.3692 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0252 | 0.0476 | -0.53 | 0.6016 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | 0.0017 | 0.0497 | 0.03 | 0.9725 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0010 | 0.0030 | -0.33 | 0.7439 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_null_rate_2024_2020 | -0.0017 | 0.0024 | -0.72 | 0.4764 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0003 | 0.0025 | 0.12 | 0.9033 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | 0.0004 | 0.0048 | 0.09 | 0.9270 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | -0.0007 | 0.0011 | -0.65 | 0.5234 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | -0.0002 | 0.0003 | -0.69 | 0.4955 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0002 | 0.0032 | -0.06 | 0.9540 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0034 | 0.0087 | -0.39 | 0.7027 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | 0.0005 | 0.0020 | 0.26 | 0.8002 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0036 | 0.0050 | -0.73 | 0.4745 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0065 | 0.0028 | 2.29 | 0.0310 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0121 | 0.0121 | -1.00 | 0.3282 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0101 | 0.0069 | 1.46 | 0.1567 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0002 | 0.0017 | 0.10 | 0.9185 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0134 | 0.0583 | -0.23 | 0.8205 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0058 | 0.0451 | -0.13 | 0.8992 | 71.76 | 5560 | 26 |
| adversarial | fd | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0240 | 0.0317 | -0.76 | 0.4546 | 71.76 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | primary | delta_runnerup_vote_share_2024_2020 | -0.0394 | 0.0149 | -2.65 | 0.0138 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | primary | delta_margin_top1_top2_2024_2020 | 0.0882 | 0.0282 | 3.13 | 0.0044 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | secondary | delta_winner_vote_share_2024_2020 | 0.0488 | 0.0163 | 2.99 | 0.0062 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | secondary | delta_winner_majority_2024_2020 | 0.0847 | 0.0622 | 1.36 | 0.1853 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | secondary | delta_others_vote_share_2024_2020 | -0.0116 | 0.0140 | -0.83 | 0.4124 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | secondary | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0489 | 0.0286 | -1.71 | 0.0997 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_female_vote_share_2024_2020 | -0.0489 | 0.0383 | -1.27 | 0.2143 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_female_share_2024_2020 | -0.0435 | 0.0375 | -1.16 | 0.2564 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_nonwhite_vote_share_2024_2020 | 0.0192 | 0.0623 | 0.31 | 0.7609 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_new_candidate_vote_share_2024_2020 | -0.0512 | 0.0375 | -1.37 | 0.1837 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_incumbent_candidate_vote_share_2024_2020 | 0.0529 | 0.0448 | 1.18 | 0.2489 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_winner_is_female_2024_2020 | -0.0289 | 0.0483 | -0.60 | 0.5560 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | composition | delta_winner_is_new_vs_2020_2024_2020 | -0.0272 | 0.0539 | -0.50 | 0.6181 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_turnout_rate_2024_2020 | -0.0015 | 0.0030 | -0.50 | 0.6180 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_null_rate_2024_2020 | -0.0000 | 0.0027 | -0.00 | 0.9990 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_blank_rate_2024_2020 | 0.0017 | 0.0022 | 0.77 | 0.4490 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_valid_vote_rate_2024_2020 | -0.0032 | 0.0045 | -0.70 | 0.4888 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_null_rate_vereador_2024_2020 | -0.0007 | 0.0011 | -0.59 | 0.5611 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_blank_rate_vereador_2024_2020 | -0.0001 | 0.0003 | -0.27 | 0.7893 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_valid_vote_rate_vereador_2024_2020 | -0.0007 | 0.0032 | -0.23 | 0.8181 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_facultative_turnout_2024_2020 | -0.0042 | 0.0089 | -0.47 | 0.6394 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_compulsory_turnout_2024_2020 | -0.0000 | 0.0019 | -0.02 | 0.9875 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_low_ed_turnout_2024_2020 | -0.0039 | 0.0051 | -0.78 | 0.4424 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_high_ed_turnout_2024_2020 | 0.0056 | 0.0029 | 1.93 | 0.0652 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_analfabeto_turnout_2024_2020 | -0.0128 | 0.0124 | -1.03 | 0.3134 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_education_turnout_gap_2024_2020 | 0.0095 | 0.0071 | 1.34 | 0.1935 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | voter_behavior | delta_sex_turnout_gap_2024_2020 | 0.0002 | 0.0017 | 0.09 | 0.9262 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | entry | delta_share_first_time_candidates_2024_2020 | -0.0168 | 0.0551 | -0.30 | 0.7629 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | entry | delta_share_serial_challenger_2024_2020 | -0.0022 | 0.0459 | -0.05 | 0.9618 | 68.27 | 5560 | 26 |
| adversarial | ancova_2020lvl | 2sls | entry | delta_share_cross_cycle_returner_2024_2020 | -0.0294 | 0.0342 | -0.86 | 0.3988 | 68.27 | 5560 | 26 |
