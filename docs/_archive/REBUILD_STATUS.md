> **⚠️ ARCHIVED / STALE — superseded by `docs/STATE_OF_THE_ART.md` (2026-06-26).**
> This document describes the RETIRED substance-family / connected-component design (with the
> old female-candidate headline). It is kept only as version history. For the current act-based
> 10-family design, the authoritative source is `docs/STATE_OF_THE_ART.md` and `code/spec_config.json`.
> _Reason this file is stale:_ it audits the old-lineage cascade where `sig_family_crosswalk.csv` was an ORPHAN and downstream scripts still ran on the substance rungs; that rebuild has since landed on the act-based `bartik_iv_act` chain.

# REBUILD_STATUS.md — SIG-family rebuild controller

Purpose: account for **every** script during the rebuild that follows the SIG
family-crosswalk redesign (see `docs/SIG_DESIGN_LOG.md`). Nothing is "done" until
every row below is `CURRENT`, `NEUTRAL`, or moved out of the live tree
(`ARCHIVE`/`DELETE`). This is the companion to `WORKFLOW.md` (which closes an
*outcome group*); this file governs the *cascade* the redesign triggers.

Last audited: 2026-06-24 (read-only I/O audit of all ~60 scripts).

## The headline finding

**The new `sig_family_crosswalk.csv` is currently an ORPHAN.** Built by
`01_family_crosswalk.py`, but *no downstream script reads it yet*. Everything in
`03_estimation/` and most of `04_analysis/` still runs on the OLD lineage
(`subject_taxonomy_v3.csv` → `zona_lawsuit_panel.csv` → component/`class_folded`
instrument → `executive_margin_design.csv`).

So the rebuild has three phases, not one:
1. **BUILD THE BRIDGE** (new script, does not exist): SIG panels + family
   crosswalk → municipality-level family Bartik components on the aggregation
   ladder. This is the single missing link; until it exists nothing can be ported.
2. **PORT** estimation/figures/tables onto the bridge output.
3. **ARCHIVE** the superseded zona/component/`subject_taxonomy_v3` engine.

## Verdict tags

- `CURRENT` — already on the SIG-family design; rerun as-is.
- `BRIDGE` — **must be written** (gap); the redesign has no equivalent yet.
- `PORT` — needed under the new design but still reads OLD inputs → rewire to the
  family lineage, then rerun.
- `NEUTRAL` — reads only raw TSE candidate/vote/covariate/admin/poll/finance/news
  data; reusable as-is, rerun only if its raw upstream changes.
- `ARCHIVE` — superseded engine of the OLD design. `git mv` to `code/_archive/`
  (preserved as a version, per the design-not-settled directive). NOT deleted.
- `DELETE` — pure regenerable junk / dead one-off (none proposed here).

## Dependency order (the new chain)

```
RAW (data/raw/*)
 └─ 00_sig_lawsuit_panel.py ............ CURRENT  → sig_lawsuits_muni_zona_{assunto,classe}.csv
     └─ 01_family_crosswalk.py ......... CURRENT  → sig_family_crosswalk.csv  (+ coverage)
         └─ [BRIDGE] family bartik builder  ← TO WRITE → municipality_family_components.csv (per ladder rung)
             └─ [PORT] assemble design ...→ data/estimation/<new>_design.csv
                 └─ [PORT] estimation IV (voter / candidate / hetero / mechanism)
                     └─ [PORT] figures, tables, report frames
NEUTRAL covariate feeders (04,04b,05,05b,06,07,08,09,10,11) ─┘ merge into assemble
```

---

## 02_build/

