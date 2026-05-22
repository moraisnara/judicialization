# Family-Split IV Analysis — fixest 2SLS

Each family IV = sum of bartik_component restricted to topics in that family.
Each family IV instruments its family-specific endogenous (delta_log1p_{family}_2024_2020).
Formula: `y ~ controls | state FE | delta_log1p_{family} ~ bartik_iv_{family}`.
SE clustered by principal electoral zone.

## First Stage by Family

| family | endogenous | coef_fs | se_fs | f_stat | nobs |
| --- | --- | --- | --- | --- | --- |
| abuse_misuse_office | delta_log1p_abuse_misuse_office_2024_2020 | -2.54 | 0.91 | 7.83 | 3311 |
| campaign_conduct | delta_log1p_campaign_conduct_2024_2020 | 1.61 | 0.27 | 35.97 | 3937 |
| eligibility_ballot_access | delta_log1p_eligibility_ballot_access_2024_2020 | -0.20 | 0.07 | 8.37 | 1772 |
| information_environment | delta_log1p_information_environment_2024_2020 | 2.29 | 0.52 | 19.69 | 3861 |

## IV Results by Family x Outcome (family-specific endogenous)

| family | outcome | coef | se | t | p | ivf | nobs | n_clusters | first_stage_F | tF_cv | ci95_low_tF | ci95_high_tF | reject_tF_5pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abuse_misuse_office | delta_runnerup_vote_share_2024_2020 | 0.0395 | 0.0278 | 1.42 | 0.1556 | 37.83 | 3311 | 1304 |  7.830106 | 3.249076 | -0.05084180 | 0.12987234 | FALSE |
| abuse_misuse_office | delta_margin_top1_top2_2024_2020 | -0.0862 | 0.0676 | -1.27 | 0.2028 | 37.83 | 3311 | 1304 |  7.830106 | 3.249076 | -0.30585740 | 0.13352336 | FALSE |
| abuse_misuse_office | delta_winner_vote_share_2024_2020 | -0.0467 | 0.0454 | -1.03 | 0.3039 | 37.83 | 3311 | 1304 |  7.830106 | 3.249076 | -0.19401468 | 0.10071118 | FALSE |
| abuse_misuse_office | delta_winner_majority_2024_2020 | -0.0818 | 0.1167 | -0.70 | 0.4835 | 37.83 | 3311 | 1304 |  7.830106 | 3.249076 | -0.46099906 | 0.29739682 | FALSE |
| abuse_misuse_office | delta_log1p_n_candidates_with_votes_2024_2020 | 0.0066 | 0.0375 | 0.17 | 0.8612 | 37.83 | 3311 | 1304 |  7.830106 | 3.249076 | -0.11534847 | 0.12846775 | FALSE |
| campaign_conduct | delta_runnerup_vote_share_2024_2020 | -0.0066 | 0.0110 | -0.61 | 0.5449 | 148.03 | 3937 | 1557 | 35.973616 | 1.960000 | -0.02813553 | 0.01485287 | FALSE |
| campaign_conduct | delta_margin_top1_top2_2024_2020 | 0.0183 | 0.0238 | 0.77 | 0.4416 | 148.03 | 3937 | 1557 | 35.973616 | 1.960000 | -0.02833843 | 0.06498414 | FALSE |
| campaign_conduct | delta_winner_vote_share_2024_2020 | 0.0117 | 0.0152 | 0.77 | 0.4409 | 148.03 | 3937 | 1557 | 35.973616 | 1.960000 | -0.01802228 | 0.04138533 | FALSE |
| campaign_conduct | delta_winner_majority_2024_2020 | -0.0343 | 0.0426 | -0.80 | 0.4214 | 148.03 | 3937 | 1557 | 35.973616 | 1.960000 | -0.11775009 | 0.04923063 | FALSE |
| campaign_conduct | delta_log1p_n_candidates_with_votes_2024_2020 | -0.0042 | 0.0202 | -0.21 | 0.8361 | 148.03 | 3937 | 1557 | 35.973616 | 1.960000 | -0.04386398 | 0.03548876 | FALSE |
| eligibility_ballot_access | delta_runnerup_vote_share_2024_2020 | 0.0313 | 0.0846 | 0.37 | 0.7116 | 1.28 | 1772 |  701 |  8.373618 | 3.139013 | -0.23421975 | 0.29678884 | FALSE |
| eligibility_ballot_access | delta_margin_top1_top2_2024_2020 | -0.0642 | 0.1470 | -0.44 | 0.6626 | 1.28 | 1772 |  701 |  8.373618 | 3.139013 | -0.52557066 | 0.39724122 | FALSE |
| eligibility_ballot_access | delta_winner_vote_share_2024_2020 | -0.0329 | 0.0638 | -0.52 | 0.6063 | 1.28 | 1772 |  701 |  8.373618 | 3.139013 | -0.23303157 | 0.16727122 | FALSE |
| eligibility_ballot_access | delta_winner_majority_2024_2020 | 0.2891 | 0.1491 | 1.94 | 0.0529 | 1.28 | 1772 |  701 |  8.373618 | 3.139013 | -0.17895805 | 0.75714394 | FALSE |
| eligibility_ballot_access | delta_log1p_n_candidates_with_votes_2024_2020 | -0.1086 | 0.0726 | -1.50 | 0.1349 | 1.28 | 1772 |  701 |  8.373618 | 3.139013 | -0.33636243 | 0.11915613 | FALSE |
| information_environment | delta_runnerup_vote_share_2024_2020 | -0.0095 | 0.0145 | -0.66 | 0.5109 | 72.01 | 3861 | 1529 | 19.690415 | 2.179288 | -0.04099763 | 0.02198965 | FALSE |
| information_environment | delta_margin_top1_top2_2024_2020 | 0.0335 | 0.0291 | 1.15 | 0.2499 | 72.01 | 3861 | 1529 | 19.690415 | 2.179288 | -0.02994254 | 0.09697108 | FALSE |
| information_environment | delta_winner_vote_share_2024_2020 | 0.0240 | 0.0181 | 1.33 | 0.1841 | 72.01 | 3861 | 1529 | 19.690415 | 2.179288 | -0.01536538 | 0.06338594 | FALSE |
| information_environment | delta_winner_majority_2024_2020 | 0.0777 | 0.0642 | 1.21 | 0.2268 | 72.01 | 3861 | 1529 | 19.690415 | 2.179288 | -0.06232531 | 0.21770898 | FALSE |
| information_environment | delta_log1p_n_candidates_with_votes_2024_2020 | 0.0127 | 0.0294 | 0.43 | 0.6653 | 72.01 | 3861 | 1529 | 19.690415 | 2.179288 | -0.05130212 | 0.07672503 | FALSE |
