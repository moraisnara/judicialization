# CLAUDE.md — judicialization repo

## Companion documents

| Document | What it governs |
|---|---|
| `FRAMING.md` | The locked argument: vocabulary, the Leveling/Barrier dichotomy, confidence tiers. Binds the deck and the paper. |
| `DECK_GUIDE.md` | How the one deck (`slides_report.tex`) is built: the section spine, the frame library, the build and its checks. |
| `WRITING_GUIDE.md` | Paper structure (Evans 7-element intro). The deck is written to this structure and the paper mirrors it. |
| `DATA_GUIDE.md` | Datasets, entity tokens, and the download → build → estimation lineage. |

**Nara writes the paper.** Never draft prose into `output/paper/paper.tex` or
`output/paper/extended_abstract.tex`. Claude owns the deck (`output/presentation/`), and
records paper-affecting decisions as an apply-to-the-paper sheet.

## File & output naming conventions (standing rule)

Names must be self-explanatory: reading a script or output filename should tell you
*what dataset/purpose it is* before *how it's formatted*. Agreed with Nara 2026-07-01.

**Scripts & folders**
- Each folder is one pipeline stage: `01_download` → `02_build` → `03_estimation`
  → `04_analysis`. The numeric prefix encodes **run/dependency order only**, never a
  category; no two scripts in a folder share a number; no letter suffixes (`06b`) —
  give it a real slot. **One exception:** a letter suffix marks a *parallel twin* of
  the same-numbered main step — `b` = the legislative counterpart of the executive
  main, `c` = a patch/augment that must run right after it. So `01_assemble_design`
  (executive) / `01b_assemble_legislative_design`, and `02_iv_main` /
  `02b_iv_legislative`, are the *only* sanctioned suffixes. The `c` form is
  `exploration/03_estimation/01c_patch_family_ivs.py` — it patches the same design
  `01` writes, so it keeps the `01c` name, but it moved out of `code/` with its only
  consumer (`03_family_iv.R`). A suffix used for anything other than a twin/patch of
  the same step is still forbidden.
- Name scripts by **purpose**, not by file format. "figures" is not a purpose —
  split by what they show (`02_descriptive_figures.R` vs `03_result_figures.R`).
  **Glue** closely-related small scripts into one file with a `main()` dispatching
  named functions. **Drop dead scripts on sight** — a script is dead only if nothing
  consumes its outputs (not merely absent from `run_all.py`; robustness scripts feed
  the deck).
- **A script stays in `code/` only if it produces a paper input or result.** Three
  tests, any one sufficient: a document `\input`s/`\includegraphics`es one of its
  outputs; `04_analysis/06_abstract_macros.py` reads one of its CSVs; or it writes a
  `data/` artifact that a passing script reads. Scripts that fail all three but are
  worth keeping go to `exploration/<stage>/` — same depth, so root resolution is
  unchanged — never deleted. Verification gates (`00_verify_*`) are exempt as
  pipeline infrastructure. Run `python code/utils/audit_pipeline.py` to re-check.
- **Download scripts are named by the dataset they pull** (drop the redundant
  `download_` verb — the folder already says it): `01_lawsuits`, `02_candidates`,
  `03_historical_elections`, `04_votes`, `05_municipal_characteristics`,
  `06_municipality_crosswalk`.

**Entity threading (download → build → results dataset).** Four canonical entity
tokens thread the whole pipeline so `grep <token> code/ data/` traces a dataset's
full lineage. Every script and clean/estimation dataset leads with its token:
- `lawsuit` → the instrument: `01_lawsuits.py` → `00_verify_lawsuits`,
  `01_lawsuit_panel`, `02_shift_share_design` → `zona_lawsuit_panel.csv`,
  `municipality_bartik_components.csv` (`bartik` is the accepted derived-instrument token).
- `candidate` → `02_candidates.py` (+`03_historical_elections`) → `04_candidate_history`
  → `office_candidate_outcomes_panel.csv`, `candidate_experience_panel.csv`.
- `vote`/`voter` → `04_votes.py` → `03_vote_outcomes`, `05_turnout_ballot_outcomes`,
  `06_turnout_profile_panel`, `07_turnout_profile_outcomes` →
  `office_vote_outcomes_panel.csv`, `*_vote_shift_share_design.csv`.
- `municipal` → `05_municipal_characteristics.R` + `06_municipality_crosswalk.R` →
  `08_electoral_controls_2016`, `09_municipal_covariates` → `municipal_covariates.csv`.

Existing clean/estimation `.csv` files already carry these tokens and are **not
renamed** (every reader would have to change); only *new* datasets must conform.

**Output filenames — topic-first `<domain>_<specific>[_<variant>]`.** The name says
*what it shows* before *how it's drawn*; chart-type (`coefplot`/`forest`/`map`/
`histogram`/`binscatter`) is a **suffix**, used only to disambiguate. One shared
domain vocabulary for figures **and** tables: `instrument`, `litigation`, `sample`,
`firststage`, `representation`, `entrant`, `competition`, `concentration`, `turnout`,
`voterbehavior`, `pretrend`, `placebo`, plus `executive_iv`/`legislative_iv`
subsample prefixes for regression tables. Canonical figure names:
`instrument_histogram`, `instrument_map`, `sample_map`, `firststage_linear`,
`representation_coefplot`, `entrant_coefplot`, `turnout_coefplot`,
`candidate_supply_coefplot`, `legislative_coefplot`, `heterogeneity_seat_coefplot`,
`gender_consolidation_coefplot`, `pretrend_coefplot`, `litigation_timing_shape`.

