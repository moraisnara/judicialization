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

> **Current design = act-based shift-share (2026-06-26).** The lawsuit source is
> SIG TSE municipality microdata; the instrument is a 10 *act-family* Bartik built
> by `01d_act_family_crosswalk.py` → `01d_act_family_ivs.py`. The old zona-level
> reconstruction (`zona_lawsuit_panel.csv`) and the subject-family Bartik
> components (`municipality_bartik_components.csv`,
> `municipality_family_components.csv`) are **retired** — kept on disk as history
> only. See `docs/STATE_OF_THE_ART.md` (authoritative).

### 2a. Lawsuit panel (SIG municipality microdata) — CURRENT
Built by `code/02_build/00_sig_lawsuit_panel.py` from SIG TSE "Processos
eleitorais" microdata, resolved to município de origem. Three sibling panels at
different aggregations (2016 not available in SIG):

**`sig_lawsuits_muni_zona_classe_assunto.csv`** — unit: year × UF × zona × municipality × class × subject (`pair_id`). **This is the panel the instrument reads.**
**`sig_lawsuits_muni_zona_classe.csv`** — same, aggregated to case class.
**`sig_lawsuits_muni_zona_assunto.csv`** — same, aggregated to subject.

| Column | Description |
|--------|-------------|
| `election_year` | 2020 or 2024 |
| `uf` | UF abbreviation |
| `zona` | TSE electoral zone number |
| `id_municipio` | 7-digit IBGE municipality code |
| `id_municipio_tse` | TSE municipality code (string, zero-padded 5) |
| `pair_id` | class×subject pair key (only in `..._classe_assunto.csv`); `classe` / `assunto` in the sibling files |
| `n_proc` | Count of lawsuits in cell (pre-election filtered) |
| `n_proc_orig` | Count before pre-election filtering |
| `n_proc_pre_eleic` | Count filed before election date |
| `n_dec` | Lawsuits with a decision |
| `tempo_med_dias` | Mean days to decision |

### 2b. Act-family crosswalk and instrument components — CURRENT

**`act_family_crosswalk.csv`** — unit: class×subject `pair_id`. The locked
act-based 10-family taxonomy (built by `01d_act_family_crosswalk.py`).

| Column | Description |
|--------|-------------|
| `pair_id` | class×subject pair key (joins to SIG panel) |
| `cod_classe` / `classe` | TSE case class code / name |
| `cod_assunto` / `assunto` | TSE subject code / name |
| `fam_act10` | Act family (one of the 10 below), or blank if not kept |
| `kept` | `True` if the pair is in the adversarial act universe |

The 10 act families (`fam_act10`): `abuso`, `vote_buying`, `finance`,
`inelegib`, `fraude` (incl. candidatura fictícia 12597), `honra`,
`direito_resposta`, `conduta_vedada`, `pesquisa_adv`, `ballot_integrity`.

**`municipality_act_components.csv`** — unit: municipality × act family. The long
decomposition of the instrument; **single source for the Rotemberg / shift /
balance / leave-one-out diagnostics** (built by `01d_act_family_ivs.py`).

| Column | Description |
|--------|-------------|
| `id_municipio_tse` | TSE municipality code (string) |
| `uf` | UF abbreviation |
| `rung` | Always `"act"` (taxonomy level) |
| `family` | Act family (one of the 10) |
| `L2020` / `L2024` | Kept lawsuit counts in the family, by year |
| `share2020` | Municipality's 2020 share of family $k$ (sums to 1 per muni) |
| `shift_leavestate` | Leave-own-state-out 2020→2024 log-growth shock of family $k$ |
| `bartik_component` | `share2020 × shift_leavestate` |
| `delta_log1p_family` | `log1p(L2024) − log1p(L2020)` for the family |

**`sig_family_crosswalk.csv`** — the older *substance* crosswalk
(`fam_subst13`, `fam_theme9`, `fam_fine7`, …). **Retired for estimation**; kept
for descriptive coverage tables only.

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
| `new_candidate_vote_share_{year}` | Vote share by new entrants |
| `incumbent_candidate_vote_share_{year}` | Vote share by incumbents |
| `winner_vote_share_{year}` | First-place vote share |
| `runnerup_vote_share_{year}` | Second-place vote share |
| `margin_top1_top2_{year}` | Margin (winner − runner-up) |
| `winner_majority_{year}` | Indicator: winner got > 50% |
| `winner_is_female_{year}` | Winner gender indicator |
| `winner_is_new_vs_2020_{year}` | Winner was new entrant |
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

> **Instrument/treatment summary (current act design):**
> instrument = `bartik_iv_act`; endogenous treatment = `delta_log1p_act_lawsuits`.
> These live **only** in `act_design.csv`. `executive_margin_design.csv` is the
> instrument-FREE base (outcomes + controls + `cluster_id`).
> **Clustering is at the STATE level** (`cluster_id`, ~27 UFs) — the leave-own-state
> shift is constant within a state. First-stage **F ≈ 25.5**, K_eff ≈ 6.8.
> There are **no** `bartik_iv_<family>` columns and **no**
> `delta_log1p_competition_lawsuits_*` — those are retired.

