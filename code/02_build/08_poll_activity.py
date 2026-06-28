"""
Builds municipality-level registered-poll activity from TSE
pesquisa_eleitoral files for 2020 and 2024.

The TSE poll registry is metadata only (one row per registered poll): firm,
office, municipality, fieldwork dates, sample size, cost and methodology. It
carries NO vote-intention results. We therefore summarise poll *activity /
intensity* per municipality, which proxies the local information environment.

Restricts to mayoral races (DS_CARGO contains "Prefeito"). One row per
registered poll, deduplicated on NR_PROTOCOLO_REGISTRO. Aggregates to
municipality x cycle, then pivots wide with 2020/2024 columns and deltas.

Outputs:
  data/clean/poll_activity_panel.csv   municipality x year (long)
  data/clean/poll_activity_design.csv  municipality (wide, *_2020/*_2024/delta_*)

Wide columns (per cycle suffix):
  n_polls, polled, n_firms, total_sample, mean_sample,
  total_cost, mean_cost, n_own_polls, n_polls_last30,
  last_poll_days_before_election
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

# First-round election day per cycle (used for poll-timing features).
ELECTION_DAY = {2020: pd.Timestamp("2020-11-15"),
                2024: pd.Timestamp("2024-10-06")}

USECOLS = [
    "AA_ELEICAO", "SG_UF", "SG_UE", "NM_UE", "DS_CARGO",
    "NR_PROTOCOLO_REGISTRO", "NM_EMPRESA", "NR_CNPJ_EMPRESA",
    "QT_ENTREVISTADO", "VR_PESQUISA", "ST_PESQUISA_PROPRIA",
    "DT_INICIO_PESQUISA", "DT_FIM_PESQUISA",
]


def load_year(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"pesquisa_eleitoral_{year}"
    files = sorted(folder.glob(f"pesquisa_eleitoral_{year}_*.csv"))
    # exclude the empty BR / BRASIL aggregate files
    files = [f for f in files if "_BR" not in f.name.upper()]
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

    # Mayoral races only.
    df = df[df["DS_CARGO"].str.contains("Prefeito", na=False)].copy()
    # One row per registered poll.
    df = df.drop_duplicates(subset="NR_PROTOCOLO_REGISTRO").copy()

    # Numeric fields. QT_ENTREVISTADO has occasional negative/garbage values.
    df["sample"] = pd.to_numeric(df["QT_ENTREVISTADO"], errors="coerce")
    df.loc[df["sample"] <= 0, "sample"] = np.nan
    df["cost"] = pd.to_numeric(
        df["VR_PESQUISA"].str.replace(".", "", regex=False)
                         .str.replace(",", ".", regex=False),
        errors="coerce")
    df.loc[df["cost"] <= 0, "cost"] = np.nan

    df["is_own"] = (df["ST_PESQUISA_PROPRIA"].str.upper() == "S").astype(int)

    # Poll timing relative to election day (use fieldwork end date).
    eday = ELECTION_DAY[year]
    end = pd.to_datetime(df["DT_FIM_PESQUISA"], errors="coerce")
    df["days_before"] = (eday - end).dt.days
    df["is_last30"] = ((df["days_before"] >= 0) & (df["days_before"] <= 30)).astype(int)

    df["year"] = year
    print(f"  {year}: {len(df):,} registered mayoral polls", flush=True)
    return df


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["year", "SG_UF", "SG_UE", "NM_UE"])
    out = g.agg(
        n_polls=("NR_PROTOCOLO_REGISTRO", "size"),
        n_firms=("NR_CNPJ_EMPRESA", "nunique"),
        total_sample=("sample", "sum"),
        mean_sample=("sample", "mean"),
        total_cost=("cost", "sum"),
        mean_cost=("cost", "mean"),
        n_own_polls=("is_own", "sum"),
        n_polls_last30=("is_last30", "sum"),
    ).reset_index()
    # Earliest (largest days_before) poll lead time.
    lead = g["days_before"].max().reset_index(name="last_poll_days_before_election")
    out = out.merge(lead, on=["year", "SG_UF", "SG_UE", "NM_UE"], how="left")
    out["polled"] = 1
    return out


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    frames = [load_year(y) for y in (2020, 2024)]
    frames = [f for f in frames if not f.empty]
    if not frames:
        raise RuntimeError("No poll data loaded.")
    polls = pd.concat(frames, ignore_index=True)

    panel = summarise(polls).rename(columns={
        "SG_UF": "state",
        "SG_UE": "municipality_id_tse",
        "NM_UE": "municipality_name",
        "year": "election_year",
    })

    long_out = DERIVED_DIR / "poll_activity_panel.csv"
    panel.to_csv(long_out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {long_out.relative_to(PROJECT_ROOT)}  ({len(panel):,} rows)")

    # Wide: one row per municipality, *_2020 / *_2024 / delta_*.
    feat = ["n_polls", "polled", "n_firms", "total_sample", "mean_sample",
            "total_cost", "mean_cost", "n_own_polls", "n_polls_last30",
            "last_poll_days_before_election"]
    keys = ["municipality_id_tse", "state", "municipality_name"]
    wide = None
    for yr in (2020, 2024):
        sub = panel[panel["election_year"] == yr][keys + feat].copy()
        sub = sub.rename(columns={c: f"{c}_{yr}" for c in feat})
        wide = sub if wide is None else wide.merge(sub, on=keys, how="outer")

    # Municipalities with no poll in a cycle: counts -> 0, polled -> 0.
    zero_fill = ["n_polls", "polled", "n_firms", "total_sample",
                 "n_own_polls", "n_polls_last30"]
    for yr in (2020, 2024):
        for c in zero_fill:
            wide[f"{c}_{yr}"] = wide[f"{c}_{yr}"].fillna(0)

    for c in feat:
        wide[f"delta_{c}_2024_2020"] = wide[f"{c}_2024"] - wide[f"{c}_2020"]
    wide["polled_both"] = ((wide["polled_2020"] == 1) & (wide["polled_2024"] == 1)).astype(int)
    wide["polled_either"] = ((wide["polled_2020"] == 1) | (wide["polled_2024"] == 1)).astype(int)

    wide_out = DERIVED_DIR / "poll_activity_design.csv"
    wide.to_csv(wide_out, index=False, encoding="utf-8-sig")
    print(f"Saved: {wide_out.relative_to(PROJECT_ROOT)}  ({len(wide):,} municipalities)")
    print(f"  polled both cycles : {int(wide['polled_both'].sum()):,}")
    print(f"  polled either cycle: {int(wide['polled_either'].sum()):,}")


if __name__ == "__main__":
    main()
