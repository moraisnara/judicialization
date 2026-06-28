# Judicialization and Electoral Competition in Brazil

**PhD dissertation project — Nara Lívia Morais, FEA-USP**

Causal identification of the effect of the **judicialization of electoral competition** on
municipal (mayoral and city-council) elections in Brazil, using a topic shift-share (Bartik)
instrument built from TSE processual microdata.

The research question is the impact of judicialization on **voters and candidates broadly** —
turnout, valid/blank/null voting, electoral competition, candidate entry, party fragmentation,
and the composition of who runs and who wins. Composition outcomes (female, nonwhite, incumbency)
remain in the outcome sweep but are **not** the headline; this project is no longer led by a
female-candidate-specific result.

> **Authoritative design record.** The current econometric design (instrument, controls, FE,
> clustering, inference, per-outcome lagged-DV map, dropped specs) lives in
> **`docs/STATE_OF_THE_ART.md`** and the machine-readable **`code/spec_config.json`** (read by
> `code/utils/spec_config.{R,py}`). If a script disagrees with those, those are right and the
> script is stale. (`SPECIFICATION.md` has been archived as stale — refer to
> `docs/STATE_OF_THE_ART.md` instead.)

---

## Identification Strategy

The instrument is a municipality-level act-based shift-share (Ash, Morelli & Vannoni 2025 style):

```
B_i = Σ_k  s_ik(2020 share)  ×  g_ik(leave-own-state-out 2020→2024 log-growth shock)
```

- `s_ik` = municipality `i`'s 2020 baseline share of lawsuits in **act family** `k`.
- `g_ik` = national log-growth of family `k` from 2020→2024, **leaving `i`'s own state out**:
  `g = log(N24 − S24 + 1) − log(N20 − S20 + 1)`.
- Instrument column: **`bartik_iv_act`** (a single shift-share).
- Endogenous treatment: **`delta_log1p_act_lawsuits`** = `log1p(2024 kept lawsuits) − log1p(2020)`.

**Estimator.** 2SLS via `fixest::feols()`. Per-outcome formula:
`y ~ baseline controls + per-outcome lagged DV | state FE | endogenous ~ instrument`.

**Baseline controls.** `log_pop_2010`, `urban_share_2010`, `log_income_pc_2010`, `margin_2016`,
`log1p_total_valid_votes_2020`, plus the outcome's own 2020 level (lagged DV).

**Clustering.** At the **state** level (`cluster_id`, ~27 UFs) — the leave-own-state shift is
constant within a state. (Not the electoral zone.)

**Diagnostics.** First-stage F ≈ 25.5, K_eff ≈ 6.8. Weak-IV inference uses the Lee et al. (2022)
tF correction; LIML ≡ 2SLS at K=1. Covariate balance: joint F = 2.83, **p = 0.037** — one yellow
flag (`log_pop` and `log_valid_votes` predict exposure, but both are second-stage controls). This
is reported honestly; no clean-exogeneity claim is made.

### The 10 act-based families

Built by `code/02_build/01d_act_family_crosswalk.py` → `data/clean/act_family_crosswalk.csv`
(column `fam_act10`). Families = the *act alleged*, merging civil and criminal vehicles of the
same act:

`abuso` (abuse of power), `vote_buying` (captação + corrupção + boca de urna), `finance`
(illicit campaign finance), `inelegib` (ineligibility), `fraude` (document/registration fraud,
incl. candidatura fictícia code 12597), `honra` (defamation), `direito_resposta` (right of reply),
`conduta_vedada` (prohibited conduct), `pesquisa_adv` (adversarial poll challenges),
`ballot_integrity` (vote-tally / sufrágio interference).

**Drops.** Mandatory administrative filings (RRC/DRAP/prestação de contas, ~48.5% of all
lawsuits); ancillary/downstream procedural vehicles (execução, cumprimento, habeas, embargos,
mandado de segurança); **propaganda dropped entirely** (defamation kept separately as `honra`);
online propaganda (reform-contaminated). About **6.4%** of all lawsuits are kept.

