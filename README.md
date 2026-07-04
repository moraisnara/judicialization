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
This produces the primary instrument `bartik_iv_2020_2024` (first-stage F ≈ 102).

**Estimator:** the headline is an ANCOVA on the 2016 pre-window baseline —
`Y_2024 ~ D̂ + Y_2016 + controls | state FE`, state-clustered — with the first-difference
specification demoted to the appendix.

Inference is conventional cluster-robust SE (headline), with appendix robustness layers:
GPS (2020) Rotemberg-weight decomposition and BHJ (2022/2024) diagnostics, Lee et al. (2022)
tF weak-instrument critical values, Anderson–Rubin wild-cluster restricted bootstrap
(`06_wild_bootstrap_ar.R`), and AKM (2019) / BHJ (2022) exposure-robust standard errors
(`07_exposure_robust_se.R`).

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
│   │   ├── regressions/  — regression coefficients (CSV)
│   │   ├── descriptives/ — shift-share diagnostics and summary statistics (CSV)
│   │   └── tex/          — LaTeX table fragments \input into the deck and paper
│   ├── presentation/ — Beamer report deck (TeX source + compiled PDF)
│   └── paper/        — paper draft and extended abstract (TeX + compiled PDF)
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
| `02_iv_main.R` | Main 2SLS for executive outcomes across specs × primary and secondary outcomes. Includes tF correction and LIML comparison. Also writes the hand-built LaTeX table fragments (`output/tables/tex/*.tex`). | `executive_margin_iv_fixest.csv`, `executive_margin_first_stage_fixest.csv`, `liml_comparison.csv`, deck `.tex` fragments |
| `02b_iv_legislative.R` | 2SLS for legislative outcomes (vereadores) across specs × outcomes; writes the legislative `.tex` fragments. | `legislative_iv_fixest.csv`, `legislative_first_stage_fixest.csv`, deck `.tex` fragments |
| `03_family_iv.R` | Family-split IV: each topic family IV instruments its family-specific endogenous variable. Mechanism analysis. | `family_iv_results.csv` |
| `04_placebo_nonadversarial.R` | Placebo shift-share on excluded (non-adversarial) filings + non-adversarial intensity control (BHJ generic-shares test) | `nonadversarial_placebo.csv`, `nonadversarial_placebo_rf.tex`, `nonadversarial_robustness.tex` |
| `05_pretrend_balance.R` | Instrument pre-trend / balance falsification (2016→2020 placebo-in-time) | `pretrend_balance.csv`, `pretrend_balance_*.tex`, `pretrend_coefplot.pdf` |
| `06_wild_bootstrap_ar.R` | Anderson–Rubin wild-cluster restricted bootstrap inference (G = 26 states) | `wild_bootstrap_ar.csv` |
| `07_multiplicity.R` | Family-wise multiple-testing correction (Holm + Benjamini–Hochberg) over the primary executive family | `multiplicity_adjusted.csv` |

**Instrument in `02_iv_main.R`:**

| Column | Description |
|---|---|
| `bartik_iv_2020_2024` | Primary instrument — adversarial filter applied at build stage (F ≈ 102) |

**Specifications (both executive and legislative):**

| Spec | Description |
|---|---|
| `baseline` | ANCOVA-2016 headline: 2016-baseline lag + controls + state FE |
| `single_zone` | Same, restricted to single-zone municipalities |
| `extended_controls` | Adds 7 demographic/composition controls |
| `open_seat` | 2020 winner was term-limited (no incumbent in 2024) |
| `contested_seat` | Incumbent can seek reelection in 2024 |
| `broader_treatment` | Baseline + `log1p_lawsuits_no_rrc_2020` as covariate |
| `fd` | First-difference (appendix; over-differences a barely-persistent outcome) |
| `ancova_2020lvl` | ANCOVA on the 2020 level instead of the 2016 baseline (robustness) |

### `code/04_analysis/`

Descriptives, figures, GPS (2020) / BHJ (2022/2024) diagnostics, and validation.