| Script | Verdict | Reads → Writes | Note |
|---|---|---|---|
| 00_sig_lawsuit_panel.py | CURRENT | raw SIG zips → sig_lawsuits_muni_zona_{assunto,classe}.csv | New panel foundation |
| 01_family_crosswalk.py | CURRENT | raw SIG zips → sig_family_crosswalk.csv, sig_family_coverage.csv | Family map + ladder (just rebuilt) |
| 00_verify_processual.py | NEUTRAL | raw TSE lawsuit files → inventory.csv | Raw-data validation |
| 00b_check_tr_mapping.py | NEUTRAL | raw → tr_mapping_validation.csv | TR-code check |
| 04_candidate_history.py | NEUTRAL | consulta_cand 2012–2024 → candidate_experience_panel.csv | Mayor experience |
| 04b_council_history.py | NEUTRAL | consulta_cand 2012–2024 → council_experience_panel.csv | Council experience |
| 05_electoral_admin.py | NEUTRAL | detalhe_votacao → electoral_admin_outcomes.csv | Turnout/blank/null |
| 05b_office_ballot_spoilage.py | NEUTRAL | detalhe_votacao → office_ballot_spoilage.csv | Per-office spoilage |
| 06_electoral_controls_2016.py | NEUTRAL | votacao 2016 → electoral_controls_2016.csv | 2016 baseline controls |
| 07_municipal_covariates.py | NEUTRAL | census + 2016 + experience → municipal_covariates.csv | Master covariates |
| 08_poll_activity.py | NEUTRAL | pesquisa_eleitoral → poll_activity_{panel,design}.csv | Poll activity |
| 09_poder360_trajectory.R | NEUTRAL | basedosdados API → poder360_trajectory.rds | Poll trajectory |
| 10_spce_build.py | NEUTRAL | despesas_candidatos → spce spending | Campaign finance |
| 11_build_atlas_noticias.R | NEUTRAL | atlas raw → atlas_noticias.csv | News ecosystem |
| 03_vote_outcomes.py | PORT | consulta_cand, votacao, **executive_shift_share_design** → vote panels + *_vote_shift_share_design | Vote outcomes; currently welded to OLD shift-share files — rewire to new design key |
| 02_bartik_inputs.py | ARCHIVE→**replace by BRIDGE** | zona_lawsuit_panel + **subject_taxonomy_v3** → bartik_iv_*_design.csv | OLD subject-taxonomy shift-share builder; the BRIDGE supersedes it |
| 01a0_taxonomy_worksheet.py | ARCHIVE | tpu_assunto_reference → taxonomy_review_worksheet.csv | Builds the OLD subject_taxonomy_v3 lineage |
| 01a_build_taxonomy.py | ARCHIVE | worksheet → **subject_taxonomy_v3.csv** | The OLD taxonomy the family crosswalk replaces |
| 05c_zona_voter_design.py | ARCHIVE | detalhe_votacao + 02_bartik shocks → zona_voter_design.csv | Zona-unit design; built to fight zona-nesting that SIG fixes at source |
| 05d_component_voter_design.py | ARCHIVE | component crosswalk → component_voter_design.csv | Connected-component design; same — SIG muni-resolves |
| 05e_component_election_design.py | ARCHIVE | component crosswalk → component_{exec,leg}_design.csv | Component election outcomes |
| instrument/ (whole folder, 10 files) | ARCHIVE | zona_lawsuit_panel, tpu, class_folded → component instruments | The OLD component/`class_folded` instrument engine end-to-end |

---

## 03_estimation/

| Script | Verdict | Note |
|---|---|---|
| 01_assemble_design.py | PORT | Assembles exec design from OLD component instrument + covariates → rewire to BRIDGE output |
| 01b_assemble_legislative_design.py | PORT | Legislative design, inherits instrument from exec → same |
| 01c_family_ivs.py | PORT | Adds family IVs from **municipality_bartik_components** (OLD components) → repoint to new family components |
| 04_candidate_outcomes_iv.R | PORT | Candidate outcome IV groups A–E; reads exec/leg design → rerun on new design |
| 06_heterogeneity_polls.R | PORT | Heterogeneity by poll activity |
| 07_iv_mechanism_media.R | PORT | SPCE finance mechanism |
| 08_heterogeneity_atlas.R | PORT | News-desert heterogeneity |
| 09_heterogeneity_population.R | PORT | Population heterogeneity |
| 10_heterogeneity_pop_x_atlas.R | PORT | Pop × news-desert |
| 03_voter_behavior_iv.R | PORT | Voter behavior IV (full sample) on muni design |
| _voter_behavior_core.R | PORT | Shared voter engine sourced by 03/03b |
| 03b_voter_behavior_single_zone.R | ARCHIVE | Single-zone heterogeneity (zona apparatus) |
| 03c_voter_behavior_zona.R | ARCHIVE | Estimated at zona unit |
| 03d_voter_behavior_component.R | ARCHIVE | Component-unit voter behavior |
| 03e_election_outcomes_component.R | ARCHIVE | Component-unit election outcomes |
| 03f_null_diagnostics.R | ARCHIVE | Diagnostics on component null results |
| 03d_version_first_stage.R | ARCHIVE | First stage across OLD taxonomy versions (G3–B10) |
| 01h_version_instruments.py | ARCHIVE | Builds OLD taxonomy-version instruments (lives in 03? — it builds, archive with taxonomy engine) |

---

## 04_analysis/

