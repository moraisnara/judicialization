# Judicialization and Electoral Competition in Brazil

**PhD dissertation project — Nara Lívia Morais, FEA-USP**

Causal identification of the effect of pre-election judicial challenges on mayoral and city-council
election outcomes in Brazil, using a Bartik shift-share instrument built from TSE processual data.

---

## What this repo produces

The pipeline exists to produce four deliverables. Everything else is an intermediate.

| Deliverable | Path | Built by |
|---|---|---|
| **Report deck** (the full research report) | `output/presentation/slides_report.pdf` | `pdflatex` on `slides_report.tex` |
| **Advisor deck** (10-min preliminary results) | `output/presentation/slides_advisor.pdf` | `pdflatex` on `slides_advisor.tex` |
| **Estimating-equations note** | `output/paper/estimating_equations.pdf` | `pdflatex`, no pipeline dependency |
| **Extended abstract / paper draft** | `output/paper/extended_abstract.pdf`, `paper.pdf` | `pdflatex` + `bibtex` |

Both decks are pure consumers: every number in them comes from
`output/tables/tex/abstract_macros.tex`, every table from an `output/tables/tex/*.tex`
fragment, every figure from `output/figures/*.pdf`. Nothing is typed by hand into a slide.
That is why `04_analysis/06_abstract_macros.py` must be the **last** script to run.

---

## Quickstart: what to run to get the final results

```bash
# Full pipeline, correct order, ~1 command
python code/run_all.py

# Then compile the decks (three passes for nav/refs/bib)
cd output/presentation
pdflatex -interaction=nonstopmode slides_report.tex
bibtex slides_report
pdflatex -interaction=nonstopmode slides_report.tex
pdflatex -interaction=nonstopmode slides_report.tex

pdflatex -interaction=nonstopmode slides_advisor.tex
pdflatex -interaction=nonstopmode slides_advisor.tex
```

`run_all.py` encodes the correct dependency order, which is **not** the numeric order of the
filenames in two places (see the order table below). Prefer it over running scripts by hand.

### If you only changed one thing

| You changed… | Re-run, in this order |
|---|---|
| A **figure's** look | `04_analysis/03_result_figures.R` (results) or `02_descriptive_figures.R` (descriptives) |
| A **table's** layout | `03_estimation/02_iv_main.R` (executive) or `02b_iv_legislative.R` (council) |
| A **specification** (controls, sample, estimator) | all of `03_estimation/`, then all of `04_analysis/` |
| An **outcome definition** | `02_build/03_vote_outcomes.py` → `03_estimation/01*` → all of `03_estimation/` → all of `04_analysis/` |
| The **instrument** (topics, filter, shares) | `02_build/02_shift_share_design.py` onward — i.e. everything |
| **Deck prose only** | nothing; just recompile |

After *any* estimation re-run, `04_analysis/06_abstract_macros.py` must run again before the
deck is recompiled, or the slides will show the previous vintage's numbers.

### Minimum path to the headline number

If you only want the consolidation estimate and its first stage (not the full deck):

```
02_build/01_lawsuit_panel.py → 02_shift_share_design.py → 04_candidate_history.py
  → 03_vote_outcomes.py → 05_turnout_ballot_outcomes.py → 06_turnout_profile_panel.py
  → 07_turnout_profile_outcomes.py → 08_electoral_controls_2016.py → 09_municipal_covariates.py
03_estimation/01_assemble_design.py → 02_iv_main.R
```

Result lands in `output/tables/regressions/executive_margin_iv_fixest.csv` and
`executive_margin_first_stage_fixest.csv`.

---

## Full run order

The numeric prefix is meant to encode run order. It currently does so **except** at the two
rows marked ⚠ — `run_all.py` is the authority, not the filenames.

### Stage 01 — download (run once; ~several GB from TSE/IBGE)

| # | Script | Pulls |
|---|---|---|
| 00 | `00_verify_raw_data.py` | checks expected raw files exist |
| 01 | `01_lawsuits.py` | TSE processual docket (processo, assuntos, decisoes, recursos) |
| 02 | `02_candidates.py` | candidate registry 2020/2024 |
| 03 | `03_historical_elections.py` | 2016 votes, 2012/2016 candidates, detalhe_votacao |
| 04 | `04_votes.py` | candidate vote counts 2020/2024 |
| 05 | `05_municipal_characteristics.R` | Census 2010 via `censobr` |
| 06 | `06_municipality_crosswalk.R` | IBGE ↔ TSE crosswalk via `basedosdados` |

