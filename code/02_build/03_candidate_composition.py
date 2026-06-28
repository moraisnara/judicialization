"""
03_candidate_composition.py — candidate-composition OUTCOMES builder.

Extracted (2026-06-24) from the archived `02_bartik_inputs.py`, which entangled
two unrelated jobs: (a) the OLD zona/subject-taxonomy shift-share instrument and
(b) the candidate-composition outcomes. The instrument moved to the act-based
design (`00_sig_lawsuit_panel` -> `01d_act_family_crosswalk` -> `01d_act_family_ivs`);
this script keeps ONLY the outcome half, so the live pipeline can regenerate the
outcomes with no archived dependency and no dead old-instrument code.

Behaviour-preserving: the candidate loading, person-key history flags, and the
office-level outcome aggregation are copied verbatim from the archived script, so
the numbers are identical. The ONLY change is that the per-office design no longer
merges in the old bartik / judicialization-totals columns — it is outcomes only.
The new SIG family instrument is attached later, at the Stage-3 assemble step.

Inputs (data/raw/):
  consulta_cand_2020/..._BRASIL.csv, consulta_cand_2024/..._BRASIL.csv  (candidates)
  lista-zonas-municipios-10-07-24.csv                                   (muni universe)

Outputs (data/clean/):
  office_candidate_outcomes_panel.csv   muni x office x year composition outcomes
  executive_shift_share_design.csv      muni-wide (2020/2024) prefeito composition
  legislative_shift_share_design.csv    muni-wide (2020/2024) vereador composition
The two design files are the base read by 03b_vote_outcomes.py (which adds vote
shares) and ultimately by the Stage-3 assemble.

Municipality key is the TSE code, written as a zero-padded 5-char string
(`municipality_id_tse`); names are never used as a merge key.
"""
from __future__ import annotations

from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"
TABLES_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"
LOOKUP_PATH = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"

TARGET_YEARS = [2020, 2024]

STANDARD_TO_LEGACY = {
    "election_year": "ANO_ELEICAO",
    "state": "SG_UF",
    "municipality_id_tse": "SG_UE",
    "municipality_name": "NM_UE",
}
LEGACY_TO_STANDARD = {value: key for key, value in STANDARD_TO_LEGACY.items()}
OFFICE_MAP = {
    "PREFEITO": "executive",
    "VEREADOR": "legislative",
}
ELECTED_STATUSES = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÃ‰DIA", "ELEITO POR MÉDIA"}


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip().upper()
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return " ".join(text.split())


