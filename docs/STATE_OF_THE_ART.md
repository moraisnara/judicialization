# State of the art — judicialization paper

**Last updated:** 2026-06-26. **Status:** this is the single current-truth document.
It supersedes the scattered design logs (`SIG_DESIGN_LOG.md`, `REBUILD_STATUS.md`)
as the description of *what we are doing now*. Those older files are kept as history,
not as instructions.

---

## 1. Research question (current framing)

Does the **judicialization of electoral competition** affect elections?

"Judicialization" = the expanded role of the judicial arena in the campaign, via
two channels: (1) **institutional/supply** — TSE rule growth gives the court more
to police; (2) **strategic/demand** — candidates weaponize lawsuits offensively and
defensively. The object is the *litigation climate at the place (municipality)
level*, not the effect of being sued on one candidate.

**Reframing (2026-06-26):** the story is the impact of judicialization on
**voters and candidates broadly** — turnout, valid/blank/null voting, competition,
entry, fragmentation, and the composition of who runs and wins. We are **no longer
leading with female-candidate-specific results.** Composition outcomes (female,
nonwhite, incumbency) remain in the outcome set, but as part of a broad sweep, not
as the headline. Earlier drafts (abstract, paper, slides) that headline the
female-candidate channel are **stale** and slated for revision.

---

## 2. Identification — the instrument we are using now

A topic **shift-share (Bartik) instrument** à la Ash, Morelli & Vannoni (2025):

```
B_i = Σ_k  s_ik(2020 share)  ×  g_ik(leave-own-state-out 2020→2024 log-growth shock)
```

- `s_ik` = municipality i's 2020 share of lawsuits in family k.
- `g_ik` = national log-growth of family k from 2020→2024, **leaving i's own state out**
  (`g = log(N24 − S24 + 1) − log(N20 − S20 + 1)`).
- Endogenous treatment: `delta_log1p_act_lawsuits = log1p(2024 kept lawsuits) − log1p(2020)`.
- Clustering: **state** (27 UFs; the column is `cluster_id`, the
  "electoral zone" comments are misleading — it is state-level clustering).

### Lawsuit data source

**SIG TSE "Processos eleitorais" municipality microdata** (built by
`code/02_build/00_sig_lawsuit_panel.py` → `sig_lawsuits_muni_zona_classe_assunto.csv`).
This resolves each lawsuit to its município de origem and **replaces the old
zona-level reconstruction** and its connected-component municipality unit. 2016 is
not available in SIG (no pre-period placebo from this source).

---

## 3. The current taxonomy — 10 act-based families

Built by `code/02_build/01d_act_family_crosswalk.py` →
`data/clean/act_family_crosswalk.csv` (pair_id-keyed, column `fam_act10`).

| Family | What it captures |
|--------|------------------|
| `abuso` | Abuse of economic/political/media power |
| `vote_buying` | Vote buying — civil (captação art.41-A) **and** criminal (corrupção art.299), boca de urna, arregimentação |
| `finance` | Illicit campaign finance, donations, illegal spending |
| `inelegib` | Ineligibility challenges |
| `fraude` | Document/registration fraud **incl. candidatura fictícia (12597)** |
| `honra` | Defamation — calúnia, difamação, injúria (its own family, not inside propaganda) |
| `direito_resposta` | Right of reply |
| `conduta_vedada` | Prohibited conduct by public officials |
| `pesquisa_adv` | Adversarial poll challenges (not administrative poll registration) |
| `ballot_integrity` | Vote-tally / sufrágio interference |

**Diagnostics (AMV / shift-exogeneity lane):** K_eff ≈ 6.8, first-stage **F ≈ 25.5**
(n ≈ 5009, state-clustered, run in R). Rotemberg weights all positive (top
fraude 0.33, vote_buying 0.21, pesquisa 0.18). Leave-state shock sd ≤ 0.03 (no
family driven by 1–2 states). Covariate balance joint **F = 2.83, p = 0.037** — the
one yellow flag: log_pop and log_valid_votes predict exposure, but both are
second-stage controls. We report this honestly, we do **not** claim clean exogeneity.

---

## 4. Decisions made (drops, folds, constructions)

**Construction decisions**
- **Act-based, not vehicle-based.** Families = the *act alleged*, merging civil and
  criminal vehicles of the same act. This rescues criminal-vehicle vote-buying/fraud
  the substance whitelist drops — validated as only **1.7%** of kept volume, all
  on-act. The act universe agrees **98.3%** with the audited whitelist.
- **Leave-own-state-out** shocks (not leave-one-municipality-out).
- 2020 shares; 2020→2024 growth; log1p treatment.

**Drop decisions**
- **Mandatory administrative filings dropped** (RRC / DRAP / prestação de contas) —
  every candidate must file these (~48.5% of all lawsuits); not adversarial.
- **Ancillary / downstream procedural vehicles dropped** by class keyword (execução,
  cumprimento de sentença, habeas, embargos, mandado de segurança, …) — they
  double-count the underlying accusation.
