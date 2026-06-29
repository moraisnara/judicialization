# CLAUDE.md — judicialization repo

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
4. **Drop the fixed-effects row when uniform.** Every table is state-(UF) FE, so
   pass `drop.section = "fixef"` and state the FE in the slide caption.
5. **Drop the observations row when N is constant** across columns (`fitstat =
   if (same_n) NA else ~ n`); report the constant N in the caption. Keep the N
   row only where it varies (e.g. open vs contested subsamples).
6. **Standard significance stars:** `*** = 1%, ** = 5%, * = 10%` (`ETABLE_SIGNIF
   <- c("***"=.01,"**"=.05,"*"=.10)`).

Note: `write_etable_frag()` keeps only the `tabular` block and the report wraps
fragments in `\resizebox{...}{!}{\input{...}}`, so etable `notes` are stripped —
FE / constant-N facts belong in the frame caption, not the table note.

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
