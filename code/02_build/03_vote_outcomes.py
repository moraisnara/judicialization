"""Municipality-level vote outcomes by office, built on the first-instance
shift-share design.

Outcome families: winner/runner-up vote shares; victory margin; top-two
concentration; candidate-vote HHI and effective number of candidates; party-vote
HHI and effective number of parties; vote shares for female, nonwhite, and
highly-educated candidates; vote shares for new candidates and incumbents
(year-relative: each cycle vs its own prior cycle); and vote-weighted
(intensive-margin) career categories (first-time, career 3+ priors, prior-winner,
serial-challenger, cross-cycle returner).

Each categorical trait has BOTH an extensive-margin candidate share (in
candidate_experience_panel.csv / office_candidate_outcomes_panel.csv) and an
intensive-margin *_vote_share here. Career and cross-cycle vote shares are
left-censored before 2024 (no 2016 baseline).

Years and the 2016 baseline: outcomes are built for 2016, 2020 and 2024 with
identical definitions, separately by office (executive = PREFEITO, legislative =
VEREADOR). 2016 is a pre-treatment outcome baseline only (lawsuits exist only for
2020/2024; 2012 vote microdata are unavailable), so the design files carry *_2016
levels (lagged controls) and pretrend_*_2020_2016 trends (placebo). Renewal/
incumbency outcomes are year-relative and so DO carry a 2016 (vs 2012) baseline;
only career and cross-cycle return stay left-censored.
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

EXECUTIVE_DESIGN_PATH = DERIVED_DIR / "executive_shift_share_design.csv"
LEGISLATIVE_DESIGN_PATH = DERIVED_DIR / "legislative_shift_share_design.csv"
# Candidate-level career/experience flags produced by 04_candidate_history.py.
# Merged onto the vote panel to build vote-weighted (intensive-margin) versions
# of the career categories, parallel to female_vote_share etc.
CAND_FLAGS_PATH = DERIVED_DIR / "candidate_experience_flags.csv"
EXPERIENCE_FLAGS = [
    "is_first_time", "is_career", "is_prior_winner",
    "is_serial_challenger", "is_cross_cycle_returner",
    # Year-relative renewal/incumbency (same seat vs each cycle's own prior
    # cycle), so 2016/2020/2024 are all comparable and a 2016 baseline exists.
    "is_new_vs_prior", "is_incumbent_from_prior",
]

# 2016 is included to build a pre-treatment outcome baseline (lagged levels and
# 2016->2020 pre-trends). Treatment (lawsuits) only exists for 2020/2024, so 2016
# never enters the endogenous variable; it is outcomes-only. 2012 vote microdata
# are absent, so 2016 is the earliest available outcome cycle. Renewal/incumbency
# composition (new-candidate / incumbent vote shares, winner-is-new) is defined
# relative to 2020 and therefore is NOT produced for 2016.
TARGET_YEARS = [2016, 2020, 2024]
RENEWAL_BASELINE_YEAR = 2020  # cycle whose candidates define "new vs prior"
STANDARD_TO_LEGACY = {
    "election_year": "ANO_ELEICAO",
    "state": "SG_UF",
    "municipality_id_tse": "SG_UE",
    "municipality_name": "NM_UE",
}
LEGACY_TO_STANDARD = {value: key for key, value in STANDARD_TO_LEGACY.items()}
LEGACY_TO_STANDARD.update({
    "SQ_CANDIDATO": "candidate_id",
    "NR_PARTIDO": "party_code",
    "NR_PARTIDO_cand": "party_code_cand",
})
OFFICE_MAP = {
    "PREFEITO": "executive",
    "VEREADOR": "legislative",
}
ELECTED_STATUSES = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÃ‰DIA", "ELEITO POR MÉDIA"}


def resolve_year_files(folder: Path, stem: str) -> list[Path]:
    """Return the CSV(s) for a TSE export. Prefer the single ``*_BRASIL.csv``
    bundle (2020/2024); fall back to per-UF state files (2016, which ships no
    national bundle for votacao_candidato_munzona)."""
    brasil = folder / f"{stem}_BRASIL.csv"
    if brasil.exists():
        return [brasil]
    files = sorted(
        f for f in folder.glob(f"{stem}_*.csv") if "leiame" not in f.name.lower()
    )
    if not files:
        raise FileNotFoundError(f"No files matching {stem}_*.csv in {folder}")
    return files


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
        folder = RAW_DIR / f"consulta_cand_{year}"
        for path in resolve_year_files(folder, f"consulta_cand_{year}"):
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
    candidates["title_key"] = candidates["title_key"].replace({"-4": "", "-1": "", "#NULO#": ""})
    # person_key must match 04_candidate_history.py exactly so the experience
    # flags merge aligns: title when it has >3 chars, else name|dob fallback.
    candidates["person_key"] = (
        candidates["NM_CANDIDATO"].map(normalize_text)
        + "|"
        + candidates["DT_NASCIMENTO"].dt.strftime("%Y-%m-%d").fillna("")
    )
    candidates["person_key"] = candidates["title_key"].where(
        candidates["title_key"].str.len() > 3,
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
    # Accent-fold before matching (see 02_shift_share_design): raw latin-1 value is
    # "INDIGENA" with an accent; the literal spelling dropped indigenous candidates.
    candidates["is_nonwhite"] = candidates["DS_COR_RACA"].map(normalize_text).isin(
        ["PRETA", "PARDA", "AMARELA", "INDIGENA"]
    ).astype(int)
    candidates["is_higher_education"] = candidates["DS_GRAU_INSTRUCAO"].fillna("").str.contains(
        "SUPERIOR", regex=False
    ).astype(int)
    candidates["is_married"] = (candidates["DS_ESTADO_CIVIL"] == "CASADO(A)").astype(int)
    candidates["is_elected"] = candidates["DS_SIT_TOT_TURNO"].isin(ELECTED_STATUSES).astype(int)

    # Renewal/incumbency (is_new_vs_prior, is_incumbent_from_prior) and the
    # career/experience flags are year-relative and history-aware; they are built
    # once in 04_candidate_history.py and merged here so the vote panel can build
    # their vote-weighted (intensive-margin) twins.
    candidates = attach_experience_flags(candidates)
    for col in ("is_new_vs_prior", "is_incumbent_from_prior"):
        if col in candidates.columns:
            candidates[col] = candidates[col].fillna(0).astype(int)

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
            *EXPERIENCE_FLAGS,
        ]
    ]


def attach_experience_flags(candidates: pd.DataFrame) -> pd.DataFrame:
    """Merge candidate-level career flags from 04_candidate_history.py onto the
    candidate metadata, keyed on (year, office, state, municipality, person)."""
    if not CAND_FLAGS_PATH.exists():
        print(
            f"  WARNING: {CAND_FLAGS_PATH.name} not found; experience vote shares "
            "will be NaN. Run 04_candidate_history.py first.",
            flush=True,
        )
        for col in EXPERIENCE_FLAGS:
            candidates[col] = np.nan
        return candidates
    flags = pd.read_csv(
        CAND_FLAGS_PATH,
        dtype={"municipality_id_tse": str, "person_key": str},
        low_memory=False,
    )
    flags = flags.rename(columns={
        "election_year": "ANO_ELEICAO",
        "state": "SG_UF",
        "municipality_id_tse": "SG_UE",
    })
    keys = ["ANO_ELEICAO", "SG_UF", "SG_UE", "office_group", "person_key"]
    flags = flags.loc[flags["person_key"].notna() & flags["person_key"].ne(""), keys + EXPERIENCE_FLAGS]
    flags = flags.drop_duplicates(subset=keys, keep="first")
    candidates["SG_UE"] = candidates["SG_UE"].astype(str)
    merged = candidates.merge(flags, on=keys, how="left", validate="many_to_one")
    matched = merged[EXPERIENCE_FLAGS[0]].notna().mean()
    print(f"  experience flags matched on {matched:.1%} of candidate-vote rows", flush=True)
    return merged


def load_vote_rows() -> pd.DataFrame:
    usecols = [
        "ANO_ELEICAO",
        "NR_TURNO",
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
        folder = RAW_DIR / f"votacao_candidato_munzona_{year}"
        for path in resolve_year_files(folder, f"votacao_candidato_munzona_{year}"):
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
        (votes["NR_TURNO"] == "1")
        & (votes["TP_ABRANGENCIA"] == "M")
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

    # Winner (rank 1) attributes — extracted before pivoting
    winner_chars = (
        candidate_rank[candidate_rank["vote_rank"] == 1]
        [["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE",
          "is_female", "is_new_vs_prior"]]
        .drop_duplicates(subset=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"])
        .rename(columns={
            "is_female": "winner_is_female",
            "is_new_vs_prior": "winner_is_new",
        })
    )

    # Runner-up (rank 2) gender, for the top-two GENDER DECOMPOSITION below.
    runnerup_chars = (
        candidate_rank[candidate_rank["vote_rank"] == 2]
        [["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE", "is_female"]]
        .drop_duplicates(subset=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"])
        .rename(columns={"is_female": "runnerup_is_female"})
    )

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
    top_two["others_vote_share"] = (1 - top_two["top2_vote_share"]).clip(lower=0)
    top_two["winner_majority"] = (top_two["winner_vote_share"].fillna(0) > 0.5).astype(int)
    top_two = top_two.merge(
        winner_chars,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
    )
    top_two = top_two.merge(
        runnerup_chars,
        on=["office_group", "ANO_ELEICAO", "SG_UF", "SG_UE"],
        how="left",
    )

    # ---- GENDER DECOMPOSITION OF THE TOP TWO -------------------------------
    # Splits the consolidation outcomes into the part accruing to female vs male
    # front-runners, so "the winner gains, the runner-up loses" can be asked as
    # "WHOSE vote share moves?".
    #
    # UNCONDITIONAL by construction: a race whose runner-up is male contributes
    # 0 -- not a missing value -- to female_runnerup_vote_share. So the female
    # and male parts sum back to the totals already used in the main results
    # (female_ + male_ == winner_vote_share / runnerup_vote_share), N is
    # identical to the layer-3 regressions, and nothing conditions on the
    # ENDOGENOUS question of which gender placed where. Conditioning instead on
    # "races where a woman was runner-up" would select on an outcome and is not
    # a causal object -- do not swap these for conditional means.
    #
    # is_female is 0/1 at source (blank DS_GENERO reads as male), so the fillna
    # below only fires where the rank row is absent entirely -- an uncontested
    # race with no runner-up -- where the vote share is 0 regardless. This
    # matches the fillna(0) convention already used for margin/top2 above.
    _w  = top_two["winner_vote_share"].fillna(0)
    _r  = top_two["runnerup_vote_share"].fillna(0)
    _wf = top_two["winner_is_female"].fillna(0)
    _rf = top_two["runnerup_is_female"].fillna(0)
    top_two["female_winner_vote_share"]   = _w * _wf
    top_two["male_winner_vote_share"]     = _w * (1 - _wf)
    top_two["female_runnerup_vote_share"] = _r * _rf
    top_two["male_runnerup_vote_share"]   = _r * (1 - _rf)
    # Votes to female candidates within the top-two bloc, as a share of all
    # valid votes (female_winner + female_runnerup).
    top_two["female_top2_vote_share"] = _w * _wf + _r * _rf
    # Gender gap in the top two: female minus male top-two vote share. Negative
    # everywhere on average; the question is whether the shock widens it.
    top_two["female_male_top2_gap"] = (
        top_two["female_top2_vote_share"]
        - (_w * (1 - _wf) + _r * (1 - _rf))
    )
    # Slot-specific gender gaps. These carry the DIFFERENTIAL test the frame needs:
    # the consolidation moves vote from the runner-up slot to the winner slot, and
    # the question is whether that transfer is gender-neutral. Regressing the female
    # and male columns separately and comparing their significance is the classic
    # "difference in significance is not significance of the difference" error, so
    # each gap is estimated as its OWN outcome and its p-value is the real test.
    top_two["female_male_winner_gap"]   = _w * _wf - _w * (1 - _wf)
    top_two["female_male_runnerup_gap"] = _r * _rf - _r * (1 - _rf)

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
                s[panel.loc[s.index, "is_new_vs_prior"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            incumbent_candidate_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_incumbent_from_prior"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            # Vote-weighted (intensive-margin) career categories
            first_time_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_first_time"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            career_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_career"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            prior_winner_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_prior_winner"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            serial_challenger_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_serial_challenger"] == 1].sum() / s.sum()
            ) if s.sum() > 0 else np.nan),
            cross_cycle_returner_vote_share=("candidate_vote_total", lambda s: float(
                s[panel.loc[s.index, "is_cross_cycle_returner"] == 1].sum() / s.sum()
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
    design = pd.read_csv(base_path, dtype={"municipality_id_tse": str}, low_memory=False)
    design = design.rename(columns=STANDARD_TO_LEGACY)
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
    # Renewal/incumbency are now YEAR-RELATIVE (new/incumbent vs each cycle's own
    # prior cycle), so 2016 (vs 2012) is a valid baseline and is KEPT. What stays
    # genuinely left-censored at 2016: career (needs 3+ prior cycles, i.e. 2008 +
    # 2004) and cross-cycle return (needs a prior BEFORE the skipped cycle); both
    # are ~0 in 2016 by construction, so their 2016 slot is still dropped.
    invalid_2016 = [
        "career_vote_share_2016",
        "cross_cycle_returner_vote_share_2016",
    ]
    wide = wide.drop(columns=[c for c in invalid_2016 if c in wide.columns])
    out = design.merge(wide, on=["SG_UF", "SG_UE"], how="left")

    diff_pairs = {
        # Concentration / margin
        "winner_vote_share": "delta_winner_vote_share_2024_2020",
        "runnerup_vote_share": "delta_runnerup_vote_share_2024_2020",
        "margin_top1_top2": "delta_margin_top1_top2_2024_2020",
        "top2_vote_share": "delta_top2_vote_share_2024_2020",
        "others_vote_share": "delta_others_vote_share_2024_2020",
        "winner_majority": "delta_winner_majority_2024_2020",
        "vote_hhi_candidate": "delta_vote_hhi_candidate_2024_2020",
        "effective_n_candidates_vote": "delta_effective_n_candidates_vote_2024_2020",
        "vote_hhi_party": "delta_vote_hhi_party_2024_2020",
        "effective_n_parties_vote": "delta_effective_n_parties_vote_2024_2020",
        # Vote-weighted composition
        "female_vote_share": "delta_female_vote_share_2024_2020",
        "nonwhite_vote_share": "delta_nonwhite_vote_share_2024_2020",
        "higher_education_vote_share": "delta_higher_education_vote_share_2024_2020",
        "new_candidate_vote_share": "delta_new_candidate_vote_share_2024_2020",
        "incumbent_candidate_vote_share": "delta_incumbent_candidate_vote_share_2024_2020",
        # Vote-weighted career categories (intensive margin)
        "first_time_vote_share": "delta_first_time_vote_share_2024_2020",
        "career_vote_share": "delta_career_vote_share_2024_2020",
        "prior_winner_vote_share": "delta_prior_winner_vote_share_2024_2020",
        "serial_challenger_vote_share": "delta_serial_challenger_vote_share_2024_2020",
        "cross_cycle_returner_vote_share": "delta_cross_cycle_returner_vote_share_2024_2020",
        # Winner identity
        "winner_is_female": "delta_winner_is_female_2024_2020",
        "winner_is_new": "delta_winner_is_new_2024_2020",
        # Gender decomposition of the top two
        "runnerup_is_female": "delta_runnerup_is_female_2024_2020",
        "female_winner_vote_share": "delta_female_winner_vote_share_2024_2020",
        "male_winner_vote_share": "delta_male_winner_vote_share_2024_2020",
        "female_runnerup_vote_share": "delta_female_runnerup_vote_share_2024_2020",
        "male_runnerup_vote_share": "delta_male_runnerup_vote_share_2024_2020",
        "female_top2_vote_share": "delta_female_top2_vote_share_2024_2020",
        "female_male_top2_gap": "delta_female_male_top2_gap_2024_2020",
        "female_male_winner_gap": "delta_female_male_winner_gap_2024_2020",
        "female_male_runnerup_gap": "delta_female_male_runnerup_gap_2024_2020",
        # Electorate size
        "total_valid_votes": "delta_total_valid_votes_2024_2020",
    }
    for base, diff_name in diff_pairs.items():
        col_2020 = f"{base}_2020"
        col_2024 = f"{base}_2024"
        if col_2020 in out.columns and col_2024 in out.columns:
            out[diff_name] = out[col_2024] - out[col_2020]

    # Pre-treatment trend (2020 - 2016) for the outcomes that are defined
    # identically in 2016. Used as a placebo (reduced form should be flat
    # pre-2020) and to absorb pre-existing convergence. Year-relative
    # renewal/incumbency now qualify (each cycle vs its own prior cycle, so 2016
    # is defined vs 2012). The 2016 *levels* (e.g. winner_vote_share_2016) flow
    # through the pivot above and serve as lagged controls.
    pretrend_bases = [
        "winner_vote_share", "runnerup_vote_share", "margin_top1_top2",
        "top2_vote_share", "others_vote_share", "winner_majority",
        "vote_hhi_candidate", "effective_n_candidates_vote",
        "vote_hhi_party", "effective_n_parties_vote",
        "female_vote_share", "nonwhite_vote_share", "higher_education_vote_share",
        "winner_is_female", "total_valid_votes",
        # Gender decomposition of the top two — all defined identically in 2016
        # (gender and vote rank are observed every cycle), so each carries a
        # clean 2016 baseline for the ANCOVA and a pre-trend placebo.
        "runnerup_is_female",
        "female_winner_vote_share", "male_winner_vote_share",
        "female_runnerup_vote_share", "male_runnerup_vote_share",
        "female_top2_vote_share", "female_male_top2_gap",
        "female_male_winner_gap", "female_male_runnerup_gap",
        # Year-relative renewal/incumbency now have a valid 2016 (vs 2012) baseline.
        "new_candidate_vote_share", "incumbent_candidate_vote_share", "winner_is_new",
        # Career categories well-defined in 2016 (2012 is an available prior cycle).
        # career_vote_share and cross_cycle_returner_vote_share are excluded: both
        # are mechanically ~0 in 2016 given the 2012 left-censor (no pre-trend).
        "first_time_vote_share", "prior_winner_vote_share", "serial_challenger_vote_share",
    ]
    for base in pretrend_bases:
        col_2016 = f"{base}_2016"
        col_2020 = f"{base}_2020"
        if col_2016 in out.columns and col_2020 in out.columns:
            out[f"pretrend_{base}_2020_2016"] = out[col_2020] - out[col_2016]
    if "n_candidates_with_votes_2016" in out.columns and "n_candidates_with_votes_2020" in out.columns:
        out["pretrend_log1p_n_candidates_with_votes_2020_2016"] = (
            np.log1p(out["n_candidates_with_votes_2020"])
            - np.log1p(out["n_candidates_with_votes_2016"])
        )
    if "total_valid_votes_2020" in out.columns and "total_valid_votes_2024" in out.columns:
        out["delta_log_total_valid_votes_2024_2020"] = (
            np.log1p(out["total_valid_votes_2024"]) - np.log1p(out["total_valid_votes_2020"])
        )
    if "n_candidates_with_votes_2020" in out.columns and "n_candidates_with_votes_2024" in out.columns:
        out["delta_log1p_n_candidates_with_votes_2024_2020"] = (
            np.log1p(out["n_candidates_with_votes_2024"])
            - np.log1p(out["n_candidates_with_votes_2020"])
        )
    return out


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    candidate_meta = load_candidate_metadata()
    candidate_votes = load_vote_rows()
    candidate_vote_panel, vote_outcomes = build_vote_outcomes(candidate_votes, candidate_meta)

    executive_vote_design = build_wide_design(EXECUTIVE_DESIGN_PATH, "executive", vote_outcomes)
    legislative_vote_design = build_wide_design(LEGISLATIVE_DESIGN_PATH, "legislative", vote_outcomes)

    candidate_vote_panel.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "candidate_vote_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    vote_outcomes.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "office_vote_outcomes_panel.csv",
        index=False,
        encoding="utf-8-sig",
    )
    executive_vote_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "executive_vote_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    legislative_vote_design.rename(columns=LEGACY_TO_STANDARD).to_csv(
        DERIVED_DIR / "legislative_vote_shift_share_design.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print("Wrote vote-outcome design files.")


if __name__ == "__main__":
    main()
