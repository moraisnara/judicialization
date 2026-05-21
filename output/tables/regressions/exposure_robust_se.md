# Exposure-Robust SE — BHJ (2024) / AKM (2019)

Adversarial IV (administrative/procedural excluded at build stage), baseline_state_fe.
K = 215 topics | HHI = 0.3356 | K_eff (Rotemberg) = 2.98
First-stage F = 19.6 -> tF critical value (Lee et al. 2022) = 2.18

**Caveat:** BHJ exposure-robust asymptotics require K_eff >> 1.
Here K_eff = 2.98 (Rotemberg-weight HHI = 0.336).
These SEs should be treated as a sensitivity bound, not a replacement
for the conventional municipality-clustered SE.

## SE Comparison by Outcome

| Outcome | tau_2SLS | SE_conv | SE_BHJ | SE_AKM | SE_BHJ/SE_conv | tF_cv | CI95_tF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| winner_majority | 0.1398 | 0.0903 | 2.0623 | 2.0683 | 22.83 | 2.18 | [-0.0573, 0.3370] |
| margin_top1_top2 | 0.0619 | 0.0431 | 0.7873 | 0.7896 | 18.27 | 2.18 | [-0.0321, 0.1560] |
| winner_vote_share | 0.0312 | 0.0251 | 0.5463 | 0.5479 | 21.78 | 2.18 | [-0.0235, 0.0860] |
| blank_rate | 0.0126 | 0.0053 | 0.0552 | 0.0554 | 10.37 | 2.18 | [0.0009, 0.0242] |

## Notes
- **SE_conv**: clustered by principal electoral zone (fixest output).
- **SE_BHJ**: BHJ exposure-robust SE = sqrt(sum_k (alpha_k * (tau_k - tau_2SLS))^2) / sum_k alpha_k^2.
  Valid asymptotically when K_eff -> ∞; here K_eff = 2.98.
- **SE_AKM**: SE_BHJ * sqrt(K/(K-1)) — Adao, Kolesar & Morales (2019) finite-K correction.
- **tF_cv**: Lee et al. (2022) critical value; CIs use tF_cv instead of 1.96.
- The BHJ SE uses residuals from the *shift-level* regression: residual_k = alpha_k * (tau_k - tau_2SLS).
  A large SE_BHJ/SE_conv ratio suggests the Bartik estimate is driven by a few shocks
  (consistent with K_eff = 2.98).