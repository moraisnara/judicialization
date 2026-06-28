"""
Full pipeline runner — ACT-BASED design (2026-06-26).

Run from the project root:
  python code/run_all.py

R scripts are called via Rscript and must be on PATH (or edit RSCRIPT below).

Stage overview:
  01 download   — pull raw TSE / census / poll / atlas / SPCE data
  02 build      — clean panels, build the act-based 10-family taxonomy, assemble
                  covariates and outcome panels
  03 estimation — assemble the base design, build the act shift-share instrument
                  (bartik_iv_act) + components, run the headline 2SLS and the
                  voter / candidate / heterogeneity / mechanism IVs
  04 analysis   — descriptives, figures, Rotemberg / BHJ shift-share diagnostics

CURRENT DESIGN (see docs/STATE_OF_THE_ART.md):
  instrument  = bartik_iv_act           (act-based 10-family municipality shift-share)
  endogenous  = delta_log1p_act_lawsuits
  built by    01d_act_family_crosswalk.py -> 01d_act_family_ivs.py
  config      code/spec_config.json (instrument/endogenous/controls; read by the R scripts)

PENDING ACT REPOINT (NOT in the active pipeline below — still on the retired
substance-family instrument; need per-family act columns or a legislative act build):
  03_estimation/01b_assemble_legislative_design.py   (legislative reuses exec instrument)
  03_estimation/05_cluster_robustness.R              (config-driven; needs design repoint)
  03_estimation/11_family_iv_channels.R              (per-family bartik_iv_<family> cols)
  03_estimation/12_mechanism_blocks_iv.R             (per-family / block instruments)
  04_analysis/11_inference_robustness.R              (reads old municipality_bartik)
  04_analysis/15_report_descriptives.py              (fam_{rung} crosswalk + theme9 labels)
  04_analysis/21_leave_one_family_out.R              (per-family bartik_iv_<family> cols)
  04_analysis/22_exposure_robust_se.R                (expects per-family bartik_iv_* design cols)
"""
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RSCRIPT = "Rscript"


def run_py(relative_path: str) -> None:
    script_path = PROJECT_ROOT / relative_path
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=PROJECT_ROOT)


def run_r(relative_path: str) -> None:
    script_path = PROJECT_ROOT / relative_path
    subprocess.run([RSCRIPT, str(script_path)], check=True, cwd=PROJECT_ROOT)


