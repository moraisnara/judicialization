"""
Patches the design matrix with a third Bartik IV variant that excludes
both RRC (11618) and DRAP (12044) from the shift-share instrument.

Adds two columns to data/estimation/executive_margin_design.csv:
  bartik_iv_no_rrc_drap
  delta_log1p_lawsuits_no_rrc_drap_2024_2020

Reads  : data/estimation/executive_margin_design.csv
         data/clean/municipality_bartik_components.csv
         data/clean/municipality_competition_subject_panel.csv
Writes : data/estimation/executive_margin_design.csv  (in-place patch)
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
DESIGN_PATH    = PROJECT_ROOT / "data" / "estimation" / "executive_margin_design.csv"
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_bartik_components.csv"
PANEL_PATH     = PROJECT_ROOT / "data" / "clean" / "municipality_competition_subject_panel.csv"

EXCLUDE = {"11618", "12044"}   # RRC + DRAP


def main() -> None:
    print("Loading design matrix …")
    design = pd.read_csv(DESIGN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    print(f"  {len(design):,} rows, {len(design.columns)} columns")

    # ------------------------------------------------------------------ #
    # 1. Rebuild Bartik IV without RRC and DRAP
    # ------------------------------------------------------------------ #
    print("Loading Bartik components …")
    comp = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["municipality_id_tse"].astype(str).str.zfill(5)
    comp["main_subject_code"]   = comp["main_subject_code"].astype(str).str.strip()

    comp_alt = comp[~comp["main_subject_code"].isin(EXCLUDE)].copy()
    comp_alt["n_lawsuits"] = pd.to_numeric(comp_alt["n_lawsuits"], errors="coerce").fillna(0)
    comp_alt["shock"]      = pd.to_numeric(
        comp_alt["shock_log_growth_2020_2024"], errors="coerce"
    ).fillna(0)

    # Re-normalise shares after exclusion (same logic as assemble_design.py)
    base_totals = comp_alt.groupby(
        ["state", "municipality_id_tse"]
    )["n_lawsuits"].transform("sum")
    comp_alt["share_no_rrc_drap"] = comp_alt["n_lawsuits"] / base_totals.replace(0, np.nan)
    comp_alt["component"]         = comp_alt["share_no_rrc_drap"] * comp_alt["shock"]

    bartik_alt = (
        comp_alt.groupby("municipality_id_tse", as_index=False)
        .agg(
            bartik_iv_no_rrc_drap        = ("component",    "sum"),
            baseline_lawsuits_no_rrc_drap_2020 = ("n_lawsuits", "sum"),
        )
    )
    bartik_alt["bartik_iv_no_rrc_drap"] = bartik_alt["bartik_iv_no_rrc_drap"].fillna(0)

    # ------------------------------------------------------------------ #
    # 2. Endogenous variable: delta log1p lawsuits excl. RRC + DRAP
    # ------------------------------------------------------------------ #
    print("Loading subject panel …")
    panel = pd.read_csv(
        PANEL_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    panel["municipality_id_tse"] = panel["municipality_id_tse"].astype(str).str.zfill(5)
    panel["main_subject_code"]   = panel["main_subject_code"].astype(str).str.strip()
    panel["election_year"]       = pd.to_numeric(panel["election_year"], errors="coerce")

    sp_alt = panel[
        (~panel["main_subject_code"].isin(EXCLUDE)) &
        (panel["election_year"].isin([2020, 2024]))
    ].copy()
    sp_alt["n_lawsuits"] = pd.to_numeric(sp_alt["n_lawsuits"], errors="coerce").fillna(0)

    totals = (
        sp_alt.groupby(["election_year", "municipality_id_tse"], as_index=False)
        .agg(lawsuits=("n_lawsuits", "sum"))
    )
    wide = totals.pivot_table(
        index="municipality_id_tse",
        columns="election_year",
        values="lawsuits",
        fill_value=0,
    )
    wide.columns = [f"lawsuits_no_rrc_drap_{int(c)}" for c in wide.columns]
    wide = wide.reset_index()
    for col in ["lawsuits_no_rrc_drap_2020", "lawsuits_no_rrc_drap_2024"]:
        if col not in wide.columns:
            wide[col] = 0
    wide["delta_log1p_lawsuits_no_rrc_drap_2024_2020"] = (
        np.log1p(wide["lawsuits_no_rrc_drap_2024"])
        - np.log1p(wide["lawsuits_no_rrc_drap_2020"])
    )

    # ------------------------------------------------------------------ #
    # 3. Merge into design (drop old columns if present, re-add cleanly)
    # ------------------------------------------------------------------ #
    new_cols = ["bartik_iv_no_rrc_drap", "delta_log1p_lawsuits_no_rrc_drap_2024_2020",
                "lawsuits_no_rrc_drap_2020", "lawsuits_no_rrc_drap_2024",
                "baseline_lawsuits_no_rrc_drap_2020"]
    for c in new_cols:
        if c in design.columns:
            design = design.drop(columns=[c])

    design["municipality_id_tse"] = design["municipality_id_tse"].astype(str).str.zfill(5)

    patch = bartik_alt.merge(
        wide[["municipality_id_tse",
              "lawsuits_no_rrc_drap_2020", "lawsuits_no_rrc_drap_2024",
              "delta_log1p_lawsuits_no_rrc_drap_2024_2020"]],
        on="municipality_id_tse", how="outer",
    )
    for c in new_cols:
        if c in patch.columns:
            patch[c] = patch[c].fillna(0)

    design = design.merge(patch, on="municipality_id_tse", how="left")
    for c in new_cols:
        if c in design.columns:
            design[c] = design[c].fillna(0)

    # ------------------------------------------------------------------ #
    # 4. Save
    # ------------------------------------------------------------------ #
    design.to_csv(DESIGN_PATH, index=False, encoding="utf-8-sig")
    print(f"\nPatched design saved: {DESIGN_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(design):,}  |  Columns: {len(design.columns)}")

    # Quick sanity check
    n_nonzero = (design["bartik_iv_no_rrc_drap"] != 0).sum()
    mean_iv   = design["bartik_iv_no_rrc_drap"].mean()
    mean_end  = design["delta_log1p_lawsuits_no_rrc_drap_2024_2020"].mean()
    print(f"\n  bartik_iv_no_rrc_drap : {n_nonzero:,} nonzero, mean={mean_iv:.4f}")
    print(f"  delta_log1p_lawsuits_no_rrc_drap_2024_2020 : mean={mean_end:.4f}")

    # Compare variants
    print("\nInstrument comparison (design means):")
    for col in ["bartik_iv_2020_2024", "bartik_iv_no_rrc", "bartik_iv_no_rrc_drap"]:
        if col in design.columns:
            print(f"  {col}: mean={design[col].mean():.4f}, std={design[col].std():.4f}, "
                  f"nonzero={(design[col] != 0).sum():,}")
    print("\nEndogenous variable comparison (design means):")
    for col in ["delta_log1p_competition_lawsuits_2024_2020",
                "delta_log1p_lawsuits_no_rrc_2024_2020",
                "delta_log1p_lawsuits_no_rrc_drap_2024_2020"]:
        if col in design.columns:
            print(f"  {col}: mean={design[col].mean():.4f}, std={design[col].std():.4f}")


if __name__ == "__main__":
    main()
