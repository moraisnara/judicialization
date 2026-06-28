> **⚠️ ARCHIVED / STALE — superseded by `docs/STATE_OF_THE_ART.md` (2026-06-26).**
> This document describes the RETIRED substance-family / connected-component design (with the
> old female-candidate headline). It is kept only as version history. For the current act-based
> 10-family design, the authoritative source is `docs/STATE_OF_THE_ART.md` and `code/spec_config.json`.
> _Reason this file is stale:_ it promotes the `class_folded` zone-level **connected-component** instrument with the `bartik_iv_2020_2024 = z_ls` alias — both the connected-component unit and that instrument column no longer exist; the live instrument is `bartik_iv_act` on SIG municipality microdata.

# SPECIFICATION.md — Estimation Design Decisions

Canonical record of the econometric choices for the executive (mayoral) and
legislative (council) IV analyses. **If a script disagrees with this file, this
file is right and the script is stale.** Last revised 2026-06-19.

---

## 1. Design

> **✓ INSTRUMENT PROMOTED 2026-06-23.** The instrument is now `class_folded`: shock
> families = all 10 adversarial procedural CLASSES (tiny ones folded), built at the
> zone-level **connected-component** unit after the many-to-many fix. Headline shock
> = `z_ls` (leave-own-state), carried in the column `bartik_iv_2020_2024`; `z_nat`
> (national/share-driven) carried in `bartik_iv_national` as a robustness arm.
> Component F 15.7–17.8 (z_ls), **robust to the leave-state shock** (no longer
> share-only weak-GPS). Built by `code/02_build/instrument/05_promote_class_folded.py`
> and broadcast to municipalities in `01_assemble_design.py`. See
> `code/02_build/instrument/README.md`. §1 below documents the CURRENT design; the
> OLD 14-family national-shock muni instrument is fully replaced.

- **Unit:** municipality (cross-section), with treatment and instrument defined at
  the connected-component ("municipality-zona cluster") unit (2,104 components over
  ~5,560 munis) and broadcast to member municipalities. Outcomes vary by
  municipality; the instrument/treatment vary by component.
- **Structure:** first difference, 2020→2024. `ΔY_m = Y_{m,2024} − Y_{m,2020}`.
  With exactly two periods this is numerically identical to a municipality-FE
  two-period panel, so the state dummies below are equivalent to state×year
  effects in levels.
- **Treatment (endogenous):** `Δlog(1+ℓ_c)`, the 2020→2024 change in adversarial,
  first-instance, pre-election lawsuit counts at the connected component `c`
  (counted once per lawsuit; no zona→muni duplication), assigned to each member
  municipality.
- **Instrument:** single Bartik shift-share `bartik_iv_2020_2024` = z_ls
  = Σ_k s_{c,k,2020} · g^{(−UF)}_{k}, where shares s are the component's 2020
  procedural-class portfolio (`class_folded`, 7 folded families) and g are
  leave-own-state-out log-growth shocks per family. The national-shock variant
  z_nat (`bartik_iv_national`) is the share-identified robustness arm.
- **Identifying assumption.** `class_folded`'s first stage survives the
  leave-own-state (genuine-shock, BHJ-licensed) test (Fls 15.7–17.8), so relevance
  does **not** lean on the 2020-portfolio-share channel — reversing the prior
  weak-GPS verdict (which held only for the old many-to-many 14-family design).
  Headline identification rests on the leave-state shock; the z_nat arm documents
  the share-driven channel for comparison.
- **Clustering — connected component.** Because the instrument and treatment are
  constant within a component, SEs cluster at the component (`cluster_id` = comp),
  not the electoral zone (which would understate uncertainty).

---

## 2. Baseline specification (the one preferred spec)

Every reported outcome is estimated at this spec.

`ΔY_m = α + τ·Δlog(1+ℓ_m) + X_m'γ + δ_UF(m) + u_m`, with
`Δlog(1+ℓ_m)` instrumented by `bartik_iv_2020_2024`.

### Controls X_m — the "option 1a" set
Universal controls (predetermined, absorb the municipality characteristics that
drive both the 2020 litigation portfolio and outcome trends):

1. `log_pop_2010`
2. `urban_share_2010`
3. `log_income_pc_2010`
4. `margin_2016`
5. `log1p_total_valid_votes_2020`  (baseline race scale)

**plus the per-outcome lagged dependent variable** = the 2020 level of whatever
outcome is being estimated (see §7 map).

> **Change from the inherited set:** the old baseline hard-coded
> `margin_top1_top2_2020` and `log1p_total_candidates_2020` as *universal*
> controls. That meant every regression controlled for the 2020 level of two
> *arbitrary* outcomes while never controlling for the 2020 level of the outcome
> actually being run. We replace that with the principled rule: drop the two
> arbitrary outcome-levels, add `Y_2020` for the current outcome (mean-reversion
> / convergence control for a changes design).

Notes:
- 2010 demographics are stale for 2020–2024 outcomes; population is updatable to
  the 2022 Census, income/urbanization are not (long-form is 2010). Acceptable
  (predetermined → no bias), to be flagged as a limitation.
