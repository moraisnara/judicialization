# Exposure-Robust SE — BHJ (2024) / AKM (2019)

Adversarial-only IV (no-RRC, no-DRAP), baseline_state_fe.
K = 29 topics | HHI = 0.3804 | K_eff (Rotemberg) = 2.63
First-stage F = 10.4 -> tF critical value (Lee et al. 2022) = 2.81

**Caveat:** BHJ exposure-robust asymptotics require K_eff >> 1.
Here K_eff = 2.63 (Rotemberg-weight HHI = 0.380).
These SEs should be treated as a sensitivity bound, not a replacement
for the conventional municipality-clustered SE.

## SE Comparison by Outcome

| Outcome | tau_2SLS | SE_conv | SE_BHJ | SE_AKM | SE_BHJ/SE_conv | tF_cv | CI95_tF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| winner_majority | 0.1126 | 0.0997 | 0.2943 | 0.2995 | 2.95 | 2.81 | [-0.1674, 0.3926] |
| margin_top1_top2 | 0.0569 | 0.0514 | 0.0976 | 0.0993 | 1.90 | 2.81 | [-0.0874, 0.2012] |
| winner_vote_share | 0.0376 | 0.0298 | 0.0717 | 0.0730 | 2.41 | 2.81 | [-0.0461, 0.1212] |
| blank_rate | 0.0039 | 0.0041 | 0.0109 | 0.0111 | 2.67 | 2.81 | [-0.0075, 0.0153] |

## Notes
- **SE_conv**: clustered by principal electoral zone (fixest output).
- **SE_BHJ**: BHJ exposure-robust SE = sqrt(sum_k (alpha_k * (tau_k - tau_2SLS))^2) / sum_k alpha_k^2.
  Valid asymptotically when K_eff -> ∞; here K_eff = 2.63.
- **SE_AKM**: SE_BHJ * sqrt(K/(K-1)) — Adao, Kolesar & Morales (2019) finite-K correction.
- **tF_cv**: Lee et al. (2022) critical value; CIs use tF_cv instead of 1.96.
- The BHJ SE uses residuals from the *shift-level* regression: residual_k = alpha_k * (tau_k - tau_2SLS).
  A large SE_BHJ/SE_conv ratio suggests the Bartik estimate is driven by a few shocks
  (consistent with K_eff = 2.63).