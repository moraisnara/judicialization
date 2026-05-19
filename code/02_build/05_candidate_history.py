"""
Builds a candidate experience panel from TSE consulta_cand files (2012–2024).

For each candidate running for PREFEITO, computes at time of filing how many
times they have run before and how many times they have won.  Aggregates to
municipality × year level for use as controls (2020) and outcomes (2024).

Output: data/clean/candidate_experience_panel.csv
Columns: ANO_ELEICAO, SG_UF, SG_UE, NM_UE,
         share_first_time_candidates, mean_prior_candidacies,
         share_prior_winners, share_career_politicians
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

    # Municipal elections (CD_TIPO_ELEICAO == "2"), mayoral race, first round
    if "CD_TIPO_ELEICAO" in df.columns:
        df = df[df["CD_TIPO_ELEICAO"] == "2"].copy()
    if "NR_TURNO" in df.columns:
        df = df[df["NR_TURNO"] == "1"].copy()
    if "DS_CARGO" in df.columns:
        df = df[df["DS_CARGO"].str.upper().str.contains("PREFEITO", na=False)].copy()

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

    # One row per candidate per municipality
    df = df.drop_duplicates(subset=["ANO_ELEICAO", "SG_UF", "SG_UE", "person_key"])
    return df[["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE", "person_key", "is_elected"]]


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    print("[1] Loading candidate files 2012–2024", flush=True)
    all_frames = []
    for yr in YEARS:
        df = load_year(yr)
        if not df.empty:
            print(f"  {yr}: {len(df):,} mayoral candidates", flush=True)
            all_frames.append(df)

    if not all_frames:
        raise RuntimeError("No candidate data loaded.")

    all_cands = pd.concat(all_frames, ignore_index=True)

    print("\n[2] Computing prior candidacy counts", flush=True)
    # Sort by year so earlier records come first
    all_cands = all_cands.sort_values("ANO_ELEICAO").reset_index(drop=True)

    results = []
    for yr in YEARS:
        current = all_cands[all_cands["ANO_ELEICAO"] == yr].copy()
        prior   = all_cands[all_cands["ANO_ELEICAO"] < yr]

        prior_counts = (
            prior.groupby("person_key")
            .agg(n_prior_candidacies=("ANO_ELEICAO", "count"),
                 n_prior_wins=("is_elected", "sum"))
            .reset_index()
        )

        current = current.merge(prior_counts, on="person_key", how="left")
        current["n_prior_candidacies"] = current["n_prior_candidacies"].fillna(0).astype(int)
        current["n_prior_wins"]        = current["n_prior_wins"].fillna(0).astype(int)
        current["is_first_time"]       = (current["n_prior_candidacies"] == 0).astype(int)
        current["is_career"]           = (current["n_prior_candidacies"] >= 3).astype(int)
        results.append(current)

    all_with_history = pd.concat(results, ignore_index=True)

    print("\n[3] Aggregating to municipality × year", flush=True)
    panel = (
        all_with_history
        .groupby(["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"], as_index=False)
        .agg(
            share_first_time_candidates=("is_first_time", "mean"),
            mean_prior_candidacies=("n_prior_candidacies", "mean"),
            share_prior_winners=("n_prior_wins", lambda s: (s > 0).mean()),
            share_career_politicians=("is_career", "mean"),
            n_candidates=("person_key", "count"),
        )
    )

    out = DERIVED_DIR / "candidate_experience_panel.csv"
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(panel):,}")
    print(f"  Years: {sorted(panel['ANO_ELEICAO'].unique())}")
    for yr in YEARS:
        sub = panel[panel["ANO_ELEICAO"] == yr]
        if not sub.empty:
            print(f"  {yr}: {len(sub):,} municipalities, "
                  f"mean first-timers={sub['share_first_time_candidates'].mean():.2f}")


if __name__ == "__main__":
    main()
