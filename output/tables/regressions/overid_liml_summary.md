# Overidentification Tests and LIML — GPS (2020) Section V.C

Using adversarial instrument (administrative/procedural excluded at build stage).
Estimation sample: N=4002 municipalities. State FE + 7 baseline controls.

## Sargan-Hansen J Test (2SLS overidentified with all K=29 shares)

K=215 topic components; K-1=214 over-identifying restrictions. Null = all shares are valid instruments.
Under GPS (share exogeneity), J test should NOT reject.

| Outcome | 2SLS coef | SE | J stat | df | p(J) |
| --- | --- | --- | --- | --- | --- |
| delta_runnerup_vote_share_2024_2020 | 0.0244 | 0.0138 | 160.72 | 214 | 0.997 |
| delta_margin_top1_top2_2024_2020 | -0.0771 | 0.0334 | 158.60 | 214 | 0.998 |
| delta_winner_vote_share_2024_2020 | -0.0528 | 0.0214 | 169.64 | 214 | 0.989 |
| delta_winner_majority_2024_2020 | -0.1061 | 0.0504 | 193.53 | 214 | 0.839 |

## LIML vs 2SLS Comparison

LIML (k-class estimator) reduces many-instrument bias. Large LIML-2SLS gap
signals bias; small gap supports 2SLS reliability.

| Outcome | k_LIML | LIML coef | SE | 2SLS(JI) coef | SE | Diff |
| --- | --- | --- | --- | --- | --- | --- |
| delta_runnerup_vote_share_2024_2020 | 1.000 | 0.0244 | 0.0117 | -0.0506 | 0.0438 | 0.0749 |
| delta_margin_top1_top2_2024_2020 | 1.000 | -0.0771 | 0.0229 | 0.1705 | 0.0888 | -0.2477 |
| delta_winner_vote_share_2024_2020 | 1.000 | -0.0528 | 0.0136 | 0.1200 | 0.0538 | -0.1728 |
| delta_winner_majority_2024_2020 | 1.000 | -0.1061 | 0.0453 | 0.4146 | 0.1775 | -0.5206 |

## Notes
- **J test**: Sargan-Hansen statistic from fixest::fitstat(..., 'sargan').
  Rejection at 5% means some shares predict residuals -> share endogeneity concern.
- **LIML**: k-class estimator; k_LIML = smallest eigenvalue of B^{-1}A.
  2SLS(JI) = just-identified 2SLS using the Bartik aggregate as single instrument.
  k_LIML = 1 -> LIML = 2SLS; k_LIML > 1 -> LIML more robust to many-instrument bias.
- SE are conventional (homoskedastic), not clustered; use as comparison only.
