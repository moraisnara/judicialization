# Executive Margin Analysis — Baseline and Robustness Specifications

## Specifications
1. **baseline_state_fe** — 7 controls (Census 2010 × 3, margin_2016, 2020: log_valid_votes, margin, n_candidates) + state FE, all municipalities
2. **baseline_state_fe_sz** — same, single-zone municipalities only (exact clustering)
3. **robustness_full_controls** — 14 controls (baseline + composition, party/coalition, voter behavior baseline, candidate pool) + state FE
4. **robustness_microregion_fe** — baseline controls + microregion FE (~558 cells)
5. **subsample_le200k** — baseline controls + state FE, municipalities with ≤200k registered voters (single-round regime, Art. 29-II CF/88)
6. **subsample_gt200k** — baseline controls + state FE, municipalities with >200k registered voters (second-round eligible)

**Note:** `incumbent_ran_2024` is an outcome variable, never a control.

## First Stage

| spec | coef | se | t | p | first_stage_F | nobs | n_clusters | n_controls | fe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | 1.4495 | 0.2137 | 6.7823 | 0.0000 | 45.9999 | 5491 | 2179 | 7 | SG_UF |
| baseline_state_fe_sz | 1.4709 | 0.2168 | 6.7840 | 0.0000 | 46.0233 | 5303 | 2042 | 7 | SG_UF |
| robustness_full_controls | 1.4555 | 0.2143 | 6.7916 | 0.0000 | 46.1260 | 5491 | 2179 | 17 | SG_UF |
| robustness_microregion_fe | 1.5596 | 0.2193 | 7.1128 | 0.0000 | 50.5925 | 5491 | 2179 | 7 | code_micro |
| subsample_le200k | 1.4971 | 0.2188 | 6.8429 | 0.0000 | 46.8257 | 5271 | 2011 | 7 | SG_UF |
| subsample_gt200k | 1.0842 | 0.8467 | 1.2805 | 0.2004 | 1.6396 | 220 | 220 | 7 | SG_UF |

## IV Results

