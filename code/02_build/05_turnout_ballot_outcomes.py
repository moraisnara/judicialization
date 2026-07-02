"""
Builds municipality-level electoral administration outcomes from TSE
detalhe_votacao_munzona files for 2020 and 2024.

Keeps BOTH municipal ballots, first round (NR_TURNO = 1):
  * PREFEITO  (mayoral)  -> the base ballot-composition columns
  * VEREADOR  (council)  -> the same columns with a `_vereador` suffix
Aggregates zones to municipality, then computes rates per office.

Turnout and abstention are OFFICE-INVARIANT: a voter shows up once and receives
both ballots, so QT_APTOS / QT_COMPARECIMENTO are identical across cargos within a
municipality-zone for ~98-99% of municipalities. They are reported once (from the
mayoral rows, unchanged from the prior build). The remaining ~1-2% tail with a
nonzero gap is driven by QT_APTOS mismatches in municipalities with supplementary
or annulled mayoral races (the mayoral electorate is re-snapshotted); the printed
consistency check reports how many municipalities exceed a 1pp gap. Only ballot
composition (blank, null, valid) differs by office and is split.

Output: data/clean/electoral_admin_outcomes.csv
Columns:
  election_year, state, municipality_id_tse, municipality_name,
  registered_voters, turnout_count, abstentions_count,
  turnout_rate, abstention_rate,                         (office-invariant)
  blank_votes, null_votes, valid_votes, total_votes,     (mayoral / prefeito)
  blank_rate, null_rate, valid_vote_rate,                (mayoral / prefeito)
  blank_votes_vereador, null_votes_vereador, valid_votes_vereador,
  blank_rate_vereador, null_rate_vereador, valid_vote_rate_vereador  (council)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

YEARS = [2016, 2020, 2024]

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
    # exclude the BRASIL aggregate file — state files already cover all municipalities
    files = [f for f in files if "leiame" not in f.name.lower()
             and "BRASIL" not in f.name]
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

    # First round only; keep both municipal ballots (mayoral + council).
    df = df[df["NR_TURNO"] == "1"].copy()
    cargo = df["DS_CARGO"].str.upper().str.strip()
    # Exact match so VICE-PREFEITO (no separate ballot) is not swept into PREFEITO.
    df = df[cargo.isin(["PREFEITO", "VEREADOR"])].copy()
    df["cargo"] = cargo[cargo.isin(["PREFEITO", "VEREADOR"])].values

    for col in COUNT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    n_pref = int((df["cargo"] == "PREFEITO").sum())
    n_ver  = int((df["cargo"] == "VEREADOR").sum())
    print(f"  {year}: {n_pref:,} mayoral + {n_ver:,} council zone-rows (round 1)",
          flush=True)
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

    # Aggregate zones -> municipality, separately per office.
    group_cols = ["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE", "cargo"]
    agg = (
        all_data
        .groupby(group_cols, as_index=False)[COUNT_COLS]
        .sum()
    )

    # Per-office ballot composition. All rates use registered voters (QT_APTOS)
    # as the denominator, so they are unconditional probabilities over the
    # eligible electorate (turnout + null + blank + abstention ~= 1).
    aptos = agg["QT_APTOS"].replace(0, float("nan"))
    agg["turnout_rate"]    = agg["QT_COMPARECIMENTO"]    / aptos
    agg["abstention_rate"] = agg["QT_ABSTENCOES"]        / aptos
    agg["null_rate"]       = agg["QT_TOTAL_VOTOS_NULOS"] / aptos
    agg["blank_rate"]      = agg["QT_VOTOS_BRANCOS"]     / aptos
    agg["valid_votes"]     = (agg["QT_VOTOS"] - agg["QT_VOTOS_BRANCOS"]
                              - agg["QT_TOTAL_VOTOS_NULOS"])
    agg["valid_vote_rate"] = agg["valid_votes"]          / aptos

    key = ["ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE"]
    pref = agg[agg["cargo"] == "PREFEITO"].copy()
    ver  = agg[agg["cargo"] == "VEREADOR"].copy()

    # --- Mayoral (prefeito): the base columns (unchanged from the prior build) ---
    mun = pref.rename(columns={
        "QT_APTOS": "registered_voters",
        "QT_COMPARECIMENTO": "turnout_count",
        "QT_ABSTENCOES": "abstentions_count",
        "QT_VOTOS": "total_votes",
        "QT_VOTOS_BRANCOS": "blank_votes",
        "QT_TOTAL_VOTOS_NULOS": "null_votes",
    }).drop(columns=["cargo"])

    # --- Council (vereador): ballot composition only, suffixed ---
    ver_cols = ["blank_votes_vereador", "null_votes_vereador", "valid_votes_vereador",
                "blank_rate_vereador", "null_rate_vereador", "valid_vote_rate_vereador"]
    ver = ver.rename(columns={
        "QT_VOTOS_BRANCOS": "blank_votes_vereador",
        "QT_TOTAL_VOTOS_NULOS": "null_votes_vereador",
        "valid_votes": "valid_votes_vereador",
        "blank_rate": "blank_rate_vereador",
        "null_rate": "null_rate_vereador",
        "valid_vote_rate": "valid_vote_rate_vereador",
    })[key + ver_cols]

    # Consistency check: turnout/abstention must match across offices (same
    # electorate). Compare the council turnout against the mayoral turnout.
    ver_turnout = agg[agg["cargo"] == "VEREADOR"][key + ["turnout_rate"]].rename(
        columns={"turnout_rate": "turnout_rate_ver"})
    chk = mun[key + ["turnout_rate"]].merge(ver_turnout, on=key, how="inner")
    gap = (chk["turnout_rate"] - chk["turnout_rate_ver"]).abs()
    n_gap = int((gap > 0.01).sum())
    print(f"  Office-invariance check: {n_gap}/{len(chk)} munis with "
          f"|turnout_pref - turnout_ver| > 1pp (supplementary/annulled races); "
          f"max = {gap.max():.2e}")

    mun = mun.merge(ver, on=key, how="left")

    mun = mun.rename(columns={
        "ANO_ELEICAO": "election_year",
        "SG_UF": "state",
        "SG_UE": "municipality_id_tse",
        "NM_UE": "municipality_name",
    })

    out = DERIVED_DIR / "electoral_admin_outcomes.csv"
    mun.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(mun):,}")
    for yr in YEARS:
        sub = mun[mun["election_year"] == str(yr)]
        if sub.empty:
            sub = mun[mun["election_year"] == yr]
        if not sub.empty:
            print(f"  {yr}: {len(sub):,} municipalities, "
                  f"turnout={sub['turnout_rate'].mean():.3f}, "
                  f"null(pref)={sub['null_rate'].mean():.3f}, "
                  f"null(ver)={sub['null_rate_vereador'].mean():.3f}, "
                  f"blank(pref)={sub['blank_rate'].mean():.3f}, "
                  f"blank(ver)={sub['blank_rate_vereador'].mean():.3f}")


if __name__ == "__main__":
    main()
