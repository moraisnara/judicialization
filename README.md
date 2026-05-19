# Judicialization and Electoral Competition in Brazil

**PhD dissertation project — Nara Lívia Morais, FEA-USP**

Causal identification of the effect of electoral court lawsuits on mayoral election outcomes
in Brazil, using a Bartik shift-share instrument built from TSE processual data.

---

## Directory Structure

```
judicialization/
├── data/
│   ├── raw/          — original downloads from TSE/IBGE, never modified
│   ├── clean/        — intermediate datasets produced by 02_build scripts
│   └── estimation/   — regression-ready design matrix (input to 03_analysis)
│
├── output/
│   ├── figures/      — all figures (PDF and PNG)
│   ├── tables/
│   │   ├── regressions/  — regression coefficients (CSVs + markdown)
│   │   └── descriptives/ — setup notes and summary statistics
│   └── presentation/ — Beamer slides (TeX source + compiled PDF)
│
├── code/
│   ├── 01_download/  — scripts that download raw data from TSE/IBGE
│   ├── 02_build/     — data cleaning and construction pipeline
│   ├── 03_analysis/  — estimation, heterogeneity, and figures
│   └── run_all.py    — runs the full pipeline end to end
│
├── docs/             — supplementary documentation
└── logs/             — pipeline run logs
```

---

## Data

### `data/raw/`

Original files downloaded from the TSE public data portal and IBGE. Never overwritten by any script.

| Folder / File | Contents |
|---|---|
| `processo_eleitoral_YYYY/` | Case-level docket registry (2018–2024) |
| `processos_eleitorais_assuntos_YYYY/` | Case × legal subject mapping |
| `processos_eleitorais_partes_2020/` | Case × party links |
| `decisoes_YYYY/` | Judicial decisions |
| `recursos_YYYY/` | Electoral appeals |
| `consulta_cand_YYYY/` | Candidate registry by state |
| `votacao_candidato_munzona_YYYY/` | Candidate vote counts by zone |
| `detalhe_votacao_munzona_YYYY/` | Aggregate vote detail by zone (turnout, null, blank) |
| `lista-zonas-municipios-10-07-24.csv` | Official TSE zone → municipality lookup |

### `data/clean/`

Intermediate datasets produced by the `02_build` pipeline. Derived from raw data
and used as inputs to subsequent build steps or to the analysis.

| File | Produced by | Contents |
|---|---|---|
| `zona_lawsuit_panel.csv` | `01_lawsuit_panel.py` | Zone × class × subject panel, pre-election cases |
| `shift_share_subject_crosswalk.csv` | manual | Subject code → litigation family mapping |
| `municipality_bartik_components.csv` | `02_bartik_inputs.py` | One row per (municipality, subject): Bartik component and baseline share |
| `municipality_competition_subject_panel.csv` | `02_bartik_inputs.py` | Panel (municipality, subject, year): lawsuit counts |
| `executive_shift_share_design.csv` | `02_bartik_inputs.py` | Executive design before vote outcomes are joined |
| `legislative_shift_share_design.csv` | `02_bartik_inputs.py` | Legislative design (placebo comparison) |
| `executive_vote_shift_share_design.csv` | `03_vote_outcomes.py` | Executive design with vote outcomes merged in |
| `legislative_vote_shift_share_design.csv` | `03_vote_outcomes.py` | Legislative design with vote outcomes |
| `candidate_vote_panel.csv` | `03_vote_outcomes.py` | Candidate-level vote panel |
| `office_candidate_outcomes_panel.csv` | `02_bartik_inputs.py` | Office-level candidate outcomes |
| `office_vote_outcomes_panel.csv` | `03_vote_outcomes.py` | Office-level vote outcomes |
| `censo2010_municipal_ibge.csv` | `04_census_covariates.R` | Census 2010: log pop, urban share, income per capita |
| `candidate_experience_panel.csv` | `05_candidate_history.py` | Prior candidacies and wins per municipality (2012–2024) |
| `electoral_admin_outcomes.csv` | `06_electoral_admin.py` | Turnout, blank/null share, registered voters (2020 and 2024) |
| `electoral_controls_2016.csv` | `07_electoral_controls_2016.py` | 2016 baseline: margin, HHI, ENP, winner identity |
| `municipal_covariates.csv` | `08_municipal_covariates.py` | Master covariate table (merges all of the above) |
| `zona_eleitoral_lookup.csv` | `01_lawsuit_panel.py` | Zone-level lookup table |

### `data/estimation/`

The single flat file that enters the regressions. Produced by `03_analysis/01_assemble_design.py`
by merging the executive design, Bartik components, subject panel, and master covariates.

| File | Contents |
|---|---|
| `executive_margin_design.csv` | One row per municipality, N ≈ 5,571. Contains instrument (`bartik_iv_no_rrc`), treatment (`delta_log1p_lawsuits_no_rrc_2024_2020`), all outcomes, all controls, and clustering identifier (`cluster_id`). |

---

## Code

### `code/01_download/`