| Script | Purpose | Output |
|---|---|---|
| `01_descriptives.py` | Candidate-pool descriptives, overview tables (lawsuits/voters/candidates), litigation composition and timing, and the BHJ shift-distribution table | `candidate_pool_descriptives.csv`, `overview_{lawsuits,voters,candidates}.csv`, `litigation_composition.csv`, `litigation_family_shares.csv`, `litigation_timing_panel.csv`, `shift_descriptives.csv` |
| `02_descriptive_figures.R` | Descriptive figures: litigation timing, data-universe map, and Bartik IV distribution/map | `litigation_timing_{count,rate,share,shape}.pdf`, `sample_map.pdf`, `instrument_histogram.pdf`, `instrument_map.pdf` |
| `03_result_figures.R` | Result figures: first-stage binscatter and linear fit, voter-behavior forest, and null-family coefplots | `firststage_binscatter.pdf`, `firststage_linear.pdf`, `voterbehavior_forest.pdf`, `representation_coefplot.pdf`, `entrant_coefplot.pdf`, `turnout_coefplot.pdf` |
| `04_iv_diagnostics.py` | GPS Rotemberg α_k weights + per-topic F_k, and GPS share-balance (covariate R² and pre-trend) tests | `rotemberg_weights.csv`, `gps_balance_tests.csv` |
| `05_validation.R` | FD-vs-ANCOVA comparison and ANCOVA specification validation | `fd_vs_ancova_comparison.csv`, `ancova_validation.csv` |
| `06_abstract_macros.py` | Generates the deck/paper number macros and the abstract table from the overview and regression CSVs | `abstract_macros.tex`, `abstract_table.tex` |
| `07_exposure_robust_se.R` | Genuine AKM (2019) / BHJ (2022) exposure-robust standard errors (shift-level clustering) | `exposure_robust_se.csv`, `exposure_robust_akm.csv` |

### `code/run_all.py`

Runs the full pipeline in order: `01_download` → `02_build` → `03_estimation` → `04_analysis`.
R scripts are called via `Rscript`; Python scripts via `sys.executable`.

---

## Output

Figures carry no baked-in titles/captions (those live on the Beamer frame); all
producing scripts source `code/utils/figure_style.R` for the shared theme and palette.

### `output/figures/`

| File | Produced by | Description |
|---|---|---|
| `litigation_timing_{count,rate,share,shape}.pdf` | `02_descriptive_figures.R` | Litigation timing over the electoral calendar |
| `sample_map.pdf` | `02_descriptive_figures.R` | Data-universe map: municipalities in the estimation sample |
| `instrument_histogram.pdf` | `02_descriptive_figures.R` | Distribution of the Bartik IV (residualized on state FE) |
| `instrument_map.pdf` | `02_descriptive_figures.R` | Geographic distribution of the IV across Brazil |
| `firststage_binscatter.pdf` | `03_result_figures.R` | Binscatter (cubic): Bartik IV → Δlog(lawsuits) |
| `firststage_linear.pdf` | `03_result_figures.R` | First stage, linear AMV-style fit with F |
| `voterbehavior_forest.pdf` | `03_result_figures.R` | Forest plot: voter-behavior outcomes across specs |
| `representation_coefplot.pdf` | `03_result_figures.R` | Null-family coefplot: representation outcomes |
| `entrant_coefplot.pdf` | `03_result_figures.R` | Null-family coefplot: candidate-entrant typology |
| `turnout_coefplot.pdf` | `03_result_figures.R` | Null-family coefplot: turnout outcomes |
| `pretrend_coefplot.pdf` | `05_pretrend_balance.R` | Standardized instrument pre-trend / balance coefplot |

### `output/tables/regressions/` (CSV)

