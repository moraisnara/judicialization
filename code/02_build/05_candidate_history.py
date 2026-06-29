"""
Builds a candidate experience panel from TSE consulta_cand files (2012–2024).

Prior electoral experience is measured across ANY municipal office: a person's
prior candidacies/wins pool their PREFEITO and VEREADOR runs, so a long-serving
vereador who later runs for mayor is correctly counted as experienced (not a
first-timer). Aggregates are produced separately BY OFFICE SOUGHT
(office_group = executive [PREFEITO] / legislative [VEREADOR]) so each race has
its own career composition.

Note on left-censoring: "first-time" means no municipal candidacy in 2012–2024;
someone who last ran in 2008 or earlier is unavoidably labelled a first-timer.

Output: data/clean/candidate_experience_panel.csv
Columns: election_year, office_group, state, municipality_id_tse, municipality_name,
         share_first_time_candidates  — no prior municipal candidacy (any office) 2012+
         mean_prior_candidacies       — mean number of prior cycles run (any office)
         share_prior_winners          — share who previously won somewhere (any office)
         share_career_politicians     — share with 3+ prior cycles (any office)
         share_serial_challenger      — ran in same muni last cycle (any office), lost
         share_cross_cycle_returner   — has prior history but sat out last cycle
         n_candidates                 — candidates in the office × muni × year cell
         open_seat                    — executive only: 1 if the prior-cycle mayor
                                        served two consecutive terms (term-limited).
                                        NaN for legislative (no term limit).
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

YEARS = [2012, 2016, 2020, 2024]

OFFICE_MAP = {"PREFEITO": "executive", "VEREADOR": "legislative"}

ELECTED_STATUSES = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA", "ELEITO POR MEDIA",
                    "ELEITO POR MÉ DIA", "ELEITO POR ME DIA"}

USECOLS = [
    "ANO_ELEICAO",
    "SG_UF", "SG_UE", "NM_UE",
    "DS_CARGO",
    "CD_TIPO_ELEICAO",
    "NR_TURNO",
    "NR_TITULO_ELEITORAL_CANDIDATO",
    "NM_CANDIDATO",
    "DT_NASCIMENTO",
    "DS_SIT_TOT_TURNO",
]


def normalize(s: object) -> str:
    t = "" if pd.isna(s) else str(s).strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return " ".join(t.split())


def load_year(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"consulta_cand_{year}"
    files = sorted(folder.glob(f"consulta_cand_{year}_BRASIL.csv"))
    if not files:
        # Fall back to per-state files
        files = sorted(folder.glob(f"consulta_cand_{year}_*.csv"))
        files = [f for f in files if "leiame" not in f.name.lower()]
    if not files:
        print(f"  WARNING: no consulta_cand file found for {year}", flush=True)
        return pd.DataFrame()

    frames = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath, sep=";", encoding="latin-1",
                             usecols=lambda c: c in USECOLS,
                             dtype=str, low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"  WARNING: could not read {fpath.name}: {e}", flush=True)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Municipal ordinary elections (CD_TIPO_ELEICAO == "2"), first round, both
    # mayoral and council races (office tracked via office_group).
    if "CD_TIPO_ELEICAO" in df.columns:
        df = df[df["CD_TIPO_ELEICAO"] == "2"].copy()
    if "NR_TURNO" in df.columns:
        df = df[df["NR_TURNO"] == "1"].copy()
    df["office_group"] = df["DS_CARGO"].str.upper().str.strip().map(OFFICE_MAP)
    df = df[df["office_group"].notna()].copy()

    df["ANO_ELEICAO"] = year
    df["title_key"] = df["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip()
    df["title_key"] = df["title_key"].replace({"#NULO#": "", "-4": "", "-1": ""})
    df["NM_CANDIDATO_norm"] = df["NM_CANDIDATO"].map(normalize)
    df["DT_NASC_norm"] = pd.to_datetime(df.get("DT_NASCIMENTO", ""), format="%d/%m/%Y",
                                         errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df["person_key"] = df["title_key"].where(
        df["title_key"].str.len() > 3,
        df["NM_CANDIDATO_norm"] + "|" + df["DT_NASC_norm"],
    )
    df["is_elected"] = (
        df["DS_SIT_TOT_TURNO"].str.upper().str.strip().isin(ELECTED_STATUSES)
    ).astype(int)

    # One row per candidate per office per municipality. (A person contests a
    # single office in a single municipality per cycle, so person_key is unique
    # within a year across offices — preserved for any-office pooling.)
    df = df.drop_duplicates(subset=["ANO_ELEICAO", "office_group", "SG_UF", "SG_UE", "person_key"])
    df = df[["ANO_ELEICAO", "office_group", "SG_UF", "SG_UE", "NM_UE", "person_key", "is_elected"]]
    return df.rename(columns={
        "ANO_ELEICAO": "election_year",
        "SG_UF": "state",
        "SG_UE": "municipality_id_tse",
        "NM_UE": "municipality_name",
    })


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    print("[1] Loading candidate files 2012–2024 (prefeito + vereador)", flush=True)
    all_frames = []
    for yr in YEARS:
        df = load_year(yr)
        if not df.empty:
            by_office = df["office_group"].value_counts().to_dict()
            print(f"  {yr}: {len(df):,} candidates {by_office}", flush=True)
            all_frames.append(df)

    if not all_frames:
        raise RuntimeError("No candidate data loaded.")

    all_cands = pd.concat(all_frames, ignore_index=True)

    print("\n[2] Computing prior candidacy counts (pooled across municipal offices)", flush=True)
    # Sort by year so earlier records come first
    all_cands = all_cands.sort_values("election_year").reset_index(drop=True)

    results = []
    for yr in YEARS:
        current = all_cands[all_cands["election_year"] == yr].copy()
        # Prior experience pools ALL municipal offices: count distinct prior
        # cycles a person appeared in (prefeito OR vereador) and their wins.
        prior = all_cands[all_cands["election_year"] < yr]
        prior_counts = (
            prior.groupby("person_key")
            .agg(n_prior_candidacies=("election_year", "nunique"),
                 n_prior_wins=("is_elected", "sum"))
            .reset_index()
        )
        current = current.merge(prior_counts, on="person_key", how="left")
        current["n_prior_candidacies"] = current["n_prior_candidacies"].fillna(0).astype(int)
        current["n_prior_wins"]        = current["n_prior_wins"].fillna(0).astype(int)
        current["is_first_time"]       = (current["n_prior_candidacies"] == 0).astype(int)
        current["is_career"]           = (current["n_prior_candidacies"] >= 3).astype(int)
        current["is_prior_winner"]     = (current["n_prior_wins"] > 0).astype(int)
        results.append(current)

    all_with_history = pd.concat(results, ignore_index=True)

    # ------------------------------------------------------------------ #
    # [3] Open seat (EXECUTIVE only): municipality where the mayor served two
    #     consecutive terms and is term-limited in the following cycle. Vereadores
    #     are not term-limited, so open_seat is undefined for the legislative race.
    # ------------------------------------------------------------------ #
    print("\n[3] Computing open-seat flags (mayoral term limit)", flush=True)
    exec_cands = all_cands[all_cands["office_group"] == "executive"]

    open_seat_rows = []
    for yr in YEARS:
        prev_yr      = yr - 4
        prev_prev_yr = yr - 8
        munis_yr = (
            exec_cands[exec_cands["election_year"] == yr][["municipality_id_tse"]]
            .drop_duplicates()
            .copy()
        )
        if prev_yr not in YEARS or prev_prev_yr not in YEARS:
            munis_yr["open_seat"] = np.nan
        else:
            w_prev = (
                exec_cands[(exec_cands["election_year"] == prev_yr) & (exec_cands["is_elected"] == 1)]
                [["municipality_id_tse", "person_key"]]
            )
            w_prev_prev = (
                exec_cands[(exec_cands["election_year"] == prev_prev_yr) & (exec_cands["is_elected"] == 1)]
                [["municipality_id_tse", "person_key"]]
            )
            consec = w_prev.merge(w_prev_prev, on=["municipality_id_tse", "person_key"], how="inner")
            open_munis = set(consec["municipality_id_tse"])
            munis_yr["open_seat"] = munis_yr["municipality_id_tse"].isin(open_munis).astype(float)
        munis_yr["election_year"] = yr
        open_seat_rows.append(munis_yr)

    open_seat_df = pd.concat(open_seat_rows, ignore_index=True)

    # ------------------------------------------------------------------ #
    # [4] Serial challenger and cross-cycle returner flags (per candidate)
    #     Both pool across offices (same-municipality repeat candidacy).
    # ------------------------------------------------------------------ #
    flagged_results = []
    for yr in YEARS:
        current = all_with_history[all_with_history["election_year"] == yr].copy()
        prev_yr = yr - 4

        # Serial challenger: ran in same municipality in yr-4 (any office), lost
        if prev_yr in YEARS:
            prev_cycle = (
                all_cands[all_cands["election_year"] == prev_yr]
                .sort_values("is_elected")
                .drop_duplicates(subset=["municipality_id_tse", "person_key"], keep="last")
                [["municipality_id_tse", "person_key", "is_elected"]]
                .rename(columns={"is_elected": "_prev_elected"})
            )
            current = current.merge(
                prev_cycle, on=["municipality_id_tse", "person_key"], how="left"
            )
            current["is_serial_challenger"] = (
                current["_prev_elected"].notna() & (current["_prev_elected"] == 0)
            ).astype(int)
            current = current.drop(columns=["_prev_elected"])
        else:
            current["is_serial_challenger"] = 0

        # Cross-cycle returner: has any prior candidacy but did NOT run in yr-4 (anywhere)
        if prev_yr in YEARS:
            ran_prev = set(all_cands[all_cands["election_year"] == prev_yr]["person_key"].dropna())
        else:
            ran_prev = set()
        current["is_cross_cycle_returner"] = (
            (current["n_prior_candidacies"] > 0) &
            (~current["person_key"].isin(ran_prev))
        ).astype(int)

        flagged_results.append(current)

    all_with_flags = pd.concat(flagged_results, ignore_index=True)

    # ------------------------------------------------------------------ #
    # [5a] Candidate-level flag export (one row per candidate × office × year).
    #      Consumed by 03_vote_outcomes.py to build vote-weighted (intensive
    #      margin) versions of these categories.
    # ------------------------------------------------------------------ #
    flag_cols = ["election_year", "office_group", "state", "municipality_id_tse",
                 "person_key", "is_elected", "n_prior_candidacies", "n_prior_wins",
                 "is_first_time", "is_career", "is_prior_winner",
                 "is_serial_challenger", "is_cross_cycle_returner"]
    flags_out = DERIVED_DIR / "candidate_experience_flags.csv"
    all_with_flags[flag_cols].to_csv(flags_out, index=False, encoding="utf-8-sig")
    print(f"\n[5a] Saved candidate-level flags: {flags_out.relative_to(PROJECT_ROOT)} "
          f"({len(all_with_flags):,} rows)", flush=True)

    print("\n[5b] Aggregating to office × municipality × year", flush=True)
    panel = (
        all_with_flags
        .groupby(["election_year", "office_group", "state",
                  "municipality_id_tse", "municipality_name"], as_index=False)
        .agg(
            share_first_time_candidates=("is_first_time", "mean"),
            mean_prior_candidacies=("n_prior_candidacies", "mean"),
            share_prior_winners=("is_prior_winner", "mean"),
            share_career_politicians=("is_career", "mean"),
            share_serial_challenger=("is_serial_challenger", "mean"),
            share_cross_cycle_returner=("is_cross_cycle_returner", "mean"),
            n_candidates=("person_key", "count"),
        )
    )

    # open_seat attaches to the executive race only (mayoral term limit)
    panel = panel.merge(
        open_seat_df[["municipality_id_tse", "election_year", "open_seat"]],
        on=["municipality_id_tse", "election_year"],
        how="left",
    )
    panel.loc[panel["office_group"] != "executive", "open_seat"] = np.nan

    out = DERIVED_DIR / "candidate_experience_panel.csv"
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(panel):,}")
    print(f"  Years: {sorted(panel['election_year'].unique())}")
    for office in ["executive", "legislative"]:
        print(f"  -- {office} --")
        for yr in YEARS:
            sub = panel[(panel["election_year"] == yr) & (panel["office_group"] == office)]
            if not sub.empty:
                print(f"    {yr}: {len(sub):,} munis, "
                      f"first-timers={sub['share_first_time_candidates'].mean():.2f}, "
                      f"career={sub['share_career_politicians'].mean():.2f}, "
                      f"serial={sub['share_serial_challenger'].mean():.2f}, "
                      f"cross_cycle={sub['share_cross_cycle_returner'].mean():.2f}", flush=True)


if __name__ == "__main__":
    main()
