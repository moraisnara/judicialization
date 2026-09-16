# Data Guide — Judicialization and Electoral Competition in Brazil

Quick reference for all datasets in this project. Use this to check whether a
variable exists and which file to load — without reading the actual data.

Join keys across files: `state` (2-letter UF) + `municipality_id_tse` (5-digit TSE
integer, stored as string with leading zero e.g. `"01007"`). IBGE codes are in
`municipality_id_ibge` / `bd_municipio_tse_ibge.csv`.

---

## 1. Raw Data (`data/raw/`)

Sources sit here as extracted folders; some downloaded zips remain beside them.

| File | Format | Content |
|------|--------|---------|
| `processos_eleitorais.csv.zip` (2020), `processos_eleitorais_2024.csv` (2024) | SIG zip (the 2024 file is a zip despite its extension) | SIG lawsuit export, resolved to municipality; the instrument source, read by `02_shift_share_design.py` |
| `processo_eleitoral_YYYY/` (2018/2020/2022/2024) | TSE CSV + zip | Portal docket registry: class (`CD_CLASSE`), main subject (`CD_ASSUNTO_PRINCIPAL`), filing date (`DT_AUTUACAO`), instance (`NR_INSTANCIA`); read by `01_lawsuit_panel.py` and for the SIG label bridge in `02_shift_share_design.py` |
| `assuntos_YYYY/`, `processos_eleitorais_assuntos_YYYY.zip` (2018–2024) | TSE CSV + zip | Case × subject mapping |
| `processos_eleitorais_partes_2020.zip` | TSE zip | Parties to each lawsuit (petitioner / respondent) |
| `consulta_cand_YYYY/` (2012/2016/2020/2024) | TSE CSV by state | Candidate registry: `DS_GENERO`, `DS_COR_RACA`, `DS_GRAU_INSTRUCAO`, `DS_ESTADO_CIVIL`, `DT_NASCIMENTO`, office (`CD_CARGO`), party, TSE municipality code (`SG_UE`) |
| `votacao_candidato_munzona_YYYY/` (2016/2020/2024) | TSE CSV | Candidate votes by zone |
| `detalhe_votacao_munzona_YYYY/` (2016/2020/2024) | TSE CSV | Turnout, blank and null votes by zone |
| `perfil_comparecimento_abstencao_YYYY/` (2020/2024) | TSE CSV + zip | Turnout and abstention by voter trait; read by `06_turnout_profile_panel.py` |
| `spce_candidatos_YYYY/`, `prestacao_de_contas_eleitorais_candidatos_YYYY.zip` (2020/2024) | TSE | Campaign finance; read by `10_candidate_finance.py` |
| `SAC-JE_769756-Distribuicao_de_casos_novos_por_eleicao.xlsx` | xlsx | TRE-SP new cases by election, a state-level pre-2020 snapshot; read by `08_lawsuit_composition_sp.py` |
| `bd_municipio_tse_ibge.csv` | CSV | Crosswalk: `id_municipio` (7-digit IBGE) ↔ `id_municipio_tse` (TSE code) |
| `bd_diretorio_municipio.csv` | CSV | Municipality directory (`id_municipio`, `id_municipio_tse` and regional codes) |
| `lista-zonas-municipios-10-07-24.csv` | CSV (sep=`;`) | TSE official zone→municipality list: `UF`, `ZONA`, `COD_LOCALIDADE` (TSE muni code), `NOM_LOCALIDADE` |
| `tpu_eleitoral_tree.json`, `tpu_{assunto,classe}_reference.csv` | JSON, CSV | TPU subject and class codes; read by `exploration/04_analysis/11_lawsuit_topic_selection.py` |

No script reads `78_Tabela_Classes_Justica_Eleitoral_ZE.xls`,
`79_Tabela_Assuntos_Justica_Eleitoral_ZE.xls`, `560520_distribuicao_zonas_eleicao_2016.xlsx`,
`atlas_noticias/` or `poder360_sample.rds`. The `decisoes_YYYY` and `recursos_YYYY` zips that
`01_download/01_lawsuits.py` targets are not on disk.