- Control set must stay consistent with the GPS balance test
  (`output/tables/descriptives/gps_balance_tests.csv`): any covariate that
  significantly predicts the high-weight shares belongs here.

### Fixed effects — state (27 UF dummies)
Not merely a geography control. The shift `g` is leave-own-state-out, hence
**constant within a state**, so state FE absorb the state-mean of the instrument
and leave identification to run off **within-state variation in the 2020 shares**
— exactly the GPS estimand. State is also the TRE/MPE jurisdiction that generates
the litigation waves, so state FE soak up statewide enforcement/political trends.
Going finer (mesoregion) is a robustness check, not the baseline (it discards
within-state share variation for no identification gain under GPS).

### Clustering — principal electoral zone
Conventional SEs cluster by `cluster_id` = principal electoral zone, the level at
which treatment (lawsuits) is measured (municipalities can share a zone).

### Inference — exposure-robust is the headline
Because the shift-share mechanically correlates municipalities sharing the same
state-level shocks, zone clustering understates uncertainty. **Report the
BHJ/AKM exposure-robust SE (`code/04_analysis/11_exposure_robust_se.py`) as the
preferred inference, with zone-clustered SE shown alongside** for the headline
outcomes. Also report the Lee et al. (2022) tF weak-instrument correction
(critical value depends on first-stage F). LIML is reported as a check and equals
2SLS at K=1.

### Estimator — 2SLS (`fixest::feols`).

---

## 3. Robustness set (primary outcome[s] only)

A single stability table on the primary outcome(s), not a re-run of the paper:

1. **Extended controls** — add the wider covariate block (omitted-variable check).
2. **Mesoregion FE** — IBGE mesoregion (137 groups) instead of state; tighter
   within-region share identification.
3. **Single-zone municipalities** — measurement check (treatment cleanly
   assigned where a municipality is one zone).
4. **Inference** — exposure-robust vs zone-clustered SE; tF; LIML.

---

## 4. Heterogeneity (separate section — NOT robustness)

Subsample splits / interactions, motivated by mechanism:

- **Open seat vs contested seat** (`open_seat_2024`). Report the **subsample
  first-stage F** in each cell, not just the second stage.
- Pre-treatment **poll activity** (`06_heterogeneity_polls.R`).
- **Media salience** (`07_iv_mechanism_media.R`, `08_heterogeneity_atlas.R`).
- **Population** and **population × media** (`09_`, `10_`).

---

## 5. Dropped / deprecated

- **`broader_treatment` spec** — mislabeled (it only added
  `log1p_lawsuits_no_rrc_2020` as a control; it did not broaden the treatment)
  and built on the redundant no-RRC column. Removed.
- **No-RRC instrument variant** (`bartik_iv_no_rrc`, `lawsuits_no_rrc_*`) —
  redundant: RRC (subject 11618) is already DROP in the build-stage taxonomy, so
  the no-RRC instrument was identical to the baseline. Removed from the build
  (`01_assemble_design.py`), from `01b`, and from the `07` spec list.

---

## 6. Identification caveats (drive outcome tiers — §-to-come)

> **⚠ STALE for the new instrument (2026-06-23).** Everything in §6 below — the
> Rotemberg ~71%-on-impugnacao weight, the HHI≈0.60, and the pre-trend placebo
> p-values — was computed on the OLD 14-family national-shock muni instrument. The
> promoted `class_folded` instrument has 7 families and identifies off the
> leave-state shock, so these numbers must be **recomputed** (GPS balance,
> Rotemberg weights/F_k, pre-trend placebos for the dominant class). PENDING. Until
> then, treat the tiers below as provisional. Note the new instrument's relevance
> no longer depends on the share channel, which weakens the original GPS-only
> rationale for share-exogeneity as the *sole* identifying lane.

From the verified GPS diagnostics (instrument unchanged after the 2026-06-17 fix):

- Rotemberg weight ~**71% on `impugnacao_registro`** (registration challenges);
  `propaganda_rua` (16%) and `propaganda_digital` (14%) are the only other
  meaningful contributors. Rotemberg HHI ≈ 0.60.
- Pre-trend (placebo, 2016→2020) tests for the dominant share:
  - **Margin (W−RU): p = 0.93 → clean.** Competition/margin outcomes rest on
    credible identification.
  - **Winner vote share: p = 0.027 → fails.**
  - **Candidate count: p = 0.012 (β = −0.26) → fails.** Registration-heavy
    municipalities were already on declining-candidate-count trends pre-treatment;
    the lagged-DV control does **not** fix this (the pre-trend test already
    includes it).
- **Implication:** build the paper's spine on the competition/margin outcomes;
  demote candidate-count ("field thinning") and winner-vote-share to
  secondary/exploratory with the pre-trend caveat stated. (Final primary/
  secondary/exploratory list still to be fixed.)

---

## 6b. Outcome selection (in progress — group by group)

### Voter behavior — DECIDED (office-aware)
**Round.** First round only (`NR_TURNO == 1`) everywhere. It is the only round all
~5,570 municipalities hold; runoffs occur only in municipalities >200k voters
(~50 cities) and would select on size. Enforced in `05_electoral_admin.py` and
`05b_office_ballot_spoilage.py`.

