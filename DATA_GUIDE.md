# Data Guide — Judicialization and Electoral Competition in Brazil

Quick reference for all datasets in this project. Use this to check whether a
variable exists and which file to load — without reading the actual data.

Join keys across files: `state` (2-letter UF) + `municipality_id_tse` (5-digit TSE
integer, stored as string with leading zero e.g. `"01007"`). IBGE codes are in
`municipality_id_ibge` / `bd_municipio_tse_ibge.csv`.

---

## 1. Raw Data (`data/raw/`)

| File | Format | Content |
|------|--------|---------|
| `consulta_cand_2020.zip` / `..._2024.zip` | TSE zip | Candidate registry: `DS_GENERO`, `DS_COR_RACA`, `DS_GRAU_INSTRUCAO`, `DS_ESTADO_CIVIL`, `NR_IDADE_DATA_POSSE`, office codes, party, IBGE municipality code |
| `processo_eleitoral_2020.zip` / `..._2024.zip` | TSE zip | Lawsuit records: class code, subject code (`CD_ASSUNTO`), filing date, instance |
| `processos_eleitorais_assuntos_*.zip` | TSE zip | Subject-level panel 2018–2024 |
| `processos_eleitorais_partes_2020.zip` | TSE zip | Parties to each lawsuit (petitioner / respondent) |
| `decisoes_2020.zip` / `..._2024.zip` | TSE zip | Decisions per lawsuit |
| `recursos_2020.zip` / `..._2024.zip` | TSE zip | Appeals |
| `bd_municipio_tse_ibge.csv` | CSV | Crosswalk: `id_municipio` (7-digit IBGE) ↔ `id_municipio_tse` (TSE code) |
| `lista-zonas-municipios-10-07-24.csv` | CSV (sep=`;`) | TSE official zone→municipality list: `UF`, `ZONA`, `COD_LOCALIDADE` (TSE muni code), `NOM_LOCALIDADE` |

---

## 2. Clean / Intermediate Data (`data/clean/`)

### 2a. Lawsuit panel
**`zona_lawsuit_panel.csv`** — unit: zona × year × subject code

| Column | Description |
|--------|-------------|
| `election_year` | 2020 or 2024 |
| `state` | UF abbreviation |
| `electoral_zone` | TSE zone number (integer) |
| `municipality_id_tse` | TSE municipality code |
| `municipality_name` | Municipality name |
| `n_municipalities_in_zone` | How many municipalities share this zone |
| `case_class_code` / `case_class_name` | Case class (e.g. 11532 = RRC, 11534 = AIRC) |
| `main_subject_code` / `main_subject_name` | Subject code (e.g. 11616, 11617) |
| `n_lawsuits` | Count of lawsuits in cell |

### 2b. Bartik instrument components
**`municipality_bartik_components.csv`** — unit: municipality × subject × year

| Column | Description |
|--------|-------------|
| `election_year` | 2020 or 2024 |
| `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `main_subject_code` / `main_subject_name` | Subject code |
| `topic_family` | Family: `information_environment`, `campaign_conduct`, `eligibility_ballot_access`, `abuse_misuse_office` |
| `n_lawsuits` | Raw count |
| `baseline_share_2020` | Municipality's share of topic $k$ in 2020 (sums to 1 per muni) |
| `leave_uf_out_2020` / `leave_uf_out_2024` | State total leaving this muni out |
| `shock_log_growth_2020_2024` | LOO log growth of topic $k$ in state |
| `bartik_component` | `baseline_share_2020 × shock_log_growth` |

### 2c. Candidate and electoral outcomes panel
**`office_candidate_outcomes_panel.csv`** — unit: office × year × municipality

| Column | Description |
|--------|-------------|
| `office_group` | `executive` or `legislative` |
| `election_year` | 2020 or 2024 |
| `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `total_candidates`, `elected_candidates` | Counts |
| `party_count`, `coalition_count` | Party/coalition counts |
| `female_share`, `nonwhite_share`, `higher_education_share`, `married_share` | Candidate pool shares |
| `mean_age`, `sd_age` | Age distribution |
| `elected_female_share`, `elected_nonwhite_share`, `elected_higher_education_share`, `elected_mean_age` | Elected pool |
| `new_candidate_count`, `incumbent_candidate_count`, `incumbent_reelected_count` | Entry/incumbency counts |
| `new_candidate_share`, `incumbent_candidate_share`, `incumbent_reelected_share` | Entry/incumbency shares |
| `candidate_hhi_party`, `effective_party_count_candidates` | Party competition among candidates |