### Stage 02 — build

| # | Script | Writes |
|---|---|---|
| 00 | `00_verify_lawsuits.py` | `logs/tse_processual_inventory.csv` |
| 01 | `01_lawsuit_panel.py` | `zona_lawsuit_panel.csv` |
| 02 | `02_shift_share_design.py` | `municipality_bartik_components.csv`, `municipality_competition_subject_panel.csv`, `office_candidate_outcomes_panel.csv`, `executive_shift_share_design.csv`, `legislative_shift_share_design.csv`, `label_code_bridge.csv` |
| ⚠ 04 | `04_candidate_history.py` | `candidate_experience_panel.csv`, `candidate_experience_flags.csv` |
| ⚠ 03 | `03_vote_outcomes.py` | `candidate_vote_panel.csv`, `office_vote_outcomes_panel.csv`, `executive_vote_shift_share_design.csv`, `legislative_vote_shift_share_design.csv` |
| 05 | `05_turnout_ballot_outcomes.py` | `electoral_admin_outcomes.csv` |
| 06 | `06_turnout_profile_panel.py` | `comparecimento_disaggregated.csv` |
| 07 | `07_turnout_profile_outcomes.py` | `voter_disaggregated_outcomes.csv` |
| 08 | `08_electoral_controls_2016.py` | `electoral_controls_2016.csv` |
| 09 | `09_municipal_covariates.py` | `municipal_covariates.csv` |
| 10 | `10_candidate_finance.py` | `candidate_finance_panel.csv` |

⚠ **04 runs before 03.** `03_vote_outcomes.py` merges the `candidate_experience_flags.csv`
that `04_candidate_history.py` writes. Run 03 first on a clean clone and the experience
vote-shares are silently `NaN` — no error is raised.

### Stage 03 — estimation (all regressions in R/`fixest`)

| # | Script | Writes |
|---|---|---|
| 01 | `01_assemble_design.py` | `data/estimation/executive_margin_design.csv` |
| 01b | `01b_assemble_legislative_design.py` | `data/estimation/legislative_design.csv` |
| 02 | `02_iv_main.R` | headline executive 2SLS + 14 `.tex` fragments + `executive_margin_{iv,first_stage}_fixest.csv` |
| 02b | `02b_iv_legislative.R` | council 2SLS + 3 `.tex` fragments + `legislative_{iv,first_stage}_fixest.csv` |
| 04 | `04_placebo_nonadversarial.R` | `nonadversarial_placebo.csv`, `nonadversarial_robustness.tex` |
| 05 | `05_pretrend_balance.R` | `pretrend_balance.csv`, `pretrend_coefplot.pdf` |
| 06 | `06_wild_bootstrap_ar.R` | `wild_bootstrap_ar.csv` — the headline AR-WCR inference |
| 07 | `07_multiplicity.R` | `multiplicity_adjusted.csv` |
| 09 | `09_extensive_margin.R` | `extensive_margin{,_decomposition}.{tex,csv}`, `zero_exposure_robustness.csv` |
| 10 | `10_mechanism_finance.R` | `mechanism_finance_fixest.csv`, `mechanism_finance_seat.tex` |
| 11 | `11_summary_indices.R` | `summary_indices*.{tex,csv}`, `romano_wolf_stepdown.{tex,csv}` |
| 12 | `12_treatment_definition.R` | `treatment_definition{,_macros}.tex`, `treatment_definition.csv` |
| 13 | `13_reclassification_robustness.R` | `reclassification_robustness{,_macros}.tex` + `.csv` |

The family-IV patch `01c_patch_family_ivs.py` moved to `exploration/03_estimation/` with
its only consumer, `03_family_iv.R`: nothing under `code/` reads the columns it adds. It
still rewrites `executive_margin_design.csv` in place, so run `01` before it if the design
already carries family IVs. The legislative branch is unaffected — it uses only
`bartik_iv_2020_2024`, never the family IVs.

Exploration scripts for this stage live in `exploration/03_estimation/` — see
`exploration/README.md`.

### Stage 04 — analysis, figures, macros

