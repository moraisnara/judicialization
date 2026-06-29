# Vote Outcomes Setup

This build adds municipality-level vote outcomes by office on top of the
first-instance shift-share design.

## Outcome Families

- winner and runner-up vote shares
- victory margin
- top-two concentration
- candidate-vote HHI and effective number of candidates
- party-vote HHI and effective number of parties
- vote shares for female, nonwhite, and highly educated candidates
- vote shares for new candidates and incumbents in 2024
- vote-weighted (intensive-margin) career categories: first-time,
  career (3+ priors), prior-winner, serial-challenger, cross-cycle returner

Each categorical trait now has BOTH an extensive-margin share (fraction of
candidates, in candidate_experience_panel.csv / office_candidate_outcomes_panel.csv)
and an intensive-margin `*_vote_share` (fraction of votes) here. career and
cross-cycle vote shares are left-censored before 2024 (no 2016 baseline).

## Years and the 2016 baseline

Outcomes are built for 2016, 2020 and 2024 with identical definitions,
separately by office (executive = PREFEITO, legislative = VEREADOR).
2016 is a pre-treatment outcome baseline only: lawsuits (the treatment)
exist only for 2020/2024, and 2012 vote microdata are unavailable. The
design files therefore carry `*_2016` levels (lagged controls) and
`pretrend_*_2020_2016` trends (placebo). Renewal/incumbency outcomes are
2020-relative and are NOT produced for 2016.

- municipality-office-year rows in vote panel: 33,368
- election cycles: [2016, 2020, 2024]