---

## 2. Clean / Intermediate Data (`data/clean/`)

### 2a. Lawsuit panel
**`zona_lawsuit_panel.csv`** — unit: zone × class × subject × year

Built by `01_lawsuit_panel.py` from the Portal `processo_eleitoral_YYYY` dockets
(pre-election cases). It is not the instrument source (that is the SIG export, §2b) and
only `08_lawsuit_composition_sp.py` reads it.

| Column | Description |
|--------|-------------|
| `election_year` | 2020, 2022 or 2024 on disk (the script's year list also includes 2018) |
| `state` | UF abbreviation |
| `electoral_zone` | TSE zone number (integer) |
| `municipality_id_tse` | TSE municipality code |
| `municipality_name` | Municipality name |
| `n_municipalities_in_zone` | How many municipalities share this zone |
| `case_class_code` / `case_class_name` | Case class (e.g. 11532 = Registro de Candidatura, 11527 = AIJE, 11541 = Representação) |
| `main_subject_code` / `main_subject_name` | Subject code (e.g. 11616 = Impugnação ao Registro de Candidatura) |
| `n_lawsuits` | Count of lawsuits in cell |

### 2b. Bartik instrument components
**`municipality_bartik_components.csv`** — unit: municipality × subject, at the 2020 baseline

Built by `02_shift_share_design.py` from the SIG export. Every row has
`election_year` = 2020 (22,590 rows).

| Column | Description |
|--------|-------------|
| `election_year` | 2020 |
| `state`, `municipality_id_tse`, `municipality_name` | IDs |
| `main_subject_code` / `main_subject_name` | Subject code |
| `topic_family` | Family: `information_environment`, `campaign_conduct`, `eligibility_ballot_access`, `abuse_misuse_office`, or `unmapped` |
| `n_lawsuits` | Raw 2020 count |
| `baseline_share_2020` | Municipality's share of topic $k$ in 2020 (sums to 1 per muni) |
| `uf_2020` / `uf_2024` | Own-state count of topic $k$ |
| `national_2020` / `national_2024` | National count of topic $k$ |
| `leave_uf_out_2020` / `leave_uf_out_2024` | National count minus the own-state count |
| `shock_log_growth_2020_2024` | `log1p(leave_uf_out_2024) − log1p(leave_uf_out_2020)`: leave-own-state-out national growth of topic $k$ |
| `bartik_component` | `baseline_share_2020 × shock_log_growth_2020_2024` |

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
| `blank_votes_vereador`, `null_votes_vereador`, `valid_votes_vereador` | Council-ballot counts |
| `blank_rate_vereador`, `null_rate_vereador`, `valid_vote_rate_vereador` | Council-ballot rates |

Turnout by voter trait is in two other files:

**`comparecimento_disaggregated.csv`** (`06_turnout_profile_panel.py`) — long, unit:
municipality × year × dimension × category, 2020 and 2024. Columns: `election_year`,
`municipality_id_tse`, `dimension`, `category`, `aptos`, `comparecimento`, `turnout_rate`.
`dimension` takes `overall`, `compulsory_status`, `sex`, `education`, `age_band`, `race`.

**`voter_disaggregated_outcomes.csv`** (`07_turnout_profile_outcomes.py`) — wide, unit:
municipality. Facultative, compulsory, low-education, high-education, illiterate
(`analfabeto`), female and male turnout for 2020 and 2024, their 2024−2020 changes, and the
education and sex turnout gaps.

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
**`candidate_experience_panel.csv`** — unit: municipality × office × year

Prior experience pools every municipal office (mayor and council) since 2012; shares are
computed separately by office sought.

| Column | Description |
|--------|-------------|
| `election_year`, `office_group`, `state`, `municipality_id_tse`, `municipality_name` | IDs; `office_group` is `executive` or `legislative` |
| `share_first_time_candidates` | Share with no prior municipal candidacy (any office) since 2012 |
| `mean_prior_candidacies` | Mean number of prior cycles run (any office) |
| `share_prior_winners` | Share who previously won (any office) |
| `share_career_politicians` | Share with 3+ prior cycles (any office); identically 0 before 2024 because of the 2012 left-censor |
| `share_serial_challenger` | Ran in the same municipality last cycle and lost |
| `share_cross_cycle_returner` | Has prior history but did not run last cycle |
| `n_candidates`, `open_seat` | Candidates in the cell / seat status (executive only: 1 if the prior-cycle mayor was term-limited) |

### 2h. Lookups and crosswalks
**`zona_eleitoral_lookup.csv`** — columns: `SG_UF`, `zona` (integer), `nome_zona`. It has
no municipality column, and no script reads or writes it.

---

## 3. Estimation-Ready Datasets (`data/estimation/`)

### `executive_margin_design.csv` — **THE MAIN ANALYSIS FILE**
Unit: municipality. 5,571 rows × 346 columns; estimation N = 5,560.

**Key instrument and treatment columns:**

| Column | Description |
|--------|-------------|
| `bartik_iv_2020_2024` | Main Bartik IV (adversarial filter applied) |
| `placebo_bartik_iv_2020_2024` | Placebo IV: the same construction over the non-adversarial filings |
| `bartik_iv_no_rrc` | Broader IV (excludes RRC only, not DRAP) |
| `delta_log1p_competition_lawsuits_2024_2020` | Endogenous variable (main) |
| `delta_log1p_lawsuits_no_rrc_2024_2020` | Endogenous for broader IV |
| `competition_lawsuits_2020` / `..._2024` | Raw adversarial lawsuit counts |
| `log1p_competition_lawsuits_2020` | 2020 level of the treatment; the added control in `base_conditioned` |
| `log1p_lawsuits_no_rrc_2020` | The added control in `broader_treatment` |
| `baseline_*_2020` | 2020 baseline lawsuit and subject counts (adversarial, non-adversarial, no-RRC) |

The family IVs (`bartik_iv_{family}`), their endogenous variables and the topic shares
(`share_{code}_2020`) are not in this file. `exploration/03_estimation/01c_patch_family_ivs.py`
adds them in place when the family lane is run.

**Clustering and zone columns:**

| Column | Description |
|--------|-------------|
| `n_zones_in_municipality` | Number of electoral zones in this municipality |
| `principal_zone` | TSE zone number of principal zone |
| `principal_zone_id` | String: `{UF}_{zone_number}` e.g. `"AC_1"` |
| `cluster_id` | The state (`SG_UF`, e.g. `"AC"`), set in `01_assemble_design.py`; used for SE clustering (26 states in the estimation sample) |

**Controls (`BASELINE_CONTROLS` in `02_iv_main.R`, 6):**

| Column | Description |
|--------|-------------|
| `log_pop_2010` | Log Census population |
| `urban_share_2010` | Urban population share |
| `log_income_pc_2010` | Log per-capita income |
| `higher_educ_share_2010` | Census 2010 higher-education share |
| `margin_2016` | 2016 mayoral margin (share, 0–1) |
| `log1p_total_valid_votes_2020` | Log 2020 valid votes |

The headline also controls for the outcome's own 2016 level where one exists (`ANCOVA_MAP`
in `02_iv_main.R`). `margin_top1_top2_2020` and `log1p_total_candidates_2020` enter only the
`ancova_2020lvl` spec. The `extended_controls` additions are listed in `README.md`
(Specifications).