**Margins.** All electoral-admin rates over registered voters (aptos) satisfy
`valid + blank + null + abstention = 1`, so they carry only 3 independent
quantities. We report:

- **Ballot spoilage, by office sought (MAIN).** Blank/null are cast on a *separate
  ballot* for mayor and for council, so spoilage is a per-office outcome — like the
  candidate-composition outcomes, reported for both the executive and the
  legislative race. Denominator = votes cast for that office (`QT_VOTOS` =
  comparecimento). Built per office in `05b_office_ballot_spoilage.py`
  (`{office}_{null,blank,invalid}_share_cast_{year}`). Three measures: `null`,
  `blank`, and combined `invalid` (= non-valid = blank+null), the single natural
  disengagement margin under electronic voting (both are discarded from valid
  votes; the historical conformity/protest split no longer applies). Two panels:
  Mayor and Council. (The within-municipality roll-off vereador − prefeito is built
  in 05b but **not reported** — dropped from the table per the final voter-group
  decision.)
- **Turnout** (`turnout_rate`, voted/registered) — office-invariant (one
  comparecimento); reported once, municipality-wide. Extensive-margin /
  "participation unmoved" check.
- **Abstention** (`abstention_rate`, = 1 − turnout exactly) — reported alongside
  turnout so the "did not vote" margin reads off directly. Its IV coefficient is
  the exact negative of turnout's (same SE, same p); shown for interpretability,
  not as independent evidence. Reconstructed from admin for the 2020→2024 delta;
  the design carries `abstention_rate_2020` as the lagged DV.
- **Dropped `valid_vote_rate` (effective participation)** — superseded by abstention
  as the second municipality-wide margin.

**Scripts.** Estimation logic is shared in `_voter_behavior_core.R`:
`03_voter_behavior_iv.R` is the MAIN spec (full sample, office-aware);
`03b_voter_behavior_single_zone.R` is a heterogeneity re-estimate on the
single-zone sample (municipality == zone). Both write office-spoilage + turnout
tables (`voter_office_spoilage*.tex`, `voter_turnout*.tex`).

**Pending.** `blank_share_cast` + turnout still to be added to the GPS pre-trend
placebo battery (currently untested for voter behavior).

### Candidate performance — TBD

## 7. Per-outcome lagged-DV map

`Δoutcome_2024_2020` → 2020 level to include as the lagged DV.

| Outcome (delta) | Lagged DV (2020 level) |
|---|---|
| winner_majority | winner_majority_2020 |
| margin_top1_top2 | margin_top1_top2_2020 |
| winner_vote_share | winner_vote_share_2020 |
| runnerup_vote_share | runnerup_vote_share_2020 |
| others_vote_share | others_vote_share_2020 |
| top2_vote_share | top2_vote_share_2020 |
| log1p_n_candidates_with_votes | log1p(n_candidates_with_votes_2020) — derive |
| blank_rate | blank_rate_2020 |
| turnout_rate | turnout_rate_2020 |
| null_rate | null_rate_2020 |
| valid_vote_rate | valid_vote_rate_2020 — **missing, add in assemble** |
| female_vote_share | female_vote_share_2020 |
| female_share | female_share_2020 |
| nonwhite_vote_share | nonwhite_vote_share_2020 |
| winner_is_female | winner_is_female_2020 |
| new_candidate_vote_share | new_candidate_vote_share_2020 |
| incumbent_candidate_vote_share | incumbent_candidate_vote_share_2020 |
| winner_is_new_vs_2020 | winner_is_new_vs_2020_2020 |
| share_first_time_candidates | share_first_time_candidates_2020 |
| share_serial_challenger | share_serial_challenger_2020 |
| share_cross_cycle_returner | share_cross_cycle_returner_2020 |
| effective_n_candidates_vote | effective_n_candidates_vote_2020 |
| effective_n_parties_vote | effective_n_parties_vote_2020 |
| effective_party_count_candidates | effective_party_count_candidates_2020 |
| vote_hhi_candidate | vote_hhi_candidate_2020 |
| vote_hhi_party | vote_hhi_party_2020 |
| candidate_hhi_party | candidate_hhi_party_2020 |

---

## 8. Implementation status

The baseline control list is currently **duplicated across ~15 scripts** (both IV
scripts, all heterogeneity scripts, legislative design, summary stats, figures,
GPS/Rotemberg diagnostics) rather than defined once. Trimming `BASELINE_CONTROLS`
in one file would desync the others.

**To do (pending outcome selection):**
1. Centralize the control list + lagged-DV map in one source both R and Python
   read (e.g. `code/spec_config.json`), so this document and the code share a
   single definition.
2. Wire the per-outcome lagged DV into `run_iv` / `run_first_stage` (consequence:
   one first stage per outcome, since controls now vary by outcome).
3. Drop `broader_treatment` and the no-RRC build (§5).
4. Add `valid_vote_rate_2020` in `01_assemble_design.py`.
5. Move open/contested out of the spec list into the heterogeneity section, with
   subsample first-stage F reported.
</content>
</invoke>
