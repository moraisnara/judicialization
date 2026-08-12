# SPECIFICATION — TSE shift-share design (branch `tse-shift-share`)

**Status:** working specification, written 2026-07-04 from the from-scratch redesign
(2026-07-03 onward). This is the *specified* design — the estimation harness must be
built to THIS document, not inherited from the committed `main` mold
(`02_iv_main.R`, ANCOVA-on-2016). The committed propaganda-Bartik/ANCOVA design on
`main` is the preserved fallback, never broken.

Legend: **[DECIDED]** settled on paper before touching data · **[BUILT]** constructed
and checked this session · **[OPEN]** genuine choice still to make (flagged inline).

---

## 1. Research question & frame

Does the **judicialization of electoral competition** — the judiciary becoming an active
arena of the contest — change how **voters** and **candidates** behave? Organize outcomes
into a **voter-side bundle** and a **candidate-side bundle** (AMV headline-vs-mechanism
structure). Mechanism (Layer 2): adversarial litigation as "noise" that disrupts the local
arena; the sign is read off the outcomes, not assumed.

Template: Ash, Morelli & Vannoni, *More Laws, More Growth?* (JPE 2025) shift-share / Bartik.

## 2. Unit, panel, estimator [DECIDED]

- **Unit:** municipality × municipal cycle. Treated cycles **2020 and 2024**.
- **Estimator:** **first difference** (municipality FE across the two cycles + cycle FE).
  With only 2020↔2024 this collapses to a single cross-section of within-muni changes:

  ```
  ΔY_m  =  β · ΔW_m  +  γ' X_m  +  ε_m           (headline: no geographic FE)
  ΔW_m  instrumented by  Z_m                      (2SLS)
  ```

  Honest label: "panel-flavored first-difference shift-share," NOT AMV's long TWFE.
- **NOT** the committed ANCOVA-on-2016-baseline. ANCOVA is a `main`-design object.
- **Baseline period — TEST BOTH 2016 and 2020 [DECIDED 2026-07-04]:** run the outcome
  difference from a **2020** baseline (ΔY = Y_2024 − Y_2020, treatment-window-aligned) AND
  from a **2016** baseline (ΔY = Y_2024 − Y_2016, longer pre-window, guards against a
  covid-contaminated 2020 baseline). The instrument and ΔW stay pinned to 2020→2024
  (muni-level 2016 litigation shares are not available — only 2020 SIG). Data constraint:
  2016 levels exist for null/blank rate and effective-N candidates, but NOT for
  first-time-candidate entry (2016 requires 2012 history → left-censored) → the 2016-baseline
  test runs on the vote-rate and competition outcomes only.
- 2012/2016 municipal outcomes = pre-trend / placebo spine (if 2016 litigation baseline
  is secured; 2012 would promote 2016 to a third treated cycle → real TWFE + event study).
- **Geographic FE:** headline is national (leave-state-out shifts carry identification);
  **UF fixed effects = robustness** (the "UF×cycle" bracket), not the headline. [DECIDED]

## 3. Instrument — K\*-selected, leaf-granular, first-instance-flow Bartik [BUILT]

```
Z_m  =  Σ_{k ∈ K*}  s_{m,k,2020}  ·  g_k^(−uf)

  s_{m,k,2020}  = muni m's baseline (2020) share of topic k within the kept universe
  g_k^(−uf)     = leave-own-state-out log-growth of first-instance flows on topic k,
                  g_k = log1p(flow_{k,2024}^{−uf}) − log1p(flow_{k,2020}^{−uf})
```

- **Shift = ordinary first-instance adversarial lawsuit FLOWS**, at **leaf granularity**
  (`CD_ASSUNTO_PRINCIPAL`, no roll-up that cancels opposite-signed subtopics).
  NOT the TSE normative-corpus decision flow — that route FAILED the linchpin
  (denominator/coverage artifact, no genuine differential shift) and is a documented
  tested-and-rejected version. The normative agenda survives only as the topic **selector**.
