# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design: the LEGISLATIVE
# arm reuses the retired executive instrument columns (bartik_iv_2020_2024 etc.)
# that no longer exist in executive_margin_design.csv. It will NOT run correctly
# against the current act-based design (instrument bartik_iv_act, treatment
# delta_log1p_act_lawsuits, cluster = state) and will FAIL on rerun until ported.
# Reason stale: merges bartik_iv_2020_2024 / per-family bartik_iv_<family> cols
# from the executive design that the act rebuild removed.
# ===========================================================================
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

    # ---- 2b. Merge council (vereador) entrant typology ----
    # Cross-cycle candidate experience for the council race (04b_council_history.py):
    # first-time / serial-challenger / cross-cycle-returner shares, 2020 baseline
    # level + 2024-2020 delta outcome. Mirrors the executive entrant typology.
    council_path = CLEAN_DIR / "council_experience_panel.csv"
    if council_path.exists():
        ce = pd.read_csv(council_path, dtype={"municipality_id_tse": str})
        ce["municipality_id_tse"] = ce["municipality_id_tse"].astype(str).str.zfill(5)
        typ = {
            "share_first_time_candidates": "share_first_time_candidates",
            "share_serial_challenger":     "share_serial_challenger",
            "share_cross_cycle_returner":  "share_cross_cycle_returner",
        }
        for yr in (2020, 2024):
            sub = ce[ce["election_year"] == yr][["municipality_id_tse", *typ]].copy()
            sub = sub.rename(columns={k: f"{v}_{yr}" for k, v in typ.items()})
            leg = leg.merge(sub, on="municipality_id_tse", how="left", validate="m:1")
        for v in typ.values():
            c24, c20 = f"{v}_2024", f"{v}_2020"
            if c24 in leg.columns and c20 in leg.columns:
                leg[f"delta_{v}_2024_2020"] = (
                    pd.to_numeric(leg[c24], errors="coerce") -
                    pd.to_numeric(leg[c20], errors="coerce")
                )
        print(f"Council experience merged: "
              f"{leg['share_first_time_candidates_2020'].notna().sum():,} municipalities")

    # ---- 2c. Merge municipality vote-share outcomes (groups A-D) ----
    # The vote-weighted legislative outcomes are built by 03b_vote_outcomes.py
    # (legislative_vote_shift_share_design.csv) but are NOT in the candidate-
    # composition design loaded above. Pull them in so legislative carries the
    # SAME vote-share outcomes as executive. Groups A (representation),
    # B (renewal/incumbency) and C (fragmentation) are comparable across offices;
    # group D (winner/closeness) is merged for completeness but only meaningful
    # for the single-winner executive race. Nothing is dropped: the existing
    # candidate-share / elected-share outcomes are kept alongside these.
    legvote_path = CLEAN_DIR / "legislative_vote_shift_share_design.csv"
    if legvote_path.exists():
        lv = pd.read_csv(legvote_path, dtype={"municipality_id_tse": str}, low_memory=False)
        lv["municipality_id_tse"] = lv["municipality_id_tse"].astype(str).str.zfill(5)
        vote_bases = [
            # A. descriptive representation
            "female_vote_share", "nonwhite_vote_share", "higher_education_vote_share",
            # B. renewal / incumbency
            "new_candidate_vote_share", "incumbent_candidate_vote_share",
            # C. fragmentation
            "effective_n_candidates_vote", "vote_hhi_candidate",
            "effective_n_parties_vote", "vote_hhi_party",
            # D. winner / contest closeness (executive-only in tables)
            "winner_vote_share", "runnerup_vote_share", "margin_top1_top2",
            "top2_vote_share", "others_vote_share", "winner_majority",
            "winner_is_female", "winner_is_new_vs_2020",
        ]
        vote_cols: list[str] = []
        for b in vote_bases:
            vote_cols += [f"{b}_2020", f"{b}_2024", f"delta_{b}_2024_2020"]
        vote_cols = [c for c in vote_cols if c in lv.columns]
        # keep the candidate-composition version of any name that already exists
        keep = ["municipality_id_tse"] + [c for c in vote_cols if c not in leg.columns]
        leg = leg.merge(lv[keep], on="municipality_id_tse", how="left", validate="m:1")
        print(f"Vote-share outcomes merged: {len(keep) - 1} columns "
              f"({leg['delta_female_vote_share_2024_2020'].notna().sum():,} municipalities)")
    else:
        print("  WARNING: legislative_vote_shift_share_design.csv not found; "
              "vote-share outcomes unavailable for legislative.")

    # ---- 3. Merge instrument + controls from executive design ----
    # The executive design (01_assemble_design.py) is the single authoritative
    # source for the SIG family shift-share instrument and the endogenous
    # kept-litigation delta, so both offices share ONE instrument definition.
    # We pull every aggregation rung (bartik_iv_<rung> / delta_log1p_kept_<rung>)
    # plus the headline aliases; cluster_id is the state (leave-own-state shift).
    RUNGS = ["subst13", "subst11", "theme9", "theme7", "triad3",
             "fine7_archive", "fine7", "fine8", "fine7_literal"]
    exe_cols = [
        "municipality_id_tse", "cluster_id",
        "bartik_iv_2020_2024",
        "delta_log1p_competition_lawsuits_2024_2020",
        *[f"bartik_iv_{r}" for r in RUNGS],
        *[f"delta_log1p_kept_{r}" for r in RUNGS],
        "n_zones_in_municipality",
        "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
        "margin_2016",
        "log1p_total_valid_votes_2020",   # electorate size baseline
        # IBGE sub-state geography for the tighter-than-state FE specification
        "code_meso", "code_micro", "code_imediata", "code_intermediaria",
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

    leg = leg.merge(exe, on="municipality_id_tse", how="left", validate="one_to_one")
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
