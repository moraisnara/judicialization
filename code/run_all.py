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
    run_py("code/01_download/01_download_processual.py")
    run_py("code/01_download/02_download_candidate_data.py")
    run_py("code/01_download/02_download_covariates_data.py")
    run_py("code/01_download/04_download_vote_results.py")
    run_r("code/01_download/05_download_census_covariates.R")
    run_r("code/01_download/06_download_municipality_crosswalk.R")

    print("\n=== 02 Build ===")
    run_py("code/02_build/00_verify_processual.py")
    run_py("code/02_build/01_lawsuit_panel.py")
    run_py("code/02_build/02_bartik_inputs.py")
    run_py("code/02_build/03_vote_outcomes.py")
    run_py("code/02_build/05_candidate_history.py")
    run_py("code/02_build/06_electoral_admin.py")
    run_py("code/02_build/07_electoral_controls_2016.py")
    run_py("code/02_build/08_municipal_covariates.py")

    print("\n=== 03 Estimation ===")
    run_py("code/03_estimation/01_assemble_design.py")
    run_r("code/03_estimation/02_iv_main.R")           # 2SLS + tF correction
    run_r("code/03_estimation/03_overid_liml.R")       # GPS J test + LIML

    print("\n=== 04 Analysis ===")
    run_py("code/04_analysis/01_figures_descriptive.py")
    run_r("code/04_analysis/02_figures_causal.R")
    run_py("code/04_analysis/05_rotemberg_weights.py") # GPS Rotemberg + F_k
    run_py("code/04_analysis/08_gps_balance_tests.py") # GPS share balance tests
    run_py("code/04_analysis/09_visual_iv.py")         # GPS visual IV graph
    run_py("code/04_analysis/10_shift_descriptives.py")# BHJ shift table
    run_py("code/04_analysis/11_exposure_robust_se.py")# BHJ / AKM SEs

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