def load_zone_lookup() -> pd.DataFrame:
    """Full municipality universe from the raw TSE zona->municipality list."""
    lookup = pd.read_csv(LOOKUP_PATH, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(
        columns={
            "UF": "SG_UF",
            "ZONA": "zona_eleitoral",
            "COD_LOCALIDADE": "COD_MUN",
            "NOM_LOCALIDADE": "NM_UE",
        }
    )
    lookup = lookup[lookup["SG_UF"] != "ZZ"].copy()
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup = lookup[["SG_UF", "SG_UE", "NM_UE"]].drop_duplicates()
    return lookup


def load_candidates() -> pd.DataFrame:
    usecols = [
        "ANO_ELEICAO", "DT_ELEICAO", "NR_TURNO", "TP_ABRANGENCIA", "CD_TIPO_ELEICAO",
        "SG_UF", "SG_UE", "NM_UE", "DS_CARGO", "SQ_CANDIDATO", "NM_CANDIDATO",
        "NR_TITULO_ELEITORAL_CANDIDATO", "NR_PARTIDO", "NM_COLIGACAO", "DS_GENERO",
        "DS_GRAU_INSTRUCAO", "DS_ESTADO_CIVIL", "DS_COR_RACA", "DT_NASCIMENTO",
        "DS_SIT_TOT_TURNO",
    ]
    frames: list[pd.DataFrame] = []
    for year in TARGET_YEARS:
        path = RAW_DIR / f"consulta_cand_{year}" / f"consulta_cand_{year}_BRASIL.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, sep=";", encoding="latin-1", usecols=usecols,
                         dtype=str, low_memory=False)
        frames.append(df)
    if not frames:
        return pd.DataFrame()

    candidates = pd.concat(frames, ignore_index=True)
    candidates = candidates.loc[
        (candidates["TP_ABRANGENCIA"] == "MUNICIPAL")
        & (candidates["CD_TIPO_ELEICAO"] == "2")
        & (candidates["DS_CARGO"].isin(OFFICE_MAP))
    ].copy()
    candidates["SG_UE"] = candidates["SG_UE"].str.strip().str.zfill(5)
    candidates["ANO_ELEICAO"] = pd.to_numeric(candidates["ANO_ELEICAO"], errors="coerce")
    candidates["office_group"] = candidates["DS_CARGO"].map(OFFICE_MAP)
    candidates["DT_ELEICAO"] = pd.to_datetime(
        candidates["DT_ELEICAO"], format="%d/%m/%Y", errors="coerce")
    candidates["NR_TURNO"] = pd.to_numeric(candidates["NR_TURNO"], errors="coerce")
    candidates["DT_NASCIMENTO"] = pd.to_datetime(
        candidates["DT_NASCIMENTO"], format="%d/%m/%Y", errors="coerce")
    candidates["candidate_age"] = (
        (candidates["DT_ELEICAO"] - candidates["DT_NASCIMENTO"]).dt.days / 365.25)
    candidates["is_female"] = (candidates["DS_GENERO"] == "FEMININO").astype(int)
    candidates["is_nonwhite"] = candidates["DS_COR_RACA"].isin(
        ["PRETA", "PARDA", "AMARELA", "INDÃGENA", "INDIGENA"]).astype(int)
    candidates["is_higher_education"] = candidates["DS_GRAU_INSTRUCAO"].fillna("").str.contains(
        "SUPERIOR", regex=False).astype(int)
    candidates["is_married"] = (candidates["DS_ESTADO_CIVIL"] == "CASADO(A)").astype(int)
    candidates["is_elected"] = candidates["DS_SIT_TOT_TURNO"].isin(ELECTED_STATUSES).astype(int)
    candidates["title_key"] = (
        candidates["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip())
    candidates["title_key"] = candidates["title_key"].replace({"-4": "", "#NULO#": ""})
    candidates["person_key"] = (
        candidates["NM_CANDIDATO"].map(normalize_text)
        + "|"
        + candidates["DT_NASCIMENTO"].dt.strftime("%Y-%m-%d").fillna(""))
    candidates["person_key"] = candidates["title_key"].where(
        candidates["title_key"].ne(""), candidates["person_key"])
    # Keep one row per candidate within year and municipality, preferring the later
    # turn when second-round rows duplicate first-round records.
    candidates = candidates.sort_values(
        ["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO", "NR_TURNO"])
    candidates = candidates.drop_duplicates(
        subset=["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO"],
        keep="last")
    return candidates


def add_candidate_history_flags(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    candidates = candidates.copy()
    baseline = candidates[candidates["ANO_ELEICAO"] == 2020].copy()
    baseline_keys = (
        baseline.loc[baseline["person_key"].ne(""), ["SG_UF", "SG_UE", "office_group", "person_key"]]
        .drop_duplicates().assign(ran_in_2020=1))
    elected_keys = (
        baseline.loc[
            (baseline["person_key"].ne("")) & (baseline["is_elected"] == 1),
            ["SG_UF", "SG_UE", "office_group", "person_key"]]
        .drop_duplicates().assign(elected_in_2020=1))

    candidates = candidates.merge(
        baseline_keys, on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left", validate="many_to_one")
    candidates = candidates.merge(
        elected_keys, on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left", validate="many_to_one")
    candidates["ran_in_2020"] = candidates["ran_in_2020"].fillna(0).astype(int)
    candidates["elected_in_2020"] = candidates["elected_in_2020"].fillna(0).astype(int)
    candidates["is_new_candidate_vs_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["ran_in_2020"] == 0)).astype(int)
    candidates["is_incumbent_from_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["elected_in_2020"] == 1)).astype(int)
    candidates["is_reelected_incumbent_2024"] = (
        (candidates["is_incumbent_from_2020"] == 1) & (candidates["is_elected"] == 1)).astype(int)
    return candidates


def safe_mean(series: pd.Series) -> float:
    valid = series.dropna()
    if valid.empty:
        return float("nan")
    return float(valid.mean())


def safe_sum(series: pd.Series) -> int:
    return int(series.fillna(0).sum())


def summarize_office_outcomes(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame()

    outcomes = (
        candidates.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            total_candidates=("SQ_CANDIDATO", "nunique"),
            elected_candidates=("is_elected", "sum"),
            party_count=("NR_PARTIDO", lambda s: s.fillna("").replace("", pd.NA).dropna().nunique()),
            coalition_count=("NM_COLIGACAO", lambda s: s.fillna("").replace("", pd.NA).dropna().nunique()),
            female_share=("is_female", "mean"),
            nonwhite_share=("is_nonwhite", "mean"),
            higher_education_share=("is_higher_education", "mean"),
            married_share=("is_married", "mean"),
            mean_age=("candidate_age", "mean"),
            sd_age=("candidate_age", "std"),
            elected_female_share=("is_female", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_nonwhite_share=("is_nonwhite", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_higher_education_share=("is_higher_education", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            elected_mean_age=("candidate_age", lambda s: safe_mean(s[candidates.loc[s.index, "is_elected"] == 1])),
            new_candidate_count=("is_new_candidate_vs_2020", safe_sum),
            incumbent_candidate_count=("is_incumbent_from_2020", safe_sum),
            incumbent_reelected_count=("is_reelected_incumbent_2024", safe_sum),
        )
    )

    denominator = outcomes["total_candidates"].replace(0, np.nan)
    elected_denominator = outcomes["elected_candidates"].replace(0, np.nan)
    outcomes["new_candidate_share"] = outcomes["new_candidate_count"] / denominator
    outcomes["incumbent_candidate_share"] = outcomes["incumbent_candidate_count"] / denominator
    outcomes["incumbent_reelected_share"] = outcomes["incumbent_reelected_count"] / elected_denominator
    outcomes["candidate_hhi_party"] = np.nan
    outcomes["effective_party_count_candidates"] = np.nan

    party_counts = (
        candidates.groupby(
            ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NR_PARTIDO"], as_index=False)
        .agg(n_candidates=("SQ_CANDIDATO", "nunique")))
    party_totals = party_counts.groupby(
        ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False
    )["n_candidates"].sum().rename(columns={"n_candidates": "total_candidates_tmp"})
    party_counts = party_counts.merge(
        party_totals, on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left", validate="many_to_one")
    party_counts["party_share"] = party_counts["n_candidates"] / party_counts["total_candidates_tmp"]
    concentration = (
        party_counts.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(
            candidate_hhi_party=("party_share", lambda s: float((s**2).sum())),
            effective_party_count_candidates=("party_share", lambda s: float(1 / (s**2).sum()) if (s**2).sum() > 0 else np.nan),
        ))
    outcomes = outcomes.merge(
        concentration, on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left", validate="one_to_one", suffixes=("", "_calc"))
    outcomes["candidate_hhi_party"] = outcomes["candidate_hhi_party_calc"]
    outcomes["effective_party_count_candidates"] = outcomes["effective_party_count_candidates_calc"]
    outcomes = outcomes.drop(columns=["candidate_hhi_party_calc", "effective_party_count_candidates_calc"])
    return outcomes


def build_municipality_universe(
    zone_lookup: pd.DataFrame, office_outcomes: pd.DataFrame) -> pd.DataFrame:
    universe = (
        zone_lookup.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(NM_UE=("NM_UE", "first")))
    if not office_outcomes.empty:
        outcome_universe = (
            office_outcomes.groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first")))
        universe = (
            pd.concat([universe, outcome_universe], ignore_index=True)
            .groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first")))
    return universe


def build_design_for_office(
    office_group: str,
    municipality_universe: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Outcomes-only per-office design: pivot composition outcomes to 2020/2024
    wide + within-municipality deltas. NO instrument columns (attached at assemble)."""
    office_panel = office_outcomes[office_outcomes["office_group"] == office_group].copy()
    design = municipality_universe.copy()

    if not office_panel.empty:
        value_cols = [
            col for col in office_panel.columns
            if col not in {"office_group", "SG_UF", "SG_UE", "NM_UE", "ANO_ELEICAO"}]
        office_wide = office_panel.pivot_table(
            index=["SG_UF", "SG_UE"], columns="ANO_ELEICAO",
            values=value_cols, fill_value=0)
        office_wide.columns = [f"{name}_{year}" for name, year in office_wide.columns]
        office_wide = office_wide.reset_index()
        # universe is one row per (SG_UF, SG_UE); office_wide likewise -> 1:1.
        design = design.merge(
            office_wide, on=["SG_UF", "SG_UE"], how="left", validate="one_to_one")

    if "total_candidates_2020" in design.columns and "total_candidates_2024" in design.columns:
        design["delta_total_candidates_2024_2020"] = (
            design["total_candidates_2024"] - design["total_candidates_2020"])
    if "female_share_2020" in design.columns and "female_share_2024" in design.columns:
        design["delta_female_share_2024_2020"] = (
            design["female_share_2024"] - design["female_share_2020"])
    if "candidate_hhi_party_2020" in design.columns and "candidate_hhi_party_2024" in design.columns:
        design["delta_candidate_hhi_party_2024_2020"] = (
            design["candidate_hhi_party_2024"] - design["candidate_hhi_party_2020"])
    if ("effective_party_count_candidates_2020" in design.columns
            and "effective_party_count_candidates_2024" in design.columns):
        design["delta_effective_party_count_candidates_2024_2020"] = (
            design["effective_party_count_candidates_2024"]
            - design["effective_party_count_candidates_2020"])
    return design


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    zone_lookup = load_zone_lookup()
    candidates = load_candidates()
    candidates = add_candidate_history_flags(candidates)
    office_outcomes = summarize_office_outcomes(candidates)
    municipality_universe = build_municipality_universe(zone_lookup, office_outcomes)

    executive_design = build_design_for_office("executive", municipality_universe, office_outcomes)
    legislative_design = build_design_for_office("legislative", municipality_universe, office_outcomes)

    # zero-pad the TSE key everywhere before write (never carry names as a key)
    for df in (office_outcomes, executive_design, legislative_design):
        if "SG_UE" in df.columns:
            df["SG_UE"] = df["SG_UE"].astype(str).str.zfill(5)

    office_outcomes.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "office_candidate_outcomes_panel.csv", index=False, encoding="utf-8-sig")
    executive_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "executive_shift_share_design.csv", index=False, encoding="utf-8-sig")
    legislative_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "legislative_shift_share_design.csv", index=False, encoding="utf-8-sig")

    print(f"office_candidate_outcomes_panel: {len(office_outcomes):,} rows "
          f"({office_outcomes['SG_UE'].nunique():,} munis x office x year)")
    print(f"executive_shift_share_design:    {len(executive_design):,} munis, "
          f"{len(executive_design.columns)} cols")
    print(f"legislative_shift_share_design:  {len(legislative_design):,} munis, "
          f"{len(legislative_design.columns)} cols")


if __name__ == "__main__":
    main()
