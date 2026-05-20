from __future__ import annotations

from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"
TABLES_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"

ZONA_PANEL_PATH = DERIVED_DIR / "zona_lawsuit_panel.csv"
CROSSWALK_PATH = DERIVED_DIR / "shift_share_subject_crosswalk.csv"
OVERRIDES_PATH = DERIVED_DIR / "shift_share_subject_manual_assignments.csv"
LOOKUP_PATH = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"

TARGET_YEARS = [2020, 2024]
STANDARD_TO_LEGACY = {
    "election_year": "ANO_ELEICAO",
    "state": "SG_UF",
    "electoral_zone": "zona_eleitoral",
    "municipality_id_tse": "SG_UE",
    "municipality_name": "NM_UE",
    "n_municipalities_in_zone": "n_municipios_zona",
    "case_class_code": "CD_CLASSE",
    "case_class_name": "DS_CLASSE",
    "main_subject_code": "CD_ASSUNTO_PRINCIPAL",
    "main_subject_name": "DS_ASSUNTO_PRINCIPAL",
}
LEGACY_TO_STANDARD = {value: key for key, value in STANDARD_TO_LEGACY.items()}
MAIN_FAMILIES = {
    "eligibility_ballot_access",
    "abuse_misuse_office",
    "campaign_conduct",
    "information_environment",
}
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


def load_crosswalk() -> pd.DataFrame:
    crosswalk = pd.read_csv(
        CROSSWALK_PATH,
        dtype={"CD_ASSUNTO_PRINCIPAL": str},
        keep_default_na=False,
    )
    if OVERRIDES_PATH.exists():
        overrides = pd.read_csv(
            OVERRIDES_PATH,
            dtype={"CD_ASSUNTO_PRINCIPAL": str},
            keep_default_na=False,
        )
        crosswalk = crosswalk.merge(
            overrides,
            on="CD_ASSUNTO_PRINCIPAL",
            how="left",
            validate="one_to_one",
            suffixes=("", "_override"),
        )
        crosswalk["manual_family"] = crosswalk["manual_family_override"].where(
            crosswalk["manual_family_override"].str.strip().ne(""),
            crosswalk["manual_family"],
        )
        crosswalk["notes"] = crosswalk["notes_override"].where(
            crosswalk["notes_override"].str.strip().ne(""),
            crosswalk["notes"],
        )
    crosswalk["topic_family"] = crosswalk["manual_family"].where(
        crosswalk["manual_family"].str.strip().ne(""),
        crosswalk["suggested_family"],
    )
    return crosswalk[["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"]]


def load_zone_lookup() -> pd.DataFrame:
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
    lookup["zona_eleitoral"] = pd.to_numeric(lookup["zona_eleitoral"], errors="coerce")
    lookup = lookup.dropna(subset=["zona_eleitoral"])
    lookup["zona_eleitoral"] = lookup["zona_eleitoral"].astype(int)
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup = lookup[["SG_UF", "zona_eleitoral", "SG_UE", "NM_UE"]].drop_duplicates()
    return lookup


def load_zone_subject_panel(crosswalk: pd.DataFrame) -> pd.DataFrame:
    panel = pd.read_csv(
        ZONA_PANEL_PATH,
        dtype={"municipality_id_tse": str, "case_class_code": str, "main_subject_code": str},
        low_memory=False,
    )
    panel = panel.rename(columns=STANDARD_TO_LEGACY)
    panel = panel[panel["ANO_ELEICAO"].isin(TARGET_YEARS)].copy()
    panel = (
        panel.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "zona_eleitoral",
                "CD_CLASSE",
                "DS_CLASSE",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
            ],
            as_index=False,
        )
        .agg(n_lawsuits=("n_lawsuits", "max"))
    )
    panel = panel.merge(
        crosswalk,
        on=["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"],
        how="left",
        validate="many_to_one",
    )
    panel["topic_family"] = panel["topic_family"].fillna("unmapped")
    panel["zone_id"] = panel["SG_UF"].astype(str) + "_" + panel["zona_eleitoral"].astype(str)
    return panel


def build_municipality_subject_panel(
    zone_subject_panel: pd.DataFrame,
    zone_lookup: pd.DataFrame,
) -> pd.DataFrame:
    municipal = zone_subject_panel.merge(
        zone_lookup,
        on=["SG_UF", "zona_eleitoral"],
        how="left",
        validate="many_to_many",
    )
    municipal["competition_case"] = municipal["topic_family"].isin(MAIN_FAMILIES)
    return municipal