### 2d. Wide shift-share designs (pre-estimation)

**`executive_shift_share_design.csv`** — municipality wide, candidate composition only (no vote shares)
**`executive_vote_shift_share_design.csv`** — municipality wide, adds vote-share outcomes

Both have the same columns pivoted to `_2020` / `_2024` suffixes plus `delta_*` first-differences.
Vote-share columns (only in `executive_vote_shift_share_design.csv`):

| Column pattern | Description |
|----------------|-------------|
| `female_vote_share_{year}` | Vote share received by female candidates |
| `nonwhite_vote_share_{year}` | Vote share received by nonwhite candidates |
| `higher_education_vote_share_{year}` | Vote share by higher-ed candidates |
| `new_candidate_vote_share_{year}` | Vote share by new entrants (year-relative: did not contest this seat in the prior cycle) |
| `incumbent_candidate_vote_share_{year}` | Vote share by incumbents (won this seat in the prior cycle) |
| `winner_vote_share_{year}` | First-place vote share |
| `runnerup_vote_share_{year}` | Second-place vote share |
| `margin_top1_top2_{year}` | Margin (winner − runner-up) |
| `winner_majority_{year}` | Indicator: winner got > 50% |
| `winner_is_female_{year}` | Winner gender indicator |
| `winner_is_new_{year}` | Winner was a new entrant (did not contest this seat in the prior cycle) |
| `effective_n_candidates_vote_{year}` | ENP by votes |
| `vote_hhi_candidate_{year}` / `vote_hhi_party_{year}` | Vote HHI |

**`legislative_shift_share_design.csv`** — same structure, city council (vereador) candidates (no vote-share outcomes)

### 2e. Electoral administration (voter-side)
**`electoral_admin_outcomes.csv`** — unit: municipality × year

| Column | Description |
|--------|-------------|
| `election_year` | 2020 or 2024 |
| `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `registered_voters` | Total registered voters |
| `turnout_count`, `abstentions_count` | Counts |
| `total_votes`, `valid_votes`, `blank_votes`, `null_votes` | Vote type counts |
| `turnout_rate`, `abstention_rate`, `null_rate`, `blank_rate`, `valid_vote_rate` | Rates (denominator = registered voters) |

**Not available here:** voter breakdown by gender (requires TSE *perfil do eleitorado*).

### 2f. Municipal covariates
**`municipal_covariates.csv`** — unit: municipality (cross-section, latest values)

| Column | Description |
|--------|-------------|
| `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `municipality_id_ibge`, `state_abbrev_ibge` | IBGE codes |
| `pop_2010`, `urban_share_2010`, `income_pc_2010`, `higher_educ_share_2010` | Census 2010 |
| `n_candidates_2016`, `top1_share_2016`, `margin_2016`, `hhi_2016`, `enp_2016` | 2016 mayoral baseline |
| `winner_party_2016`, `winner_candidate_id_2016`, `winner_name_2016` | 2016 winner info |
| `share_first_time_candidates_2020`, `mean_prior_candidacies_2020` | Experience baseline |
| `share_prior_winners_2020`, `share_career_politicians_2020` | Career type shares |
| `share_serial_challenger_2020`, `share_cross_cycle_returner_2020` | Entry typology |
| `open_seat_2020` | 1 if 2020 winner was already in 2nd term (so 2024 is open seat) |
| `turnout_rate_2020`, `abstention_rate_2020`, `blank_rate_2020`, `null_rate_2020` | 2020 voter behavior |
| `incumbent_ran_2024`, `incumbent_won_2024`, `party_switch_2024` | 2024 incumbent outcomes |

### 2g. Candidate experience panel
**`candidate_experience_panel.csv`** — unit: municipality × year

