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
EXPERIENCE_PATH    = CLEAN_DIR / "candidate_experience_panel.csv"
VOTER_DISAGG_PATH  = CLEAN_DIR / "voter_disaggregated_outcomes.csv"

# Subject code excluded from the no-RRC Bartik variant (Recursos de Reclamação)
EXCLUDE_RRC = {"11618"}
STANDARD_TO_LEGACY = {
    "election_year": "ANO_ELEICAO",
    "state": "SG_UF",
    "electoral_zone": "zona_eleitoral",
    "municipality_id_tse": "SG_UE",
    "municipality_name": "NM_UE",
    "case_class_code": "CD_CLASSE",
    "case_class_name": "DS_CLASSE",
    "main_subject_code": "CD_ASSUNTO_PRINCIPAL",
    "main_subject_name": "DS_ASSUNTO_PRINCIPAL",
}
LEGACY_TO_STANDARD = {value: key for key, value in STANDARD_TO_LEGACY.items()}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_design() -> pd.DataFrame:
    df = pd.read_csv(EXECUTIVE_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    df = df.rename(columns=STANDARD_TO_LEGACY)
    return df.drop_duplicates(subset=["SG_UF", "SG_UE"], keep="first").reset_index(drop=True)


def load_components() -> pd.DataFrame:
    return pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    ).rename(columns=STANDARD_TO_LEGACY)


def load_subject_panel() -> pd.DataFrame:
    return pd.read_csv(
        SUBJECT_PANEL_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    ).rename(columns=STANDARD_TO_LEGACY)


