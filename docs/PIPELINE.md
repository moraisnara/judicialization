# PIPELINE.md — the clean script chain (act-based design, 2026-06-26)

The ordered list of scripts that turn raw TSE/SIG data into the estimation
design, and the merge discipline that joins the instrument to the outcomes. This
is the live chain after the act-based redesign; the old zona / `subject_taxonomy_v3`
engines are in `code/_archive/`. The authoritative current-truth doc is
`docs/STATE_OF_THE_ART.md`.

**One key, never names.** The municipality join key is the TSE code,
`municipality_id_tse`, a zero-padded **5-char string** everywhere (integer
coercion silently drops leading-zero codes). The litigation join key is the
integer **`pair_id`** (one per distinct `(classe, assunto)`); the ~50-char
classe/assunto names never appear in any merge or estimation file. Official
CNJ/TSE codes ride along reference-only and are never a merge key.

## The design in one line

A **single** topic shift-share (Bartik) instrument and a **single** endogenous
treatment, built on a **flat 10-family** act-based taxonomy:

- Instrument: **`bartik_iv_act`** (act-based 10-family municipality shift-share).
- Endogenous treatment: **`delta_log1p_act_lawsuits`** (Δlog(1+kept act lawsuits),
  2020→2024).
- Families (flat, NOT a granularity ladder): `abuso`, `vote_buying`, `finance`,
  `inelegib`, `fraude`, `honra`, `direito_resposta`, `conduta_vedada`,
  `pesquisa_adv`, `ballot_integrity`.
- Cluster: **state** (27 UFs; `cluster_id`). First-stage **F ≈ 25.5**, K_eff ≈ 6.8.

There is **no aggregation ladder, no rung pivot, and no per-rung
`bartik_iv_<rung>` / `delta_log1p_kept_<rung>` columns.** The old substance-family
rungs (`fine7`, `theme9`, `subst13`, …) and the alias
`bartik_iv_2020_2024 = bartik_iv_fine7` are retired. Both columns are read from
`code/spec_config.json` (`instrument` / `endogenous`).

## Stage 0–2 — build (`code/02_build/`)

Run in this order. The instrument branch has a hard ordering dependency:
**01 → 00 → 01d** (01 mints `pair_id` + the substance crosswalk; 00 stamps
`pair_id` onto the panel; 01d routes each pair to one of the 10 act families).

| # | Script | Reads | Writes |
|---|--------|-------|--------|
| 1 | `01_family_crosswalk.py` | SIG processos zips (raw) | `sig_family_crosswalk.csv` — `(classe,assunto)`→substance family + `pair_id` dictionary |
| 2 | `00_sig_lawsuit_panel.py` | SIG zips + crosswalk (`pair_id`) | `sig_lawsuits_muni_zona_classe_assunto.csv` joint panel, keyed on `pair_id` (names dropped) |
| 3 | `01d_act_family_crosswalk.py` | joint SIG panel + `pair_id` dictionary | `data/clean/act_family_crosswalk.csv` — pair_id → one of the 10 act families (column `fam_act10`) |
| 4 | `03_candidate_composition.py` | `consulta_cand_{2020,2024}` + zone lookup | `office_candidate_outcomes_panel.csv`, `executive_shift_share_design.csv`, `legislative_shift_share_design.csv` (composition OUTCOMES only — no instrument) |
| 5 | `03b_vote_outcomes.py` | the two `*_shift_share_design.csv` + votacao files | `executive_vote_shift_share_design.csv`, `legislative_vote_shift_share_design.csv` |

Other `02_build` scripts (`04_candidate_history`, `04b_council_history`,
`05_electoral_admin`, …) build covariate/outcome side-inputs and are unchanged.

The **instrument** (Bartik) and the **outcomes** (composition + vote) are built on
two independent branches that never touch until the Stage-3 merge. Each carries
its own clean key, so the join is exact.

### Lawsuit data source

The litigation panel is **SIG TSE "Processos eleitorais" municipality microdata**,
which resolves each lawsuit to its município de origem. This **replaced the old
zona-level reconstruction** (and its connected-component municipality unit). 2016
is not available in SIG (no pre-period placebo from this source).

