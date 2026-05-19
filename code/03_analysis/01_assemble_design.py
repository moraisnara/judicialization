"""
Assemble the analysis design matrix.

Merges shift-share inputs, covariates, electoral outcomes, and zone structure
into a single flat file used by the estimation scripts.

Inputs  (from data/clean/):
  executive_vote_shift_share_design.csv
  municipality_bartik_components.csv
  municipality_competition_subject_panel.csv
  municipal_covariates.csv
  electoral_admin_outcomes.csv

Input (from data/raw/):
  lista-zonas-municipios-10-07-24.csv   — zone → municipality lookup

Output:
  data/estimation/executive_margin_design.csv
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
CLEAN_DIR      = PROJECT_ROOT / "data" / "clean"
ESTIMATION_DIR = PROJECT_ROOT / "data" / "estimation"
LOOKUP_PATH    = PROJECT_ROOT / "data" / "raw" / "lista-zonas-municipios-10-07-24.csv"

EXECUTIVE_PATH     = CLEAN_DIR / "executive_vote_shift_share_design.csv"
COMPONENTS_PATH    = CLEAN_DIR / "municipality_bartik_components.csv"
SUBJECT_PANEL_PATH = CLEAN_DIR / "municipality_competition_subject_panel.csv"
COVARIATES_PATH    = CLEAN_DIR / "municipal_covariates.csv"
ADMIN_PATH         = CLEAN_DIR / "electoral_admin_outcomes.csv"

# Subject code excluded from the no-RRC Bartik variant (Recursos de Reclamação)
EXCLUDE_RRC = {"11618"}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_design() -> pd.DataFrame:
    df = pd.read_csv(EXECUTIVE_PATH, dtype={"SG_UE": str}, low_memory=False)
    return df.drop_duplicates(subset=["SG_UF", "SG_UE"], keep="first").reset_index(drop=True)


def load_components() -> pd.DataFrame:
    return pd.read_csv(
        COMPONENTS_PATH,
        dtype={"SG_UE": str, "CD_ASSUNTO_PRINCIPAL": str},
        low_memory=False,
    )


def load_subject_panel() -> pd.DataFrame:
    return pd.read_csv(
        SUBJECT_PANEL_PATH,
        dtype={"SG_UE": str, "CD_ASSUNTO_PRINCIPAL": str},
        low_memory=False,
    )


def load_covariates() -> pd.DataFrame:
    cov = pd.read_csv(COVARIATES_PATH, dtype={"SG_UE": str}, low_memory=False)
    cov["SG_UE"] = cov["SG_UE"].str.zfill(5)
    return cov


def load_voter_behavior_deltas() -> pd.DataFrame:
    adm = pd.read_csv(ADMIN_PATH, dtype={"SG_UE": str}, low_memory=False)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")
    for col in ["turnout_rate", "null_share", "blank_share"]:
        adm[col] = pd.to_numeric(adm[col], errors="coerce")
    a20 = adm[adm["ANO_ELEICAO"] == 2020][
        ["SG_UF", "SG_UE", "turnout_rate", "null_share", "blank_share"]
    ]
    a24 = adm[adm["ANO_ELEICAO"] == 2024][
        ["SG_UF", "SG_UE", "turnout_rate", "null_share", "blank_share"]
    ]
    m = a20.merge(a24, on=["SG_UF", "SG_UE"], suffixes=("_2020", "_2024"))
    m["delta_turnout_rate_2024_2020"] = m["turnout_rate_2024"] - m["turnout_rate_2020"]
    m["delta_null_share_2024_2020"]   = m["null_share_2024"]   - m["null_share_2020"]
    m["delta_blank_share_2024_2020"]  = m["blank_share_2024"]  - m["blank_share_2020"]
    return m[
        ["SG_UF", "SG_UE",
         "delta_turnout_rate_2024_2020", "delta_null_share_2024_2020",
         "delta_blank_share_2024_2020"]
    ]


# ---------------------------------------------------------------------------
# Design transformations
# ---------------------------------------------------------------------------

def add_zone_structure(df: pd.DataFrame) -> pd.DataFrame:
    lookup = pd.read_csv(LOOKUP_PATH, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(
        columns={"UF": "SG_UF", "ZONA": "zona_eleitoral", "COD_LOCALIDADE": "COD_MUN"}
    )
    lookup = lookup[lookup["SG_UF"] != "ZZ"].copy()
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup["zona_eleitoral"] = pd.to_numeric(lookup["zona_eleitoral"], errors="coerce")
    zone_info = (
        lookup.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(
            n_zones_in_municipality=("zona_eleitoral", "nunique"),
            principal_zone=("zona_eleitoral", "min"),
        )
    )
    zone_info["principal_zone_id"] = (
        zone_info["SG_UF"].astype(str) + "_"
        + zone_info["principal_zone"].astype("Int64").astype(str)
    )
    return df.merge(zone_info, on=["SG_UF", "SG_UE"], how="left", validate="m:1")


def add_log_controls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["total_candidates_2020", "party_count_2020",
                "coalition_count_2020", "total_valid_votes_2020"]:
        if col in df.columns:
            df[f"log1p_{col}"] = np.log1p(df[col])
    df["log1p_n_zones_in_municipality"] = np.log1p(
        df["n_zones_in_municipality"].fillna(1)
    )
    return df


def build_no_rrc_variant(
    design: pd.DataFrame,
    components: pd.DataFrame,
    subject_panel: pd.DataFrame,
) -> pd.DataFrame:
    """Add Bartik IV and lawsuits count excluding subject code 11618 (RRC)."""
    comp_alt = components[~components["CD_ASSUNTO_PRINCIPAL"].isin(EXCLUDE_RRC)].copy()
    comp_alt["n_lawsuits"] = pd.to_numeric(comp_alt["n_lawsuits"], errors="coerce").fillna(0)
    comp_alt["shock_log_growth_2020_2024"] = pd.to_numeric(
        comp_alt["shock_log_growth_2020_2024"], errors="coerce"
    ).fillna(0)
    base_totals = comp_alt.groupby(["SG_UF", "SG_UE"])["n_lawsuits"].transform("sum")
    comp_alt["baseline_share_no_rrc_2020"] = comp_alt["n_lawsuits"] / base_totals
    comp_alt["bartik_component_no_rrc"] = (
        comp_alt["baseline_share_no_rrc_2020"] * comp_alt["shock_log_growth_2020_2024"]
    )
    bartik_alt = (
        comp_alt.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(
            bartik_iv_no_rrc=("bartik_component_no_rrc", "sum"),
            baseline_lawsuits_no_rrc_2020=("n_lawsuits", "sum"),
            baseline_subjects_no_rrc_2020=("CD_ASSUNTO_PRINCIPAL", "nunique"),
        )
    )
    sp_alt = subject_panel[~subject_panel["CD_ASSUNTO_PRINCIPAL"].isin(EXCLUDE_RRC)].copy()
    totals = (
        sp_alt.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(lawsuits=("n_lawsuits", "sum"))
    )
    wide = (
        totals.pivot_table(
            index=["SG_UF", "SG_UE"], columns="ANO_ELEICAO",
            values="lawsuits", fill_value=0,
        )
        .rename(columns={2020: "lawsuits_no_rrc_2020", 2024: "lawsuits_no_rrc_2024"})
        .reset_index()
    )
    for col in ["lawsuits_no_rrc_2020", "lawsuits_no_rrc_2024"]:
        if col not in wide.columns:
            wide[col] = 0
    wide["delta_log1p_lawsuits_no_rrc_2024_2020"] = (
        np.log1p(wide["lawsuits_no_rrc_2024"]) - np.log1p(wide["lawsuits_no_rrc_2020"])
    )
    out = design.merge(bartik_alt, on=["SG_UF", "SG_UE"], how="left")
    out = out.merge(wide, on=["SG_UF", "SG_UE"], how="left")
    for col in [
        "bartik_iv_no_rrc", "baseline_lawsuits_no_rrc_2020",
        "baseline_subjects_no_rrc_2020", "lawsuits_no_rrc_2020",
        "lawsuits_no_rrc_2024", "delta_log1p_lawsuits_no_rrc_2024_2020",
    ]:
        out[col] = out[col].fillna(0)
    return out


# ---------------------------------------------------------------------------
# Control variable lists (reference for estimation scripts)
# ---------------------------------------------------------------------------

BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]

ROBUSTNESS_CONTROLS = BASELINE_CONTROLS + [
    "enp_2016",
    "female_vote_share_2020", "nonwhite_vote_share_2020",
    "higher_education_vote_share_2020",
    "log1p_party_count_2020", "log1p_coalition_count_2020",
    "turnout_rate_2020", "null_share_2020",
    "share_first_time_candidates_2020", "share_career_politicians_2020",
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading inputs...")
    design = load_design()
    design = add_zone_structure(design)
    design = add_log_controls(design)
    design["cluster_id"] = design["principal_zone_id"]
    design = build_no_rrc_variant(design, load_components(), load_subject_panel())

    # Covariates (drop string/identifier columns not used in regressions)
    cov = load_covariates()
    drop_cols = {
        "NM_UE", "winner_party_2016", "winner_sq_2016",
        "winner_name_2016", "winner_party_2020", "incumbent_ran_2024",
    }
    design = design.merge(
        cov[[c for c in cov.columns if c not in drop_cols]],
        on=["SG_UF", "SG_UE"], how="left",
    )

    # Voter-behavior deltas (turnout, null, blank share 2024 − 2020)
    design = design.merge(load_voter_behavior_deltas(), on=["SG_UF", "SG_UE"], how="left")

    # Baseline voter-behavior levels (2020) and registered voters (2024)
    adm = pd.read_csv(ADMIN_PATH, dtype={"SG_UE": str}, low_memory=False)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")

    adm_2020 = (
        adm[adm["ANO_ELEICAO"] == 2020]
        [["SG_UF", "SG_UE", "turnout_rate", "null_share", "blank_share"]]
        .rename(columns={
            "turnout_rate": "turnout_rate_2020",
            "null_share":   "null_share_2020",
            "blank_share":  "blank_share_2020",
        })
    )
    if "turnout_rate_2020" not in design.columns:
        design = design.merge(adm_2020, on=["SG_UF", "SG_UE"], how="left")

    adm_2024_aptos = (
        adm[adm["ANO_ELEICAO"] == 2024]
        [["SG_UF", "SG_UE", "qt_aptos"]]
        .rename(columns={"qt_aptos": "qt_aptos_2024"})
    )
    design = design.merge(adm_2024_aptos, on=["SG_UF", "SG_UE"], how="left")

    print(f"Design: {len(design):,} municipalities, {len(design.columns)} columns")

    out_path = ESTIMATION_DIR / "executive_margin_design.csv"
    design.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
