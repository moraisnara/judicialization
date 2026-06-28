# CLAUDE.md — judicialization repo

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

### Current design (act-based shift-share, 2026-06-26)
Instrument `bartik_iv_act`, treatment `delta_log1p_act_lawsuits`, lives in
`data/estimation/act_design.csv`. Cluster = **STATE** (`cluster_id`, ~27 UFs).
First-stage **F ≈ 25.5**, K_eff ≈ 6.8. Lawsuit source = SIG TSE municipality
microdata. Framing = voters AND candidates broadly (no female-candidate headline).
The old substance-family / zona / female-headline lineage is retired. See
`docs/STATE_OF_THE_ART.md` (authoritative) and `code/spec_config.json`.

### Clean data (`data/clean/`) — key files

| File | Unit | Key columns |
|------|------|-------------|
| `sig_lawsuits_muni_zona_classe_assunto.csv` (+ `_classe`, `_assunto` siblings) | year × UF × zona × muni × class × subject | `id_municipio_tse`, `pair_id`, `n_proc` — SIG lawsuit panel (replaces `zona_lawsuit_panel.csv`) |
| `act_family_crosswalk.csv` | class×subject `pair_id` | `fam_act10` (10 act families), `kept` — act taxonomy |
| `municipality_act_components.csv` | municipality × act family | `family`, `share2020`, `shift_leavestate`, `bartik_component`, `delta_log1p_family` — instrument decomposition; single source for Rotemberg/shift/balance |
| `sig_family_crosswalk.csv` | class×subject `pair_id` | substance crosswalk (`fam_subst13`, `fam_theme9`, …) — **descriptives only** |
| `office_candidate_outcomes_panel.csv` | municipality × office × year | `female_share`, `nonwhite_share`, `higher_education_share`, `mean_age`, `elected_*_share`, `new_candidate_share`, `incumbent_candidate_share`, `incumbent_reelected_share`, `total_candidates`, `party_count` |
| `executive_vote_shift_share_design.csv` | municipality (wide, 2020+2024) | Composition pivoted to `_2020`/`_2024` + `female_vote_share_*`, `winner_is_female_*`, `delta_*` |
| `executive_shift_share_design.csv` | municipality (wide) | Candidate composition wide, no vote shares |
| `legislative_shift_share_design.csv` | municipality (wide) | Same structure as executive, vereadores |
| `electoral_admin_outcomes.csv` | municipality × year | `registered_voters`, `turnout_rate`, `blank_rate`, `null_rate`, `valid_vote_rate` — **no voter gender breakdown** |
| `municipal_covariates.csv` | municipality | Census 2010 controls + 2016 electoral baseline |
| `candidate_experience_panel.csv` | municipality × year | Cross-cycle history for new/serial/returning typology |
| `zona_eleitoral_lookup.csv` | zona | TSE zona → municipality crosswalk |

> Retired (history only): `zona_lawsuit_panel.csv`,
> `municipality_bartik_components.csv`, `municipality_family_components.csv`.

### Estimation data (`data/estimation/`)

| File | Content |
|------|---------|
| `executive_margin_design.csv` | Instrument-FREE base: executive outcomes + 5 controls + `cluster_id` (state). Built by `01_assemble_design.py`. No instrument columns. |
| `act_design.csv` | Base + `bartik_iv_act` + `delta_log1p_act_lawsuits`. Built by `01d_act_family_ivs.py`. **Headline 2SLS reads this** (`02c_act_iv.R`). |
| `legislative_design.csv` | Legislative outcomes. STILL on the retired substance instrument (`bartik_iv_fine7`/`bartik_iv_2020_2024` etc.) — **not yet ported to act**. |

### Output tables (`output/tables/`)

| Path | Content |
|------|---------|
| `regressions/act_iv_results.csv` | Headline act-instrument 2SLS, all outcomes |
| `regressions/act_first_stage_fixest.csv` | Act first stage (F ≈ 25.5, state-clustered) |
| `regressions/voter_behavior_iv.csv` | Voter-behavior outcomes on act instrument |
| `regressions/voter_turnout_iv.csv` | Turnout IV |
| `regressions/voter_office_spoilage_iv.csv` | Blank/null spoilage IV |
| `regressions/voter_rolloff_placebo_iv.csv` | Roll-off placebo |
| `regressions/voter_first_stage.csv` | Voter-lane first stage |
| `descriptives/rotemberg_weights.csv` | Rotemberg alpha, F_k per act family |
| `descriptives/gps_balance_tests.csv` | Share balance tests (covariate + pre-trend) |
| `descriptives/shift_descriptives.csv` | BHJ shift table |

> Retired (old female-headline design, not yet ported):
> `regressions/executive_margin_iv_fixest.csv`, `family_iv_results.csv`,
> `legislative_iv_fixest.csv`, `liml_comparison.csv`, `exposure_robust_se.csv`,
> and the `tables/tex/*` fragments.

### What is NOT in this project
- Voter registration by gender (needs TSE *perfil do eleitorado* — separate download)
- 2016 lawsuit panel (SIG has no 2016 — no pre-period placebo)
- TRE judge composition data

## Environment
- Python: `C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe`
- R: `C:\Program Files\R\R-4.6.0\bin\Rscript.exe` (not on PATH, call explicitly)
- Shell: PowerShell, Windows 11
- Working dir: `c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization`