def load_covariates() -> pd.DataFrame:
    cov = pd.read_csv(COVARIATES_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    cov = cov.rename(columns=STANDARD_TO_LEGACY)
    cov["SG_UE"] = cov["SG_UE"].str.zfill(5)
    return cov


def load_voter_behavior_deltas() -> pd.DataFrame:
    adm = pd.read_csv(ADMIN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    adm = adm.rename(columns=STANDARD_TO_LEGACY)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")
    # Mayoral (prefeito) ballot composition + office-invariant turnout, PLUS the
    # council (vereador) ballot composition. Turnout/abstention are reported once.
    rate_candidates = [
        "turnout_rate", "null_rate", "blank_rate", "valid_vote_rate",
        "null_rate_vereador", "blank_rate_vereador", "valid_vote_rate_vereador",
    ]
    for col in rate_candidates:
        if col in adm.columns:
            adm[col] = pd.to_numeric(adm[col], errors="coerce")
    rate_cols = [c for c in rate_candidates if c in adm.columns]
    a20 = adm[adm["ANO_ELEICAO"] == 2020][["SG_UF", "SG_UE"] + rate_cols]
    a24 = adm[adm["ANO_ELEICAO"] == 2024][["SG_UF", "SG_UE"] + rate_cols]
    m = a20.merge(a24, on=["SG_UF", "SG_UE"], suffixes=("_2020", "_2024"))
    for col in rate_cols:
        m[f"delta_{col}_2024_2020"] = m[f"{col}_2024"] - m[f"{col}_2020"]
    delta_cols = [f"delta_{col}_2024_2020" for col in rate_cols]
    return m[["SG_UF", "SG_UE"] + delta_cols]


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
    if "pop_2010" in df.columns:
        pop = pd.to_numeric(df["pop_2010"], errors="coerce")
        df["log_pop_2010"] = np.where(pop > 0, np.log(pop), np.nan)
    if "income_pc_2010" in df.columns:
        income = pd.to_numeric(df["income_pc_2010"], errors="coerce")
        df["log_income_pc_2010"] = np.where(income >= 0, np.log1p(income), np.nan)
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
    "turnout_rate_2020", "null_rate_2020",
    "share_first_time_candidates_2020", "share_career_politicians_2020",
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading inputs...")
    design = load_design()
    design = add_zone_structure(design)
    # Cluster at the STATE level: the leave-own-state-out shift is constant within
    # a state, and first-instance litigation is correlated within state through the
    # TRE (binding jurisprudence) — the electoral zone is nested in the state, so
    # state clustering is the conservative envelope (Adão–Kolesár–Morales 2019).
    # principal_zone_id is retained for the zone-clustering robustness column.
    design["cluster_id"] = design["SG_UF"]
    design = build_no_rrc_variant(design, load_components(), load_subject_panel())

    # Covariates (drop string/identifier columns not used in regressions)
    cov = load_covariates()
    drop_cols = {
        "NM_UE", "winner_party_2016", "winner_candidate_id_2016",
        "winner_name_2016", "winner_party_2020", "incumbent_ran_2024",
    }
    design = design.merge(
        cov[[c for c in cov.columns if c not in drop_cols]],
        on=["SG_UF", "SG_UE"], how="left",
    )
    design = add_log_controls(design)

    # Voter-behavior deltas (turnout, null, blank share 2024 − 2020)
    design = design.merge(load_voter_behavior_deltas(), on=["SG_UF", "SG_UE"], how="left")

    # Disaggregated turnout elastic margins (facultative/compulsory, education, sex).
    # Under compulsory voting the aggregate turnout null is mechanical; these are the
    # margins where a voter-engagement effect would surface. Keyed on municipality_id_tse
    # (= SG_UE, nationally unique TSE UE code).
    if VOTER_DISAGG_PATH.exists():
        vdis = pd.read_csv(VOTER_DISAGG_PATH, dtype={"municipality_id_tse": str},
                           low_memory=False)
        vdis["SG_UE"] = vdis["municipality_id_tse"].str.strip().str.zfill(5)
        vdis = vdis.drop(columns=["municipality_id_tse"])
        design = design.merge(vdis, on="SG_UE", how="left", validate="m:1")

    # Baseline voter-behavior levels (2020) and registered voters (2024)
    adm = pd.read_csv(ADMIN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    adm = adm.rename(columns=STANDARD_TO_LEGACY)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")

    level_cols_2020 = [c for c in [
        "turnout_rate", "null_rate", "blank_rate", "valid_vote_rate",
        "null_rate_vereador", "blank_rate_vereador", "valid_vote_rate_vereador",
    ] if c in adm.columns]
    adm_2020 = (
        adm[adm["ANO_ELEICAO"] == 2020]
        [["SG_UF", "SG_UE"] + level_cols_2020]
        .rename(columns={c: f"{c}_2020" for c in level_cols_2020})
    )
    # Merge only the 2020-level columns not already present (some mayoral levels
    # arrive earlier via the competition design); this also brings in the council
    # ballot levels and mayoral valid-vote level used as table baseline rows.
    new_level_cols = [f"{c}_2020" for c in level_cols_2020
                      if f"{c}_2020" not in design.columns]
    if new_level_cols:
        design = design.merge(adm_2020[["SG_UF", "SG_UE"] + new_level_cols],
                              on=["SG_UF", "SG_UE"], how="left")

    # Pre-window (2016) and post (2024) voter-behavior levels. The 2016 levels
    # come from detalhe_votacao_munzona_2016 (added to 05_turnout_ballot_outcomes.py);
    # they give voter outcomes the same clean pre-window anchor the competition
    # outcomes already have, enabling (a) ANCOVA-2016 on Y_2024 and (b) the
    # 2016->2020 pre-trend used as a falsification check.
    for yr in (2016, 2024):
        cols_yr = [c for c in level_cols_2020 if c in adm.columns]
        if not cols_yr:
            continue
        adm_yr = (
            adm[adm["ANO_ELEICAO"] == yr]
            [["SG_UF", "SG_UE"] + cols_yr]
            .rename(columns={c: f"{c}_{yr}" for c in cols_yr})
        )
        new_yr = [f"{c}_{yr}" for c in cols_yr if f"{c}_{yr}" not in design.columns]
        if new_yr:
            design = design.merge(adm_yr[["SG_UF", "SG_UE"] + new_yr],
                                  on=["SG_UF", "SG_UE"], how="left")

    # Voter-behavior pre-trends (2020 - 2016): the change over the *pre-treatment*
    # window. A valid instrument should not predict these.
    for c in level_cols_2020:
        if f"{c}_2020" in design.columns and f"{c}_2016" in design.columns:
            design[f"pretrend_{c}_2020_2016"] = (
                design[f"{c}_2020"] - design[f"{c}_2016"]
            )

    adm_2024_aptos = (
        adm[adm["ANO_ELEICAO"] == 2024]
        [["SG_UF", "SG_UE", "registered_voters"]]
        .rename(columns={"registered_voters": "registered_voters_2024"})
    )
    design = design.merge(adm_2024_aptos, on=["SG_UF", "SG_UE"], how="left")

    design = design.rename(columns={
        "code_muni": "municipality_id_ibge",
        "abbrev_state": "state_abbrev_ibge",
    })

    # ---- Candidate entrant-typology outcomes (2024 wave) and open-seat indicator ----
    # NOTE: design uses legacy column SG_UE internally; renamed to municipality_id_tse on save.
    if EXPERIENCE_PATH.exists():
        cexp = pd.read_csv(EXPERIENCE_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
        cexp["municipality_id_tse"] = cexp["municipality_id_tse"].str.strip().str.zfill(5)
        cexp["election_year"] = pd.to_numeric(cexp["election_year"], errors="coerce")
        # Experience panel is now BY OFFICE; this is the executive (mayoral) design.
        if "office_group" in cexp.columns:
            cexp = cexp[cexp["office_group"] == "executive"]
        cexp = cexp.rename(columns={"municipality_id_tse": "SG_UE"})

        # 2024 wave: outcome columns
        exp_cols_2024 = ["share_first_time_candidates", "share_serial_challenger",
                         "share_cross_cycle_returner", "open_seat"]
        cexp_2024 = cexp[cexp["election_year"] == 2024].copy()
        for col in exp_cols_2024:
            if col in cexp_2024.columns:
                cexp_2024[col] = pd.to_numeric(cexp_2024[col], errors="coerce")
        rename_24 = {c: f"{c}_2024" for c in exp_cols_2024 if c in cexp_2024.columns}
        cexp_2024 = cexp_2024.rename(columns=rename_24)
        keep_24 = ["SG_UE"] + list(rename_24.values())
        design = design.merge(
            cexp_2024[[c for c in keep_24 if c in cexp_2024.columns]],
            on="SG_UE", how="left",
        )

        # 2020 wave: add serial_challenger and cross_cycle_returner (not in covariates yet)
        exp_extra_2020 = ["share_serial_challenger", "share_cross_cycle_returner"]
        cexp_2020 = cexp[cexp["election_year"] == 2020].copy()
        for col in exp_extra_2020:
            if col in cexp_2020.columns:
                cexp_2020[col] = pd.to_numeric(cexp_2020[col], errors="coerce")
        rename_20 = {c: f"{c}_2020" for c in exp_extra_2020 if c in cexp_2020.columns}
        cexp_2020 = cexp_2020.rename(columns=rename_20)
        new_20 = [v for v in rename_20.values() if v not in design.columns]
        if new_20:
            design = design.merge(
                cexp_2020[["SG_UE"] + new_20],
                on="SG_UE", how="left",
            )

        # Delta outcomes
        delta_pairs = [
            ("share_first_time_candidates_2024", "share_first_time_candidates_2020"),
            ("share_serial_challenger_2024",     "share_serial_challenger_2020"),
            ("share_cross_cycle_returner_2024",  "share_cross_cycle_returner_2020"),
        ]
        for col24, col20 in delta_pairs:
            if col24 in design.columns and col20 in design.columns:
                delta_name = "delta_" + col24.replace("_2024", "_2024_2020")
                design[delta_name] = design[col24] - design[col20]

        n_open = int(design["open_seat_2024"].sum()) if "open_seat_2024" in design.columns else 0
        print(f"  open_seat_2024: {n_open:,} municipalities")
    else:
        print("  WARNING: candidate_experience_panel.csv not found; entrant typology skipped.")

    print(f"Design: {len(design):,} municipalities, {len(design.columns)} columns")

    out_path = ESTIMATION_DIR / "executive_margin_design.csv"
    design.rename(columns=LEGACY_TO_STANDARD).to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
