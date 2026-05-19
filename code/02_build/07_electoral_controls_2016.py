"""
Builds 2016 municipal-level electoral controls from TSE
votacao_candidato_munzona_2016 files.

Restricts to mayoral race (DS_CARGO = PREFEITO), first round.
Aggregates zones to municipality.

Output: data/clean/electoral_controls_2016.csv
Columns:
  SG_UF, SG_UE, NM_UE,
  n_candidates_2016        count of candidates with votes > 0
  top1_share_2016          winner vote share
  margin_2016              winner - runner-up vote share
  hhi_2016                 Herfindahl index of vote shares
  enp_2016                 effective number of parties = 1/hhi
  winner_party_2016        party abbreviation of winner
  winner_sq_2016           SQ_CANDIDATO of winner (for incumbency matching)
  winner_name_2016         name of winner
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

USECOLS = [
    "ANO_ELEICAO", "NR_TURNO", "SG_UF", "SG_UE", "NM_UE",
    "DS_CARGO", "SQ_CANDIDATO", "NM_CANDIDATO",
    "SG_PARTIDO",
    "QT_VOTOS_NOMINAIS",
    "DS_SIT_TOT_TURNO",
]

ELECTED_STATUSES = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA",
                    "ELEITO POR MEDIA", "ELEITO POR MÉ DIA"}


def load_2016() -> pd.DataFrame:
    folder = RAW_DIR / "votacao_candidato_munzona_2016"
    files = sorted(folder.glob("votacao_candidato_munzona_2016_*.csv"))
    files = [f for f in files if "leiame" not in f.name.lower()]
    if not files:
        raise FileNotFoundError("No 2016 vote files found.")

    frames = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath, sep=";", encoding="latin-1",
                             usecols=lambda c: c in USECOLS,
                             dtype=str, low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"  WARNING: {fpath.name}: {e}", flush=True)

    df = pd.concat(frames, ignore_index=True)

    # Mayoral race, first round
    df = df[df["NR_TURNO"] == "1"].copy()
    df = df[df["DS_CARGO"].str.upper().str.contains("PREFEITO", na=False)].copy()
    df["QT_VOTOS_NOMINAIS"] = pd.to_numeric(df["QT_VOTOS_NOMINAIS"], errors="coerce").fillna(0)
    print(f"  Raw zone×candidate rows: {len(df):,}", flush=True)
    return df


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    print("[1] Loading 2016 votacao_candidato_munzona", flush=True)
    df = load_2016()

    # Aggregate zones -> candidate totals per municipality
    cand = (
        df.groupby(["SG_UF", "SG_UE", "NM_UE", "SQ_CANDIDATO",
                    "NM_CANDIDATO", "SG_PARTIDO", "DS_SIT_TOT_TURNO"],
                   as_index=False)
        .agg(votes=("QT_VOTOS_NOMINAIS", "sum"))
    )

    # Keep candidates with votes > 0
    cand = cand[cand["votes"] > 0].copy()

    print(f"  Municipalities: {cand[['SG_UF','SG_UE']].drop_duplicates().shape[0]:,}", flush=True)

    print("\n[2] Computing municipality-level statistics", flush=True)
    results = []
    for (uf, ue, nm_ue), grp in cand.groupby(["SG_UF", "SG_UE", "NM_UE"]):
        total = grp["votes"].sum()
        if total == 0:
            continue
        grp = grp.copy()
        grp["share"] = grp["votes"] / total
        grp = grp.sort_values("votes", ascending=False).reset_index(drop=True)

        top1 = grp.iloc[0]
        n_cands = len(grp)
        top1_share = top1["share"]
        top2_share = grp.iloc[1]["share"] if n_cands > 1 else 0.0
        margin = top1_share - top2_share
        hhi = (grp["share"] ** 2).sum()
        enp = 1.0 / hhi if hhi > 0 else np.nan

        is_elected = (
            top1["DS_SIT_TOT_TURNO"].strip().upper() in ELECTED_STATUSES
            if pd.notna(top1["DS_SIT_TOT_TURNO"]) else False
        )

        results.append({
            "SG_UF": uf, "SG_UE": ue, "NM_UE": nm_ue,
            "n_candidates_2016": n_cands,
            "top1_share_2016": top1_share,
            "margin_2016": margin,
            "hhi_2016": hhi,
            "enp_2016": enp,
            "winner_party_2016": top1["SG_PARTIDO"],
            "winner_sq_2016": top1["SQ_CANDIDATO"],
            "winner_name_2016": top1["NM_CANDIDATO"],
            "winner_elected_2016": int(is_elected),
        })

    panel = pd.DataFrame(results)

    out = DERIVED_DIR / "electoral_controls_2016.csv"
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(panel):,}")
    print(f"  Mean n_candidates_2016: {panel['n_candidates_2016'].mean():.2f}")
    print(f"  Mean margin_2016:       {panel['margin_2016'].mean():.3f}")


if __name__ == "__main__":
    main()