- **K\* selector** = normatively-salient, non-procedural, non-sparse, non-covid leaf
  subjects. Operationalized in `code/04_analysis/11_lawsuit_topic_selection.py` →
  `output/tables/descriptives/lawsuit_topic_selection_worksheet.csv`
  (`keep_suggestion` starter = in a normative family & not sparse (<50) & not procedural
  & not covid-suspect). Per-subtopic keep/drop/roll-up decisions are Nara's to finalize;
  the worksheet is the ledger. [OPEN — final K\* list]
  - **What is feeding results RIGHT NOW:** the automated `keep_suggestion` **starter**
    (120 keep-suggested leaves → 89 present in the SIG muni panel). We agreed the selection
    *framework* (normative salience) but have NOT yet done the manual per-subtopic pass. The
    first correct headline runs on this starter; manual K\* refinement is a later robustness
    layer, not a blocker.
- **Leave-own-origin-out:** drop from g_k any flow originating in muni m / state S
  (appeal-chain reverse causality). Implemented leave-state-out.
- **Identification bet = the SHIFTS (BHJ), not the shares.** The baseline share is "about
  the local market" (endogenous) → shares enter as **controls** (§6) so only the
  share×shift interaction identifies.
- **Muni resolution:** SIG município-resolved export ("Município de origem"), 2020+2024,
  no zona→muni many-to-many duplication. Built by reusing the debugged
  `build_sig_municipal_panel` floor.
- **Mandatory-filing exclusion:** drop RRC / DRAP / prestação de contas **by class**
  (≈48.5% of all lawsuits) before anything else. Keep only the adversarial universe.

Built characterization: 89 leaf subjects, K_eff ≈ 18.6, ~76% of munis nonzero; the
propaganda split into differentially-moving sub-leaves is load-bearing (corr with a
collapsed-propaganda variant only 0.62–0.68; splitting doubles the first-stage F,
114.7 vs 43.8).

## 4. Endogenous variable W [DECIDED / to REBUILD on K\*]

- **W = log(1 + adversarial first-instance count)**, adversarial-only (mandatory dropped),
  **restricted to the same K\* topic universe as the instrument** — Z and W share one topic
  set. ΔW = W_2024 − W_2020. Counts already built: `kstar_endog_counts.csv`
  (`c20_base`, `c24_base`; `_imp` variants for the impugnação test).
- The comparison run earlier used the committed all-adversarial `delta_log1p_competition_
  lawsuits` — that was the wrong (non-K\*) endogenous and is superseded here.
- **Zero-handling — run BOTH log1p and Poisson [DECIDED 2026-07-04: try both, compare]:**
  `log1p` puts every silent muni at the same floor (0), which manufactures the
  extensive-margin/convergence spike. Run (i) `log1p` first difference; (ii) **Poisson (PPML)
  ANCOVA** on the count (`c24 ~ Z + f(c20) + controls`), which handles zeros natively and
  matches the count nature of W. Do this under **both baseline periods** (§2). Compare — if
  they agree, the zero-handling is not driving the result; if they diverge, that divergence
  is itself a finding to report.

## 5. Sample [BUILT — DECIDED this session]

- **Population floor: municipalities with pop_2010 ≥ 5,000.**
  Rationale (tested, not assumed): the ~24% of munis with zero adversarial litigation are
  *structurally* zero — they differ from the rest **only in size** (pop ratio 0.18; income,
  competitiveness, turnout identical), too small/thin a candidate pool to generate any
  contestation. Dropping them is not selection-on-outcome bias: with population-decile FE
  (size held fully flexible) the first stage is unchanged (F 114→114, coef identical), so
  identification is not "big-vs-small." The floor **strengthens** the first stage
  (F 115→155 at ≥5,000) and keeps 666 zeros among *peer* munis, preserving the
  extensive-margin contrast between comparably-sized towns.
- **Do NOT** instead restrict to "covered only" (drop all zeros): that deletes the
  identifying variation (first stage collapses to F ≈ 7). Population floor ≠ covered-only.
- Threshold robustness: report the outcome across floors (0 / 2k / 5k / 10k / 20k). [DECIDED]

## 6. Controls — baseline shares (BHJ) + predetermined covariates [OPEN — choose form]

