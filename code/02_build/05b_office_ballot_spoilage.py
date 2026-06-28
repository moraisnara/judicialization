"""
Per-office ballot spoilage (blank / null) for mayor vs council.

Voters attend the election once (a single comparecimento), so TURNOUT is not
office-specific. But BLANK and NULL votes ARE cast separately for each office on
the same ballot: a voter present can cast a valid mayoral vote and a blank/null
council vote, or vice versa. Comparing spoilage across the two contests within
the same municipality isolates CONTEST-SPECIFIC disengagement -- whether the
litigated race draws more protest/abstention-on-the-ballot than the other race
the same voters faced -- and differences out municipality-wide turnout shocks.

Source: TSE detalhe_votacao_munzona (same files as 05_electoral_admin.py, which
keeps only PREFEITO). Here we keep BOTH prefeito and vereador, first round.

Denominator: votes cast for that office (QT_VOTOS), matching the votes-cast
shares used in 03_voter_behavior_iv.R.

Output: data/clean/office_ballot_spoilage.csv
  Wide by municipality, one row per municipality:
    {office}_null_share_cast_{year}, {office}_blank_share_cast_{year}
    delta_{office}_null_share_cast_2024_2020, ...blank...
    rolloff_null_share_cast_{year}   = vereador - prefeito (within-year gap)
    rolloff_blank_share_cast_{year}
    delta_rolloff_null_share_cast_2024_2020, ...blank...
  office in {prefeito, vereador}.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
YEARS = [2020, 2024]

USECOLS = [
    "ANO_ELEICAO", "NR_TURNO", "SG_UF", "SG_UE", "NM_UE", "DS_CARGO",
    "QT_VOTOS", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS",
]
COUNT_COLS = ["QT_VOTOS", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS"]
OFFICES = {"PREFEITO": "prefeito", "VEREADOR": "vereador"}


def load_year(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"detalhe_votacao_munzona_{year}"
    files = sorted(folder.glob(f"detalhe_votacao_munzona_{year}_*.csv"))
    files = [f for f in files if "leiame" not in f.name.lower()
             and "BRASIL" not in f.name]
    if not files:
        print(f"  WARNING: no files for {year}", flush=True)
        return pd.DataFrame()
    frames = []
    for fpath in files:
        try:
            frames.append(pd.read_csv(
                fpath, sep=";", encoding="latin-1",
                usecols=lambda c: c in USECOLS, dtype=str, low_memory=False))
        except Exception as e:
            print(f"  WARNING: {fpath.name}: {e}", flush=True)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = df[df["NR_TURNO"] == "1"].copy()
    up = df["DS_CARGO"].str.upper()
    df["office"] = None
    for raw, short in OFFICES.items():
        df.loc[up.str.contains(raw, na=False), "office"] = short
    df = df[df["office"].notna()].copy()
    for col in COUNT_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    print(f"  {year}: {len(df):,} zone-rows (prefeito + vereador, round 1)", flush=True)
    return df


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    frames = [load_year(y) for y in YEARS]
    frames = [f for f in frames if not f.empty]
    if not frames:
        raise RuntimeError("No spoilage data loaded.")
    data = pd.concat(frames, ignore_index=True)

    # zones -> municipality x year x office
    g = (data.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE", "office"], as_index=False)
              [COUNT_COLS].sum())
    cast = g["QT_VOTOS"].replace(0, float("nan"))
    g["null_share_cast"]    = g["QT_TOTAL_VOTOS_NULOS"] / cast
    g["blank_share_cast"]   = g["QT_VOTOS_BRANCOS"]     / cast
    g["invalid_share_cast"] = (g["QT_TOTAL_VOTOS_NULOS"] + g["QT_VOTOS_BRANCOS"]) / cast
    g = g.rename(columns={"SG_UF": "state", "SG_UE": "municipality_id_tse",
                          "ANO_ELEICAO": "election_year"})
    g["municipality_id_tse"] = g["municipality_id_tse"].astype(str).str.zfill(5)
    g["election_year"] = pd.to_numeric(g["election_year"], errors="coerce")

    # pivot to wide: {office}_{measure}_{year}
    measures = ["null_share_cast", "blank_share_cast", "invalid_share_cast"]
    wide = g.pivot_table(index="municipality_id_tse", columns=["office", "election_year"],
                         values=measures)
    wide.columns = [f"{off}_{meas}_{int(yr)}" for meas, off, yr in wide.columns]
    wide = wide.reset_index()

    # within-municipality deltas per office, and the roll-off gap (vereador - prefeito)
    for off in OFFICES.values():
        for meas in measures:
            c20, c24 = f"{off}_{meas}_2020", f"{off}_{meas}_2024"
            if c20 in wide.columns and c24 in wide.columns:
                wide[f"delta_{off}_{meas}_2024_2020"] = wide[c24] - wide[c20]
    for meas in measures:
        for yr in YEARS:
            pv, vv = f"prefeito_{meas}_{yr}", f"vereador_{meas}_{yr}"
            if pv in wide.columns and vv in wide.columns:
                wide[f"rolloff_{meas}_{yr}"] = wide[vv] - wide[pv]
        r20, r24 = f"rolloff_{meas}_2020", f"rolloff_{meas}_2024"
        if r20 in wide.columns and r24 in wide.columns:
            wide[f"delta_rolloff_{meas}_2024_2020"] = wide[r24] - wide[r20]

    out = CLEAN_DIR / "office_ballot_spoilage.csv"
    wide.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}  ({len(wide):,} municipalities, {len(wide.columns)} cols)")
    for meas in measures:
        for off in OFFICES.values():
            c = f"{off}_{meas}_2024"
            if c in wide.columns:
                print(f"  mean {c} = {wide[c].mean():.4f}")
        rc = f"rolloff_{meas}_2024"
        if rc in wide.columns:
            print(f"  mean {rc} (vereador-prefeito, 2024) = {wide[rc].mean():.4f}")


if __name__ == "__main__":
    main()