---

## Directory Structure

```
judicialization/
├── data/
│   ├── raw/          — original downloads from TSE/IBGE, never modified
│   ├── clean/        — intermediate datasets produced by 02_build scripts
│   └── estimation/   — regression-ready design matrices (input to 03_estimation)
│
├── output/
│   ├── figures/      — figures (PDF)
│   ├── tables/
│   │   ├── regressions/  — regression coefficients (CSV)
│   │   └── descriptives/ — shift-share diagnostics and summary statistics
│   └── presentation/ — Beamer report (TeX source + compiled PDF)
│
├── code/
│   ├── 01_download/  — scripts that download raw data from TSE/IBGE/etc.
│   ├── 02_build/     — data cleaning, act taxonomy, outcome panels, covariates
│   ├── 03_estimation/ — design assembly, act instrument, IV estimation
│   ├── 04_analysis/   — Rotemberg/BHJ diagnostics, figures, descriptives, robustness
│   ├── _archive/      — retired scripts from the old substance-family design
│   └── run_all.py    — runs the live pipeline end to end
│
├── docs/             — STATE_OF_THE_ART.md (authoritative) + design logs
└── logs/             — pipeline run logs
```

---

## Data

### `data/raw/`

Original files from the TSE public data portal and IBGE. Never overwritten by any script.
Includes the SIG "Processos eleitorais" exports, TSE candidate registry (`consulta_cand`), vote
detail files, the TPU subject/class references, the census covariates, and the IBGE↔TSE crosswalk.

### `data/clean/` — key files

| File | Produced by | Contents |
|---|---|---|
| `sig_lawsuits_muni_zona_classe_assunto.csv` (+ `_classe`, `_assunto` siblings) | `00_sig_lawsuit_panel.py` | SIG lawsuit panels resolved to município de origem (joint panel keyed on `pair_id`) |
| `sig_family_crosswalk.csv` | `01_family_crosswalk.py` | Per (classe, assunto): canonical `pair_id` + substance crosswalk |
| `act_family_crosswalk.csv` | `01d_act_family_crosswalk.py` | Per `pair_id`: act-family label (`fam_act10`) |
| `municipality_act_components.csv` | `01d_act_family_ivs.py` | Long muni × family decomposition (`rung == "act"`); single source for Rotemberg/shift/balance diagnostics |
| `office_candidate_outcomes_panel.csv` | `03_candidate_composition.py` | Office-level candidate composition outcomes |
| `office_vote_outcomes_panel.csv` | `03b_vote_outcomes.py` | Office-level vote outcomes |
| `office_ballot_spoilage.csv` | `05b_office_ballot_spoilage.py` | Per-office blank/null + roll-off |
| `electoral_admin_outcomes.csv` | `05_electoral_admin.py` | Turnout, blank/null/valid share, registered voters (2020, 2024) |
| `electoral_controls_2016.csv` | `06_electoral_controls_2016.py` | 2016 baseline: margin, HHI, ENP, winner identity |
| `candidate_experience_panel.csv` | `04_candidate_history.py` | Prior candidacies/wins per municipality |
| `council_experience_panel.csv` | `04b_council_history.py` | Council (vereador) experience panel |
| `municipal_covariates.csv` | `07_municipal_covariates.py` | Master covariate table (census 2010 + 2016 baseline + experience) |
| poll-activity panels | `08_poll_activity.py` | Pre-treatment poll activity for heterogeneity splits |

2016 is **not** available in SIG, so there is no pre-period placebo from this lawsuit source.

### `data/estimation/`

| File | Produced by | Contents |
|---|---|---|
| `executive_margin_design.csv` | `01_assemble_design.py` | Instrument-**free** base design: one row per municipality, all outcomes + baseline controls + `cluster_id`. |
| `act_design.csv` | `01d_act_family_ivs.py` | Base design **+ `bartik_iv_act` + `delta_log1p_act_lawsuits`**. This is the headline analysis file. |
| `legislative_design.csv` | `01b_assemble_legislative_design.py` | Legislative (vereadores) design — **still on the retired instrument** (see Status / caveats). |