### `executive_margin_design.csv` — **INSTRUMENT-FREE BASE**
Unit: municipality. Built by `code/03_estimation/01_assemble_design.py`. Holds all
executive outcomes, controls, IDs, and `cluster_id`, but **no instrument**.
`01d_act_family_ivs.py` reads this and appends the two act columns to produce
`act_design.csv`.

### `act_design.csv` — **THE HEADLINE 2SLS FILE**
Unit: municipality. = `executive_margin_design.csv` + two columns. Read by
`code/03_estimation/02c_act_iv.R`.

| Column | Description |
|--------|-------------|
| `bartik_iv_act` | Act-based 10-family Bartik instrument |
| `delta_log1p_act_lawsuits` | Endogenous treatment: `log1p(2024 kept act lawsuits) − log1p(2020)` |

**Clustering and zone columns (carried from the base):**

| Column | Description |
|--------|-------------|
| `cluster_id` | **State (UF)** — the SE clustering unit (~27 clusters) |
| `n_zones_in_municipality` | Number of electoral zones in this municipality |
| `principal_zone` / `principal_zone_id` | Principal TSE zone number / `{UF}_{zone}` string (descriptive only, not the cluster) |

**Controls (5 baseline, from `code/spec_config.json`):**

| Column | Description |
|--------|-------------|
| `log_pop_2010` | Log Census population |
| `urban_share_2010` | Urban population share |
| `log_income_pc_2010` | Log per-capita income |
| `margin_2016` | 2016 electoral margin (pp) |
| `log1p_total_valid_votes_2020` | Log 2020 valid votes |

A per-outcome **lagged dependent variable** (the outcome's own 2020 level) is
appended at estimation time; see `spec_config.json` → `lagged_dv`.

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
`delta_winner_is_female_2024_2020`, `delta_winner_is_new_vs_2020_2024_2020`,
`delta_new_candidate_vote_share_2024_2020`, `delta_incumbent_candidate_vote_share_2024_2020`

Entry typology (deltas):
`delta_share_first_time_candidates_2024_2020`,
`delta_share_serial_challenger_2024_2020`,
`delta_share_cross_cycle_returner_2024_2020`

Open seat:
`open_seat_2024` (1 = 2020 winner term-limited; exogenous to 2024 litigation)

---

### `legislative_design.csv`
Unit: municipality. City council (vereador) outcomes.

> **Not yet ported to the act design.** This file still carries the **retired**
> substance-family instrument columns (`bartik_iv_fine7`, `bartik_iv_subst11`,
> `bartik_iv_theme9`, …, plus the old `bartik_iv_2020_2024` /
> `delta_log1p_competition_lawsuits_2024_2020`). The legislative IV has **not**
> been re-run on `bartik_iv_act` yet — treat its instrument columns as stale.

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

### Regression results (`output/tables/regressions/`) — CURRENT (act design)
State-clustered, instrument `bartik_iv_act`, treatment `delta_log1p_act_lawsuits`,
first-stage **F ≈ 25.5**. Produced by `code/03_estimation/02c_act_iv.R` and the
voter/candidate outcome scripts.

| File | Content |
|------|---------|
| `act_iv_results.csv` | Headline act-instrument 2SLS, all outcomes |
| `act_first_stage_fixest.csv` | Act first stage |
| `voter_behavior_iv.csv` | Voter-behavior outcomes on the act instrument |
| `voter_turnout_iv.csv` | Turnout IV |
| `voter_office_spoilage_iv.csv` | Blank/null spoilage IV |
| `voter_rolloff_placebo_iv.csv` | Roll-off placebo |
| `voter_first_stage.csv` | First stage for the voter lane |

> Retired (old substance/female-headline design):
> `executive_margin_iv_fixest.csv`, `family_iv_results.csv`,
> `legislative_iv_fixest.csv`, `liml_comparison.csv`, `exposure_robust_se.csv`,
> and the `tables/tex/*` fragments built off them. Not yet ported to the act
> instrument.

### Diagnostics (`output/tables/descriptives/`)
The Rotemberg / shift / balance diagnostics now decompose the act instrument from
`data/clean/municipality_act_components.csv` (one row per municipality × act
family). Column schemas below reflect the legacy per-topic layout and are being
repointed to the act families.

**`rotemberg_weights.csv`** — Rotemberg alpha per family/topic
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
**Result tables** are generated by `code/04_analysis/21_results_tables.py` (one row
per outcome; combined Mayor-vs-Council columns where both races have an analogue):
`combined_field_fragmentation.tex`, `combined_composition.tex`,
`combined_entry_typology.tex`, `combined_elected.tex`, plus mayor-only
`executive_iv_competition.tex` and `executive_iv_voter_behavior.tex`.
**Spec-column fragments** still come from the R scripts via `etable()`:
`first_stage.tex`, `robustness_winner_majority.tex`, `open_seat_blank_rate.tex`.
(`02_iv_main.R` / `02b_iv_legislative.R` write only result CSVs for the families.)

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