def main() -> None:
    print(f"Pipeline root: {PROJECT_ROOT}\n")

    print("=== 01 Download ===")
    run_py("code/01_download/00_verify_raw_data.py")
    run_py("code/01_download/01_download_processual.py")
    run_py("code/01_download/02_download_candidate_data.py")
    run_py("code/01_download/02_download_covariates_data.py")
    run_py("code/01_download/03_download_tpu_assuntos.py")    # TPU subject reference (crosswalk input)
    run_py("code/01_download/03b_download_tpu_classes.py")    # TPU class reference (crosswalk input)
    run_py("code/01_download/04_build_subject_reference.py")
    run_py("code/01_download/04_download_vote_results.py")
    run_r("code/01_download/05_download_census_covariates.R")
    run_r("code/01_download/06_download_municipality_crosswalk.R")
    run_py("code/01_download/09_download_bd_municipio_directory.py")  # name+UF->IBGE for SIG panel
    run_py("code/01_download/07_download_polls.py")
    run_r("code/01_download/08_download_poder360_coverage.R")
    run_py("code/01_download/09_download_spce.py")
    run_r("code/01_download/10_download_atlas_noticias.R")
    run_py("code/01_download/11_download_comparecimento_abstencao.py")  # disaggregated turnout

    print("\n=== 02 Build ===")
    run_py("code/02_build/00_verify_processual.py")
    run_py("code/02_build/00b_check_tr_mapping.py")          # validates TR->state mapping
    # --- SIG lawsuit panel + act-based 10-family crosswalk ---
    # ORDER MATTERS: 01 mints the (classe,assunto) pair_id dictionary + the substance
    # crosswalk (sig_family_crosswalk.csv); 00 stamps pair_id onto the joint lawsuit
    # panel; 01d routes each pair to one of the 10 ACT families (act_family_crosswalk.csv).
    run_py("code/02_build/01_family_crosswalk.py")
    run_py("code/02_build/00_sig_lawsuit_panel.py")
    run_py("code/02_build/01d_act_family_crosswalk.py")
    # --- candidate-composition + vote outcomes + covariates (instrument-free) ---
    run_py("code/02_build/03_candidate_composition.py")
    run_py("code/02_build/03b_vote_outcomes.py")
    run_py("code/02_build/04_candidate_history.py")
    run_py("code/02_build/04b_council_history.py")
    run_py("code/02_build/05_electoral_admin.py")
    run_py("code/02_build/05b_office_ballot_spoilage.py")     # per-office blank/null + roll-off
    run_py("code/02_build/05c_comparecimento_disaggregated.py")  # turnout by voter trait
    run_py("code/02_build/05d_voter_disaggregated_outcomes.py")  # facultative/low-ed turnout outcomes
    run_py("code/02_build/06_electoral_controls_2016.py")
    run_py("code/02_build/07_municipal_covariates.py")
    run_py("code/02_build/08_poll_activity.py")
    run_r("code/02_build/09_poder360_trajectory.R")
    run_py("code/02_build/10_spce_build.py")
    run_r("code/02_build/11_build_atlas_noticias.R")

    print("\n=== 03 Estimation ===")
    run_py("code/03_estimation/01_assemble_design.py")        # instrument-free base design
    run_py("code/03_estimation/01d_act_family_ivs.py")        # + bartik_iv_act, act components
    run_r("code/03_estimation/02c_act_iv.R")                  # HEADLINE 2SLS (on-spec: 5 ctrls + lagged DV, tF)
    run_r("code/03_estimation/02d_leave_fraude_robustness.R") # Rotemberg leave-one-family-out (fraude/pesquisa/abuso)
    # decided outcome groups (config-driven via spec_config.json -> act):
    run_r("code/03_estimation/03_voter_behavior_iv.R")        # voter behaviour (aggregate)
    run_r("code/03_estimation/03b_voter_disaggregated_iv.R")  # facultative/low-ed turnout (+leave-fraude)
    run_r("code/03_estimation/04_candidate_outcomes_iv.R")    # candidate / composition outcomes
    # heterogeneity (hardcoded instrument -> act):
    run_r("code/03_estimation/06_heterogeneity_polls.R")
    run_r("code/03_estimation/07_iv_mechanism_media.R")
    run_r("code/03_estimation/08_heterogeneity_atlas.R")
    run_r("code/03_estimation/09_heterogeneity_population.R")
    run_r("code/03_estimation/10_heterogeneity_pop_x_atlas.R")

    print("\n=== 04 Analysis ===")
    run_py("code/04_analysis/00_candidate_descriptives.py")
    run_py("code/04_analysis/02_descriptives_overview.py")
    run_r("code/04_analysis/02_figures_causal.R")
    run_r("code/04_analysis/03_map_data_universe.R")
    run_py("code/04_analysis/05_rotemberg_weights.py")        # Rotemberg weights + F_k (act components)
    run_py("code/04_analysis/08_gps_balance_tests.py")        # share balance tests
    run_py("code/04_analysis/10_shift_descriptives.py")       # BHJ shift table
    run_py("code/04_analysis/20_summary_stats.py")
    run_r("code/04_analysis/23_mde_power.R")                  # MDE / bounding for the null defense
    run_py("code/04_analysis/24_shock_granularity.py")        # K_eff + instrument at act10/subject/pair grain
    run_r("code/04_analysis/24b_shock_granularity_fstage.R")  # first-stage F + 2SLS by grain
    run_r("code/04_analysis/24c_shock_granularity_figure.R")  # AMV-style estimate-vs-grain robustness figure
    run_py("code/04_analysis/13_poll_coverage_report.py")
    run_py("code/04_analysis/15_spce_descriptives.py")
    run_r("code/04_analysis/16_atlas_noticias_maps.R")
    # --- current SIG descriptives ---
    run_py("code/04_analysis/30_sig_subject_shares.py")
    run_py("code/04_analysis/31_sig_class_shares.py")
    run_py("code/04_analysis/32_sig_coding_compatibility.py")
    run_py("code/04_analysis/33_sig_class_subject_breakdown.py")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
