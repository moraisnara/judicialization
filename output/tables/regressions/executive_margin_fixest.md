# Executive Margin Analysis — fixest 2SLS (R)

Benchmark: Ash, Morelli & Vannoni (2025, JPE) — `ivreghdfe` → `feols()` in fixest.
Formula: `y ~ controls | FE | Δlog(lawsuits) ~ Bartik_IV`.
SE clustered by principal electoral zone.

## Specifications
1. **baseline_state_fe** — 7 baseline controls + state FE, all municipalities
2. **baseline_state_fe_sz** — same, single-zone municipalities only
3. **robustness_full_controls** — 14 controls + state FE
4. **robustness_microregion_fe** — 7 baseline controls + microregion FE (~558 cells)
5. **subsample_le200k** — baseline + state FE, ≤200k registered voters (single-round regime, Art. 29-II CF/88)
6. **subsample_gt200k** — baseline + state FE, >200k registered voters (second-round eligible)

**Note:** `incumbent_ran_2024` is an outcome variable, never a control.

## First Stage

| spec | coef | se | t | p | first_stage_F | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | 1.4495 | 0.2137 | 6.78 | 0.0000 | 46.00 | 5491 | 2179 |
| baseline_state_fe_sz | 1.4709 | 0.2168 | 6.78 | 0.0000 | 46.02 | 5303 | 2042 |
| robustness_full_controls | 1.4555 | 0.2143 | 6.79 | 0.0000 | 46.13 | 5491 | 2179 |
| robustness_microregion_fe | 1.5596 | 0.2193 | 7.11 | 0.0000 | 50.59 | 5491 | 2179 |
| subsample_le200k | 1.4971 | 0.2188 | 6.84 | 0.0000 | 46.83 | 5271 | 2011 |
| subsample_gt200k | 1.0842 | 0.8371 | 1.30 | 0.1966 | 1.68 |  220 |  220 |

## IV Results

