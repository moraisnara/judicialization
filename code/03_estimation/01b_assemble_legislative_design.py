"""
Assemble the legislative (vereadores) estimation design matrix.

Merges legislative_shift_share_design.csv with baseline municipal controls
from the executive design, computes delta outcomes for elected composition,
and writes data/estimation/legislative_design.csv.

Endogenous variable: delta_log1p_competition_lawsuits_2024_2020
Instrument:         bartik_iv_2020_2024
Outcome families:
  candidate_pool   — who runs: female/nonwhite share, party diversity, candidate count
  elected_comp     — who wins: elected female/nonwhite/education/age shares, incumbent reelection
  party_comp       — party competition: party count, HHI, coalition count

Controls (same as executive, adapted for legislative baseline):
  log_pop_2010, urban_share_2010, log_income_pc_2010, margin_2016 (executive)
  log1p_total_candidates_2020 (legislative), effective_party_count_candidates_2020
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
CLEAN_DIR      = PROJECT_ROOT / "data" / "clean"
ESTIMATION_DIR = PROJECT_ROOT / "data" / "estimation"
ESTIMATION_DIR.mkdir(parents=True, exist_ok=True)

LEG_PATH = CLEAN_DIR / "legislative_shift_share_design.csv"
EXE_PATH = ESTIMATION_DIR / "executive_margin_design.csv"


def main() -> None:
    # ---- 1. Load legislative shift-share design ----
    leg = pd.read_csv(
        LEG_PATH,
        dtype={"municipality_id_tse": str},
        low_memory=False,
    )
    leg["municipality_id_tse"] = leg["municipality_id_tse"].astype(str).str.zfill(5)
    print(f"Legislative design: {len(leg):,} municipalities")

    # ---- 2. Compute delta outcomes not yet in the legislative design ----
    level_pairs = [
        ("elected_female_share",            "delta_elected_female_share_2024_2020"),
        ("elected_nonwhite_share",          "delta_elected_nonwhite_share_2024_2020"),
        ("elected_higher_education_share",  "delta_elected_higher_ed_share_2024_2020"),
        ("elected_mean_age",                "delta_elected_mean_age_2024_2020"),
        ("incumbent_reelected_share",       "delta_incumbent_reelected_share_2024_2020"),
        ("new_candidate_share",             "delta_new_candidate_share_2024_2020"),
        ("nonwhite_share",                  "delta_nonwhite_share_2024_2020"),
        ("party_count",                     "delta_party_count_2024_2020"),
        ("coalition_count",                 "delta_coalition_count_2024_2020"),
        ("incumbent_candidate_share",       "delta_incumbent_candidate_share_2024_2020"),
        ("higher_education_share",          "delta_higher_education_share_2024_2020"),
        ("mean_age",                        "delta_mean_age_2024_2020"),
    ]
    new_cols: dict[str, pd.Series] = {}
    for base, delta_name in level_pairs:
        col_2024 = f"{base}_2024"
        col_2020 = f"{base}_2020"
        if col_2024 in leg.columns and col_2020 in leg.columns:
            new_cols[delta_name] = (
                pd.to_numeric(leg[col_2024], errors="coerce") -
                pd.to_numeric(leg[col_2020], errors="coerce")
            )

    # log(1 + total_candidates) — legislative baseline
    if "total_candidates_2020" in leg.columns and "total_candidates_2024" in leg.columns:
        tc20 = pd.to_numeric(leg["total_candidates_2020"], errors="coerce")
        tc24 = pd.to_numeric(leg["total_candidates_2024"], errors="coerce")
        new_cols["log1p_total_candidates_2020_leg"] = np.log1p(tc20)
        new_cols["log1p_total_candidates_2024_leg"] = np.log1p(tc24)
        new_cols["delta_log1p_total_candidates_2024_2020"] = (
            np.log1p(tc24) - np.log1p(tc20)
        )

    for col, vals in new_cols.items():
        leg[col] = vals

    # ---- 3. Merge instrument + controls from executive design ----
    # The executive design uses executive_vote_shift_share_design.csv which has
    # a different (processed) Bartik IV than the raw legislative clean file.
    # Use the executive design as the single authoritative source for both the
    # instrument and the endogenous variable so both analyses are comparable.
    exe_cols = [
        "municipality_id_tse", "cluster_id",
        "bartik_iv_2020_2024",
        "bartik_iv_no_rrc_drap",
        "delta_log1p_competition_lawsuits_2024_2020",
        "delta_log1p_lawsuits_no_rrc_drap_2024_2020",
        "n_zones_in_municipality",
        "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
        "margin_2016",
        "log1p_total_valid_votes_2020",   # electorate size baseline
        "log1p_lawsuits_no_rrc_2020",     # broader competition count (excl. RRC only)
    ]
    # Only request columns that actually exist in the executive design
    exe_available = pd.read_csv(EXE_PATH, nrows=0).columns.tolist()
    exe_cols = [c for c in exe_cols if c in exe_available]

    exe = pd.read_csv(
        EXE_PATH,
        dtype={"municipality_id_tse": str, "cluster_id": str},
        usecols=exe_cols,
        low_memory=False,
    )
    exe["municipality_id_tse"] = exe["municipality_id_tse"].astype(str).str.zfill(5)

    # Drop raw legislative versions of any column we're taking from the executive design
    for drop_col in exe_cols:
        if drop_col != "municipality_id_tse" and drop_col in leg.columns:
            leg = leg.drop(columns=[drop_col])

    leg = leg.merge(exe, on="municipality_id_tse", how="left")
    print(f"After merging controls: {leg['log_pop_2010'].notna().sum():,} municipalities with full controls")

    # ---- 4. Drop rows with no instrument or no controls ----
    req = [
        "bartik_iv_2020_2024",
        "delta_log1p_competition_lawsuits_2024_2020",
        "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
        "margin_2016", "cluster_id",
    ]
    req = [c for c in req if c in leg.columns]
    before = len(leg)
    leg = leg.dropna(subset=req).reset_index(drop=True)
    print(f"Estimation sample: {len(leg):,} municipalities (dropped {before - len(leg):,} for missing controls/IV)")

    # ---- 5. Describe key outcomes ----
    outcomes = [c for c in leg.columns if c.startswith("delta_") and "2024_2020" in c
                and c != "delta_log1p_competition_lawsuits_2024_2020"]
    print(f"\nOutcome variables: {len(outcomes)}")
    for o in sorted(outcomes):
        n_nonmiss = leg[o].notna().sum()
        print(f"  {o}: {n_nonmiss:,} non-missing")

    # ---- 6. Save ----
    out_path = ESTIMATION_DIR / "legislative_design.csv"
    leg.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_path.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(leg):,}  |  Columns: {len(leg.columns)}")


if __name__ == "__main__":
    main()