| Script | Verdict | Note |
|---|---|---|
| 30_sig_subject_shares.py | CURRENT | SIG assunto shares |
| 31_sig_class_shares.py | CURRENT | SIG classe shares |
| 32_sig_coding_compatibility.py | CURRENT | Nestedness / cross-TRE stability |
| 33_sig_class_subject_breakdown.py | CURRENT | Subjects per class bucket |
| 02_figures_causal.R | PORT | Main IV figures; reads exec_margin_design → rerun on new design |
| 05_rotemberg_weights.py | PORT | Rotemberg weights; reads OLD components → repoint to family components |
| 08_gps_balance_tests.py | PORT | GPS balance + pre-trend |
| 10_shift_descriptives.py | PORT | Shock dispersion/HHI; repoint to family components |
| 15_report_descriptives.py | PORT | Report macros; reads subject_taxonomy_v3 → family crosswalk |
| 18_specifications.py | PORT | Spec tables from fixest output |
| 20_summary_stats.py | PORT | Summary stats from design |
| 21_leave_one_family_out.R | PORT | Leave-one-family-out (maps naturally onto family ladder) |
| 22_exposure_robust_se.R | PORT | BHJ/AKM exposure-robust SEs |
| 02_descriptives_overview.py | PORT | Scale-of-phenomenon counts; reads zona_lawsuit_panel → SIG panels |
| 00_candidate_descriptives.py | NEUTRAL | Candidate demographics (reads vote panels) |
| 13_poll_coverage_report.py | NEUTRAL | Poll coverage audit |
| 15_spce_descriptives.py | NEUTRAL | Spending exposure |
| 16_atlas_noticias_maps.R | NEUTRAL | News maps |
| 16_candidate_descriptives.py | NEUTRAL | Candidate vs elected composition |
| 17_electorate_descriptives.py | NEUTRAL | Electorate metrics |
| 19_candidate_experience.py | NEUTRAL | Prior experience distribution |
| 23_mde_power.R | NEUTRAL | MDE/power (reads result CSVs; rerun last) |
| 03_map_data_universe.R | NEUTRAL | Zone geographic coverage map |
| 24_rotemberg_voter.R | ARCHIVE | Voter Rotemberg on OLD components |
| 19_instrument_selection.py | ARCHIVE | OLD taxonomy-version horse-race |
| 02b_figures_zona.R | ARCHIVE | Zona-unit figures |
| 02c_zona_spec_ladder.R | ARCHIVE | Zona spec ladder |
| 02d_zona_cluster_design.py | ARCHIVE | Component dedup design (OLD) |
| 02e_component_figures.R | ARCHIVE | Component figures |
| 02f_component_instrument_diagnostics.py | ARCHIVE | OLD shock variance decomposition |
| 02g_class_dimension_audit.py | ARCHIVE | OLD class×subject audit (superseded by 32/33) |
| 02h_joint_taxonomy_proposal.py | ARCHIVE | OLD joint-taxonomy proposal (superseded by family crosswalk) |
| 02i_joint_component_firststage.py | ARCHIVE | OLD joint component first stage |
| 02j_leaveout_level_test.py | ARCHIVE | OLD leave-out level test |
| 02k_keep_drop_full_audit.py | ARCHIVE | OLD keep/drop audit (superseded by family coverage) |
| 25_family_shock_independence.py | ARCHIVE | OLD 9-family shock independence |

---

## Decision (2026-06-24): the `?` rows are ARCHIVE

DECIDED: the zona/connected-component apparatus is **retired**. The new SIG design
is **municipality-unit only**. The component machinery existed to fix the
zona→municipality duplication that inflated the first stage; SIG is
*município-resolved at source*, so that problem is gone. All previously-`?` rows
(05c/05d/05e build; 03b/03c/03d/03d_version/03e/03f estimation; 02b/02c/02e/24
analysis) are now `ARCHIVE`. They are preserved as a recoverable version
(`git mv` to `code/_archive/`), never deleted.

## Cross-cutting safeguards (proposed, not yet done)

1. `git tag pre-sig-rebuild` now — names the entire OLD-design state as a recoverable version.
2. Quarantine OLD data artifacts (`zona_lawsuit_panel.csv`, `municipality_bartik_components.csv`, `*_shift_share_design.csv`, `executive_margin_design.csv`, `legislative_design.csv`, component/zona designs) by `git mv` into `data/_stale_olddesign/` so any un-ported script **fails loudly** instead of silently reading old data.
3. Build manifest: each build script stamps source + date into `data/clean/_BUILD_MANIFEST.csv`; assemble asserts inputs are newer than the crosswalk.
4. Rewrite `run_all.py` to call ONLY `CURRENT` + `BRIDGE` + ported scripts in the dependency order above.