Scripts that download and verify raw data. Run once before the build pipeline.

| Script | Purpose |
|---|---|
| `00_verify_raw_data.py` | Checks that expected raw files exist |
| `01_download_processual.py` | Downloads TSE processual docket files |
| `02_download_candidate_data.py` | Downloads TSE candidate registry files |
| `02_download_covariates_data.py` | Downloads vote results and detalhe_votacao files |
| `03_download_vote_results.py` | Downloads vote count files |

### `code/02_build/`

Sequential pipeline that transforms raw data into analysis-ready inputs. Output always goes to `data/clean/`.

| Script | Inputs | Output |
|---|---|---|
| `00_verify_processual.py` | `data/raw/` | Log to `logs/` |
| `01_lawsuit_panel.py` | processual + assuntos + zone lookup | `zona_lawsuit_panel.csv` |
| `02_bartik_inputs.py` | zona_lawsuit_panel + crosswalk + consulta_cand | `municipality_bartik_components.csv`, `municipality_competition_subject_panel.csv`, `executive_shift_share_design.csv`, `legislative_shift_share_design.csv` |
| `03_vote_outcomes.py` | executive/legislative designs + votacao files | `executive_vote_shift_share_design.csv`, `candidate_vote_panel.csv` |
| `04_census_covariates.R` | censobr (downloads automatically) | `censo2010_municipal_ibge.csv` |
| `05_candidate_history.py` | consulta_cand 2012–2024 | `candidate_experience_panel.csv` |
| `06_electoral_admin.py` | detalhe_votacao_munzona 2020+2024 | `electoral_admin_outcomes.csv` |
| `07_electoral_controls_2016.py` | votacao_candidato_munzona_2016 | `electoral_controls_2016.csv` |
| `08_municipal_covariates.py` | censo2010 + electoral_controls + candidate_experience + electoral_admin | `municipal_covariates.csv` |

### `code/03_analysis/`

Estimation and output scripts. All IV estimation is done in R via `fixest::feols()`.

| Script | Purpose | Output |
|---|---|---|
| `01_assemble_design.py` | Merges clean data into regression-ready flat file | `data/estimation/executive_margin_design.csv` |
| `02_iv_main.R` | Main 2SLS: 6 specs × 6 outcomes via `feols()` | `output/tables/regressions/executive_margin_iv_fixest.csv` |
| `03_heterogeneity.py` | Subgroup IV: ideology, volatility, incumbency, gender | `output/tables/regressions/extended_heterogeneity_iv.csv` |
| `04_figures_descriptive.py` | Descriptive figures (family composition, Bartik breakdown) | `output/figures/*.png` |
| `05_figures_causal.R` | Causal figures: binscatter, forest plot, IV histogram, choropleth | `output/figures/*.pdf` |

### `code/run_all.py`

Runs the full pipeline in the correct order: `01_download` → `02_build` → `03_analysis`.
R scripts are called via `Rscript`; Python scripts via `sys.executable`.

---

## Output

### `output/figures/`

| File | Produced by | Description |
|---|---|---|
| `binscatter_first_stage.pdf` | `05_figures_causal.R` | Binscatter: Bartik IV → Δlog(lawsuits) |
| `forest_voter_behavior.pdf` | `05_figures_causal.R` | Forest plot: voter behavior outcomes, 6 specs |
| `bartik_histogram.pdf` | `05_figures_causal.R` | Distribution of the IV (residualized on state FE) |
| `bartik_choropleth.pdf` | `05_figures_causal.R` | Geographic distribution of the IV across Brazil |
| `family_composition_2020_2024.png` | `04_figures_descriptive.py` | Case composition by litigation family |
| `instrument_concentration_compare.png` | `04_figures_descriptive.py` | HHI before/after RRC exclusion |

### `output/tables/regressions/`

| File | Contents |
|---|---|
| `executive_margin_iv_fixest.csv` | 2SLS estimates: 6 specs × 6 outcomes (fixest) |
| `executive_margin_first_stage_fixest.csv` | First-stage estimates: F-stats, coefs, N |
| `executive_margin_fixest.md` | Formatted markdown summary |
| `extended_heterogeneity_iv.csv` | Heterogeneity IV estimates |
| `extended_heterogeneity_iv.md` | Formatted markdown summary |

### `output/tables/descriptives/`

| File | Contents |
|---|---|
| `office_shift_share_setup.md` | Shift-share design summary (sample sizes, top topics) |
| `vote_outcomes_setup.md` | Vote outcome construction summary |

### `output/presentation/`

| File | Contents |
|---|---|
| `electoral_judicialization.tex` | Beamer source (57 slides, `\usetheme{default}`) |
| `electoral_judicialization.pdf` | Compiled presentation |

---

## How to Reproduce

```bash
# 1. Install Python dependencies
pip install pandas numpy statsmodels linearmodels

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

> **Note:** The first run will download raw data (~several GB).
> The estimation step (`02_iv_main.R`) takes approximately 2–5 minutes.