| Column | Description |
|--------|-------------|
| `election_year`, `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `share_first_time_candidates` | Share with no prior mayoral candidacy in 2012–prior |
| `mean_prior_candidacies` | Average prior runs |
| `share_prior_winners` | Share who won before |
| `share_career_politicians` | Share with prior legislative/exec experience |
| `share_serial_challenger` | Ran in same muni in the previous cycle |
| `share_cross_cycle_returner` | Has prior history but sat out previous cycle |
| `n_candidates`, `open_seat` | Counts / seat status |

### 2h. Lookups and crosswalks
**`zona_eleitoral_lookup.csv`** — columns: `SG_UF`, `zona` (integer), `nome_zona`

---

## 3. Estimation-Ready Datasets (`data/estimation/`)

### `executive_margin_design.csv` — **THE MAIN ANALYSIS FILE**
Unit: municipality. N ≈ 5,560–5,571. ~177 columns.

**Key instrument and treatment columns:**

| Column | Description |
|--------|-------------|
| `bartik_iv_2020_2024` | Main Bartik IV (adversarial filter applied) |
| `bartik_iv_no_rrc` | Broader IV (excludes RRC only, not DRAP) |
| `bartik_iv_information_environment` | Family IV: information environment topics |
| `bartik_iv_campaign_conduct` | Family IV: campaign conduct topics |
| `bartik_iv_eligibility_ballot_access` | Family IV: eligibility/ballot access topics |
| `bartik_iv_abuse_misuse_office` | Family IV: abuse/misuse of office topics |
| `delta_log1p_competition_lawsuits_2024_2020` | Endogenous variable (main) |
| `delta_log1p_lawsuits_no_rrc_2024_2020` | Endogenous for broader IV |
| `delta_log1p_information_environment_2024_2020` | Endogenous for IE family IV |
| `delta_log1p_campaign_conduct_2024_2020` | Endogenous for CC family IV |
| `delta_log1p_eligibility_ballot_access_2024_2020` | Endogenous for EBA family IV |
| `delta_log1p_abuse_misuse_office_2024_2020` | Endogenous for AMO family IV |
| `competition_lawsuits_2020` / `..._2024` | Raw adversarial lawsuit counts |

**Clustering and zone columns:**

| Column | Description |
|--------|-------------|
| `n_zones_in_municipality` | Number of electoral zones in this municipality |
| `principal_zone` | TSE zone number of principal zone |
| `principal_zone_id` | String: `{UF}_{zone_number}` e.g. `"AC_1"` |
| `cluster_id` | Same as `principal_zone_id` — used for SE clustering |

**Controls (7 baseline):**

| Column | Description |
|--------|-------------|
| `log_pop_2010` | Log Census population |
| `urban_share_2010` | Urban population share |
| `log_income_pc_2010` | Log per-capita income |
| `margin_2016` | 2016 electoral margin (pp) |
| `log1p_total_valid_votes_2020` | Log 2020 valid votes |
| `margin_top1_top2_2020` | 2020 margin (winner − runner-up) |
| `log1p_total_candidates_2020` | Log 2020 candidate count |

**Outcome variables (delta = 2024 − 2020):**

Electoral competition:
`delta_winner_vote_share_2024_2020`, `delta_runnerup_vote_share_2024_2020`,
`delta_margin_top1_top2_2024_2020`, `delta_winner_majority_2024_2020`,
`delta_log1p_n_candidates_with_votes_2024_2020`

Voter behavior:
`delta_turnout_rate_2024_2020`, `delta_blank_rate_2024_2020`,
`delta_null_rate_2024_2020`, `delta_valid_vote_rate_2024_2020`

Composition (candidate pool):
`delta_female_share_2024_2020`, `delta_nonwhite_share_2024_2020`,
`delta_higher_education_share_2024_2020`, `delta_mean_age_2024_2020`

Composition (vote-weighted):
`delta_female_vote_share_2024_2020`, `delta_nonwhite_vote_share_2024_2020`,
`delta_winner_is_female_2024_2020`, `delta_winner_is_new_2024_2020`,
`delta_new_candidate_vote_share_2024_2020`, `delta_incumbent_candidate_vote_share_2024_2020`

Entry typology (deltas):
`delta_share_first_time_candidates_2024_2020`,
`delta_share_serial_challenger_2024_2020`,
`delta_share_cross_cycle_returner_2024_2020`

Open seat:
`open_seat_2024` (1 = 2020 winner term-limited; exogenous to 2024 litigation)

Bartik topic shares (for AMV robustness):
`share_11616_2020`, `share_11617_2020`, `share_11662_2020`, `share_11679_2020`

---

### `legislative_design.csv`
Unit: municipality. N = 5,560. Same Bartik IV as executive. City council (vereador) outcomes.

Key columns not in executive design:
`log1p_total_candidates_2020_leg`, `log1p_total_candidates_2024_leg`,
`delta_log1p_total_candidates_2024_2020`,
`delta_elected_female_share_2024_2020`, `delta_elected_nonwhite_share_2024_2020`,
`delta_elected_higher_ed_share_2024_2020`, `delta_elected_mean_age_2024_2020`,
`delta_incumbent_reelected_share_2024_2020`, `delta_new_candidate_share_2024_2020`,
`delta_nonwhite_share_2024_2020`, `delta_party_count_2024_2020`,
`delta_coalition_count_2024_2020`, `delta_incumbent_candidate_share_2024_2020`,
`delta_higher_education_share_2024_2020`, `bartik_iv_no_rrc_drap`

---

## 4. Output Tables (`output/tables/`)

### Regression results (`output/tables/regressions/`)

**`executive_margin_iv_fixest.csv`** — all IV results, long format
Columns: `variant`, `spec`, `estimator`, `family`, `outcome`, `coef`, `se`, `t`, `p`,
`ivf` (first-stage F), `nobs`, `n_clusters`, `tF_cv`, `ci95_low_tF`, `ci95_high_tF`, `reject_tF_5pct`

**`executive_margin_first_stage_fixest.csv`** — first-stage by spec
Columns: `variant`, `spec`, `coef`, `se`, `t`, `p`, `first_stage_F`, `nobs`, `n_clusters`, `tF_cv`

**`legislative_iv_fixest.csv`** — legislative IV results (long format)
Same structure as executive; additional columns: `family` (outcome family), `first_stage_F_lookup`

**`family_iv_results.csv`** — family-split IV results
Columns: `family`, `outcome`, `coef`, `se`, `t`, `p`, `ivf`, `nobs`, `n_clusters`,
`first_stage_F`, `tF_cv`, `ci95_low_tF`, `ci95_high_tF`, `reject_tF_5pct`

**`liml_comparison.csv`** — LIML vs 2SLS (should be identical for K=1)
Columns: `outcome`, `coef_2sls`, `se_2sls`, `p_2sls`, `ivf_2sls`, `coef_liml`, `se_liml`, `p_liml`

**`exposure_robust_se.csv`** — BHJ/AKM exposure-robust SEs
Columns: `variant`, `spec`, `outcome`, `tau_2sls`, `se_conventional`, `p_conventional`,
`ci_low_conv`, `ci_high_conv`, `se_bhj`, `se_akm`, `ci_low_bhj`, `ci_high_bhj`

### Diagnostics (`output/tables/descriptives/`)

**`rotemberg_weights.csv`** — GPS Rotemberg alpha per topic
Columns: `topic_code`, `topic_name`, `alpha`, `f_stat_k`, `tau_delta_winner_majority_*`,
`tau_delta_margin_*`, `tau_delta_winner_vote_share_*`, `tau_delta_blank_rate_*`,
`alpha_pct`, `cum_alpha`

**`gps_balance_tests.csv`** — GPS share balance (covariate + pre-trend)
Columns: `topic_code`, `topic_name`, `topic_family`, `alpha`, `is_drap`, `is_ie`,
`r2_cov_balance`, `f_cov_balance`, `p_cov_balance`, `beta_margin`, `se_margin`, `p_margin`

**`shift_descriptives.csv`** — BHJ shift table (one row per topic)
Columns: `topic_code`, `topic_name`, `topic_family`, `n_munis`, `g_mean`, `g_sd`,
`g_p10`, `g_p25`, `g_p50`, `g_p75`, `g_p90`, `mean_share_local`

### LaTeX fragments (`output/tables/tex/`)
Generated by `02_iv_main.R` and `02b_iv_legislative.R` via `etable()`.
Files: `first_stage.tex`, `executive_iv_competition.tex`, `executive_iv_voter_behavior.tex`,
`executive_iv_composition.tex`, `entrant_typology.tex`, `open_seat_blank_rate.tex`,
`robustness_winner_majority.tex`
(Legislative fragments generated on next run of `02b_iv_legislative.R`.)

---

## 5. What Is NOT Available Here

| Data | Where to get it |
|------|----------------|
| Voter breakdown by gender | TSE *perfil do eleitorado* (separate download) |
| 2016 lawsuit panel | TSE open data — 2016 processual files not yet downloaded |
| Post-election proceedings | Filtered out (filing date > election date) |
| Case outcomes (win/loss/cassação) | TSE decisoes files — not yet extracted |
| TRE judge composition | Court composition data — not yet collected |
| 2016 electoral zone boundaries | Not relevant; municipality-level data is the analysis unit |
