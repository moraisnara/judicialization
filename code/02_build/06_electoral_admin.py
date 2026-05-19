"""
Builds municipality-level electoral administration outcomes from TSE
detalhe_votacao_munzona files for 2020 and 2024.

Restricts to mayoral race (DS_CARGO = PREFEITO), first round (NR_TURNO = 1).
Aggregates zones to municipality, then computes rates.

Output: data/clean/electoral_admin_outcomes.csv
Columns:
  ANO_ELEICAO, SG_UF, SG_UE, NM_UE,
  qt_aptos, qt_comparecimento, qt_abstencoes,
  qt_votos, qt_votos_brancos, qt_total_votos_nulos,
  turnout_rate, abstention_rate, blank_share, null_share
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

YEARS = [2020, 2024]

USECOLS = [
    "ANO_ELEICAO", "NR_TURNO", "SG_UF", "SG_UE", "NM_UE",
    "DS_CARGO",
    "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
    "QT_VOTOS", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS",
]

COUNT_COLS = [
    "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
    "QT_VOTOS", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS",
]


def load_year(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"detalhe_votacao_munzona_{year}"
    files = sorted(folder.glob(f"detalhe_votacao_munzona_{year}_*.csv"))
    files = [f for f in files if "leiame" not in f.name.lower()]
    if not files:
        print(f"  WARNING: no files found for {year}", flush=True)
        return pd.DataFrame()

    frames = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath, sep=";", encoding="latin-1",
                             usecols=lambda c: c in USECOLS,
                             dtype=str, low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"  WARNING: {fpath.name}: {e}", flush=True)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Restrict to mayoral race, first round
    df = df[df["NR_TURNO"] == "1"].copy()
    df = df[df["DS_CARGO"].str.upper().str.contains("PREFEITO", na=False)].copy()

    for col in COUNT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    print(f"  {year}: {len(df):,} zone-rows for mayoral first round", flush=True)
    return df


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    for year in YEARS:
        df = load_year(year)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("No electoral admin data loaded.")

    all_data = pd.concat(frames, ignore_index=True)

    # Aggregate zones -> municipality
    group_cols = ["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"]
    mun = (
        all_data
        .groupby(group_cols, as_index=False)[COUNT_COLS]
        .sum()
    )

    # Compute rates
    mun["turnout_rate"]    = mun["QT_COMPARECIMENTO"] / mun["QT_APTOS"].replace(0, float("nan"))
    mun["abstention_rate"] = mun["QT_ABSTENCOES"]     / mun["QT_APTOS"].replace(0, float("nan"))
    mun["blank_share"]     = mun["QT_VOTOS_BRANCOS"]  / mun["QT_VOTOS"].replace(0, float("nan"))
    mun["null_share"]      = mun["QT_TOTAL_VOTOS_NULOS"] / mun["QT_VOTOS"].replace(0, float("nan"))

    # Rename count columns to lower case for cleanliness
    mun = mun.rename(columns={c: c.lower() for c in COUNT_COLS})

    out = DERIVED_DIR / "electoral_admin_outcomes.csv"
    mun.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(mun):,}")
    for yr in YEARS:
        sub = mun[mun["ANO_ELEICAO"] == str(yr)]
        if sub.empty:
            sub = mun[mun["ANO_ELEICAO"] == yr]
        if not sub.empty:
            print(f"  {yr}: {len(sub):,} municipalities, "
                  f"mean turnout={sub['turnout_rate'].mean():.3f}, "
                  f"mean null_share={sub['null_share'].mean():.3f}")


if __name__ == "__main__":
    main()