| # | Script | Writes |
|---|---|---|
| 01 | `01_descriptives.py` | overview + composition + timing + BHJ shift CSVs, `litigation_composition.tex` |
| 02 | `02_descriptive_figures.R` | `litigation_timing_shape.pdf`, `sample_map.pdf`, `instrument_{histogram,map}.pdf` |
| 03 | `03_result_figures.R` | all 9 result figures (first stage + coefplots) |
| 04 | `04_iv_diagnostics.py` | `rotemberg_weights.csv`, `gps_balance_tests.csv` |
| 07 | `07_exposure_robust_se.R` | `exposure_robust_{se,akm}.csv` — needs `rotemberg_weights.csv` from 04 |
| 08 | `08_lawsuit_composition_sp.py` | `lawsuit_composition_sp.{csv,tex}` |
| 09 | `09_summary_statistics.R` | `sample_summary_statistics.tex` |
| 10 | `10_candidate_rank_profile.py` | `candidate_rank_profile.{csv,tex}` |
| ⚠ 06 | `06_abstract_macros.py` | `abstract_macros.tex`, `abstract_table.tex` — **runs last** |

⚠ **06 runs last, not sixth.** It reads 14 upstream CSVs (both estimation vintages, the
descriptives, AR-WCR, exposure-robust SEs, Rotemberg) and emits every number the decks
display. It also **degrades silently**: missing inputs are caught by `try/except
FileNotFoundError`, so a partial pipeline produces a macros file with stale or absent
numbers rather than an error. Always run it at the end of a complete pass.

Exploration scripts for this stage live in `exploration/04_analysis/` — see
`exploration/README.md`.

---

## Environment

```bash
# Python 3.13 — C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe
pip install pandas numpy scipy

# R 4.6.0 — C:\Program Files\R\R-4.6.0\bin\Rscript.exe
install.packages(c("fixest", "data.table", "dplyr", "readr", "ggplot2", "scales",
                   "sf", "geobr", "censobr", "basedosdados"))
```

`run_all.py` invokes R as bare `Rscript`, so R's `bin` directory must be on `PATH`
(it resolves in Git Bash on this machine; check before running from PowerShell).

---

## Identification strategy

The instrument is a municipality-level Bartik shift-share:

```
Z_i = Σ_k s_{ik} × g_k
```

where `s_{ik}` is municipality `i`'s 2020 baseline share of lawsuits in topic `k`, and `g_k` is
the leave-own-state-out log growth of topic `k` nationally from 2020 to 2024.

**Adversarial filter:** administrative and procedural classes/subjects (candidate registration,
party lists, campaign-finance accounts — ≈48.5% of filings) are excluded at the build stage
in `02_shift_share_design.py`, retaining only substantive electoral-competition cases.
This produces the primary instrument `bartik_iv_2020_2024`, first-stage F ≈ 102 on N = 5,560.

**Estimator:** the headline is an ANCOVA on the 2016 pre-window baseline —
`Y_2024 ~ D̂ + Y_2016 + controls | state FE`, clustered by state (G = 26) — with the
first-difference specification demoted to the appendix.

Inference is conventional cluster-robust SE (headline), with appendix layers: GPS (2020)
Rotemberg-weight decomposition, BHJ (2022/2024) diagnostics, Lee et al. (2022) tF critical
values, Anderson–Rubin wild-cluster restricted bootstrap (`06_wild_bootstrap_ar.R`), and
AKM (2019)/BHJ (2022) exposure-robust SEs (`07_exposure_robust_se.R`).

The exact equations, in Ash–Morelli–Vannoni form alongside this design's first and second
stage, are written up in `output/paper/estimating_equations.pdf`.

**Specifications** (both executive and legislative):

| Spec | Description |
|---|---|
| `baseline` | ANCOVA-2016 headline: 2016-baseline lag + controls + state FE |
| `single_zone` | Same, restricted to single-zone municipalities |
| `extended_controls` | Adds demographic/composition controls |
| `open_seat` | 2020 winner term-limited (no incumbent running in 2024) |
| `contested_seat` | Incumbent can seek reelection in 2024 |
| `broader_treatment` | Baseline + `log1p_lawsuits_no_rrc_2020` as covariate |
| `fd` | First difference (appendix; over-differences a barely-persistent outcome) |
| `ancova_2020lvl` | ANCOVA on the 2020 level instead of the 2016 baseline |

---

## Directory structure