**Outcome variables.** Each outcome is named by its `delta_*` column (2024 − 2020). Under the
headline, an outcome with a 2016 analog is estimated as its 2024 level with the 2016 level as
a control (`ANCOVA_MAP`); the rest, and every outcome in `fd`, use the change. The `_2016`,
`_2020` and `_2024` level columns are in the file.

Electoral competition:
`delta_winner_vote_share_2024_2020`, `delta_runnerup_vote_share_2024_2020`,
`delta_margin_top1_top2_2024_2020`, `delta_winner_majority_2024_2020`,
`delta_log1p_n_candidates_with_votes_2024_2020`

Voter behavior:
`delta_turnout_rate_2024_2020`, `delta_blank_rate_2024_2020`,
`delta_null_rate_2024_2020`, `delta_valid_vote_rate_2024_2020`

Composition (candidate pool):
`delta_female_share_2024_2020`; the levels `female_share`, `nonwhite_share`,
`higher_education_share`, `mean_age` and their `elected_*` counterparts, for 2020 and 2024

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

---

### `legislative_design.csv`
Unit: municipality. 5,560 rows × 98 columns. Same Bartik IV as executive
(`bartik_iv_2020_2024`, plus `placebo_bartik_iv_2020_2024`). City council (vereador) outcomes.
It also carries `log1p_lawsuits_no_rrc_2020`, `n_zones_in_municipality`,
`effective_party_count_candidates_2020` and the non-adversarial lawsuit columns, but not
`bartik_iv_no_rrc` or `delta_log1p_lawsuits_no_rrc_2024_2020`.

