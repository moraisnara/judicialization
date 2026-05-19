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

    # ── 01 Download ───────────────────────────────────────────────────────────
    print("=== 01 Download ===")
    run_py("code/01_download/00_verify_raw_data.py")
    run_py("code/01_download/01_download_processual.py")
    run_py("code/01_download/02_download_candidate_data.py")
    run_py("code/01_download/02_download_covariates_data.py")
    run_py("code/01_download/03_download_vote_results.py")

    # ── 02 Build ─────────────────────────────────────────────────────────────
    print("\n=== 02 Build ===")
    run_py("code/02_build/00_verify_processual.py")
    run_py("code/02_build/01_lawsuit_panel.py")
    run_py("code/02_build/02_bartik_inputs.py")
    run_py("code/02_build/03_vote_outcomes.py")
    run_r( "code/02_build/04_census_covariates.R")
    run_py("code/02_build/05_candidate_history.py")
    run_py("code/02_build/06_electoral_admin.py")
    run_py("code/02_build/07_electoral_controls_2016.py")
    run_py("code/02_build/08_municipal_covariates.py")

    # ── 03 Analysis ──────────────────────────────────────────────────────────
    print("\n=== 03 Analysis ===")
    run_py("code/03_analysis/01_assemble_design.py")
    run_r( "code/03_analysis/02_iv_main.R")
    run_py("code/03_analysis/03_heterogeneity.py")
    run_py("code/03_analysis/04_figures_descriptive.py")
    run_r( "code/03_analysis/05_figures_causal.R")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
