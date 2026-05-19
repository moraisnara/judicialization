from __future__ import annotations

from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"
TABLES_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"

EXECUTIVE_DESIGN_PATH = DERIVED_DIR / "executive_shift_share_design.csv"
LEGISLATIVE_DESIGN_PATH = DERIVED_DIR / "legislative_shift_share_design.csv"

TARGET_YEARS = [2020, 2024]
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


def load_candidate_metadata() -> pd.DataFrame:
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
        df = pd.read_csv(
            path,
            sep=";",
            encoding="latin-1",
            usecols=usecols,
            dtype=str,
            low_memory=False,
        )
        frames.append(df)
    candidates = pd.concat(frames, ignore_index=True)
    candidates = candidates.loc[
        (candidates["TP_ABRANGENCIA"] == "MUNICIPAL")
        & (candidates["CD_TIPO_ELEICAO"] == "2")
        & (candidates["DS_CARGO"].isin(OFFICE_MAP))
    ].copy()
    candidates["ANO_ELEICAO"] = pd.to_numeric(candidates["ANO_ELEICAO"], errors="coerce")
    candidates["NR_TURNO"] = pd.to_numeric(candidates["NR_TURNO"], errors="coerce")
    candidates["office_group"] = candidates["DS_CARGO"].map(OFFICE_MAP)
    candidates["DT_ELEICAO"] = pd.to_datetime(
        candidates["DT_ELEICAO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["DT_NASCIMENTO"] = pd.to_datetime(
        candidates["DT_NASCIMENTO"], format="%d/%m/%Y", errors="coerce"
    )
    candidates["candidate_age"] = (
        (candidates["DT_ELEICAO"] - candidates["DT_NASCIMENTO"]).dt.days / 365.25
    )
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
    candidates = candidates.sort_values(
        ["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO", "NR_TURNO"]
    )
    candidates = candidates.drop_duplicates(
        subset=["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO"],
        keep="last",
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
    return candidates[
        [
            "ANO_ELEICAO",
            "SG_UF",
            "SG_UE",
            "office_group",
            "SQ_CANDIDATO",
            "NR_PARTIDO",
            "is_female",
            "is_nonwhite",
            "is_higher_education",
            "is_married",
            "candidate_age",
            "is_elected",
            "is_new_candidate_vs_2020",
            "is_incumbent_from_2020",
        ]
    ]


def load_vote_rows() -> pd.DataFrame:
    usecols = [
        "ANO_ELEICAO",
        "TP_ABRANGENCIA",
        "CD_TIPO_ELEICAO",
        "SG_UF",
        "SG_UE",
        "NM_UE",
        "NR_ZONA",
        "DS_CARGO",
        "SQ_CANDIDATO",
        "QT_VOTOS_NOMINAIS",
        "QT_VOTOS_NOMINAIS_VALIDOS",
        "DS_SIT_TOT_TURNO",
        "NR_PARTIDO",
    ]
    frames: list[pd.DataFrame] = []
    for year in TARGET_YEARS:
        path = RAW_DIR / f"votacao_candidato_munzona_{year}" / f"votacao_candidato_munzona_{year}_BRASIL.csv"
        df = pd.read_csv(
            path,
            sep=";",
            encoding="latin-1",
            usecols=usecols,
            dtype=str,
            low_memory=False,
        )
        frames.append(df)
    votes = pd.concat(frames, ignore_index=True)
    votes = votes.loc[
        (votes["TP_ABRANGENCIA"] == "M")
        & (votes["CD_TIPO_ELEICAO"] == "2")
        & (votes["DS_CARGO"].str.upper().isin(OFFICE_MAP))
    ].copy()
    votes["ANO_ELEICAO"] = pd.to_numeric(votes["ANO_ELEICAO"], errors="coerce")
    votes["office_group"] = votes["DS_CARGO"].str.upper().map(OFFICE_MAP)
    votes["QT_VOTOS_NOMINAIS"] = pd.to_numeric(votes["QT_VOTOS_NOMINAIS"], errors="coerce").fillna(0)
    votes["QT_VOTOS_NOMINAIS_VALIDOS"] = pd.to_numeric(
        votes["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce"
    ).fillna(0)
    candidate_votes = (
        votes.groupby(
            ["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE", "office_group", "SQ_CANDIDATO", "NR_PARTIDO"],
            as_index=False,
        )
        .agg(
            total_nominal_votes=("QT_VOTOS_NOMINAIS", "sum"),
            total_valid_nominal_votes=("QT_VOTOS_NOMINAIS_VALIDOS", "sum"),
        )
    )
    candidate_votes["candidate_vote_total"] = candidate_votes["total_valid_nominal_votes"].where(
        candidate_votes["total_valid_nominal_votes"] > 0,
        candidate_votes["total_nominal_votes"],
    )
    return candidate_votes


def build_vote_outcomes(candidate_votes: pd.DataFrame, candidate_meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = candidate_votes.merge(
        candidate_meta,
        on=["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "SQ_CANDIDATO"],
        how="left",
        validate="many_to_one",
        suffixes=("", "_cand"),
    )
    panel["candidate_vote_total"] = panel["candidate_vote_total"].fillna(0)

    municipal_totals = (
        panel.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(total_valid_votes=("candidate_vote_total", "sum"))
    )
    panel = panel.merge(
        municipal_totals,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"],
        how="left",
        validate="many_to_one",
    )
    panel["vote_share"] = np.where(
        panel["total_valid_votes"] > 0,
        panel["candidate_vote_total"] / panel["total_valid_votes"],
        np.nan,
    )

    candidate_rank = panel.sort_values(
        ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "candidate_vote_total"],
        ascending=[True, True, True, True, False],
    )
    candidate_rank["vote_rank"] = candidate_rank.groupby(
        ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"]
    ).cumcount() + 1

    top_two = (
        candidate_rank[candidate_rank["vote_rank"] <= 2]
        .pivot_table(
            index=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"],
            columns="vote_rank",
            values="vote_share",
            aggfunc="first",
        )
        .rename(columns={1: "winner_vote_share", 2: "runnerup_vote_share"})
        .reset_index()
    )
    if "winner_vote_share" not in top_two.columns:
        top_two["winner_vote_share"] = np.nan
    if "runnerup_vote_share" not in top_two.columns:
        top_two["runnerup_vote_share"] = np.nan
    top_two["margin_top1_top2"] = (
        top_two["winner_vote_share"].fillna(0) - top_two["runnerup_vote_share"].fillna(0)
    )
    top_two["top2_vote_share"] = (
        top_two["winner_vote_share"].fillna(0) + top_two["runnerup_vote_share"].fillna(0)
    )

    municipal_outcomes = (
        panel.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            total_valid_votes=("total_valid_votes", "first"),
            n_candidates_with_votes=("SQ_CANDIDATO", "nunique"),
            vote_hhi_candidate=("vote_share", lambda s: float((s.fillna(0) ** 2).sum())),
            female_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_female"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            nonwhite_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_nonwhite"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            higher_education_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_higher_education"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            new_candidate_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_new_candidate_vs_2020"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            incumbent_candidate_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_incumbent_from_2020"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
        )
    )
    municipal_outcomes["effective_n_candidates_vote"] = np.where(
        municipal_outcomes["vote_hhi_candidate"] > 0,
        1 / municipal_outcomes["vote_hhi_candidate"],
        np.nan,
    )
    municipal_outcomes = municipal_outcomes.merge(
        top_two,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"],
        how="left",
        validate="one_to_one",
    )

    party_votes = (
        panel.groupby(
            ["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE", "NR_PARTIDO"],
            as_index=False,
        )
        .agg(party_votes=("candidate_vote_total", "sum"))
    )
    party_totals = (
        party_votes.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(total_party_votes=("party_votes", "sum"))
    )
    party_votes = party_votes.merge(
        party_totals,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
        validate="many_to_one",
    )
    party_votes["party_vote_share"] = np.where(
        party_votes["total_party_votes"] > 0,
        party_votes["party_votes"] / party_votes["total_party_votes"],
        np.nan,
    )
    party_outcomes = (
        party_votes.groupby(["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            vote_hhi_party=("party_vote_share", lambda s: float((s.fillna(0) ** 2).sum())),
        )
    )
    party_outcomes["effective_n_parties_vote"] = np.where(
        party_outcomes["vote_hhi_party"] > 0,
        1 / party_outcomes["vote_hhi_party"],
        np.nan,
    )
    municipal_outcomes = municipal_outcomes.merge(
        party_outcomes,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"],
        how="left",
        validate="one_to_one",
    )
    return panel, municipal_outcomes


def build_wide_design(base_path: Path, office_group: str, vote_outcomes: pd.DataFrame) -> pd.DataFrame:
    design = pd.read_csv(base_path, dtype={"SG_UE": str}, low_memory=False)
    office_panel = vote_outcomes[vote_outcomes["office_group"] == office_group].copy()
    value_cols = [
        col for col in office_panel.columns
        if col not in {"office_group", "SG_UF", "SG_UE", "NM_UE", "ANO_ELEICAO"}
    ]
    wide = office_panel.pivot_table(
        index=["SG_UF", "SG_UE"],
        columns="ANO_ELEICAO",
        values=value_cols,
        fill_value=0,
    )
    wide.columns = [f"{name}_{year}" for name, year in wide.columns]
    wide = wide.reset_index()
    out = design.merge(wide, on=["SG_UF", "SG_UE"], how="left")

    diff_pairs = {
        "winner_vote_share": "delta_winner_vote_share_2024_2020",
        "runnerup_vote_share": "delta_runnerup_vote_share_2024_2020",
        "margin_top1_top2": "delta_margin_top1_top2_2024_2020",
        "top2_vote_share": "delta_top2_vote_share_2024_2020",
        "vote_hhi_candidate": "delta_vote_hhi_candidate_2024_2020",
        "effective_n_candidates_vote": "delta_effective_n_candidates_vote_2024_2020",
        "female_vote_share": "delta_female_vote_share_2024_2020",
        "nonwhite_vote_share": "delta_nonwhite_vote_share_2024_2020",
        "higher_education_vote_share": "delta_higher_education_vote_share_2024_2020",
        "vote_hhi_party": "delta_vote_hhi_party_2024_2020",
        "effective_n_parties_vote": "delta_effective_n_parties_vote_2024_2020",
        "total_valid_votes": "delta_total_valid_votes_2024_2020",
    }
    for base, diff_name in diff_pairs.items():
        col_2020 = f"{base}_2020"
        col_2024 = f"{base}_2024"
        if col_2020 in out.columns and col_2024 in out.columns:
            out[diff_name] = out[col_2024] - out[col_2020]
    if "total_valid_votes_2020" in out.columns and "total_valid_votes_2024" in out.columns:
        out["delta_log_total_valid_votes_2024_2020"] = (
            np.log1p(out["total_valid_votes_2024"]) - np.log1p(out["total_valid_votes_2020"])
        )
    return out


def write_note(vote_outcomes: pd.DataFrame) -> None:
    lines = [
        "# Vote Outcomes Setup",
        "",
        "This build adds municipality-level vote outcomes by office on top of the",
        "first-instance shift-share design.",
        "",
        "## Outcome Families",
        "",
        "- winner and runner-up vote shares",
        "- victory margin",
        "- top-two concentration",
        "- candidate-vote HHI and effective number of candidates",
        "- party-vote HHI and effective number of parties",
        "- vote shares for female, nonwhite, and highly educated candidates",
        "- vote shares for new candidates and incumbents in 2024",
        "",
        f"- municipality-office-year rows in vote panel: {len(vote_outcomes):,}",
    ]
    (TABLES_DIR / "vote_outcomes_setup.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    candidate_meta = load_candidate_metadata()
    candidate_votes = load_vote_rows()
    candidate_vote_panel, vote_outcomes = build_vote_outcomes(candidate_votes, candidate_meta)

    executive_vote_design = build_wide_design(EXECUTIVE_DESIGN_PATH, "executive", vote_outcomes)
    legislative_vote_design = build_wide_design(LEGISLATIVE_DESIGN_PATH, "legislative", vote_outcomes)

    candidate_vote_panel.to_csv(
        DERIVED_DIR / "candidate_vote_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    vote_outcomes.to_csv(
        DERIVED_DIR / "office_vote_outcomes_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    executive_vote_design.to_csv(
        DERIVED_DIR / "executive_vote_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    legislative_vote_design.to_csv(
        DERIVED_DIR / "legislative_vote_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    write_note(vote_outcomes)
    print("Wrote vote-outcome design files.")


if __name__ == "__main__":
    main()
