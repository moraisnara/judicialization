> **⚠️ ARCHIVED / STALE — superseded by `docs/STATE_OF_THE_ART.md` (2026-06-26).**
> This document describes the RETIRED substance-family / connected-component design (with the
> old female-candidate headline). It is kept only as version history. For the current act-based
> 10-family design, the authoritative source is `docs/STATE_OF_THE_ART.md` and `code/spec_config.json`.
> _Reason this file is stale:_ every diagnostic here is for the 7-substance-family `G8rh` `bartik_iv_2020_2024` instrument (K_eff ≈ 3, F ≈ 27, zone-clustered); the live act-based `bartik_iv_act` has K_eff ≈ 6.8, F ≈ 25.5, state-clustered.

# Instrument-construction robustness readout

**Headline instrument:** `bartik_iv_2020_2024` (G8rh), a shift-share built from
**7 substance families** (elig, propaganda, polls, conduct, honor, abuso,
finance). Endogenous: Δlog(1+adversarial competition lawsuits), 2020→2024.
Design: first-difference cross-section, ~5,560 municipalities, state FE,
clustered on the principal electoral zone. Sources below are all current-language
scripts that read the live design.

This memo consolidates five diagnostics. Bottom line up front: **the instrument
is relevant but its identifying power is concentrated in 2–3 families, the
effective number of shocks is small (K_eff ≈ 3), and the single nominally
significant second-stage result (null/non-valid votes) is fragile under
shift-share-appropriate inference.** That fragility is not a flaw to hide — it is
the empirical fact the null-result defense has to be built around.

---

## 1. Why G8rh — version horse-race (`03d_version_first_stage.R`)

Matched first-stage F across taxonomy versions (same sample, N≈5,529):

| Version | #families | First-stage F |
|---|---|---|
| G3 | 3 | 4.1 |
| G6 | 6 | 6.6 |
| G8 | 8 | 7.4 |
| G11 | 11 | 7.8 |
| B10 | 10 | 3.5 |
| G7n | 7 | 17.2 |
| G8rp | 7 | 15.9 |
| **G8rh (chosen)** | **7** | **18.2** |

The "n"/"r" variants (which apply the mandatory-filing exclusion — dropping
RRC/DRAP/contas that every candidate must file) jump from F≈7 to F≈17–18. G8rh is
the strongest. **The first-stage power comes from purging mechanical filings, not
from finer topic granularity.**

## 2. Rotemberg weights (`05_rotemberg_weights.py`)

Concentration of the 2SLS estimate across families (αₖ, outcome-independent):

| Family | αₖ (%) | F_k | cum. % |
|---|---|---|---|
| elig | 46.3 | 40.4 | 46.3 |
| propaganda | 22.3 | 32.3 | 68.6 |
| polls | 16.8 | 13.4 | 85.4 |
| conduct | 10.0 | 11.6 | 95.4 |
| honor | 5.3 | 2.3 | 100.7 |
| abuso | 0.2 | 0.7 | ~100 |
| finance | −0.9 | 0.3 | 100 |

Top 3 families carry **85%** of the weight; elig alone carries **46%**.
Rotemberg HHI = 0.305 → **K_eff ≈ 3.3** effective shocks. honor/abuso/finance are
weak (F_k < 3) and near-zero weight — they ride along but identify almost nothing.

## 3. GPS share-exogeneity balance (`08_gps_balance_tests.py`)

Regressing baseline covariates on each family's local share: shares are **not**
random. elig R²=0.13 (F=25), polls R²=0.17 (F=36), propaganda R²=0.11 (F=21) — all
p<10⁻¹⁵. Identification therefore **cannot** lean on the "many exogenous shares"
(GPS/BHJ-shares) route; it must lean on the **exogeneity of the shocks** (the
common-across-municipalities change in each family's caseload) conditional on
controls + state FE. This is the Borusyak–Hull–Jaravel "exogenous shifts" lane,
and it is the defensible one here given so few effective shocks.

## 4. Leave-one-family-out (`21_leave_one_family_out.R`)

Z₋f = Z_full − bartik_iv_f, re-estimate first stage and the one significant result.

First-stage F when each family is dropped:

| Dropped | F | Δ vs full (18.2) |
|---|---|---|
| (none) | 18.2 | — |
| **elig** | **8.9** | **−9.3 (halves)** |
| propaganda | 14.5 | −3.7 |
| polls | 15.8 | −2.4 |
| conduct | 15.6 | −2.6 |
| honor | 19.7 | +1.5 |
| abuso | 18.1 | ≈0 |
| finance | 19.2 | +1.0 |

Null-vote 2SLS (coef / p / first-F) when each family is dropped:

| Dropped | coef | p | first-F |
|---|---|---|---|
| (none) | −0.0119 | 0.033 | 17.6 |
| elig | −0.0100 | **0.190** | 7.4 |
| propaganda | −0.0131 | 0.045 | 14.3 |
| polls | −0.0097 | 0.104 | 15.5 |
| conduct | −0.0133 | 0.030 | 15.6 |
| honor | −0.0121 | 0.020 | 19.5 |
| abuso | −0.0117 | 0.035 | 17.5 |
| finance | −0.0119 | 0.029 | 18.4 |

**The point estimate is stable** (always −0.010 to −0.013). What moves is
**precision**: dropping elig (the relevance engine) sends F to 7.4 and p to 0.19.
The result is not an artifact of any one family's *signal*, but its *significance*
rests on retaining elig/polls for first-stage strength.

## 5. Exposure-robust inference — BHJ/AKM (`22_exposure_robust_se.R`)

Treating the F=7 families as the inferential units (appropriate when shares are
endogenous and shocks few):

| Outcome | τ̂ | SE_clust | SE_BHJ | SE_AKM | BHJ/clust |
|---|---|---|---|---|---|
| Null share (cast) | −0.0119 | 0.0056 | 0.0096 | 0.0104 | ×1.73 |
| Non-valid (cast) | −0.0168 | 0.0091 | 0.0146 | 0.0157 | ×1.60 |

Exposure-robust SEs are **~1.7× larger**. t_BHJ ≈ −1.24 for null votes → **not
significant** under shift-share-appropriate inference.

**Convergent caveat from tF:** even with the *conventional* cluster SE, the
weak-IV-robust tF critical value at F=17.6 is 2.26, while |t| = 0.0119/0.0056 =
2.13. So the headline result **fails the tF threshold at full instrument
strength** — the naive p=0.033 is measured against 1.96, not the correct 2.26.

---

## Synthesis for the write-up

1. **Relevance is real but concentrated.** F=18.2, but ~85% from 3 families and
   K_eff≈3. Report this openly; it is the binding constraint on inference.
2. **Validity rests on exogenous shocks, not exogenous shares.** Shares fail
   balance; lean explicitly on the BHJ shifts lane + controls + state FE.
3. **The estimate is stable; only its precision is fragile.** Sign and magnitude
   of every second-stage coefficient survive every single-family drop.
4. **The one "significant" result does not survive proper weak-IV / exposure-robust
   inference.** Under tF (full strength) and under BHJ/AKM SEs it is insignificant.

This pushes the paper toward a **precisely-estimated, design-robust null**: across
candidate composition (groups A–D) and voter behaviour, no economically or
statistically reliable effect of adversarial electoral litigation on outcomes,
and the lone marginal signal (null votes) is exactly where weak-instrument
inference tells us to be most cautious. The next section (research discussion)
turns this into the affirmative argument that the null is a finding, not a failure.