## Stage 3 — assemble / build instrument (`code/03_estimation/`)

Run **01 → 01d → 02c**.

| # | Script | Produces |
|---|--------|----------|
| 1 | `01_assemble_design.py` | `data/estimation/executive_margin_design.csv` — the **instrument-free** base design (outcomes + controls) |
| 2 | `01d_act_family_ivs.py` | adds `bartik_iv_act` + `delta_log1p_act_lawsuits` → writes `data/estimation/act_design.csv`, and the long muni×family decomposition `data/clean/municipality_act_components.csv` (`rung=='act'`, for Rotemberg / shift / balance / leave-one-out diagnostics) |
| 3 | `02c_act_iv.R` | R/fixest first stage + headline 2SLS over all outcomes (with tF) → `output/tables/regressions/act_*_fixest.csv` |

### Instrument construction (`01d_act_family_ivs.py`)

```
B_i = Σ_k  s_ik(2020 share in family k)  ×  g_ik(leave-own-state-out 2020→2024 log-growth shock)
```

- `s_ik` = municipality i's 2020 share of lawsuits in act family k.
- `g_ik` = national 2020→2024 log-growth of family k, **leaving i's own state out**
  (`g = log(N24 − S24 + 1) − log(N20 − S20 + 1)`).
- A **single** `bartik_iv_act` column results — no per-rung pivot, because there is
  only one taxonomy (the flat 10 act families), not a ladder of rungs.

### Merge discipline (what "done correctly" means here)

The user requirement was: no many-to-many merges, no duplication. The assemble
enforces it mechanically:

1. **The long act-component table is collapsed to one row per municipality before
   merging.** `municipality_act_components.csv` is long (muni×family); it is
   summed into the single `bartik_iv_act` per muni, then merged one-to-one onto the
   base design. Collapsing first is what prevents the row-multiplying broadcast that
   inflated the old (zona→muni many-to-many) design.
2. **Every merge passes an explicit `validate=`** (`one_to_one` on the full key,
   `m:1` for lookup joins). pandas raises on any many-to-many key — a hard guard,
   not a check we have to remember to read.
3. **A merge ledger prints rows-in→rows-out and unmatched count** for every join.
   Row count must not change on a left join.

### Headline instrument + cluster

- Headline instrument `bartik_iv_act`; endogenous `delta_log1p_act_lawsuits`. Both
  are read from `code/spec_config.json`, so the downstream R scripts never hard-code
  the column names.
- `cluster_id` = **state**: the leave-own-state shift is common to all
  municipalities within a state, so the state is the level at which the
  instrument's identifying variation is shared. (Older comments naming an
  "electoral zone" cluster are misleading — clustering is state-level, 27 UFs.)

### Coverage

Municipalities in the composition universe that have any kept-act litigation get an
instrument; municipalities with no kept-act litigation have `bartik_iv_act` = NA
(not zero). The headline second stage runs on n ≈ 5,009 after also requiring full
controls.

## Stage 3 — downstream IVs

Once `act_design.csv` exists, the decided outcome groups and heterogeneity cuts run
off it (config-driven via `spec_config.json` → act): `03_voter_behavior_iv.R`,
`04_candidate_outcomes_iv.R`, and the heterogeneity scripts
(`06_heterogeneity_polls.R` … `10_heterogeneity_pop_x_atlas.R`). Diagnostics
(Rotemberg weights, BHJ shift descriptives, GPS balance, exposure-robust SEs) read
`municipality_act_components.csv`.

**Estimation-stack rule:** all regression OUTPUTS (first stage, 2SLS, any
coefficient/SE/F that could reach a slide or the paper) run in **R/fixest**. Python
is for data construction and pure descriptives only.

## Full rebuild

`python code/run_all.py` runs the whole chain in the order above (the `02 Build`
block sequences 01→00→01d for the instrument, then 03→03b for outcomes; Stage 3
runs 01→01d→02c).
