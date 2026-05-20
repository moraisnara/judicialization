# Overidentification Tests and LIML — GPS (2020) Section V.C

Using adversarial-only instrument (no-RRC, no-DRAP), K=29 topic components.
Estimation sample: N=4034 municipalities. State FE + 7 baseline controls.

## Sargan-Hansen J Test (2SLS overidentified with all K=29 shares)

K-1=28 over-identifying restrictions. Null = all shares are valid instruments.
Under GPS (share exogeneity), J test should NOT reject.

| Outcome | 2SLS coef | SE | J stat | df | p(J) |
| --- | --- | --- | --- | --- | --- |
| delta_runnerup_vote_share_2024_2020 | -0.0005 | 0.0108 | 21.22 | 28 | 0.816 |
| delta_margin_top1_top2_2024_2020 | 0.0090 | 0.0218 | 24.70 | 28 | 0.644 |
| delta_winner_vote_share_2024_2020 | 0.0085 | 0.0129 | 30.52 | 28 | 0.339 |
| delta_winner_majority_2024_2020 | 0.0963 | 0.0421 | 29.57 | 28 | 0.384 |

## LIML vs 2SLS Comparison

LIML (k-class estimator) reduces many-instrument bias. Large LIML-2SLS gap
signals bias; small gap supports 2SLS reliability.

| Outcome | k_LIML | LIML coef | SE | 2SLS(JI) coef | SE | Diff |
| --- | --- | --- | --- | --- | --- | --- |
| delta_runnerup_vote_share_2024_2020 | 1.000 | -0.0005 | 0.0109 | -0.0143 | 0.0285 | 0.0139 |
| delta_margin_top1_top2_2024_2020 | 1.000 | 0.0090 | 0.0212 | 0.0640 | 0.0569 | -0.0550 |
| delta_winner_vote_share_2024_2020 | 1.000 | 0.0085 | 0.0126 | 0.0497 | 0.0343 | -0.0412 |
| delta_winner_majority_2024_2020 | 1.000 | 0.0963 | 0.0424 | 0.1513 | 0.1122 | -0.0550 |

## Notes
- **J test**: Sargan-Hansen statistic from fixest::fitstat(..., 'sargan').
  Rejection at 5% means some shares predict residuals -> share endogeneity concern.
- **LIML**: k-class estimator; k_LIML = smallest eigenvalue of B^{-1}A.
  2SLS(JI) = just-identified 2SLS using the Bartik aggregate as single instrument.
  k_LIML = 1 -> LIML = 2SLS; k_LIML > 1 -> LIML more robust to many-instrument bias.
- SE are conventional (homoskedastic), not clustered; use as comparison only.