| spec | family | outcome | coef | se | t | p | ivf | nobs | n_clusters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | primary | delta_runnerup_vote_share_2024_2020 | -0.0151 | 0.0176 | -0.86 | 0.3884 | 311.64 | 5491 | 2179 |
| baseline_state_fe | primary | delta_margin_top1_top2_2024_2020 | 0.0538 | 0.0356 | 1.51 | 0.1310 | 311.64 | 5491 | 2179 |
| baseline_state_fe | secondary | delta_winner_vote_share_2024_2020 | 0.0387 | 0.0212 | 1.82 | 0.0686 | 311.64 | 5491 | 2179 |
| baseline_state_fe | voter_behavior | delta_turnout_rate_2024_2020 | -0.0034 | 0.0043 | -0.78 | 0.4351 | 311.64 | 5491 | 2179 |
| baseline_state_fe | voter_behavior | delta_null_share_2024_2020 | 0.0018 | 0.0046 | 0.38 | 0.7018 | 311.64 | 5491 | 2179 |
| baseline_state_fe | voter_behavior | delta_blank_share_2024_2020 | 0.0053 | 0.0034 | 1.57 | 0.1177 | 311.64 | 5491 | 2179 |
| baseline_state_fe_sz | primary | delta_runnerup_vote_share_2024_2020 | -0.0156 | 0.0183 | -0.85 | 0.3944 | 306.19 | 5303 | 2042 |
| baseline_state_fe_sz | primary | delta_margin_top1_top2_2024_2020 | 0.0521 | 0.0370 | 1.41 | 0.1593 | 306.19 | 5303 | 2042 |
| baseline_state_fe_sz | secondary | delta_winner_vote_share_2024_2020 | 0.0365 | 0.0219 | 1.66 | 0.0962 | 306.19 | 5303 | 2042 |
| baseline_state_fe_sz | voter_behavior | delta_turnout_rate_2024_2020 | -0.0019 | 0.0045 | -0.42 | 0.6750 | 306.19 | 5303 | 2042 |
| baseline_state_fe_sz | voter_behavior | delta_null_share_2024_2020 | 0.0018 | 0.0049 | 0.37 | 0.7132 | 306.19 | 5303 | 2042 |
| baseline_state_fe_sz | voter_behavior | delta_blank_share_2024_2020 | 0.0059 | 0.0035 | 1.65 | 0.0982 | 306.19 | 5303 | 2042 |
| robustness_full_controls | primary | delta_runnerup_vote_share_2024_2020 | -0.0136 | 0.0173 | -0.78 | 0.4330 | 314.85 | 5491 | 2179 |
| robustness_full_controls | primary | delta_margin_top1_top2_2024_2020 | 0.0531 | 0.0353 | 1.50 | 0.1331 | 314.85 | 5491 | 2179 |
| robustness_full_controls | secondary | delta_winner_vote_share_2024_2020 | 0.0395 | 0.0212 | 1.86 | 0.0624 | 314.85 | 5491 | 2179 |
| robustness_full_controls | voter_behavior | delta_turnout_rate_2024_2020 | 0.0006 | 0.0042 | 0.14 | 0.8878 | 314.85 | 5491 | 2179 |
| robustness_full_controls | voter_behavior | delta_null_share_2024_2020 | 0.0031 | 0.0036 | 0.86 | 0.3888 | 314.85 | 5491 | 2179 |
| robustness_full_controls | voter_behavior | delta_blank_share_2024_2020 | 0.0054 | 0.0032 | 1.71 | 0.0873 | 314.85 | 5491 | 2179 |
| robustness_microregion_fe | primary | delta_runnerup_vote_share_2024_2020 | -0.0272 | 0.0173 | -1.58 | 0.1151 | 315.14 | 5491 | 2179 |
| robustness_microregion_fe | primary | delta_margin_top1_top2_2024_2020 | 0.0648 | 0.0342 | 1.89 | 0.0584 | 315.14 | 5491 | 2179 |
| robustness_microregion_fe | secondary | delta_winner_vote_share_2024_2020 | 0.0376 | 0.0202 | 1.86 | 0.0633 | 315.14 | 5491 | 2179 |
| robustness_microregion_fe | voter_behavior | delta_turnout_rate_2024_2020 | -0.0041 | 0.0039 | -1.05 | 0.2952 | 315.14 | 5491 | 2179 |
| robustness_microregion_fe | voter_behavior | delta_null_share_2024_2020 | 0.0020 | 0.0047 | 0.42 | 0.6716 | 315.14 | 5491 | 2179 |
| robustness_microregion_fe | voter_behavior | delta_blank_share_2024_2020 | 0.0076 | 0.0032 | 2.37 | 0.0178 | 315.14 | 5491 | 2179 |
| subsample_le200k | primary | delta_runnerup_vote_share_2024_2020 | -0.0148 | 0.0179 | -0.82 | 0.4097 | 314.00 | 5271 | 2011 |
| subsample_le200k | primary | delta_margin_top1_top2_2024_2020 | 0.0509 | 0.0363 | 1.40 | 0.1605 | 314.00 | 5271 | 2011 |
| subsample_le200k | secondary | delta_winner_vote_share_2024_2020 | 0.0361 | 0.0215 | 1.68 | 0.0933 | 314.00 | 5271 | 2011 |
| subsample_le200k | voter_behavior | delta_turnout_rate_2024_2020 | -0.0011 | 0.0044 | -0.24 | 0.8074 | 314.00 | 5271 | 2011 |
| subsample_le200k | voter_behavior | delta_null_share_2024_2020 | 0.0021 | 0.0048 | 0.44 | 0.6568 | 314.00 | 5271 | 2011 |
| subsample_le200k | voter_behavior | delta_blank_share_2024_2020 | 0.0055 | 0.0035 | 1.57 | 0.1156 | 314.00 | 5271 | 2011 |
| subsample_gt200k | primary | delta_runnerup_vote_share_2024_2020 | -0.0418 | 0.0828 | -0.50 | 0.6145 | 7.86 |  220 |  220 |
| subsample_gt200k | primary | delta_margin_top1_top2_2024_2020 | 0.0973 | 0.1576 | 0.62 | 0.5379 | 7.86 |  220 |  220 |
| subsample_gt200k | secondary | delta_winner_vote_share_2024_2020 | 0.0555 | 0.0927 | 0.60 | 0.5502 | 7.86 |  220 |  220 |
| subsample_gt200k | voter_behavior | delta_turnout_rate_2024_2020 | -0.0360 | 0.0249 | -1.45 | 0.1494 | 7.86 |  220 |  220 |
| subsample_gt200k | voter_behavior | delta_null_share_2024_2020 | 0.0112 | 0.0232 | 0.48 | 0.6314 | 7.86 |  220 |  220 |
| subsample_gt200k | voter_behavior | delta_blank_share_2024_2020 | 0.0086 | 0.0115 | 0.75 | 0.4528 | 7.86 |  220 |  220 |