```
judicialization/
├── data/
│   ├── raw/          — TSE/IBGE downloads, never modified (27 GB, gitignored)
│   ├── clean/        — intermediate datasets from 02_build (gitignored)
│   └── estimation/   — regression-ready design matrices (gitignored)
├── output/
│   ├── figures/      — all figures, PDF only (tracked)
│   ├── tables/
│   │   ├── regressions/  — coefficients, CSV (gitignored: *.csv)
│   │   ├── descriptives/ — diagnostics + summary stats, CSV (gitignored)
│   │   └── tex/          — LaTeX fragments \input into the decks (tracked)
│   ├── presentation/ — Beamer sources + compiled decks
│   └── paper/        — paper, extended abstract, estimating-equations note
├── code/
│   ├── 01_download/  ├── 02_build/  ├── 03_estimation/  ├── 04_analysis/
│   ├── utils/        — figure_style.R, tf_critical_values.R
│   └── run_all.py
└── logs/             — verification inventory from 02_build/00
```

`csv` is the numeric source of truth; `tex` is the deck fragment. No markdown tables are
produced anywhere in the pipeline.

---

## Data reference

### `data/raw/`

| Folder / file | Contents |
|---|---|
| `processo_eleitoral_YYYY/` | case-level docket registry (2018–2024) |
| `processos_eleitorais_assuntos_YYYY/` | case × legal subject mapping (2018–2024) |
| `decisoes_YYYY/`, `recursos_YYYY/` | decisions and appeals (2018–2024) |
| `consulta_cand_YYYY/` | candidate registry by state (2012–2024) |
| `votacao_candidato_munzona_YYYY/` | candidate vote counts by zone (2016/2020/2024) |
| `detalhe_votacao_munzona_YYYY/` | turnout, blank, null by zone (2020/2024) |
| `lista-zonas-municipios-10-07-24.csv` | official TSE zone → municipality lookup |
| `bd_municipio_tse_ibge.csv`, `bd_diretorio_municipio.csv` | TSE ↔ IBGE crosswalks |
| `tpu_eleitoral_tree.json` | TPU subject-code tree (feeds `exploration/04_analysis/11_lawsuit_topic_selection.py`) |

### `data/clean/`

| File | Produced by | Contents |
|---|---|---|
| `zona_lawsuit_panel.csv` | `01_lawsuit_panel.py` | zone × class × subject panel, pre-election cases |
| `shift_share_subject_crosswalk.csv` | **hand-maintained** | subject code → litigation family |
| `label_code_bridge.csv` | `02_shift_share_design.py` (cache) | SIG text labels → TSE codes |
| `municipality_bartik_components.csv` | `02_shift_share_design.py` | per (muni, subject): `s_ik × g_k`, share, shock |
| `municipality_competition_subject_panel.csv` | `02_shift_share_design.py` | per (muni, subject, year): lawsuit counts |
| `office_candidate_outcomes_panel.csv` | `02_shift_share_design.py` | office-level candidate composition |
| `executive_shift_share_design.csv` | `02_shift_share_design.py` | executive design, pre-vote-merge |
| `legislative_shift_share_design.csv` | `02_shift_share_design.py` | legislative design, pre-vote-merge |
| `candidate_experience_panel.csv` | `04_candidate_history.py` | prior candidacies/wins per municipality |
| `candidate_experience_flags.csv` | `04_candidate_history.py` | per-candidate experience flags (120 MB) |
| `candidate_vote_panel.csv` | `03_vote_outcomes.py` | candidate × municipality votes (190 MB) |
| `office_vote_outcomes_panel.csv` | `03_vote_outcomes.py` | municipality × office × year vote outcomes |
| `executive_vote_shift_share_design.csv` | `03_vote_outcomes.py` | executive design + vote outcomes |
| `legislative_vote_shift_share_design.csv` | `03_vote_outcomes.py` | legislative design + vote outcomes |
| `electoral_admin_outcomes.csv` | `05_turnout_ballot_outcomes.py` | turnout, blank/null rate, registered voters |
| `comparecimento_disaggregated.csv` | `06_turnout_profile_panel.py` | long turnout panel by voter trait |
| `voter_disaggregated_outcomes.csv` | `07_turnout_profile_outcomes.py` | wide facultative / low-education turnout |
| `electoral_controls_2016.csv` | `08_electoral_controls_2016.py` | 2016 baseline margin, HHI, ENP, winner |
| `censo2010_municipal_ibge.csv` | `05_municipal_characteristics.R` | Census 2010 municipal covariates |
| `municipal_covariates.csv` | `09_municipal_covariates.py` | master covariate table |
| `candidate_finance_panel.csv` | `10_candidate_finance.py` | SPCE campaign spend by vote rank |

