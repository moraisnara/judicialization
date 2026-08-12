# CLAUDE.md — judicialization repo

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
  (executive) / `01b_assemble_legislative_design` / `01c_patch_family_ivs`, and
  `02_iv_main` / `02b_iv_legislative`, are the *only* sanctioned suffixes. A suffix
  used for anything other than a twin/patch of the same step is still forbidden.
- Name scripts by **purpose**, not by file format. "figures" is not a purpose —
  split by what they show (`02_descriptive_figures.R` vs `03_result_figures.R`).
  **Glue** closely-related small scripts into one file with a `main()` dispatching
  named functions. **Drop dead scripts on sight** — a script is dead only if nothing
  consumes its outputs (not merely absent from `run_all.py`; robustness scripts feed
  the deck).
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
`instrument_histogram`, `instrument_map`, `sample_map`, `firststage_binscatter`,
`firststage_linear`, `representation_coefplot`, `entrant_coefplot`, `turnout_coefplot`,
`voterbehavior_seat_coefplot`, `pretrend_coefplot`, `litigation_timing_{count,rate,share}`.

**Figures carry no baked-in titles/footnotes/captions** — those live on the Beamer
frame. Producing scripts source `code/utils/figure_style.R`, whose `theme_report()`
blanks `plot.title`/`subtitle`/`caption`, and use the shared `PAL` palette (which
mirrors the deck's `myblue`/`myred`/`mygreen`/`mygray`/`mylight`) so figure colors
match the slides. Never hard-code hex colors in a figure script.

## Regression-table conventions (standing rule)

Every regression table that reaches a slide or the paper MUST:
1. **Name outcomes in human-readable form**, never the raw variable name. In
   `fixest::etable()` this is done by merging an outcome-label vector into the
   `dict` (the dict translates the dependent-variable header row, not just
   coefficient names). See `OUTCOME_LABELS` in `code/03_estimation/02_iv_main.R`.
   Relabel FE rows and the cluster note via the same `dict` (e.g. `SG_UF` →
   "State (UF)", `cluster_id` → "state") so no raw column names leak.
2. **Report the dependent-variable mean** (a "Mean of dep. var." row). Attach
   `attr(fit, "mean_delta") <- mean(samp[[y]], na.rm = TRUE)` at fit time and
   emit it via `etable(..., extralines = ...)`. Pattern lives in the
   `iv_etable()` wrapper in `02_iv_main.R`.
3. **Not show a misleading first-stage F.** Suppress fixest's homoskedastic
   `ivf` in outcome tables; the dedicated first-stage table carries the
   cluster-robust F and tF critical value.
4. **Use the hand-built house style with a HORIZONTAL shaded band** (the
   `judicial_bias` SGD-table aesthetic; Nara reversed the brief 2026-06-29
   column-highlight back to a row band on 2026-06-30: "i prefer the horizontal
   shaded area", applied to ALL hand-built tables). Each outcome table is emitted
   by `iv_etable()` (in `02_iv_main.R`) / `leg_iv_table()` (in
   `02b_iv_legislative.R`) writing LaTeX **directly** — NOT via `etable()`:
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
   hand-built panel tables band their headline row too: the ballot two-panel
   shades Panel A (mayoral) via the `band=TRUE` arg of `panel_block()`; the
   office×open-seat table is TRANSPOSED (rows = office×seat subsamples, cols =
   blank/null/valid + N) and bands the mayoral-Contested row.
   **No "+" on positive coefficients** (absence of a sign already reads positive;
   Nara 2026-06-30) — every coef cell uses `%.3f`, never `%+.3f`. **SE stacks on
   the line BELOW the coefficient**, never inline on the side (Nara 2026-06-30):
   in the transposed office×open-seat table each subsample is two lines (coef row +
   gray-SE row beneath), both shaded when banded. That table is then
   height-bound (`\resizebox{!}{0.36\textheight}`) so the mean rows + footnote fit.
5. **Mean row(s) sit in the footer.** Executive ANCOVA tables show `2024 Mean`
   and `2016 Mean`; FD/legislative tables show a single `Mean of dep.\ var.`
   (recovered as `mean(fitted(m)+resid(m))` when no `mean_delta` attr exists).
   Always show `$N$` (formatted with `formatC(..., big.mark = ",")`). The compulsory-
   turnout table is an appendix **placebo** (`app:turnoutplacebo`), not a main result.
6. **Standard significance stars:** `*** = 1%, ** = 5%, * = 10%` (`hb_star()`
   helper; `ETABLE_SIGNIF <- c("***"=.01,"**"=.05,"*"=.10)` for any residual
   etable use). Applies to **both** generators. **Do NOT print a stars legend**
   in the slide captions ("Stars: ***/**/* at 1/5/10%") — the convention is
   universally understood, so the legend was dropped (Nara 2026-06-30); the stars
   stay on the cells, computed from the 2SLS cluster-robust p-value. (Caveat noted
   2026-06-30: those stars are keyed to the 2SLS t-test, not the headline AR-WCR
   inference — Nara chose to keep them as the standard mark anyway.)

The colors `mylight` (pale blue band) and `mygray` (SE) are defined in the deck
preamble (`slides_report.tex`); `booktabs` + `colortbl` are loaded there. The
report wraps each fragment in `\resizebox{\linewidth}{!}{\input{...}}`.

Tall two-panel tables are height-constrained
(`\resizebox{!}{0.24\textheight}{...}`) so they do not overflow the frame; the
office×open-seat table stays width-bound (`\resizebox{\linewidth}{!}`).
The multi-panel hand-built tables (`executive_iv_voter_behavior_office_openseat.tex`,
the ballot two-panel) shade their headline ROW with `\rowcolor{mylight}` to match
the main mold. `nonadversarial_robustness.tex` keeps its own bespoke 4-spec
booktabs comparison layout.

## Quick data reference

### Raw data (`data/raw/`)
All zipped TSE files. Do not unzip manually — scripts handle this.

| File | Content |
|------|---------|
| `consulta_cand_2020.zip` / `..._2024.zip` | TSE candidate registry. Cols: `DS_GENERO`, `DS_COR_RACA`, `DS_GRAU_INSTRUCAO`, `DS_ESTADO_CIVIL`, `NR_IDADE_DATA_POSSE`, office codes, party, municipality IBGE code |
| `processo_eleitoral_2020.zip` / `..._2024.zip` | Lawsuit records: class, subject code (`CD_ASSUNTO`), filing date, instance |
| `processos_eleitorais_assuntos_*.zip` | Subject-level panel (2018–2024) |
| `processos_eleitorais_partes_2020.zip` | Parties to each lawsuit (petitioner / respondent) |
| `decisoes_2020.zip` / `..._2024.zip` | Decisions per lawsuit |
| `recursos_2020.zip` / `..._2024.zip` | Appeals |
| `bd_municipio_tse_ibge.csv` | TSE↔IBGE municipality crosswalk |

### Clean data (`data/clean/`) — key files

| File | Unit | Key columns |
|------|------|-------------|
| `office_candidate_outcomes_panel.csv` | municipality × office × year | `female_share`, `nonwhite_share`, `higher_education_share`, `mean_age`, `elected_female_share`, `elected_nonwhite_share`, `elected_higher_education_share`, `elected_mean_age`, `new_candidate_share`, `incumbent_candidate_share`, `incumbent_reelected_share`, `total_candidates`, `party_count` |
| `executive_vote_shift_share_design.csv` | municipality (wide, 2020+2024) | All above pivoted to `_2020`/`_2024` + `female_vote_share_*`, `nonwhite_vote_share_*`, `winner_is_female_*`, `delta_*` |
| `executive_shift_share_design.csv` | municipality (wide) | Candidate composition wide, no vote shares |
| `legislative_shift_share_design.csv` | municipality (wide) | Same structure as executive, vereadores |
| `electoral_admin_outcomes.csv` | municipality × year | `registered_voters`, `turnout_rate`, `blank_rate`, `null_rate`, `valid_vote_rate` — **no voter gender breakdown** |
| `zona_lawsuit_panel.csv` | zona × year × subject | Lawsuit counts by topic, raw panel |
| `municipality_bartik_components.csv` | municipality × subject | Shares and shifts for Bartik IV |
| `municipal_covariates.csv` | municipality | Census 2010 controls + 2016 electoral baseline |
| `candidate_experience_panel.csv` | candidate × cycle | Cross-cycle history for new/serial/returning typology |
| `zona_eleitoral_lookup.csv` | zona | TSE zona → municipality crosswalk |

### Estimation data (`data/estimation/`)

| File | Content |
|------|---------|
| `executive_margin_design.csv` | Final analysis panel: 5,560 municipalities, ~177 cols. Instrument cols: `bartik_iv_2020_2024`, `bartik_iv_no_rrc_drap`, `bartik_iv_{family}`. Endogenous: `delta_log1p_*`. All IV outcomes. |
| `legislative_design.csv` | Same structure, legislative outcomes, same instrument from executive design |

### Output tables (`output/tables/`)

| Path | Content |
|------|---------|
| `regressions/executive_margin_iv_fixest.csv` | IV results: all specs × all outcomes, with tF columns |
| `regressions/legislative_iv_fixest.csv` | Legislative IV results |
| `regressions/legislative_first_stage_fixest.csv` | Legislative first stages |
| `regressions/family_iv_results.csv` | Family-split IV (4 families × outcomes) |
| `regressions/liml_comparison.csv` | LIML vs 2SLS (K=1, so 2SLS ≡ LIML; divergence should be 0) |
| `tables/tex/*.tex` | LaTeX fragments for presentation (generated by `02_iv_main.R` and `02b_iv_legislative.R` via `etable()`) |
| `regressions/exposure_robust_se.csv` | BHJ/AKM SEs |
| `descriptives/rotemberg_weights.csv` | Rotemberg alpha, F_k per topic |
| `descriptives/gps_balance_tests.csv` | Share balance tests (covariate + pre-trend) |
| `descriptives/shift_descriptives.csv` | BHJ shift table |

### What is NOT in this project
- Voter registration by gender (needs TSE *perfil do eleitorado* — separate download)
- 2016 lawsuit panel (needed for pre-period placebo)
- TRE judge composition data

## Environment
- Python: `C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe`
- R: `C:\Program Files\R\R-4.6.0\bin\Rscript.exe` (not on PATH, call explicitly)
- Shell: PowerShell, Windows 11
- Working dir: `c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization`
