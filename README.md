# Judicialization and Electoral Competition in Brazil

**PhD dissertation project — Nara Lívia Morais, FEA-USP**

Causal identification of the effect of pre-election judicial challenges on mayoral and city-council
election outcomes in Brazil, using a Bartik shift-share instrument built from TSE processual data.

---

## Identification Strategy

The instrument is a municipality-level Bartik shift-share:

```
Z_i = Σ_k s_{ik} × g_k
```

where `s_{ik}` is municipality `i`'s 2020 baseline share of lawsuits in topic `k`, and `g_k` is the
leave-state-out log growth of topic `k` nationally from 2020 to 2024.

**Adversarial filter:** administrative and procedural classes/subjects are excluded at the build
stage (`02_shift_share_design.py`), retaining only substantive electoral competition cases.
This produces the primary instrument `bartik_iv_2020_2024` (first-stage F ≈ 19.6).

Inference follows GPS (2020) Rotemberg-weight decomposition and BHJ (2022/2024) diagnostics.
Weak-instrument correction uses Lee et al. (2022) tF critical values.

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
│   ├── figures/      — all figures (PDF and PNG)
│   ├── tables/
│   │   ├── regressions/  — regression coefficients (CSV + markdown)
│   │   └── descriptives/ — shift-share diagnostics and summary statistics
│   └── presentation/ — Beamer slides (TeX source + compiled PDF)
│
├── code/
│   ├── 01_download/  — scripts that download raw data from TSE/IBGE
│   ├── 02_build/     — data cleaning and construction pipeline
│   ├── 03_estimation/ — design assembly and IV estimation
│   ├── 04_analysis/   — GPS/BHJ diagnostics, figures, and robustness
│   └── run_all.py    — runs the full pipeline end to end
│
└── logs/             — pipeline run logs
```

---

## Data

### `data/raw/`

Original files downloaded from the TSE public data portal and IBGE. Never overwritten by any script.

| Folder / File | Contents |
|---|---|
| `processo_eleitoral_YYYY/` | Case-level docket registry (2018–2024) |
| `processos_eleitorais_assuntos_YYYY/` | Case × legal subject mapping (2018–2024) |
| `decisoes_YYYY/` | Judicial decisions (2018–2024) |
| `recursos_YYYY/` | Electoral appeals (2018–2024) |
| `consulta_cand_YYYY/` | Candidate registry by state (2012–2024) |
| `votacao_candidato_munzona_YYYY/` | Candidate vote counts by zone (2016, 2020, 2024) |
| `detalhe_votacao_munzona_YYYY/` | Aggregate vote detail by zone: turnout, blank, null (2020, 2024) |
| `lista-zonas-municipios-10-07-24.csv` | Official TSE zone → municipality lookup |
| `bd_municipio_tse_ibge.csv` | TSE ↔ IBGE municipality crosswalk |

### `data/clean/`

Intermediate datasets produced by the `02_build` pipeline.

| File | Produced by | Contents |
|---|---|---|
| `zona_lawsuit_panel.csv` | `01_lawsuit_panel.py` | Zone × class × subject panel, pre-election cases (2018–2024) |
| `shift_share_subject_crosswalk.csv` | manual | Subject code → litigation family mapping |
| `municipality_bartik_components.csv` | `02_shift_share_design.py` | Per (municipality, subject): Bartik component `s_{ik}×g_k`, baseline share, shock |
| `municipality_competition_subject_panel.csv` | `02_shift_share_design.py` | Per (municipality, subject, year): lawsuit counts (2020 and 2024) |
| `office_candidate_outcomes_panel.csv` | `02_shift_share_design.py` | Office-level candidate composition outcomes |
| `executive_shift_share_design.csv` | `02_shift_share_design.py` | Executive design with Bartik IV before vote outcomes are joined |
| `legislative_shift_share_design.csv` | `02_shift_share_design.py` | Legislative (vereadores) design with Bartik IV |
| `executive_vote_shift_share_design.csv` | `03_vote_outcomes.py` | Executive design with vote outcomes merged in |
| `electoral_admin_outcomes.csv` | `05_turnout_ballot_outcomes.py` | Turnout, blank/null share, registered voters (2020 and 2024) |
| `electoral_controls_2016.csv` | `08_electoral_controls_2016.py` | 2016 baseline: margin, HHI, ENP, winner identity |
| `candidate_experience_panel.csv` | `04_candidate_history.py` | Prior candidacies and wins per municipality (2012–2024) |
| `censo2010_municipal_ibge.csv` | `05_municipal_characteristics.R` | Census 2010: population, urban share, income per capita |
| `municipal_covariates.csv` | `09_municipal_covariates.py` | Master covariate table (merges all of the above) |
| `zona_eleitoral_lookup.csv` | `01_lawsuit_panel.py` | Zone-level lookup (zone → municipality, state) |

### `data/estimation/`

Flat files that enter the regressions directly. Produced by `03_estimation` assembly scripts.

| File | Produced by | Contents |
|---|---|---|
| `executive_margin_design.csv` | `01_assemble_design.py` + `01c_patch_family_ivs.py` | One row per municipality (N ≈ 5,571). Instrument `bartik_iv_2020_2024`, treatment `delta_log1p_competition_lawsuits_2024_2020`, all outcomes, controls, family IVs, topic shares, cluster ID. |
| `legislative_design.csv` | `01b_assemble_legislative_design.py` | One row per municipality (N ≈ 5,560). Same instrument and controls; outcomes cover candidate composition and elected composition for vereadores. |

---

## Code

### `code/01_download/`

Scripts that download and verify raw data. Run once before the build pipeline.

| Script | Purpose |
|---|---|
| `00_verify_raw_data.py` | Checks that expected raw files exist |
| `01_lawsuits.py` | Downloads TSE processual docket files (processo, assuntos, decisoes, recursos) |
| `02_candidates.py` | Downloads TSE candidate registry files (consulta_cand 2020/2024) |
| `03_historical_elections.py` | Downloads 2016 votes, 2012/2016 candidate history, and detalhe_votacao |
| `04_votes.py` | Downloads candidate vote count files (2020/2024) |
| `05_municipal_characteristics.R` | Downloads Census 2010 microdata via `censobr` |
| `06_municipality_crosswalk.R` | Downloads the IBGE ↔ TSE crosswalk from Base dos Dados |

### `code/02_build/`

Sequential pipeline that transforms raw data into analysis-ready inputs.

| Script | Inputs | Output |
|---|---|---|
| `00_verify_lawsuits.py` | `data/raw/` | Verification log to `logs/` |
| `01_lawsuit_panel.py` | processo_eleitoral + assuntos + zone lookup | `zona_lawsuit_panel.csv` |
| `02_shift_share_design.py` | zona_lawsuit_panel + crosswalk + consulta_cand | `municipality_bartik_components.csv`, `municipality_competition_subject_panel.csv`, `office_candidate_outcomes_panel.csv`, `executive_shift_share_design.csv`, `legislative_shift_share_design.csv` |
| `03_vote_outcomes.py` | executive_shift_share_design + votacao files | `executive_vote_shift_share_design.csv` |
| `04_candidate_history.py` | consulta_cand 2012–2024 | `candidate_experience_panel.csv` |
| `05_turnout_ballot_outcomes.py` | detalhe_votacao_munzona 2020 + 2024 | `electoral_admin_outcomes.csv` |
| `06_turnout_profile_panel.py` | perfil_comparecimento_abstencao 2020 + 2024 | `comparecimento_disaggregated.csv` (long turnout panel by voter trait) |
| `07_turnout_profile_outcomes.py` | comparecimento_disaggregated | `voter_disaggregated_outcomes.csv` (wide facultative / low-education turnout outcomes) |
| `08_electoral_controls_2016.py` | votacao_candidato_munzona_2016 | `electoral_controls_2016.csv` |
| `09_municipal_covariates.py` | censo2010 + electoral_controls + candidate_experience + electoral_admin | `municipal_covariates.csv` |

### `code/03_estimation/`

Design assembly and IV estimation. All regression estimation is done in R via `fixest::feols()`.

| Script | Purpose | Output |
|---|---|---|
| `01_assemble_design.py` | Merges executive clean data, Bartik components, subject panel, and covariates into a flat regression file | `data/estimation/executive_margin_design.csv` |
| `01b_assemble_legislative_design.py` | Builds the legislative design matrix by merging legislative shift-share design with executive controls | `data/estimation/legislative_design.csv` |
| `01c_patch_family_ivs.py` | Adds family-level Bartik IVs, family-specific endogenous variables, and top-topic baseline shares to the executive design | Patches `executive_margin_design.csv` in-place |
| `02_iv_main.R` | Main 2SLS for executive outcomes: 6 specs × primary and secondary outcomes. Includes tF correction, LIML comparison, and variant comparison tables. | `executive_margin_iv_fixest.csv`, `executive_margin_first_stage_fixest.csv`, `liml_single_iv.csv`, `liml_comparison.csv` |
| `02b_iv_legislative.R` | 2SLS for legislative outcomes (vereadores): 5 specs × 14 outcomes | `legislative_iv_fixest.csv`, `legislative_first_stage_fixest.csv` |
| `03_family_iv.R` | Family-split IV: each topic family IV instruments its family-specific endogenous variable. Mechanism analysis. | `family_iv_results.csv`, `family_iv_results.md` |
| `04_placebo_nonadversarial.R` | Placebo shift-share on excluded (non-adversarial) filings + non-adversarial intensity control (BHJ generic-shares test) | `nonadversarial_placebo.csv`, `nonadversarial_placebo_rf.tex`, `nonadversarial_robustness.tex` |
| `05_pretrend_balance.R` | Instrument pre-trend / balance falsification (2016→2020 placebo-in-time) | `pretrend_balance.csv`, `pretrend_balance_*.tex`, `coefplot_pretrend_balance.pdf` |
| `06_wild_bootstrap_ar.R` | Anderson–Rubin wild-cluster restricted bootstrap inference (G = 26 states) | `wild_bootstrap_ar.csv` |
| `07_multiplicity.R` | Family-wise multiple-testing correction (Holm + Benjamini–Hochberg) over the primary executive family | `multiplicity_adjusted.csv` |

**Instrument variants in `02_iv_main.R`:**

| Column | Description |
|---|---|
| `bartik_iv_2020_2024` | Primary instrument — adversarial filter applied at build stage (F ≈ 19.6) |

**Specifications (both executive and legislative):**

| Spec | Description |
|---|---|
| `baseline` | Baseline controls + state FE (primary) |
| `single_zone` | Same, restricted to single-zone municipalities |
| `extended_controls` | Adds 7 demographic/composition controls |
| `open_seat` | 2020 winner was term-limited (no incumbent in 2024) |
| `contested_seat` | Incumbent can seek reelection in 2024 |
| `broader_treatment` | Baseline + `log1p_lawsuits_no_rrc_2020` as covariate |

### `code/04_analysis/`

GPS (2020) and BHJ (2022/2024) required diagnostics, causal figures, and robustness checks.

| Script | Purpose | Output |
|---|---|---|
| `00_candidate_descriptives.py` | Candidate and elected pool descriptives by cycle | summary CSVs in `output/tables/descriptives/` |
| `02_descriptives_overview.py` | Overview tables: lawsuits, voters, candidates (scale of phenomenon) | `overview_lawsuits.csv`, `overview_voters.csv`, `overview_candidates.csv` |
| `02_figures_causal.R` | Causal figures: binscatter first stage, forest plot, IV histogram, choropleth | `binscatter_first_stage.pdf`, `forest_voter_behavior.pdf`, `bartik_histogram.pdf`, `bartik_choropleth.pdf` |
| `03_map_data_universe.R` | Electoral zone map: municipalities per zone, colored by zone size | `map_data_universe.pdf` |
| `05_rotemberg_weights.py` | GPS Rotemberg α_k weights and per-topic F_k statistics | `rotemberg_weights.csv`, `rotemberg_weights.md` |
| `08_gps_balance_tests.py` | GPS share balance: covariate R² and pre-trend tests for top topics | `gps_balance_tests.csv`, `gps_balance_tests.md` |
| `10_shift_descriptives.py` | BHJ shift distribution table: g_k, mean shares, HHI contribution | `shift_descriptives.csv`, `shift_descriptives.md` |
| `11_exposure_robust_se.py` | BHJ/AKM exposure-robust standard errors (shift-level clustering) | `exposure_robust_se.csv`, `exposure_robust_se.md` |

### `code/run_all.py`

Runs the full pipeline in order: `01_download` → `02_build` → `03_estimation` → `04_analysis`.
R scripts are called via `Rscript`; Python scripts via `sys.executable`.

---

## Output

### `output/figures/`

| File | Produced by | Description |
|---|---|---|
| `binscatter_first_stage.pdf` | `02_figures_causal.R` | Binscatter: Bartik IV → Δlog(lawsuits) |
| `forest_voter_behavior.pdf` | `02_figures_causal.R` | Forest plot: voter behavior outcomes across specs |
| `bartik_histogram.pdf` | `02_figures_causal.R` | Distribution of the IV (residualized on state FE) |
| `bartik_choropleth.pdf` | `02_figures_causal.R` | Geographic distribution of the IV across Brazil |
| `map_data_universe.pdf` | `03_map_data_universe.R` | Electoral zones colored by number of municipalities per zone |

### `output/tables/regressions/`

| File | Contents |
|---|---|
| `executive_margin_iv_fixest.csv` | 2SLS estimates: 6 specs × all outcomes (executive) |
| `executive_margin_first_stage_fixest.csv` | First-stage: F-stats, coefs, tF critical values (executive) |
| `executive_margin_fixest.md` | Markdown summary of executive IV results |
| `first_stage_variant_comparison.csv` | First-stage summary across specs |
| `iv_variant_comparison_primary.csv` | IV estimates for primary outcomes across specs |
| `liml_single_iv.csv` | LIML estimates for baseline spec (K=1 instrument) |
| `liml_comparison.csv` | 2SLS vs LIML comparison for primary outcomes |
| `legislative_iv_fixest.csv` | 2SLS estimates: 5 specs × 14 outcomes (legislative) |
| `legislative_first_stage_fixest.csv` | First-stage: F-stats, coefs (legislative) |
| `legislative_fixest.md` | Markdown summary of legislative IV results |
| `family_iv_results.csv` | Family-split IV: per-family first-stage F and 2SLS estimates |
| `family_iv_results.md` | Markdown summary of family IV analysis |

### `output/tables/descriptives/`

| File | Contents |
|---|---|
| `rotemberg_weights.csv` | GPS Rotemberg weights α_k and per-topic F_k for all topics |
| `rotemberg_weights.md` | Formatted markdown table |
| `gps_balance_tests.csv` | Share balance: R², F-stat, p-value per top topic |
| `gps_balance_tests.md` | Formatted markdown table |
| `shift_descriptives.csv` | BHJ shift table: g_k, mean shares, HHI contribution per topic |
| `shift_descriptives.md` | Formatted markdown table |
| `shift_share_diagnostics.md` | Shift-share design audit (sample sizes, top topics, IV coverage) |
| `office_shift_share_setup.md` | Office-level shift-share construction summary |
| `vote_outcomes_setup.md` | Vote outcome construction summary |

### `output/presentation/`

| File | Contents |
|---|---|
| `electoral_judicialization.tex` | Full report presentation (56 frames) — Beamer source |
| `electoral_judicialization.pdf` | Compiled full presentation |
| `electoral_judicialization_short.tex` | Short conference version (10 slides) — Beamer source |
| `biblio.bib` | Bibliography |

---

## How to Reproduce

```bash
# 1. Install Python dependencies
pip install pandas numpy matplotlib seaborn scipy

# 2. Install R packages (run once in R)
install.packages(c("fixest", "data.table", "binsreg", "ggplot2",
                   "dplyr", "tidyr", "patchwork", "scales",
                   "geobr", "sf", "censobr"))

# 3. Run the full pipeline
python code/run_all.py

# 4. Compile the presentation
cd output/presentation
pdflatex -interaction=nonstopmode electoral_judicialization.tex
pdflatex -interaction=nonstopmode electoral_judicialization.tex
```

> **Note:** The first run will download raw data from TSE and IBGE (~several GB).
> The estimation step takes approximately 5–10 minutes total.