Key columns not in executive design:
`log1p_total_candidates_2020_leg`, `log1p_total_candidates_2024_leg`,
`delta_log1p_total_candidates_2024_2020`,
`delta_elected_female_share_2024_2020`, `delta_elected_nonwhite_share_2024_2020`,
`delta_elected_higher_ed_share_2024_2020`, `delta_elected_mean_age_2024_2020`,
`delta_incumbent_reelected_share_2024_2020`, `delta_new_candidate_share_2024_2020`,
`delta_nonwhite_share_2024_2020`, `delta_party_count_2024_2020`,
`delta_coalition_count_2024_2020`, `delta_incumbent_candidate_share_2024_2020`,
`delta_higher_education_share_2024_2020`

---

## 4. Output Tables (`output/tables/`)

### Regression results (`output/tables/regressions/`)

**`executive_margin_iv_fixest.csv`** — all IV results, long format
Columns: `variant`, `spec`, `estimator`, `family`, `outcome`, `coef`, `se`, `t`, `p`,
`ivf`, `nobs`, `n_clusters`, `first_stage_F_lookup`, `tF_cv`, `ci95_low_tF`, `ci95_high_tF`,
`reject_tF_5pct`. `ivf` is fixest's homoskedastic IV F and is never shown;
`first_stage_F_lookup` is the spec's cluster-robust first-stage F, which sets `tF_cv`.

**`executive_margin_first_stage_fixest.csv`** — first-stage by spec
Columns: `variant`, `spec`, `coef`, `se`, `t`, `p`, `first_stage_F`, `nobs`, `n_clusters`, `tF_cv`

**`legislative_iv_fixest.csv`** — legislative IV results (long format)
Columns: `variant`, `spec`, `family`, `outcome`, `coef`, `se`, `t`, `p`, `ivf`, `nobs`,
`n_clusters`, `first_stage_F_lookup`, `tF_cv`, `ci95_low_tF`, `ci95_high_tF`, `reject_tF_5pct`
(the executive columns without `estimator`)

**`legislative_first_stage_fixest.csv`** — same columns as the executive first stage

**`exploration/output/tables/regressions/family_iv_results.csv`** — family-split IV results.
Not a paper asset: produced by `exploration/03_estimation/03_family_iv.R`, in the
exploration lane, and read by no document.
Columns: `family`, `outcome`, `coef`, `se`, `t`, `p`, `ivf`, `nobs`, `n_clusters`,
`first_stage_F`, `tF_cv`, `ci95_low_tF`, `ci95_high_tF`, `reject_tF_5pct`