**Figures carry no baked-in titles/footnotes/captions** — those live on the Beamer
frame. Producing scripts source `code/utils/figure_style.R`, whose `theme_report()`
blanks `plot.title`/`subtitle`/`caption`, and use the shared `PAL` palette (which
mirrors the deck's `myblue`/`myred`/`mygreen`/`mygray`/`mylight`) so figure colors
match the slides. Never hard-code hex colors in a figure script.

## Regression-table conventions (standing rule)

Every regression table that reaches a slide or the paper MUST:
1. **Name outcomes in human-readable form**, never the raw variable name.
   `label_mods()` names each fit from `OUTCOME_LABELS`
   (`code/03_estimation/02_iv_main.R`) or `LEG_OUTCOME_LABELS`
   (`02b_iv_legislative.R`), and the table writer prints those names in the bold
   `Dep.\ var.:` header row. The tables print no FE or cluster rows, so no raw
   column names can leak there.
2. **Report the dependent-variable mean.** In `02_iv_main.R` the fit carries
   `attr(fit, "mean_delta")` (mean of the actual LHS: the 2024 level under ANCOVA,
   the delta under FD) and, for ANCOVA, `attr(fit, "mean_2016")`; `iv_etable()`
   prints them as the `2024 Mean` and `2016 Mean` rows. `leg_iv_table()` recovers
   the mean from the fit (rule 5).
3. **Not show a misleading first-stage F.** Suppress fixest's homoskedastic
   `ivf` in outcome tables; the dedicated first-stage table (`firststage.tex`)
   carries the cluster-robust F. The tF critical value comes from the regression
   CSVs (`tF_cv`) and reaches the deck as a macro (`\tFcv`), not a table row.
4. **Use the hand-built house style with a HORIZONTAL shaded band** (the
   `judicial_bias` SGD-table aesthetic; Nara reversed the brief 2026-06-29
   column-highlight back to a row band on 2026-06-30: "i prefer the horizontal
   shaded area", applied to ALL hand-built tables). Each outcome table is emitted
   by `iv_etable()` (in `02_iv_main.R`) / `leg_iv_table()` (in
   `02b_iv_legislative.R`) writing LaTeX **directly**. No script calls `etable()`;
   the `ETABLE_DICT`/`ETABLE_SIGNIF`/`write_etable_frag`/`etab_base` (`etab_leg`)
   scaffolding in both scripts is defined but unused. The layout:
   `booktabs` double rules (`\toprule\toprule` … `\bottomrule\bottomrule`), bold
   outcome headers (`Dep.\ var.: & \textbf{...}`), a `\midrule`, then the
   **Judicialization** coefficient row, then the `\textcolor{mygray}{(se)}` row
   beneath, a `\midrule`, then `$N$` + the dependent-variable mean(s). **No**
   Variables/Fixed-effects/Fit-statistics dividers — the uniform `State (UF)` FE
   and the state-clustered SE are stated in the slide caption instead.
   **Shade the Judicialization ROW, not a column** (matches `judicial_bias`: the
   finding IS the coefficient). Put `\rowcolor{mylight}` on its own line
   immediately before the coef row AND again before the SE row — both lines of the
   band must be shaded. No `highlight` argument; the band is automatic. The
   hand-built ballot and seat tables band their headline row too. The ballot
   result is two separate single-panel files written by `write_ballot()`, which
   calls the nested `panel_block()`: `executive_iv_ballot_mayoral.tex`
   (`band = TRUE`, main deck) and `executive_iv_ballot_council.tex`
   (`band = FALSE`, appendix). The office×open-seat table
   (`executive_iv_voter_behavior_office_openseat.tex`) is TRANSPOSED (rows = office×seat subsamples, cols =
   blank/null/valid + N) and bands the mayoral-Contested row.
   **No "+" on positive coefficients** (absence of a sign already reads positive;
   Nara 2026-06-30) — every coef cell uses `%.3f`, never `%+.3f`. **SE stacks on
   the line BELOW the coefficient**, never inline on the side (Nara 2026-06-30):
   in the transposed office×open-seat table each subsample is two lines (coef row +
   gray-SE row beneath), both shaded when banded. Its frame height-binds it so the
   mean rows and footnote fit.
5. **Mean row(s) sit in the footer.** Executive ANCOVA tables show `2024 Mean`
   and `2016 Mean`; FD/legislative tables show a single `Mean of dep.\ var.`
   (recovered as `mean(fitted(m)+resid(m))` when no `mean_delta` attr exists).
   Always show `$N$` (formatted with `formatC(..., big.mark = ",")`). The compulsory-
   turnout table is an appendix **placebo** (`app:turnoutplacebo`), not a main result.
6. **Standard significance stars:** `*** = 1%, ** = 5%, * = 10%` (`hb_star()`
   helper, defined in both scripts). Applies to **both** generators. **Do NOT print a stars legend**
   in the slide captions ("Stars: ***/**/* at 1/5/10%") — the convention is
   universally understood, so the legend was dropped (Nara 2026-06-30); the stars
   stay on the cells, computed from the 2SLS cluster-robust p-value. (Caveat noted
   2026-06-30: those stars are keyed to the 2SLS t-test, not the headline AR-WCR
   inference — Nara chose to keep them as the standard mark anyway.)

The colors `mylight` (pale blue band) and `mygray` (SE) are defined in the deck
preamble (`output/presentation/slides_preamble.tex`); `booktabs` + `colortbl` are loaded there.
Frames wrap each fragment in `\resizebox`: width-bound (`\resizebox{\linewidth}{!}`)
by default, height-bound (`\resizebox{!}{<factor>\textheight}`) for tall tables such
as the two ballot tables and the two seat tables. The factor is set on each frame.
`nonadversarial_robustness.tex` keeps its own bespoke 4-spec booktabs comparison
layout.

## Quick data reference

`DATA_GUIDE.md` is the full reference: raw sources, every clean and estimation dataset,
and the output CSV headers. The essentials:

- **Raw (`data/raw/`, 26 GB, gitignored).** Most TSE sources sit there as extracted
  folders, some also as zips. The instrument comes from the SIG municipality-resolved
  export (`processos_eleitorais.csv.zip` for 2020; `processos_eleitorais_2024.csv`, which
  is a zip despite its extension, for 2024), read by `02_build/02_shift_share_design.py`.
  The `decisoes_*` and `recursos_*` zips that `01_download/01_lawsuits.py` targets and
  `00_verify_raw_data.py` requires are not on disk.
- **Clean (`data/clean/`).**
  - `municipality_bartik_components.csv`: municipality × subject at the 2020 baseline
    (shares, leave-own-state-out shifts, components).
  - `office_candidate_outcomes_panel.csv`, `office_vote_outcomes_panel.csv`:
    municipality × office × year outcomes.
  - `electoral_admin_outcomes.csv`: registered voters, turnout, blank/null/valid rates
    (mayoral, plus `*_vereador` ballot rates). Registered voters and turnout by sex,
    education, age band, race and compulsory status are in
    `comparecimento_disaggregated.csv` (long); `voter_disaggregated_outcomes.csv` carries
    the wide facultative/compulsory, education and sex turnout columns.
  - `municipal_covariates.csv`: Census 2010 controls, the 2016 electoral baseline, the
    2020 experience baseline.
  - `zona_lawsuit_panel.csv`: zone × class × subject × year counts of pre-election cases,
    built by `01_lawsuit_panel.py` from the `processo_eleitoral_YYYY` dockets. It is not
    the instrument source; only `04_analysis/08_lawsuit_composition_sp.py` reads it.
  - `zona_eleitoral_lookup.csv`: `SG_UF`, `zona`, `nome_zona` only. No script reads or
    writes it.
- **Estimation (`data/estimation/`).**
  - `executive_margin_design.csv`: 5,571 rows, 346 columns; estimation N = 5,560.
    Instruments `bartik_iv_2020_2024` (headline), `placebo_bartik_iv_2020_2024`,
    `bartik_iv_no_rrc`; endogenous `delta_log1p_competition_lawsuits_2024_2020`;
    `cluster_id` is the state (`SG_UF`). The family IVs and `share_{code}_2020` topic
    shares are not in it; `exploration/03_estimation/01c_patch_family_ivs.py` adds them in
    place for the exploration lane.
  - `legislative_design.csv`: 5,560 rows, 98 columns; the same headline instrument,
    council outcomes.
- **Output CSVs (`output/tables/regressions/`, `descriptives/`, gitignored).**
  `executive_margin_iv_fixest.csv` and `legislative_iv_fixest.csv` (all specs × outcomes,
  with the cluster-robust `first_stage_F_lookup` and the tF columns), the matching
  `*_first_stage_fixest.csv`, `wild_bootstrap_ar.csv` (AR-WCR), `exposure_robust_se.csv`
  (BHJ/AKM), `multiplicity_adjusted.csv`, `rotemberg_weights.csv`,
  `gps_balance_tests.csv`, `shift_descriptives.csv`. The 35 fragments in
  `output/tables/tex/` are tracked and are what the deck `\input`s.
- **Not in the project.** A national 2016 lawsuit panel (the only pre-2020 snapshot is
  the TRE-SP SAC-JE file, state-level shares, used by `08_lawsuit_composition_sp.py`);
  case decisions and appeals (the `decisoes`/`recursos` files are not on disk); TRE judge
  composition.

## Environment
- Python: `C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe`
- R: `C:\Program Files\R\R-4.6.0\bin\Rscript.exe`. `run_all.py` calls bare `Rscript`, so
  that `bin` directory must be on `PATH`; on this machine it resolves in both Git Bash and
  PowerShell.
- Shell: PowerShell, Windows 11
- Working dir: `c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization`