The BHJ bet requires conditioning out the **baseline exposure shares** so only the shift
identifies. We cannot enter all ~89 K\* topic shares. **DECIDED 2026-07-04: report ALL THREE
as a share-control ladder** so the headline's dependence on the control set is visible:

- **(a)** baseline total exposure only — log of the muni's 2020 K\* litigation level
  (one control).
- **(b)** (a) **+ the propaganda baseline share** — propaganda is ~80% of volume and
  dominates Z, so its share is the first-order confounder to purge.
- **(c)** (a) + the top-N largest baseline share components (N ≈ 3–5).

Plus a **predetermined covariate block** (2010 Census, strictly pre-period, no Lord's-paradox
2020 levels): `log_pop_2010, urban_share_2010, log_income_pc_2010, higher_educ_share_2010`.
NOT `margin_2016` or 2020 competition levels in the headline (those bias the FD via
regression-to-the-mean; keep for a labelled robustness bracket only).

## 7. Outcomes — two-tier [DECIDED; confirm exact variables]

**Tier 1 — headlines**
- Voter side: **null / blank vote rate** (`delta_null_rate`, `delta_blank_rate`) — the
  purest arena-degradation trace of the "noise" frame.
- Candidate side: **electoral competition / entry** — **effective N candidates**
  (`delta_effective_n_candidates_vote`) and/or **first-time-candidate entry**
  (`delta_share_first_time_candidates`) — barrier-vs-leveling, sign-agnostic.

**Tier 2 — mechanism / robustness (explicitly NOT headline)**
- Facultative turnout; all compositional outcomes (female / nonwhite share, incumbency,
  winner traits). Representation/female share was the OLD headline — **demoted** here.

**CONFIRMED 2026-07-04:** Tier-1 variables as listed (null/blank rate; effective-N and
first-time entry). Note the 2016-baseline test covers null/blank + effective-N only (entry
has no 2016 level).

## 8. Inference [DECIDED]

- Cluster at the state level (`cluster_id`).
- **BHJ/AKM exposure-robust SEs** as the shift-share-appropriate standard (the binding
  caveat from the audit).
- **AR / wild-cluster (AR-WCR)** for weak-IV-robust inference on the headline.
- Significance stars `*** / ** / *` at 1/5/10% (house convention).

## 9. Tested and rejected (preserved versions) [BUILT]

- **Normative-corpus-as-shift** (Shifter V): NO-GO — denominator/coverage artifact, no
  differential shift. Selector role only.
- **TPU depth-2 roll-up:** over-aggregates; opposite-signed subtopics cancel → spurious
  one-shock. Use leaf granularity.
- **Add-back of Impugnação ao Registro (AIRC, subj 11616):** genuinely adversarial but
  *declining* (−43%) and dispersed; added to BOTH Z and W it weakens the full first stage
  (F 115→66) and kills the continuous covered-only margin (F 7.2→0.1). **Rejected.**
- **Covered-only sample** (drop all zeros): first stage collapses (F ≈ 7). Rejected in
  favor of the population floor.

## 10. Reproducibility rules [DECIDED]

- Branch `tse-shift-share`; `main` design untouched and reproducible.
- New instrument writes to **NEW-named files** (new entity tokens); never overwrite a shared
  clean-data file in place. Shared floor (downloads, outcome panels, crosswalks) reused
  byte-identical.
- Every slide/paper number has a saved script; regressions in R/fixest only (Python for
  construction + descriptives).

---

### Decisions log (resolved 2026-07-04)
1. **§6** share controls — **do all three (a/b/c)** as a ladder. ✔
2. **§7** Tier-1 outcomes — **confirmed** (null/blank, effective-N, first-time entry). ✔
3. **§2** baseline period — **test both 2016 and 2020**. ✔
4. **§4** Poisson vs log1p — **run both, under both baselines, compare**. ✔
5. **§3** final K\* list — running on the `keep_suggestion` **starter**; manual per-subtopic
   pass deferred to a robustness layer (not a blocker). ✔

Nothing now blocks the first correct headline build.