### `data/estimation/`

| File | Produced by | Contents |
|---|---|---|
| `executive_margin_design.csv` | `01_assemble_design.py` | one row per municipality (5,571 rows, 345 cols); instrument, treatment, all executive outcomes, controls, cluster ID. Estimation N = 5,560. Family IVs and topic shares are **not** in the committed vintage — `exploration/03_estimation/01c_patch_family_ivs.py` patches them in for the family lane, and nothing in `code/` reads them. |
| `legislative_design.csv` | `01b_assemble_legislative_design.py` | same instrument and controls; vereador candidate-pool, elected-composition and party-competition outcomes. |

---

## Output reference

### `output/figures/`

Figures carry no baked-in titles, captions or footnotes — those live on the Beamer frame.
Every producing script sources `code/utils/figure_style.R` for the shared theme and `PAL`
palette, which mirrors the deck colours. Never hard-code a hex colour in a figure script.

| File | Produced by | Shown on |
|---|---|---|
| `litigation_timing_shape.pdf` | `02_descriptive_figures.R` | report |
| `sample_map.pdf`, `instrument_map.pdf`, `instrument_histogram.pdf` | `02_descriptive_figures.R` | report |
| `firststage_linear.pdf` | `03_result_figures.R` | report |
| `representation_coefplot.pdf`, `entrant_coefplot.pdf`, `turnout_coefplot.pdf` | `03_result_figures.R` | report |
| `candidate_supply_coefplot.pdf`, `legislative_coefplot.pdf` | `03_result_figures.R` | report (+ advisor) |
| `heterogeneity_seat_coefplot.pdf`, `gender_consolidation_coefplot.pdf` | `03_result_figures.R` | report + advisor |
| `voterbehavior_seat_coefplot.pdf` | `03_result_figures.R` | advisor |
| `pretrend_coefplot.pdf` | `05_pretrend_balance.R` | report |

### `output/tables/tex/`

All 35 fragments are `\input` by a deck.

The four `*_macros.tex` files (`abstract`, `extensive_margin`, `treatment_definition`,
`reclassification_robustness`) are `\input` from `slides_preamble.tex`, not from a frame.

Table style is the hand-built house mould: `booktabs` double rules, bold outcome headers,
a `\rowcolor{mylight}` horizontal band on the **Judicialization** coefficient row and its
SE row, mean-of-dep-var rows in the footer, `***/**/*` at 1/5/10% with no printed legend.
See `CLAUDE.md` for the full convention.

### `output/tables/regressions/` and `descriptives/` (CSV)

Every `.csv` under `output/tables/` is the numeric source of truth for whatever `.tex`
fragment or macro reports it. Producers are listed in the stage-03 and stage-04 tables above.

### `output/presentation/`

| File | Contents |
|---|---|
| `slides_preamble.tex` | shared Beamer preamble — house colours, `\takeaway`, `\pos`/`\negt`/`\ns`, and the `\input` of all four macro files. **Edit colours and commands here**, not in a deck. |
| `slides_report.tex` / `.pdf` | full report deck (the research report; frame count is not a constraint) |
| `slides_advisor.tex` / `.pdf` | 10-minute preliminary-results deck: one frame per layer, results-only backups |
| `biblio.bib`, `judicial system.bib` | bibliography |

### `output/paper/`

| File | Contents |
|---|---|
| `estimating_equations.tex` / `.pdf` | AMV template + this design's first and second stage + variable construction |
| `extended_abstract.tex` / `.pdf` | extended abstract |
| `paper.tex` / `.pdf` | paper draft skeleton |
| `references.bib`, `extended_abstract.bib` | bibliography |

`WRITING_GUIDE.md` (Evans 7-element intro structure + proposal guide) sits at the repo
root with `CLAUDE.md` — it is a working guide, not an output. The redesign spec is not at
the root: it lives at `exploration/SPECIFICATION_tse_shift_share.md`, with the lane it
specifies.

---

## Known gaps

Open items as of the 2026-08-05 audit, as they stand after the 2026-08-06 remediation
pass. None block a run; all affect reproducibility or completeness.

1. **Output vintages are mixed.** `executive_margin_design.csv` and the `02_iv_main.R`
   outputs date from 2026-08-04; the legislative estimation, every stage-03 robustness
   script and every stage-04 diagnostic still carry 2026-07-02/07-08 outputs. Shared
   coefficients agree across vintages (the margin estimate is identical to 10 digits),
   but a full `run_all.py` pass is needed before the results can be called reproduced.