---

## Code

The live pipeline is **`code/run_all.py`**. The order below mirrors it. Scripts from the retired
substance-family design live in `code/_archive/`; they are not part of the production engine.

### `code/01_download/`

Downloads and verifies raw data (run once before the build). Covers TSE processual dockets,
candidate registry, vote results, the TPU subject/class references, census covariates (`censobr`),
the IBGE↔TSE crosswalk, polls, Poder360 / Atlas media coverage, and SPCE.

### `code/02_build/`

| Script | Output |
|---|---|
| `00_verify_processual.py`, `00b_check_tr_mapping.py` | verification logs |
| `01_family_crosswalk.py` | `sig_family_crosswalk.csv` (mints `pair_id` + substance crosswalk) |
| `00_sig_lawsuit_panel.py` | SIG `sig_lawsuits_muni_zona_*` panels (stamps `pair_id`) |
| `01d_act_family_crosswalk.py` | `act_family_crosswalk.csv` (routes each pair to one of the 10 act families) |
| `03_candidate_composition.py` | `office_candidate_outcomes_panel.csv` |
| `03b_vote_outcomes.py` | `office_vote_outcomes_panel.csv` |
| `04_candidate_history.py`, `04b_council_history.py` | experience panels |
| `05_electoral_admin.py`, `05b_office_ballot_spoilage.py` | turnout/blank/null + roll-off |
| `06_electoral_controls_2016.py` | `electoral_controls_2016.csv` |
| `07_municipal_covariates.py` | `municipal_covariates.csv` |
| `08_poll_activity.py`, `09_poder360_trajectory.R`, `10_spce_build.py`, `11_build_atlas_noticias.R` | mechanism / heterogeneity inputs |

**ORDER MATTERS:** `01_family_crosswalk.py` mints the `pair_id` dictionary first; `00_sig_lawsuit_panel.py`
stamps it onto the joint panel; `01d_act_family_crosswalk.py` then routes pairs to act families.

### `code/03_estimation/`

All regression OUTPUTS (first stage, 2SLS, any coef/SE/F that could reach a slide or the paper)
run in **R/fixest**, reading `code/spec_config.json`. Python is for data construction only.

| Script | Purpose | Output |
|---|---|---|
| `01_assemble_design.py` | Build the instrument-free base design | `data/estimation/executive_margin_design.csv` |
| `01d_act_family_ivs.py` | Build `bartik_iv_act` + `delta_log1p_act_lawsuits` and the long act components | `data/estimation/act_design.csv`, `data/clean/municipality_act_components.csv` |
| `02c_act_iv.R` | **Headline** first stage + 2SLS over all outcomes, with tF | `act_first_stage_fixest.csv`, `act_iv_results.csv` |
| `03_voter_behavior_iv.R` | Voter-behaviour group (turnout, blank/null, spoilage, roll-off placebo) | `voter_*` CSVs |
| `04_candidate_outcomes_iv.R` | Candidate / composition outcomes | per-outcome CSVs |
| `06`–`10` (heterogeneity) | Poll activity, media (Atlas), population splits | per-script CSVs |
| `01b_assemble_legislative_design.py` | Legislative design assembly | `legislative_design.csv` (retired instrument) |

**Specifications** (`spec_config.json`): `baseline` (preferred — baseline controls + lagged DV +
state FE); robustness `extended_controls`, `region_fe` (mesoregion FE), `single_zone`.
Heterogeneity (separate from robustness): open seat, poll activity, media, population, population×media.

### `code/04_analysis/`

Shift-share diagnostics, figures, descriptives, and robustness. Key live scripts:

| Script | Output |
|---|---|
| `02_descriptives_overview.py`, `00_candidate_descriptives.py`, `20_summary_stats.py` | overview + `summary_stats.csv` |
| `02_figures_causal.R`, `03_map_data_universe.R` | causal figures, `map_data_universe.pdf` |
| `05_rotemberg_weights.py` | Rotemberg α_k + per-family F_k (`rotemberg_weights.csv`) from act components |
| `08_gps_balance_tests.py` | share balance tests (`gps_balance_tests.csv`) |
| `10_shift_descriptives.py` | BHJ shift table (`shift_descriptives.csv`) |
| `22_exposure_robust_se.R` | BHJ/AKM exposure-robust SEs |
| `23_mde_power.R` | MDE / bounding for the null defense |
| `30`–`33_sig_*.py` | SIG subject/class share and coding-compatibility descriptives |

### `code/run_all.py`

Runs the full pipeline in order: `01_download` → `02_build` → `03_estimation` → `04_analysis`.
R scripts are called via `Rscript`; Python scripts via `sys.executable`.

---

## Output

### `output/figures/`

`map_data_universe.pdf` (electoral-zone coverage). Causal figures (binscatter first stage, forest,
IV histogram, choropleth) are produced by `02_figures_causal.R`.

### `output/tables/regressions/`

| File | Contents |
|---|---|
| `act_first_stage_fixest.csv` | Act instrument first stage (F, coefs, tF critical values) |
| `act_iv_results.csv` | Headline 2SLS estimates over all outcomes |
| `voter_first_stage.csv`, `voter_behavior_iv.csv` | Voter-behaviour group |
| `voter_turnout_iv.csv`, `voter_office_spoilage_iv.csv`, `voter_rolloff_placebo_iv.csv` | Turnout, office-level spoilage, roll-off placebo |

### `output/tables/descriptives/`

`act_family_coverage.csv`, `rotemberg_weights.csv`, `gps_balance_tests.csv`,
`shift_descriptives.csv`, `summary_stats.csv`, the `sig_*` share/coding tables, and the
candidate/electorate descriptive tables.

### `output/presentation/`

`slides_report.tex` / `.pdf` — the working Beamer research report; `biblio.bib` — bibliography.

---

## Headline Result

The act instrument (n ≈ 5,009, ~26 state clusters, first-stage F ≈ 25.5) yields a **largely null**
second stage:

- **Candidate composition is null:** `female_vote_share` p = 0.39, `female_share` p = 0.77,
  `winner_is_female` p = 0.81, nonwhite p = 0.17.
- **Marginal positives** (tF-significant only): `turnout_rate` +0.011 (p = 0.024),
  `valid_vote_rate` +0.025 (p = 0.045), `others_vote_share` +0.028 (p = 0.035).

Reading: judicialization shows up faintly in **voter behaviour and competition**, not in candidate
composition — which motivates the broadened voters-and-candidates framing.

---

## Status / caveats (known-pending)

- **Legislative arm not ported.** `01b_assemble_legislative_design.py` / `legislative_design.csv`
  are still on the retired substance-family instrument; they have not been repointed to the act
  design.
- **Slides / paper macros not regenerated.** The Beamer report and several `tex` fragments still
  reflect the old design and the female-candidate headline; they are slated for revision.
- **Authoritative record.** The current design lives in `docs/STATE_OF_THE_ART.md` and
  `code/spec_config.json`. `SPECIFICATION.md` is archived/stale — do not rely on it.

---

## How to Reproduce

```bash
# 1. Python dependencies
pip install pandas numpy matplotlib seaborn scipy

# 2. R packages (run once in R)
install.packages(c("fixest", "data.table", "binsreg", "ggplot2",
                   "dplyr", "tidyr", "patchwork", "scales",
                   "geobr", "sf", "censobr"))

# 3. Run the full pipeline
python code/run_all.py

# 4. Compile the report
cd output/presentation
pdflatex -interaction=nonstopmode slides_report.tex
pdflatex -interaction=nonstopmode slides_report.tex
```

> **Note:** The first run downloads raw data from TSE/IBGE (several GB).