- **Propaganda dropped entirely** — 54% of the adversarial universe, 25% of it
  online/reform-contaminated; including it collapses K_eff 7→2.7 and F 27→3.7 by
  dominating the shares. (Defamation kept separately as `honra`.)
- **Online propaganda dropped** (reform-contaminated) — moot since all propaganda is
  dropped, kept explicit in the keyword fallback.

**Fold decisions**
- **candidatura fictícia → fraude.** Standalone it carried 52% of the Rotemberg
  weight (drop-top-1 F = 6.6, fragile). Folded into fraude → top weight 0.33,
  drop-top-1 F = 31.4. Sham candidacy *is* registration fraud; per the user's
  instruction it is **not** mixed with inelegibility.
- **ballot_integrity kept** (substance-only F = 23.2; +ballot F = 27.5).

---

## 5. Current live pipeline

```
code/02_build/00_sig_lawsuit_panel.py        # SIG muni microdata → panel
code/02_build/01d_act_family_crosswalk.py    # → data/clean/act_family_crosswalk.csv
code/03_estimation/01d_act_family_ivs.py     # Python: build B + treatment → data/estimation/act_design.csv
code/03_estimation/02c_act_iv.R              # R/fixest: first stage + 2SLS → output/tables/regressions/act_*_fixest.csv
```

**Estimation-stack rule:** all regression OUTPUTS (first stage, 2SLS, any
coefficient/SE/F that could reach a slide or the paper) run in **R/fixest**. Python
is for data construction and pure descriptives only.

---

## 6. Current headline result

Clean act instrument, on-spec second stage (n ≈ 5009, 26 clusters, first-stage
F ≈ 26.7). **Spec = 5 baseline controls + per-outcome lagged DV** (config "option 1a"),
read from `spec_config.json`.

> **2026-06-26 corrections (TWO spec artifacts removed).**
> (i) `02c_act_iv.R` had been running an OFF-SPEC regression (hard-coded 7 controls,
> including the two `margin_top1_top2_2020` / `log1p_total_candidates_2020` the config
> explicitly removed, and **no lagged DV**). Fixed to read the config.
> (ii) `valid_vote_rate_2020` was never built (line-240 merge guard in
> `01_assemble_design.py` silently dropped it), so `delta_valid_vote_rate` ran without
> its lagged DV. Now recovered from the registered-denominator identity
> (turnout = valid + null + blank). Both artifacts produced the only "significant"
> voter results — **both are GONE on-spec.**

- **All four voter-behaviour outcomes are NULL on-spec** (registered-voter denominator;
  identity valid = turnout − null − blank holds): turnout +0.008 (p=0.085),
  valid_vote_rate +0.016 (p=0.131), null −0.004 (p=0.19), blank −0.003 (p=0.34).
  The off-spec file had reported turnout +0.011 (p=0.024) ★ and valid_vote +0.029
  (p=0.029) ★; both were spec artifacts.
- **Composition / female outcomes are flatly null:** female_vote_share −0.002 (p=0.95),
  female_share −0.023 (p=0.48), winner_is_female −0.014 (p=0.71), nonwhite −0.035 (p=0.25).
- **Only marginal survivors** (tF*), both competition not voter:
  others_vote_share +0.016 (p=0.058, borderline) and
  log1p_n_candidates_with_votes +0.116 (p=0.050).

**Leave-one-family-out (`02d_leave_fraude_robustness.R` → `act_iv_leave_family_out.csv`)
is the key caveat.** The instrument's relevance is carried by 3 families:
dropping **fraude** alone collapses the first stage **F 26.6 → 3.9** (weak);
−pesquisa_adv → F 8.6; −abuso → F 12.2. None of the marginal survivors are robust:
valid_vote_rate and others_vote_share **die (and others flips sign) when pesquisa_adv
is removed**; n_candidates is significant only under −abuso. The point estimates grow
when fraude is dropped, but that is weak-IV bias, not a stronger effect.

Reading: the design defensibly supports a **precisely-estimated null on candidate
composition**. The faint participation/competition positives are **instrument-fragile**
(a fraude/pesquisa/abuso-dominated Bartik, K_eff small) and should not be presented as
robust causal effects without a shock-exogeneity defense. See also the GPS balance
flags in §2 / `gps_balance_tests.csv`.

### 6a. Disaggregated turnout (elastic-margin test, 2026-06-27)

The aggregate turnout null is near-mechanical under compulsory voting, so we
brought in TSE `perfil_comparecimento_abstencao` (download `11_…`, build
`05c_…` → `comparecimento_disaggregated.csv`, outcomes `05d_…` →
`voter_disaggregated_outcomes.csv`) and ran the on-spec act 2SLS plus a
leave-fraude variant (`03b_voter_disaggregated_iv.R` → `voter_disaggregated_iv.csv`).
TSE flags compulsory vs **facultative** (16–17, 70+, illiterate) natively.

**The disaggregation does NOT rescue a voter effect — it strengthens the null:**
- **Direct heterogeneity tests are flat null** under both instruments: education
  gap (high−low) +0.002 (p=0.68), sex gap (F−M) +0.002 (p=0.36). No *differential*
  voter response → the "confusion depresses low-education turnout" and
  "differential mobilization by sex" mechanisms are rejected.
