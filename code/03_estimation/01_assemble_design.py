"""
Assemble the INSTRUMENT-FREE base design matrix.

Merges covariates, electoral outcomes, and zone structure into a single flat
file used by the estimation scripts. The act-based instrument (bartik_iv_act)
and its endogenous treatment are added downstream by 01d_act_family_ivs.py;
this script only sets cluster_id (= state). See docs/STATE_OF_THE_ART.md.

Inputs  (from data/clean/):
  executive_vote_shift_share_design.csv   — candidate/vote OUTCOMES, outcomes only
                                            (03_candidate_composition -> 03b_vote_outcomes)
  municipal_covariates.csv
  electoral_admin_outcomes.csv
  candidate_experience_panel.csv
  municipio_region_crosswalk.csv

Input (from data/raw/):
  lista-zonas-municipios-10-07-24.csv   — zone → municipality lookup

Output:
  data/estimation/executive_margin_design.csv

MERGE DISCIPLINE: every merge here passes an explicit ``validate=`` (so pandas
raises on any many-to-many key) and goes through ``merged()``, which logs rows
before/after and the count of unmatched rows. No names are ever used as a join
key — the municipality TSE code (zero-padded 5-char) is the only key.
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
COVARIATES_PATH    = CLEAN_DIR / "municipal_covariates.csv"
ADMIN_PATH         = CLEAN_DIR / "electoral_admin_outcomes.csv"
EXPERIENCE_PATH    = CLEAN_DIR / "candidate_experience_panel.csv"

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
# Merge ledger — every join goes through here. validate= makes pandas raise on
# any many-to-many key; we additionally log rows-in/rows-out and unmatched rows.
# ---------------------------------------------------------------------------

def merged(left, right, on, how, validate, label, probe=None):
    before = len(left)
    on_cols = [on] if isinstance(on, str) else list(on)
    out = left.merge(right, on=on, how=how, validate=validate)
    if probe is None:
        rest = [c for c in right.columns if c not in on_cols]
        probe = rest[0] if rest else None
    unmatched = int(out[probe].isna().sum()) if probe else 0
    flag = "" if before == len(out) else "  <-- ROW COUNT CHANGED"
    print(f"  [merge] {label:34s} {before:,}->{len(out):,} | unmatched {unmatched:,}"
          f" (probe={probe}){flag}")
    return out


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_design() -> pd.DataFrame:
    df = pd.read_csv(EXECUTIVE_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    df = df.rename(columns=STANDARD_TO_LEGACY)
    return df.drop_duplicates(subset=["SG_UF", "SG_UE"], keep="first").reset_index(drop=True)


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
    for col in ["turnout_rate", "null_rate", "blank_rate", "valid_vote_rate"]:
        if col in adm.columns:
            adm[col] = pd.to_numeric(adm[col], errors="coerce")
    rate_cols = [c for c in ["turnout_rate", "null_rate", "blank_rate", "valid_vote_rate"]
                 if c in adm.columns]
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

def attach_family_bartik(df: pd.DataFrame) -> pd.DataFrame:
    """Set the clustering variable on the instrument-free base design.

    As of 2026-06-26 the base executive design carries OUTCOMES + CONTROLS only —
    no instrument. The act-based shift-share instrument (bartik_iv_act) and its
    endogenous treatment (delta_log1p_act_lawsuits) are added downstream by
    03_estimation/01d_act_family_ivs.py, which writes act_design.csv. The retired
    substance-family instrument (the old municipality_bartik_iv.csv) is no longer
    merged here.

    cluster_id = state (SG_UF): the leave-own-state shift is common to all
    municipalities within a state, so state is the level at which the instrument's
    identifying variation is shared.
    """
    df = df.copy()
    df["cluster_id"] = df["SG_UF"]
    print(f"  base design: outcomes + controls only (instrument added by "
          f"01d_act_family_ivs.py); cluster_id = state")
    return df


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
    # principal_zone_id kept for reference; cluster_id is set to the state inside
    # attach_family_bartik (the level at which the leave-own-state shift is shared).
    design = attach_family_bartik(design)

    # Covariates (drop string/identifier columns not used in regressions)
    cov = load_covariates()
    drop_cols = {
        "NM_UE", "winner_party_2016", "winner_candidate_id_2016",
        "winner_name_2016", "winner_party_2020", "incumbent_ran_2024",
    }
    design = merged(
        design, cov[[c for c in cov.columns if c not in drop_cols]],
        on=["SG_UF", "SG_UE"], how="left", validate="one_to_one", label="municipal covariates")
    design = add_log_controls(design)

    # Voter-behavior deltas (turnout, null, blank share 2024 − 2020)
    design = merged(design, load_voter_behavior_deltas(), on=["SG_UF", "SG_UE"],
                    how="left", validate="one_to_one", label="voter-behavior deltas")

    # Baseline voter-behavior levels (2020) and registered voters (2024)
    adm = pd.read_csv(ADMIN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    adm = adm.rename(columns=STANDARD_TO_LEGACY)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")

    level_cols_2020 = [c for c in ["turnout_rate", "null_rate", "blank_rate", "valid_vote_rate"]
                       if c in adm.columns]
    adm_2020 = (
        adm[adm["ANO_ELEICAO"] == 2020]
        [["SG_UF", "SG_UE"] + level_cols_2020]
        .rename(columns={c: f"{c}_2020" for c in level_cols_2020})
    )
    if "turnout_rate_2020" not in design.columns:
        design = merged(design, adm_2020, on=["SG_UF", "SG_UE"], how="left",
                        validate="one_to_one", label="admin levels 2020")

    adm_2024_aptos = (
        adm[adm["ANO_ELEICAO"] == 2024]
        [["SG_UF", "SG_UE", "registered_voters"]]
        .rename(columns={"registered_voters": "registered_voters_2024"})
    )
    design = merged(design, adm_2024_aptos, on=["SG_UF", "SG_UE"], how="left",
                    validate="one_to_one", label="registered voters 2024")

    # valid_vote_rate_2020 lagged DV. All admin rates share the registered-voter
    # denominator (QT_APTOS), so turnout = valid + null + blank EXACTLY; recover the
    # 2020 valid level from that identity. (The adm_2020 merge above is guarded on
    # turnout_rate_2020 already being present, so valid_vote_rate_2020 would
    # otherwise be silently dropped — and without this lagged DV the
    # delta_valid_vote_rate IV is estimated off-spec and spuriously significant.)
    if ("valid_vote_rate_2020" not in design.columns and
            {"turnout_rate_2020", "null_rate_2020", "blank_rate_2020"} <= set(design.columns)):
        design["valid_vote_rate_2020"] = (
            design["turnout_rate_2020"] - design["null_rate_2020"] - design["blank_rate_2020"])

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
        design = merged(
            design, cexp_2024[[c for c in keep_24 if c in cexp_2024.columns]],
            on="SG_UE", how="left", validate="m:1", label="cand. experience 2024")

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
            design = merged(
                design, cexp_2020[["SG_UE"] + new_20],
                on="SG_UE", how="left", validate="m:1", label="cand. experience 2020")

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

    # ---- Sub-state geography for tighter-FE specs (BD municipio directory) ----
    # Built by code/01_download/09_download_bd_municipio_directory.py. Provides
    # IBGE meso/micro/immediate/intermediate region codes keyed by TSE id, so
    # estimation can absorb regional litigation culture below the state level.
    region_cw = CLEAN_DIR / "municipio_region_crosswalk.csv"
    if region_cw.exists():
        rc = pd.read_csv(region_cw, dtype=str)
        rc["SG_UE"] = rc["id_municipio_tse"].str.strip().str.zfill(5)
        rc = rc.rename(columns={
            "id_mesorregiao":          "code_meso",
            "id_microrregiao":         "code_micro",
            "id_regiao_imediata":      "code_imediata",
            "id_regiao_intermediaria": "code_intermediaria",
        })
        keep = ["SG_UE", "code_meso", "code_micro", "code_imediata", "code_intermediaria"]
        rc = rc[[c for c in keep if c in rc.columns]].drop_duplicates("SG_UE")
        design = merged(design, rc, on="SG_UE", how="left", validate="m:1",
                        label="region crosswalk")
        print(f"  region crosswalk: {design['code_meso'].notna().sum():,}/{len(design):,} "
              f"municipalities matched (meso/micro/immediate/intermediate)")
    else:
        print("  WARNING: municipio_region_crosswalk.csv not found; region FE unavailable.")

    # ---- Intensive-margin (ELECTED) delta outcomes ----
    # Composition among those actually ELECTED (winners), not the full candidate
    # pool. For the single-winner mayoral race these reduce to 0/1 winner-attribute
    # indicators; named identically to the legislative design (01b) so the R engine
    # estimates group E on both offices with one definition.
    elected_pairs = [
        ("elected_female_share",           "delta_elected_female_share_2024_2020"),
        ("elected_nonwhite_share",         "delta_elected_nonwhite_share_2024_2020"),
        ("elected_higher_education_share", "delta_elected_higher_ed_share_2024_2020"),
        ("elected_mean_age",               "delta_elected_mean_age_2024_2020"),
        ("incumbent_reelected_share",      "delta_incumbent_reelected_share_2024_2020"),
    ]
    for base, delta_name in elected_pairs:
        c24, c20 = f"{base}_2024", f"{base}_2020"
        if c24 in design.columns and c20 in design.columns:
            design[delta_name] = (
                pd.to_numeric(design[c24], errors="coerce")
                - pd.to_numeric(design[c20], errors="coerce")
            )

    print(f"Design: {len(design):,} municipalities, {len(design.columns)} columns")

    out_path = ESTIMATION_DIR / "executive_margin_design.csv"
    design.rename(columns=LEGACY_TO_STANDARD).to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
