# Exposure-Robust SE — BHJ (2024) / AKM (2019)

Adversarial IV (administrative/procedural excluded at build stage), baseline.
K = 223 topics | HHI = 0.0988 | K_eff (Rotemberg) = 10.12
First-stage F = 28.1 -> tF critical value (Lee et al. 2022) = 1.96

**Caveat:** BHJ exposure-robust asymptotics require K_eff >> 1.
Here K_eff = 10.12 (Rotemberg-weight HHI = 0.099).
These SEs should be treated as a sensitivity bound, not a replacement
for the conventional municipality-clustered SE.

## SE Comparison by Outcome

| Outcome | tau_2SLS | SE_conv | SE_BHJ | SE_AKM | SE_BHJ/SE_conv | tF_cv | CI95_tF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| winner_majority | 0.0357 | 0.0362 | 0.4696 | 0.4710 | 12.96 | 1.96 | [-0.0353, 0.1067] |
| margin_top1_top2 | 0.0924 | 0.0280 | 0.3955 | 0.3967 | 14.14 | 1.96 | [0.0376, 0.1472] |
| winner_vote_share | 0.0480 | 0.0149 | 0.2329 | 0.2336 | 15.63 | 1.96 | [0.0188, 0.0772] |
| blank_rate | 0.0058 | 0.0017 | 0.0244 | 0.0245 | 14.31 | 1.96 | [0.0024, 0.0091] |

## Notes
- **SE_conv**: clustered by principal electoral zone (fixest output).
- **SE_BHJ**: BHJ exposure-robust SE = sqrt(sum_k (alpha_k * (tau_k - tau_2SLS))^2) / sum_k alpha_k^2.
  Valid asymptotically when K_eff -> ∞; here K_eff = 10.12.
- **SE_AKM**: SE_BHJ * sqrt(K/(K-1)) — Adao, Kolesar & Morales (2019) finite-K correction.
- **tF_cv**: Lee et al. (2022) critical value; CIs use tF_cv instead of 1.96.
- The BHJ SE uses residuals from the *shift-level* regression: residual_k = alpha_k * (tau_k - tau_2SLS).
  A large SE_BHJ/SE_conv ratio suggests the Bartik estimate is driven by a few shocks
  (consistent with K_eff = 10.12).