| File | Produced by | Contents |
|---|---|---|
| `executive_margin_iv_fixest.csv` | `02_iv_main.R` | 2SLS estimates: all specs × all outcomes (executive) |
| `executive_margin_first_stage_fixest.csv` | `02_iv_main.R` | First-stage: F-stats, coefs, tF critical values (executive) |
| `liml_comparison.csv` | `02_iv_main.R` | 2SLS vs LIML comparison (K=1, so 2SLS ≡ LIML) |
| `legislative_iv_fixest.csv` | `02b_iv_legislative.R` | 2SLS estimates: all specs × outcomes (legislative) |
| `legislative_first_stage_fixest.csv` | `02b_iv_legislative.R` | First-stage: F-stats, coefs (legislative) |
| `family_iv_results.csv` | `03_family_iv.R` | Family-split IV: per-family first-stage F and 2SLS estimates |
| `nonadversarial_placebo.csv` | `04_placebo_nonadversarial.R` | Placebo shift-share on excluded (non-adversarial) filings |
| `pretrend_balance.csv` | `05_pretrend_balance.R` | Instrument pre-trend / balance falsification |
| `wild_bootstrap_ar.csv` | `06_wild_bootstrap_ar.R` | Anderson–Rubin wild-cluster restricted bootstrap p-values |
| `multiplicity_adjusted.csv` | `07_multiplicity.R` | Holm + Benjamini–Hochberg family-wise correction |
| `fd_vs_ancova_comparison.csv` | `05_validation.R` | First-difference vs ANCOVA estimator comparison |
| `ancova_validation.csv` | `05_validation.R` | ANCOVA specification validation |
| `exposure_robust_se.csv` / `exposure_robust_akm.csv` | `07_exposure_robust_se.R` | AKM/BHJ exposure-robust standard errors |

### `output/tables/descriptives/` (CSV)

| File | Produced by | Contents |
|---|---|---|
| `candidate_pool_descriptives.csv` | `01_descriptives.py` | Candidate/elected pool composition by cycle |
| `overview_{lawsuits,voters,candidates}.csv` | `01_descriptives.py` | Scale-of-phenomenon overview tables |
| `litigation_composition.csv` / `litigation_family_shares.csv` | `01_descriptives.py` | Adversarial-litigation composition and family shares |
| `litigation_timing_panel.csv` | `01_descriptives.py` | Day-of-cycle litigation timing panel (feeds the timing figures) |
| `shift_descriptives.csv` | `01_descriptives.py` | BHJ shift table: g_k, mean shares, HHI contribution per topic |
| `rotemberg_weights.csv` | `04_iv_diagnostics.py` | GPS Rotemberg weights α_k and per-topic F_k |
| `gps_balance_tests.csv` | `04_iv_diagnostics.py` | Share balance: R², F-stat, p-value per top topic |

### `output/tables/tex/`

LaTeX table fragments `\input` into the deck and paper. Written directly (hand-built house
style) by `02_iv_main.R` (`firststage.tex`, the `executive_iv_*` and `appendix_*` fragments,
`entrant_typology.tex`), `02b_iv_legislative.R` (`legislative_iv_*`),
`04_placebo_nonadversarial.R` (`nonadversarial_*`), `05_pretrend_balance.R`
(`pretrend_*`, `open_seat_blank_rate.tex`), and `06_abstract_macros.py`
(`abstract_macros.tex`, `abstract_table.tex` — all deck/paper numbers). No `.md` tables are
produced: `.csv` is the numeric source of truth, `.tex` is the presentation fragment.

### `output/presentation/`

| File | Contents |
|---|---|
| `slides_report.tex` | Full report deck — Beamer source (all numbers pulled from `abstract_macros.tex`) |
| `slides_report.pdf` | Compiled report deck |

### `output/paper/`

| File | Contents |
|---|---|
| `paper.tex` / `paper.pdf` | Paper draft |
| `extended_abstract.tex` / `extended_abstract.pdf` | Extended abstract |
| `references.bib` | Bibliography |

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

# 4. Compile the report deck
cd output/presentation
pdflatex -interaction=nonstopmode slides_report.tex
pdflatex -interaction=nonstopmode slides_report.tex
```

> **Note:** The first run will download raw data from TSE and IBGE (~several GB).
> The estimation step takes approximately 5–10 minutes total.