- **The elastic margin is null:** facultative turnout +0.011 (p=0.157) — the
  choose-to-vote bloc where an engagement effect must appear shows nothing.
- **Every full-instrument positive is fraude-fragile and incoherent:** compulsory
  +0.008 (p=0.036)★, high-ed +0.010 (p=0.016)★, analfabeto +0.022 (p=0.005)★ all
  collapse on −fraude (p→0.08 / 0.11 / 0.30, F≈4). The pattern is incoherent
  (effect in compulsory but not facultative; high-ed but not low-ed; analfabeto
  but not its own low-ed bucket) — noise across 9 tests, not signal. The lone
  Bonferroni survivor (analfabeto) is wrong-signed for the confusion story and
  dies on leave-out.

The nominal positive sitting in the *compelled* bloc and vanishing on leave-out is
the signature of a spurious common component, not a voter decision. Voter channel =
**defended null**, not underpowered.

---

## 7. Pending (not yet done)

### Done in the 2026-06-26 doc/code reconciliation pass
- **`run_all.py` rewritten** to the act pipeline (was orchestrating 6 deleted
  scripts). Header documents the current design + a "PENDING ACT REPOINT" block
  listing the 8 scripts still on the retired instrument (see below). Compiles.
- **Docs reconciled to the act design:** `README.md`, `DATA_GUIDE.md`,
  `CLAUDE.md`, `docs/PIPELINE.md` rewritten against the actual CSV headers
  (`act_design.csv`: `bartik_iv_act` / `delta_log1p_act_lawsuits`;
  `municipality_act_components.csv`; cluster = state). Verified, not inferred.
- **Stale docs archived** to `docs/_archive/` with a ⚠️ banner: `SPECIFICATION.md`,
  `INSTRUMENT_ROBUSTNESS.md`, `NULL_DEFENSE.md`, `family_taxonomy_PROPOSAL.md`,
  `REBUILD_STATUS.md`.
- **Code comments fixed:** `02c_act_iv.R` ("zone-clustered" → "state-clustered",
  3 spots; logic was already correct); `01_assemble_design.py` and
  `03_candidate_composition.py` headers repointed to the act lineage.
- **⚠️ PENDING ACT REPOINT banners added** to the 8 scripts still on the retired
  substance-family instrument: `01b_assemble_legislative_design.py`,
  `05_cluster_robustness.R`, `11_family_iv_channels.R`, `12_mechanism_blocks_iv.R`,
  `11_inference_robustness.R`, `15_report_descriptives.py`,
  `21_leave_one_family_out.R`, `22_exposure_robust_se.R`. `22_…` was also removed
  from the active `run_all.py` path (it expects per-family `bartik_iv_*` columns
  that no longer exist).
- **STALE banners added** to `output/paper/extended_abstract.tex`,
  `output/paper/paper.tex`, `output/presentation/slides_report.tex` — documenting
  that the empirical narrative is **sign-inverted / nulled** by the act design and
  that ~22 `\input` fragments/macros are missing (deleted generators). Left for
  Nara to rewrite — authorship decision, not a mechanical fix.

### Still open (needs Nara / verified re-runs)
- **Repoint the 8 pending scripts** to `act_design.csv` + per-family act
  components, or build the legislative act design. The legislative arm
  (`legislative_design.csv`) is still on the retired instrument.
- **Rewrite the manuscript / extended abstract / slides** to the act findings
  (turnout +0.011, valid_vote +0.025, others_vote +0.028; composition null).
  Regenerate the candidate / first-stage / instrument tex fragments and
  `abstract_macros.tex` from `output/tables/regressions/act_iv_results.csv`.
- **Reconcile the Rotemberg discrepancy:** committed `05_rotemberg_weights.py`
  reports HHI 1.07, 6/10 positive weights; an earlier scratchpad note claimed
  all-positive. Trust the committed script; confirm the number for the writeup.
- **Data orphans** from the retired design remain on disk (not regenerable — old
  builders are gone). Reported to Nara for one-word delete confirmation; NOT
  deleted while away. See the audit report.

---

## 8. What is STALE (old design — slated for removal/revision)

Everything built on the **old lineage** is stale:
`subject_taxonomy_v3 → zona_lawsuit_panel → connected-component / class_folded
instrument → executive_margin_design.csv` with the **female-candidate headline**.

- **Code:** the zona/component apparatus, the instrument-search / taxonomy-version
  experimentation scripts, and the design-horserace audits (largely already moved to
  `code/_archive/`; remaining ones in `code/04_analysis/` tagged ARCHIVE in
  `REBUILD_STATUS.md`).
- **Outputs:** all `output/tables/regressions/` and `output/tables/tex/` fragments
  except `act_*` and `sig_*`; the old figures (`channel_vector_*`, female-specific
  forests, component diagnostics). NOTE: `output/paper/*.tex` and
  `output/presentation/slides_report.tex` **\input these fragments** — they break if
  fragments are deleted, so the manuscript/slides must be revised in step, not orphaned.

A concrete delete plan keyed to this section is to be confirmed before execution.
