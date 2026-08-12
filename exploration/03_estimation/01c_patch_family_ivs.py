"""
Add family-level Bartik IV columns, family-specific endogenous variables,
and top-topic baseline share columns to data/estimation/executive_margin_design.csv.

Inputs:
  data/clean/municipality_bartik_components.csv   — bartik_component, baseline_share_2020
  data/clean/municipality_competition_subject_panel.csv — n_lawsuits by (muni, year, family)
  data/estimation/executive_margin_design.csv

New columns added to executive design:
  bartik_iv_{family}              — sum of bartik_component within each topic_family
  delta_log1p_{family}_2024_2020  — log(1+lawsuits_2024) - log(1+lawsuits_2020) per family
  share_{code}_2020               — baseline_share_2020 for top-4 Rotemberg-weight topics

Top-4 topics by Rotemberg |alpha_k|:
  11616  Impugnacao ao Registro    (alpha = +40%)
  11617  Vaga Remanescente         (alpha = -30%)
  11679  Internet propaganda       (alpha = +19%)
  11662  Comicio                   (alpha = +13%)

Family IV identification:
  bartik_iv_{family} instruments delta_log1p_{family}_2024_2020 (family-specific lawsuits).
  This identifies the effect of each FAMILY of lawsuits separately (family-specific LATE).
  Different causal parameter from the aggregate — useful for mechanism analysis.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
CLEAN_DIR      = PROJECT_ROOT / "data" / "clean"
ESTIMATION_DIR = PROJECT_ROOT / "data" / "estimation"

COMPONENTS_PATH = CLEAN_DIR / "municipality_bartik_components.csv"
PANEL_PATH      = CLEAN_DIR / "municipality_competition_subject_panel.csv"
DESIGN_PATH     = ESTIMATION_DIR / "executive_margin_design.csv"

TOP_TOPICS = ["11616", "11617", "11679", "11662"]


def main() -> None:
    components = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    components["municipality_id_tse"] = (
        components["municipality_id_tse"].str.strip().str.zfill(5)
    )
    print(f"Loaded bartik components: {len(components):,} rows")
    print(f"  Topics: {components['main_subject_code'].nunique()}")
    print(f"  Municipalities: {components['municipality_id_tse'].nunique():,}")

    # Topic families present in the data (exclude unmapped / blank)
    families = sorted(
        f for f in components["topic_family"].dropna().unique()
        if str(f).strip() not in ("unmapped", "")
    )
    print(f"\nTopic families found ({len(families)}): {families}")

    # ── Family IVs ─────────────────────────────────────────────────────────────
    # One IV per family = sum of bartik_component for topics in that family
    family_ivs = (
        components[components["topic_family"].isin(families)]
        .groupby(["municipality_id_tse", "topic_family"])["bartik_component"]
        .sum()
        .unstack(fill_value=0.0)
        .reset_index()
    )
    family_ivs.columns.name = None
    family_ivs.columns = (
        ["municipality_id_tse"]
        + [
            f"bartik_iv_{str(col).lower().replace(' ', '_')}"
            for col in family_ivs.columns[1:]
        ]
    )
    fam_iv_cols = [c for c in family_ivs.columns if c != "municipality_id_tse"]
    print(f"\nFamily IV columns ({len(fam_iv_cols)}): {fam_iv_cols}")

    # ── Family-specific endogenous variables ───────────────────────────────────
    # delta_log1p_{family}_2024_2020 = log1p(total_lawsuits_2024) - log1p(total_lawsuits_2020)
    # aggregated across all adversarial topics within the family
    panel = pd.read_csv(
        PANEL_PATH,
        dtype={"municipality_id_tse": str},
        low_memory=False,
    )
    panel["municipality_id_tse"] = (
        panel["municipality_id_tse"].str.strip().str.zfill(5)
    )

    family_totals = (
        panel[panel["topic_family"].isin(families)]
        .groupby(["municipality_id_tse", "election_year", "topic_family"])["n_lawsuits"]
        .sum()
        .unstack(level="election_year", fill_value=0)
        .reset_index()
    )
    family_totals.columns.name = None
    # Rename year columns to avoid collision
    family_totals = family_totals.rename(columns={2020: "n2020", 2024: "n2024"})
    if "n2020" not in family_totals.columns:
        family_totals["n2020"] = 0
    if "n2024" not in family_totals.columns:
        family_totals["n2024"] = 0

    family_totals["delta_log1p"] = (
        np.log1p(family_totals["n2024"]) - np.log1p(family_totals["n2020"])
    )

    fam_endog = (
        family_totals
        .pivot(index="municipality_id_tse", columns="topic_family", values="delta_log1p")
        .reset_index()
    )
    fam_endog.columns.name = None
    fam_endog_cols_raw = [c for c in fam_endog.columns if c != "municipality_id_tse"]
    fam_endog.columns = (
        ["municipality_id_tse"]
        + [
            f"delta_log1p_{str(col).lower().replace(' ', '_')}_2024_2020"
            for col in fam_endog_cols_raw
        ]
    )
    fam_endog_cols = [c for c in fam_endog.columns if c != "municipality_id_tse"]
    print(f"\nFamily endogenous columns ({len(fam_endog_cols)}): {fam_endog_cols}")

    # ── Topic shares for top-4 Rotemberg-weight topics ──────────────────────────
    top_rows = components[components["main_subject_code"].isin(TOP_TOPICS)].copy()
    if not top_rows.empty:
        topic_shares = (
            top_rows
            .pivot_table(
                index="municipality_id_tse",
                columns="main_subject_code",
                values="baseline_share_2020",
                fill_value=0.0,
                aggfunc="sum",
            )
            .reset_index()
        )
        topic_shares.columns.name = None
        topic_shares.columns = (
            ["municipality_id_tse"]
            + [f"share_{col}_2020" for col in topic_shares.columns[1:]]
        )
        # Ensure all 4 requested topics have columns (fill missing with 0)
        for code in TOP_TOPICS:
            col = f"share_{code}_2020"
            if col not in topic_shares.columns:
                topic_shares[col] = 0.0
        share_cols = [c for c in topic_shares.columns if c != "municipality_id_tse"]
        print(f"Topic share columns ({len(share_cols)}): {share_cols}")
    else:
        print("WARNING: No top-topic rows found in components — share columns set to NaN")
        topic_shares = pd.DataFrame({"municipality_id_tse": pd.Series(dtype=str)})
        for code in TOP_TOPICS:
            topic_shares[f"share_{code}_2020"] = np.nan
        share_cols = [f"share_{code}_2020" for code in TOP_TOPICS]

    # ── Load and update executive design ───────────────────────────────────────
    design = pd.read_csv(
        DESIGN_PATH,
        dtype={"municipality_id_tse": str, "cluster_id": str},
        low_memory=False,
    )
    design["municipality_id_tse"] = design["municipality_id_tse"].str.strip().str.zfill(5)
    print(f"\nExecutive design before patch: {len(design):,} rows, {len(design.columns)} cols")

    # Drop any pre-existing columns (idempotent re-runs)
    new_cols = fam_iv_cols + fam_endog_cols + share_cols
    stale = [c for c in new_cols if c in design.columns]
    if stale:
        design = design.drop(columns=stale)
        print(f"  Dropped stale columns: {stale}")

    # Merge family IVs, family endogenous, and topic shares
    design = design.merge(family_ivs, on="municipality_id_tse", how="left")
    design = design.merge(fam_endog, on="municipality_id_tse", how="left")
    design = design.merge(topic_shares, on="municipality_id_tse", how="left")

    # Coverage check
    if fam_iv_cols:
        n_nonmiss = design[fam_iv_cols[0]].notna().sum()
        print(f"  Municipalities with family IVs: {n_nonmiss:,} / {len(design):,}")

    design.to_csv(DESIGN_PATH, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {DESIGN_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  Columns added: {new_cols}")
    print(f"  Total columns now: {len(design.columns)}")

    # Summary of family IV values
    print("\nFamily IV summary (first 5 municipalities):")
    print(design[["municipality_id_tse"] + fam_iv_cols].head())


if __name__ == "__main__":
    main()