| spec | family | outcome | coef | se | t | p | nobs | n_clusters | fe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_state_fe | primary | delta_runnerup_vote_share_2024_2020 | -0.0151 | 0.0175 | -0.8656 | 0.3867 | 5491 | 2179 | SG_UF |
| baseline_state_fe | primary | delta_margin_top1_top2_2024_2020 | 0.0538 | 0.0355 | 1.5157 | 0.1296 | 5491 | 2179 | SG_UF |
| baseline_state_fe | secondary | delta_winner_vote_share_2024_2020 | 0.0387 | 0.0212 | 1.8279 | 0.0676 | 5491 | 2179 | SG_UF |
| baseline_state_fe | voter_behavior | delta_turnout_rate_2024_2020 | -0.0034 | 0.0043 | -0.7831 | 0.4336 | 5491 | 2179 | SG_UF |
| baseline_state_fe | voter_behavior | delta_null_share_2024_2020 | 0.0018 | 0.0046 | 0.3842 | 0.7008 | 5491 | 2179 | SG_UF |
| baseline_state_fe | voter_behavior | delta_blank_share_2024_2020 | 0.0053 | 0.0033 | 1.5703 | 0.1164 | 5491 | 2179 | SG_UF |
| baseline_state_fe_sz | primary | delta_runnerup_vote_share_2024_2020 | -0.0156 | 0.0183 | -0.8547 | 0.3927 | 5303 | 2042 | SG_UF |
| baseline_state_fe_sz | primary | delta_margin_top1_top2_2024_2020 | 0.0521 | 0.0369 | 1.4126 | 0.1578 | 5303 | 2042 | SG_UF |
| baseline_state_fe_sz | secondary | delta_winner_vote_share_2024_2020 | 0.0365 | 0.0219 | 1.6700 | 0.0949 | 5303 | 2042 | SG_UF |
| baseline_state_fe_sz | voter_behavior | delta_turnout_rate_2024_2020 | -0.0019 | 0.0045 | -0.4207 | 0.6740 | 5303 | 2042 | SG_UF |
| baseline_state_fe_sz | voter_behavior | delta_null_share_2024_2020 | 0.0018 | 0.0049 | 0.3689 | 0.7122 | 5303 | 2042 | SG_UF |
| baseline_state_fe_sz | voter_behavior | delta_blank_share_2024_2020 | 0.0059 | 0.0035 | 1.6598 | 0.0970 | 5303 | 2042 | SG_UF |
| robustness_full_controls | primary | delta_runnerup_vote_share_2024_2020 | -0.0136 | 0.0172 | -0.7874 | 0.4311 | 5491 | 2179 | SG_UF |
| robustness_full_controls | primary | delta_margin_top1_top2_2024_2020 | 0.0531 | 0.0352 | 1.5086 | 0.1314 | 5491 | 2179 | SG_UF |
| robustness_full_controls | secondary | delta_winner_vote_share_2024_2020 | 0.0395 | 0.0211 | 1.8723 | 0.0612 | 5491 | 2179 | SG_UF |
| robustness_full_controls | voter_behavior | delta_turnout_rate_2024_2020 | 0.0006 | 0.0042 | 0.1417 | 0.8873 | 5491 | 2179 | SG_UF |
| robustness_full_controls | voter_behavior | delta_null_share_2024_2020 | 0.0031 | 0.0035 | 0.8655 | 0.3867 | 5491 | 2179 | SG_UF |
| robustness_full_controls | voter_behavior | delta_blank_share_2024_2020 | 0.0054 | 0.0032 | 1.7175 | 0.0859 | 5491 | 2179 | SG_UF |
| robustness_microregion_fe | primary | delta_runnerup_vote_share_2024_2020 | -0.0272 | 0.0164 | -1.6645 | 0.0960 | 5491 | 2179 | code_micro |
| robustness_microregion_fe | primary | delta_margin_top1_top2_2024_2020 | 0.0648 | 0.0324 | 1.9996 | 0.0455 | 5491 | 2179 | code_micro |
| robustness_microregion_fe | secondary | delta_winner_vote_share_2024_2020 | 0.0376 | 0.0192 | 1.9620 | 0.0498 | 5491 | 2179 | code_micro |
| robustness_microregion_fe | voter_behavior | delta_turnout_rate_2024_2020 | -0.0041 | 0.0037 | -1.1054 | 0.2690 | 5491 | 2179 | code_micro |
| robustness_microregion_fe | voter_behavior | delta_null_share_2024_2020 | 0.0020 | 0.0045 | 0.4477 | 0.6544 | 5491 | 2179 | code_micro |
| robustness_microregion_fe | voter_behavior | delta_blank_share_2024_2020 | 0.0076 | 0.0030 | 2.5035 | 0.0123 | 5491 | 2179 | code_micro |
| subsample_le200k | primary | delta_runnerup_vote_share_2024_2020 | -0.0148 | 0.0179 | -0.8274 | 0.4080 | 5271 | 2011 | SG_UF |
| subsample_le200k | primary | delta_margin_top1_top2_2024_2020 | 0.0509 | 0.0361 | 1.4086 | 0.1590 | 5271 | 2011 | SG_UF |
| subsample_le200k | secondary | delta_winner_vote_share_2024_2020 | 0.0361 | 0.0214 | 1.6845 | 0.0921 | 5271 | 2011 | SG_UF |
| subsample_le200k | voter_behavior | delta_turnout_rate_2024_2020 | -0.0011 | 0.0044 | -0.2446 | 0.8068 | 5271 | 2011 | SG_UF |
| subsample_le200k | voter_behavior | delta_null_share_2024_2020 | 0.0021 | 0.0048 | 0.4460 | 0.6556 | 5271 | 2011 | SG_UF |
| subsample_le200k | voter_behavior | delta_blank_share_2024_2020 | 0.0055 | 0.0035 | 1.5797 | 0.1142 | 5271 | 2011 | SG_UF |
| subsample_gt200k | primary | delta_runnerup_vote_share_2024_2020 | -0.0418 | 0.0771 | -0.5423 | 0.5876 | 220 | 220 | SG_UF |
| subsample_gt200k | primary | delta_margin_top1_top2_2024_2020 | 0.0973 | 0.1466 | 0.6633 | 0.5071 | 220 | 220 | SG_UF |
| subsample_gt200k | secondary | delta_winner_vote_share_2024_2020 | 0.0555 | 0.0862 | 0.6433 | 0.5200 | 220 | 220 | SG_UF |
| subsample_gt200k | voter_behavior | delta_turnout_rate_2024_2020 | -0.0360 | 0.0231 | -1.5556 | 0.1198 | 220 | 220 | SG_UF |
| subsample_gt200k | voter_behavior | delta_null_share_2024_2020 | 0.0112 | 0.0216 | 0.5166 | 0.6054 | 220 | 220 | SG_UF |
| subsample_gt200k | voter_behavior | delta_blank_share_2024_2020 | 0.0086 | 0.0107 | 0.8087 | 0.4187 | 220 | 220 | SG_UF |