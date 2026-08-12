"""
Full pipeline runner.

Run from the project root:
  python code/run_all.py

R scripts are called via Rscript and must be on PATH.
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
    run_py("code/01_download/01_lawsuits.py")                    # TSE processual docket (lawsuits)
    run_py("code/01_download/02_candidates.py")                  # candidate registry (2020/2024)
    run_py("code/01_download/03_historical_elections.py")            # 2016 votes + 2012/16 candidates + detalhe_votacao
    run_py("code/01_download/04_votes.py")                       # candidate vote counts (2020/2024)
    run_r("code/01_download/05_municipal_characteristics.R")     # Census 2010 municipal covariates
    run_r("code/01_download/06_municipality_crosswalk.R")        # IBGE <-> TSE crosswalk

    print("\n=== 02 Build ===")
    run_py("code/02_build/00_verify_lawsuits.py")
    run_py("code/02_build/01_lawsuit_panel.py")
    run_py("code/02_build/02_shift_share_design.py")
    # 04 before 03: vote_outcomes merges the candidate_experience_flags.csv that
    # candidate_history writes, so history must run first (on a clean clone the flags
    # would otherwise be missing and the experience vote-shares silently NaN).
    run_py("code/02_build/04_candidate_history.py")
    run_py("code/02_build/03_vote_outcomes.py")
    run_py("code/02_build/05_turnout_ballot_outcomes.py")
    run_py("code/02_build/06_turnout_profile_panel.py")    # raw perfil -> long turnout panel
    run_py("code/02_build/07_turnout_profile_outcomes.py")   # long panel -> wide voter outcomes (feeds design)
    run_py("code/02_build/08_electoral_controls_2016.py")
    run_py("code/02_build/09_municipal_covariates.py")
    run_py("code/02_build/10_candidate_finance.py")          # SPCE campaign spend by vote rank (mechanism)

    print("\n=== 03 Estimation ===")
    run_py("code/03_estimation/01_assemble_design.py")
    run_py("code/03_estimation/01b_assemble_legislative_design.py")
    run_py("code/03_estimation/01c_patch_family_ivs.py")         # add family IVs before R estimation
    run_r("code/03_estimation/02_iv_main.R")
    run_r("code/03_estimation/02b_iv_legislative.R")
    run_r("code/03_estimation/04_placebo_nonadversarial.R")      # placebo shift-share + intensity control
    run_r("code/03_estimation/05_pretrend_balance.R")            # instrument pre-trend falsification
    run_r("code/03_estimation/06_wild_bootstrap_ar.R")           # AR wild-cluster bootstrap inference
    run_r("code/03_estimation/07_multiplicity.R")                # FWER/FDR correction (needs main IV CSV)
    run_r("code/03_estimation/09_extensive_margin.R")            # extensive-vs-intensive margin decomposition (audit #10 companion)
    run_r("code/03_estimation/10_mechanism_finance.R")           # resource-drain mechanism: campaign spend by vote rank x seat type
    run_r("code/03_estimation/11_summary_indices.R")             # summary indices (Anderson/KLK) + Romano-Wolf stepdown (decision-free multiplicity)
    run_r("code/03_estimation/12_treatment_definition.R")        # treatment-form robustness: log1p/IHS/levels/rate/binary (same Bartik)
    run_r("code/03_estimation/13_reclassification_robustness.R")  # shifter reclassification robustness: family-level + drop-propaganda Bartik

    print("\n=== 04 Analysis ===")
    # Exploration scripts (family IV, mean reversion, FD-vs-ANCOVA validation,
    # topic selection) live in exploration/ and are run by hand, not here.
    # See exploration/README.md.
    run_py("code/04_analysis/01_descriptives.py")           # candidate pool + overview + shift descriptives
    run_r("code/04_analysis/02_descriptive_figures.R")      # data-universe map, litigation timing, Bartik distribution
    run_r("code/04_analysis/03_result_figures.R")           # first stage, coefplots, forest
    run_py("code/04_analysis/04_iv_diagnostics.py")         # Rotemberg weights + GPS balance tests
    run_r("code/04_analysis/07_exposure_robust_se.R")       # genuine AKM/BHJ exposure-robust SE (replaces fake py [C])
    run_py("code/04_analysis/08_lawsuit_composition_sp.py")  # SP 2016->2024 class composition (pre-sample baseline, appendix)
    run_r("code/04_analysis/09_summary_statistics.R")       # estimation-sample summary statistics table
    run_py("code/04_analysis/10_candidate_rank_profile.py")  # winner vs runner-up vs field profile (2024 mayoral)
    run_py("code/04_analysis/06_abstract_macros.py")        # deck macros (reads overview_* + regressions) -- LAST

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
