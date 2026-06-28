"""
Builds municipality-level turnout DISAGGREGATED by voter characteristics from
the TSE 'perfil_comparecimento_abstencao' files (2020, 2024).

Why this exists: the aggregate electoral-admin build (05_electoral_admin.py)
gives one turnout rate per municipality. Under Brazil's compulsory-voting rule
that rate is structurally floored, so an aggregate turnout null is nearly
mechanical. This file lets us look at the ELASTIC margins:

  * FACULTATIVE voters (16-17, 70+, and illiterates) -- they choose to show up,
    so this is where an engagement effect of judicialization would surface.
    TSE flags this directly via QT_COMPAREC_FACULTATIVO / _OBRIGATORIO (better
    than an age-band cut, which would miss illiterate facultative voters).
  * Turnout by EDUCATION  -- tests the 'confusion depresses low-education
    turnout' noise mechanism.
  * Turnout by SEX, AGE BAND, RACE -- differential mobilization.

Restricts to first round (NR_TURNO == 1) to match the mayoral-race panel.
This product has NO blank/null breakdown, so spoilage stays aggregate-only.

Denominators: each cell row carries QT_APTOS / QT_COMPARECIMENTO. For the
compulsory/facultative split, aptos is implied = comparecimento + abstencao
(there is no separate QT_APTOS_FACULTATIVO column).

Output: data/clean/comparecimento_disaggregated.csv  (long/tidy)
  election_year, municipality_id_tse, dimension, category,
  aptos, comparecimento, turnout_rate
where dimension in {overall, compulsory_status, sex, education, age_band, race}.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

YEARS = [2020, 2024]

# columns we read (cell keys + counts)
USECOLS = [
    "ANO_ELEICAO", "NR_TURNO", "SG_UF", "CD_MUNICIPIO",
    "DS_GENERO", "DS_FAIXA_ETARIA", "DS_GRAU_ESCOLARIDADE", "DS_COR_RACA",
    "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCAO",
    "QT_COMPAREC_FACULTATIVO", "QT_ABST_FACULTATIVO",
    "QT_COMPAREC_OBRIGATORIO", "QT_ABST_OBRIGATORIO",
]
COUNTS = [c for c in USECOLS if c.startswith("QT_")]

# dimension -> source column (overall + compulsory_status handled specially)
CELL_DIMS = {
    "sex": "DS_GENERO",
    "education": "DS_GRAU_ESCOLARIDADE",
    "age_band": "DS_FAIXA_ETARIA",
    "race": "DS_COR_RACA",
}


def load_year(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"perfil_comparecimento_abstencao_{year}"
    files = [f for f in sorted(folder.glob(f"*_{year}_*.csv"))
             if "BRASIL" not in f.name]
    frames = []
    for fpath in files:
        df = pd.read_csv(fpath, sep=";", encoding="latin-1",
                         usecols=lambda c: c in USECOLS, dtype=str,
                         low_memory=False)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df[df["NR_TURNO"] == "1"].copy()
    for c in COUNTS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["municipality_id_tse"] = (
        pd.to_numeric(df["CD_MUNICIPIO"], errors="coerce")
        .astype("Int64").astype(str).str.zfill(5))
    df["election_year"] = year
    print(f"  {year}: {len(df):,} cell-rows ({len(files)} UF files)", flush=True)
    return df


def tidy_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    keys = ["election_year", "municipality_id_tse"]

    # overall
    g = df.groupby(keys, as_index=False)[["QT_APTOS", "QT_COMPARECIMENTO"]].sum()
    g["dimension"] = "overall"
    g["category"] = "all"
    out.append(g.rename(columns={"QT_APTOS": "aptos",
                                 "QT_COMPARECIMENTO": "comparecimento"}))

    # compulsory vs facultative (aptos implied = comparec + abst)
    comp = df.groupby(keys, as_index=False)[
        ["QT_COMPAREC_OBRIGATORIO", "QT_ABST_OBRIGATORIO",
         "QT_COMPAREC_FACULTATIVO", "QT_ABST_FACULTATIVO"]].sum()
    for cat, cc, ac in [("compulsory", "QT_COMPAREC_OBRIGATORIO", "QT_ABST_OBRIGATORIO"),
                        ("facultative", "QT_COMPAREC_FACULTATIVO", "QT_ABST_FACULTATIVO")]:
        sub = comp[keys].copy()
        sub["comparecimento"] = comp[cc]
        sub["aptos"] = comp[cc] + comp[ac]
        sub["dimension"] = "compulsory_status"
        sub["category"] = cat
        out.append(sub)

    # cell dimensions
    for dim, col in CELL_DIMS.items():
        g = df.groupby(keys + [col], as_index=False)[
            ["QT_APTOS", "QT_COMPARECIMENTO"]].sum()
        g = g.rename(columns={col: "category", "QT_APTOS": "aptos",
                              "QT_COMPARECIMENTO": "comparecimento"})
        g["dimension"] = dim
        out.append(g)

    res = pd.concat(out, ignore_index=True)
    res = res[res["aptos"] > 0].copy()
    res["turnout_rate"] = res["comparecimento"] / res["aptos"]
    return res[["election_year", "municipality_id_tse", "dimension",
                "category", "aptos", "comparecimento", "turnout_rate"]]


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    parts = []
    for year in YEARS:
        parts.append(tidy_rows(load_year(year)))
    res = pd.concat(parts, ignore_index=True)
    out = CLEAN_DIR / "comparecimento_disaggregated.csv"
    res.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}  ({len(res):,} rows)")

    # quick national turnout by dimension (aptos-weighted)
    for yr in YEARS:
        print(f"\n=== {yr} national turnout (aptos-weighted) ===")
        sub = res[res["election_year"] == yr]
        for dim in ["compulsory_status", "sex", "education", "race"]:
            d = sub[sub["dimension"] == dim]
            agg = (d.groupby("category")[["comparecimento", "aptos"]].sum())
            agg["turnout"] = agg["comparecimento"] / agg["aptos"]
            print(f"  [{dim}]")
            for cat, row in agg.iterrows():
                print(f"    {str(cat)[:34]:34s} {row['turnout']*100:5.1f}%  "
                      f"(aptos {int(row['aptos']):,})")


if __name__ == "__main__":
    main()