2. **`legislative_vote_shift_share_design.csv` is built and never used.** The council
   branch estimates candidate-pool and elected-composition outcomes only; legislative
   *vote* outcomes exist in `data/clean/` but no design assembles them.
3. **The share-balance defense shows no numbers.** `gps_balance_tests.csv` holds the
   share-covariate balance test, but the deck asserts that defense in prose
   (`slides_report.tex:989`) without citing a figure from it — and the test is
   computed in Python, which the R-only rule bars for anything reaching a slide.
   Port to R and cite, or drop the claim.
4. **`data/clean/zona_eleitoral_lookup.csv` is referenced by no script.** It is a
   leftover of the pre-SIG zone-level design. Note that **no script writes it either**,
   so deleting it is not undoable by re-running the pipeline.
5. **`shift_share_subject_crosswalk.csv` is a hand-maintained input living in
   `data/clean/`**, which otherwise holds only generated files. It belongs with the raw
   or manual inputs. `shift_share_subject_manual_assignments.csv` is read from the same
   folder if present (guarded by `.exists()`) and is currently absent.
6. **Stage-04 estimation-flavored scripts.** Resolved 2026-08-12. `05_validation.R` fed
   no document — `fd_vs_ancova_comparison.csv` and `ancova_validation.csv` were read by
   nothing — and moved to `exploration/04_analysis/` under the three-test rule in
   `CLAUDE.md`. `07_exposure_robust_se.R` stays in `code/04_analysis/`: `06_abstract_macros.py`
   reads `exposure_robust_se.csv`, so its stage-04 slot is dependency order, not
   miscategorization — it needs the Rotemberg weights that `04_iv_diagnostics.py` writes.
7. **`06_abstract_macros.py` still holds slot 06 but runs last**, so stage-04 numbering
   does not fully encode run order. Renumbering it to 12 would touch the generated `.tex`
   headers and the deck comments that name it; deferred as a deliberate exception,
   flagged with ⚠ in the stage-04 table above.
8. **Orphan outputs.** Resolved 2026-08-12. `code/utils/audit_pipeline.py` reports
   orphan outputs on demand; the reorganization deleted the nine that existed and
   stripped the blocks that regenerated them.
9. **The spec on disk documents a different design** than the pipeline builds. Resolved
   2026-08-12. The `tse-shift-share` first-difference redesign spec moved off the repo
   root to `exploration/SPECIFICATION_tse_shift_share.md`, where its filename and its
   lane both say it is a proposal rather than documentation of the committed
   propaganda-Bartik/ANCOVA design. `exploration/README.md` records why.
10. **`output/tables/` is the declared source of truth but is entirely untracked.**
    `*.csv` is gitignored repo-wide, so a clean checkout has no saved regression
    records — they exist only on the machine that ran the pipeline. Consistent with
    "data never leaves this repo", but currently a side effect rather than a decision.
11. **`output/paper/extended_abstract.tex` cannot compile.** Found 2026-08-12. It
    `\includegraphics`es `../figures/forest_voter_behavior.pdf`, which is not on disk —
    the voter-behavior forest plot was replaced by `voterbehavior_seat_coefplot.pdf`.
    This is the one standing BUILD BREAKER `code/utils/audit_pipeline.py` reports. Nara
    writes the paper, so the fix is hers: point the include at the surviving figure or
    drop it.
12. **`run_all.py` cannot complete from a fresh state.** Found 2026-08-12. It calls
    `01_download/00_verify_raw_data.py` *before* the download scripts that produce what
    that gate verifies, so on a clean clone the very first step fails. Reproduced on this
    machine: it stops on `decisoes_{2020,2024}.zip` and `recursos_{2020,2024}.zip`, which
    are absent from `data/raw/`. Reordering changes pipeline semantics (the gate is also a
    guard against a stale or partial `data/raw/`) and cannot be tested without a full
    re-download, so it is recorded rather than fixed.

**Closed by the 2026-08-06 pass:** the deck sources are no longer git-ignored
(`.gitignore` now whitelists `output/presentation/*.tex` by extension rather than by a
stale filename list); `08b_lawsuit_topic_selection.py` was renamed to slot `11` and moved
after `10` in `run_all.py`; `WRITING_GUIDE.md` moved to the repo root.