**`exposure_robust_se.csv`** — BHJ/AKM exposure-robust SEs (`exposure_robust_akm.csv` has the same columns)
Columns: `variant`, `spec`, `outcome`, `nobs`, `tau_2sls`, `se_conventional`, `se_bhj`,
`se_akm`, `p_bhj`, `akm0_ci_low`, `akm0_ci_high`, `K_eff_rotemberg`

### Diagnostics (`output/tables/descriptives/`)

**`rotemberg_weights.csv`** — GPS Rotemberg alpha per topic
Columns: `topic_code`, `topic_name`, `alpha`, `f_stat_k`, `tau_delta_winner_majority_*`,
`tau_delta_margin_*`, `tau_delta_winner_vote_share_*`, `tau_delta_blank_rate_*`,
`alpha_pct`, `cum_alpha`

**`gps_balance_tests.csv`** — GPS share balance (covariate + pre-trend)
Columns: `topic_code`, `topic_name`, `topic_family`, `alpha`, `is_drap`, `is_ie`,
`r2_cov_balance`, `f_cov_balance`, `p_cov_balance`, `beta_margin`, `se_margin`, `p_margin`,
`beta_top1`, `se_top1`, `p_top1`, `beta_ncand`, `se_ncand`, `p_ncand`

**`shift_descriptives.csv`** — BHJ shift table (one row per topic)
Columns: `topic_code`, `topic_name`, `topic_family`, `n_munis`, `g_mean`, `g_sd`,
`g_p10`, `g_p25`, `g_p50`, `g_p75`, `g_p90`, `mean_share_local`, `s_k_bar`, `s_k_bar_norm`, `s_k_bar2`

### LaTeX fragments (`output/tables/tex/`)
35 fragments, all `\input` by the deck. The regression tables are written as LaTeX by hand in
the house style (`CLAUDE.md`), not through `etable()`.

| Producer | Fragments |
|---|---|
| `03_estimation/02_iv_main.R` | `firststage`, `executive_iv_{competition, composition, concentration, concentration_ptrobust, gender_consolidation, gender_gap, heterogeneity_seat, turnout, voter_behavior_office_openseat, ballot_mayoral, ballot_council}`, `entrant_typology`, `pretrend_falsification`, `appendix_competition_binary`, `appendix_first_difference` |
| `03_estimation/02b_iv_legislative.R` | `legislative_iv_{candidate_pool, elected_comp, party_comp}` |
| `03_estimation/04_placebo_nonadversarial.R` | `nonadversarial_robustness` |
| `03_estimation/09_extensive_margin.R` | `extensive_margin`, `extensive_margin_macros` |
| `03_estimation/10_mechanism_finance.R` | `mechanism_finance_seat` |
| `03_estimation/11_summary_indices.R` | `summary_indices`, `romano_wolf_stepdown` |
| `03_estimation/12_treatment_definition.R` | `treatment_definition`, `treatment_definition_macros` |
| `03_estimation/13_reclassification_robustness.R` | `reclassification_robustness`, `reclassification_robustness_macros` |
| `04_analysis/01_descriptives.py` | `litigation_composition` |
| `04_analysis/06_abstract_macros.py` | `abstract_macros`, `abstract_table` |
| `04_analysis/08_lawsuit_composition_sp.py` | `lawsuit_composition_sp` |
| `04_analysis/09_summary_statistics.R` | `sample_summary_statistics` |
| `04_analysis/10_candidate_rank_profile.py` | `candidate_rank_profile` |

---

## 5. What Is NOT Available Here

| Data | Where to get it |
|------|----------------|
| National 2016 lawsuit panel | Not downloaded. The only pre-2020 litigation source is the TRE-SP SAC-JE state-level snapshot (`08_lawsuit_composition_sp.py`) |
| Post-election proceedings | Filtered out (filing date > election date) |
| Case outcomes (win/loss/cassação) | TSE `decisoes` files, which are not on disk |
| TRE judge composition | Court composition data — not yet collected |
| 2016 electoral zone boundaries | Not relevant; municipality-level data is the analysis unit |