def build_municipality_bartik_components(
    municipal_panel: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    competition = municipal_panel[municipal_panel["competition_case"]].copy()

    municipality_subject = (
        competition.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "SG_UE",
                "NM_UE",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
                "topic_family",
            ],
            as_index=False,
        )
        .agg(n_lawsuits=("n_lawsuits", "sum"))
    )

    baseline = municipality_subject[municipality_subject["ANO_ELEICAO"] == 2020].copy()
    base_totals = baseline.groupby(["SG_UF", "SG_UE"])["n_lawsuits"].transform("sum")
    baseline["baseline_share_2020"] = baseline["n_lawsuits"] / base_totals

    zone_subject = (
        competition.groupby(
            [
                "ANO_ELEICAO",
                "SG_UF",
                "zona_eleitoral",
                "CD_ASSUNTO_PRINCIPAL",
                "DS_ASSUNTO_PRINCIPAL",
                "topic_family",
            ],
            as_index=False,
        )
        .agg(n_lawsuits=("n_lawsuits", "sum"))
    )
    by_uf = (
        zone_subject.groupby(
            ["ANO_ELEICAO", "SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            as_index=False,
        )
        .agg(uf_lawsuits=("n_lawsuits", "sum"))
    )

    # Shift formula: log-change of the leave-state-out aggregate across other states.
    # This is a caseload-weighted adaptation of AMV (2025, JPE): each other state's
    # contribution is weighted by its case count rather than equally, which is necessary
    # because Brazilian lawsuit topics are sparse (many states have 0 cases per topic).
    # The unweighted AMV average collapses to near-zero for sparse topics and kills
    # the first stage (F < 1); the aggregate log-change preserves the strong first stage.
    national = (
        zone_subject.groupby(
            ["ANO_ELEICAO", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            as_index=False,
        )
        .agg(national_lawsuits=("n_lawsuits", "sum"))
    )
    shifter_base = by_uf.merge(
        national,
        on=["ANO_ELEICAO", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
        how="left",
        validate="many_to_one",
    )
    shifter_base["leave_uf_out_lawsuits"] = (
        shifter_base["national_lawsuits"] - shifter_base["uf_lawsuits"]
    )

    shifters = (
        shifter_base.pivot_table(
            index=["SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
            columns="ANO_ELEICAO",
            values="leave_uf_out_lawsuits",
            fill_value=0,
        )
        .rename(columns={2020: "leave_uf_out_2020", 2024: "leave_uf_out_2024"})
        .reset_index()
    )
    for column in ["leave_uf_out_2020", "leave_uf_out_2024"]:
        if column not in shifters.columns:
            shifters[column] = 0
    shifters["shock_log_growth_2020_2024"] = (
        np.log1p(shifters["leave_uf_out_2024"]) - np.log1p(shifters["leave_uf_out_2020"])
    )

    components = baseline.merge(
        shifters,
        on=["SG_UF", "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL", "topic_family"],
        how="left",
        validate="many_to_one",
    )
    components["shock_log_growth_2020_2024"] = components["shock_log_growth_2020_2024"].fillna(0.0)
    components["bartik_component"] = (
        components["baseline_share_2020"] * components["shock_log_growth_2020_2024"]
    )

    bartik = (
        components.groupby(["SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            bartik_iv_2020_2024=("bartik_component", "sum"),
            baseline_competition_lawsuits_2020=("n_lawsuits", "sum"),
            baseline_subjects_2020=("CD_ASSUNTO_PRINCIPAL", "nunique"),
        )
    )
    return municipality_subject, components, bartik


def build_municipality_judicialization_totals(municipal_panel: pd.DataFrame) -> pd.DataFrame:
    competition = municipal_panel[municipal_panel["competition_case"]].copy()
    totals = (
        competition.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            competition_lawsuits=("n_lawsuits", "sum"),
            competition_subjects=("CD_ASSUNTO_PRINCIPAL", "nunique"),
            competition_families=("topic_family", "nunique"),
        )
    )
    wide = (
        totals.pivot_table(
            index=["SG_UF", "SG_UE", "NM_UE"],
            columns="ANO_ELEICAO",
            values=["competition_lawsuits", "competition_subjects", "competition_families"],
            fill_value=0,
        )
    )
    wide.columns = [f"{name}_{year}" for name, year in wide.columns]
    wide = wide.reset_index()
    for year in TARGET_YEARS:
        wide[f"log1p_competition_lawsuits_{year}"] = np.log1p(
            wide.get(f"competition_lawsuits_{year}", 0)
        )
    wide["delta_log1p_competition_lawsuits_2024_2020"] = (
        wide["log1p_competition_lawsuits_2024"] - wide["log1p_competition_lawsuits_2020"]
    )
    return wide


def load_candidates() -> pd.DataFrame:
    usecols = [
        "ANO_ELEICAO",
        "DT_ELEICAO",
        "NR_TURNO",
        "TP_ABRANGENCIA",
        "CD_TIPO_ELEICAO",
        "SG_UF",
        "SG_UE",
        "NM_UE",
        "DS_CARGO",
        "SQ_CANDIDATO",
        "NM_CANDIDATO",
        "NR_TITULO_ELEITORAL_CANDIDATO",
        "NR_PARTIDO",
        "NM_COLIGACAO",
        "DS_GENERO",
        "DS_GRAU_INSTRUCAO",
        "DS_ESTADO_CIVIL",
        "DS_COR_RACA",
        "DT_NASCIMENTO",
        "DS_SIT_TOT_TURNO",
    ]
    frames: list[pd.DataFrame] = []
    for year in TARGET_YEARS:
        path = RAW_DIR / f"consulta_cand_{year}" / f"consulta_cand_{year}_BRASIL.csv"
        if not path.exists():
            continue
        df = pd.read_csv(
            path,
            sep=";",
            encoding="latin-1",
            usecols=usecols,
            dtype=str,
            low_memory=False,
        )
        frames.append(df)
    if not frames:
        return pd.DataFrame()

    candidates = pd.concat(frames, ignore_index=True)
    candidates = candidates.loc[
        (candidates["TP_ABRANGENCIA"] == "MUNICIPAL")
        & (candidates["CD_TIPO_ELEICAO"] == "2")
        & (candidates["DS_CARGO"].isin(OFFICE_MAP))
    ].copy()
    candidates["ANO_ELEICAO"] = pd.to_numeric(candidates["ANO_ELEICAO"], errors="coerce")
    candidates["office_group"] = candidates["DS_CARGO"].map(OFFICE_MAP)
    candidates["DT_ELEICAO"] = pd.to_datetime(
        candidates["DT_ELEICAO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["NR_TURNO"] = pd.to_numeric(candidates["NR_TURNO"], errors="coerce")
    candidates["DT_NASCIMENTO"] = pd.to_datetime(
        candidates["DT_NASCIMENTO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["candidate_age"] = (
        (candidates["DT_ELEICAO"] - candidates["DT_NASCIMENTO"]).dt.days / 365.25
    )
    candidates["is_female"] = (candidates["DS_GENERO"] == "FEMININO").astype(int)
    candidates["is_nonwhite"] = candidates["DS_COR_RACA"].isin(
        ["PRETA", "PARDA", "AMARELA", "INDÃGENA", "INDIGENA"]
    ).astype(int)
    candidates["is_higher_education"] = candidates["DS_GRAU_INSTRUCAO"].fillna("").str.contains(
        "SUPERIOR", regex=False
    ).astype(int)
    candidates["is_married"] = (candidates["DS_ESTADO_CIVIL"] == "CASADO(A)").astype(int)
    candidates["is_elected"] = candidates["DS_SIT_TOT_TURNO"].isin(ELECTED_STATUSES).astype(int)
    candidates["title_key"] = (
        candidates["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip()
    )
    candidates["title_key"] = candidates["title_key"].replace({"-4": "", "#NULO#": ""})
    candidates["person_key"] = (
        candidates["NM_CANDIDATO"].map(normalize_text)
        + "|"
        + candidates["DT_NASCIMENTO"].dt.strftime("%Y-%m-%d").fillna("")
    )
    candidates["person_key"] = candidates["title_key"].where(
        candidates["title_key"].ne(""),
        candidates["person_key"],
    )
    # Keep one row per candidate within year and municipality, preferring the later
    # turn when second-round rows duplicate first-round records.
    candidates = candidates.sort_values(
        ["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO", "NR_TURNO"]
    )
    candidates = candidates.drop_duplicates(
        subset=["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO"],
        keep="last",
    )
    return candidates


def add_candidate_history_flags(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    candidates = candidates.copy()
    baseline = candidates[candidates["ANO_ELEICAO"] == 2020].copy()
    baseline_keys = (
        baseline.loc[baseline["person_key"].ne(""), ["SG_UF", "SG_UE", "office_group", "person_key"]]
        .drop_duplicates()
        .assign(ran_in_2020=1)
    )
    elected_keys = (
        baseline.loc[
            (baseline["person_key"].ne("")) & (baseline["is_elected"] == 1),
            ["SG_UF", "SG_UE", "office_group", "person_key"],
        ]
        .drop_duplicates()
        .assign(elected_in_2020=1)
    )

    candidates = candidates.merge(
        baseline_keys,
        on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left",
    )
    candidates = candidates.merge(
        elected_keys,
        on=["SG_UF", "SG_UE", "office_group", "person_key"],
        how="left",
    )
    candidates["ran_in_2020"] = candidates["ran_in_2020"].fillna(0).astype(int)
    candidates["elected_in_2020"] = candidates["elected_in_2020"].fillna(0).astype(int)
    candidates["is_new_candidate_vs_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["ran_in_2020"] == 0)
    ).astype(int)
    candidates["is_incumbent_from_2020"] = (
        (candidates["ANO_ELEICAO"] == 2024)
        & candidates["person_key"].ne("")
        & (candidates["elected_in_2020"] == 1)
    ).astype(int)
    candidates["is_reelected_incumbent_2024"] = (
        (candidates["is_incumbent_from_2020"] == 1) & (candidates["is_elected"] == 1)
    ).astype(int)
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
    outcomes["incumbent_reelected_share"] = (
        outcomes["incumbent_reelected_count"] / elected_denominator
    )
    outcomes["candidate_hhi_party"] = np.nan
    outcomes["effective_party_count_candidates"] = np.nan

    party_counts = (
        candidates.groupby(
            ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NR_PARTIDO"],
            as_index=False,
        )
        .agg(n_candidates=("SQ_CANDIDATO", "nunique"))
    )
    party_totals = party_counts.groupby(
        ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        as_index=False,
    )["n_candidates"].sum().rename(columns={"n_candidates": "total_candidates_tmp"})
    party_counts = party_counts.merge(
        party_totals,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
        validate="many_to_one",
    )
    party_counts["party_share"] = party_counts["n_candidates"] / party_counts["total_candidates_tmp"]
    concentration = (
        party_counts.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(
            candidate_hhi_party=("party_share", lambda s: float((s**2).sum())),
            effective_party_count_candidates=("party_share", lambda s: float(1 / (s**2).sum()) if (s**2).sum() > 0 else np.nan),
        )
    )
    outcomes = outcomes.merge(
        concentration,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_calc"),
    )
    outcomes["candidate_hhi_party"] = outcomes["candidate_hhi_party_calc"]
    outcomes["effective_party_count_candidates"] = outcomes["effective_party_count_candidates_calc"]
    outcomes = outcomes.drop(
        columns=["candidate_hhi_party_calc", "effective_party_count_candidates_calc"]
    )
    return outcomes


def build_design_for_office(
    office_group: str,
    municipality_universe: pd.DataFrame,
    judicialization_totals: pd.DataFrame,
    bartik: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    office_panel = office_outcomes[office_outcomes["office_group"] == office_group].copy()
    design = municipality_universe.merge(
        bartik[["SG_UF", "SG_UE", "NM_UE", "bartik_iv_2020_2024", "baseline_competition_lawsuits_2020", "baseline_subjects_2020"]]
        .drop_duplicates()
        .merge(judicialization_totals, on=["SG_UF", "SG_UE", "NM_UE"], how="outer"),
        on=["SG_UF", "SG_UE", "NM_UE"],
        how="left",
    )

    fill_zero_cols = [
        "bartik_iv_2020_2024",
        "baseline_competition_lawsuits_2020",
        "baseline_subjects_2020",
        "competition_families_2020",
        "competition_families_2024",
        "competition_lawsuits_2020",
        "competition_lawsuits_2024",
        "competition_subjects_2020",
        "competition_subjects_2024",
        "log1p_competition_lawsuits_2020",
        "log1p_competition_lawsuits_2024",
        "delta_log1p_competition_lawsuits_2024_2020",
    ]
    for column in fill_zero_cols:
        if column in design.columns:
            design[column] = design[column].fillna(0)

    if not office_panel.empty:
        value_cols = [
            col for col in office_panel.columns
            if col not in {"office_group", "SG_UF", "SG_UE", "NM_UE", "ANO_ELEICAO"}
        ]
        office_wide = office_panel.pivot_table(
            index=["SG_UF", "SG_UE"],
            columns="ANO_ELEICAO",
            values=value_cols,
            fill_value=0,
        )
        office_wide.columns = [f"{name}_{year}" for name, year in office_wide.columns]
        office_wide = office_wide.reset_index()
        design = design.merge(office_wide, on=["SG_UF", "SG_UE"], how="left")

    rename_map = {
        "total_candidates_2020": "total_candidates_2020",
        "total_candidates_2024": "total_candidates_2024",
    }
    design = design.rename(columns=rename_map)

    if "total_candidates_2020" in design.columns and "total_candidates_2024" in design.columns:
        design["delta_total_candidates_2024_2020"] = (
            design["total_candidates_2024"] - design["total_candidates_2020"]
        )
    if "female_share_2020" in design.columns and "female_share_2024" in design.columns:
        design["delta_female_share_2024_2020"] = (
            design["female_share_2024"] - design["female_share_2020"]
        )
    if "candidate_hhi_party_2020" in design.columns and "candidate_hhi_party_2024" in design.columns:
        design["delta_candidate_hhi_party_2024_2020"] = (
            design["candidate_hhi_party_2024"] - design["candidate_hhi_party_2020"]
        )
    if (
        "effective_party_count_candidates_2020" in design.columns
        and "effective_party_count_candidates_2024" in design.columns
    ):
        design["delta_effective_party_count_candidates_2024_2020"] = (
            design["effective_party_count_candidates_2024"]
            - design["effective_party_count_candidates_2020"]
        )
    return design


def build_municipality_universe(
    zone_lookup: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    universe = (
        zone_lookup.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(NM_UE=("NM_UE", "first"))
    )
    if not office_outcomes.empty:
        outcome_universe = (
            office_outcomes.groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first"))
        )
        universe = (
            pd.concat([universe, outcome_universe], ignore_index=True)
            .groupby(["SG_UF", "SG_UE"], as_index=False)
            .agg(NM_UE=("NM_UE", "first"))
        )
    return universe


def write_setup_note(
    executive_design: pd.DataFrame,
    legislative_design: pd.DataFrame,
    office_outcomes: pd.DataFrame,
) -> None:
    lines = [
        "# Office-Specific Shift-Share Setup",
        "",
        "This setup uses only first-instance (`NR_INSTANCIA == 1`) electoral lawsuits,",
        "which correspond to local `zonas eleitorais`, and maps them to municipalities.",
        "",
        "## Core Choices",
        "",
        "- exposure unit: municipality, aggregated from first-instance zona-eleitoral outputs",
        "- main treatment universe: competition-relevant subject codes only",
        "- primary robustness specification: exclude `11618 = RRC - Candidato`",
        "- outcome panels are separated by office sought",
        "- executive office: `PREFEITO`",
        "- legislative office: `VEREADOR`",
        "",
        "## Derived Files",
        "",
        "- `data/clean/office_candidate_outcomes_panel.csv`",
        "- `data/clean/municipality_competition_subject_panel.csv`",
        "- `data/clean/municipality_bartik_components.csv`",
        "- `data/clean/executive_shift_share_design.csv`",
        "- `data/clean/legislative_shift_share_design.csv`",
        "",
        "## Coverage",
        "",
        f"- office outcome rows: {len(office_outcomes):,}",
        f"- executive design municipalities: {len(executive_design):,}",
        f"- legislative design municipalities: {len(legislative_design):,}",
        "",
        "## Notes",
        "",
        "- `new_candidate_*` and `incumbent_*` variables are defined only relative to 2020 and",
        "  therefore are substantively meaningful for 2024 outcomes.",
        "- candidate-file-based concentration metrics (`candidate_hhi_party`,",
        "  `effective_party_count_candidates`) are useful fragmentation proxies, but not a full",
        "  ideological polarization measure.",
    ]
    (TABLES_DIR / "office_shift_share_setup.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    crosswalk = load_crosswalk()
    zone_lookup = load_zone_lookup()
    zone_subject_panel = load_zone_subject_panel(crosswalk)
    municipal_panel = build_municipality_subject_panel(zone_subject_panel, zone_lookup)
    municipality_subject, bartik_components, bartik = build_municipality_bartik_components(
        municipal_panel
    )
    judicialization_totals = build_municipality_judicialization_totals(municipal_panel)

    candidates = load_candidates()
    candidates = add_candidate_history_flags(candidates)
    office_outcomes = summarize_office_outcomes(candidates)
    municipality_universe = build_municipality_universe(zone_lookup, office_outcomes)

    executive_design = build_design_for_office(
        "executive",
        municipality_universe,
        judicialization_totals,
        bartik,
        office_outcomes,
    )
    legislative_design = build_design_for_office(
        "legislative",
        municipality_universe,
        judicialization_totals,
        bartik,
        office_outcomes,
    )

    municipality_subject.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "municipality_competition_subject_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    bartik_components.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "municipality_bartik_components.csv",
        index=False,
        encoding="utf-8-sig",
    )
    office_outcomes.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "office_candidate_outcomes_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    executive_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "executive_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    legislative_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "legislative_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )

    write_setup_note(executive_design, legislative_design, office_outcomes)
    print("Wrote office-specific shift-share inputs.")


if __name__ == "__main__":
    main()
