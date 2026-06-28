from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

CHUNKSIZE = 200_000

LEGAL_CATS = {
    "Serviços advocatícios",  # Serviços advocatícios
    "Multas eleitorais",
}

TRADITIONAL_MARKETING_CATS = {
    "Publicidade por materiais impressos",
    "Publicidade por adesivos",
    "Publicidade por jornais e revistas",
    "Publicidade por carros de som",
    "Produção de jingles, vinhetas e slogans",
    "Produção de programas de rádio, televisão ou vídeo",
}

ONLINE_MARKETING_CATS = {
    "Criação e inclusão de páginas na internet",
    "Despesa com Impulsionamento de Conteúdos",
}

MARKETING_CATS = TRADITIONAL_MARKETING_CATS | ONLINE_MARKETING_CATS

COLS_NEEDED = [
    "CD_TIPO_ELEICAO",
    "CD_CARGO",
    "SG_UE",
    "DS_ORIGEM_DESPESA",
    "VR_DESPESA_CONTRATADA",
]

# Reference: November 2024 (month of 2024 election)
REF_YM = (2024, 11)
ELECTION_YM = {2020: (2020, 11), 2024: (2024, 11)}

OFFICES = [("executive", 11), ("legislative", 13)]


def fetch_ipca_deflator(from_ym: tuple[int, int], to_ym: tuple[int, int]) -> float:
    """Cumulative IPCA factor to convert BRL from end of from_ym to end of to_ym."""
    fy, fm = from_ym
    ty, tm = to_ym
    url = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
        f"?formato=json&dataInicial=01/{fm:02d}/{fy}&dataFinal=01/{tm:02d}/{ty}"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())
    # Skip the first entry (from_ym itself); accumulate from the following month
    factor = 1.0
    for entry in data[1:]:
        rate = float(entry["valor"].replace(",", "."))
        factor *= 1 + rate / 100
    return factor


def aggregate_year(year: int, cargo_cd: int) -> pd.DataFrame:
    path = (
        RAW_DIR
        / f"spce_candidatos_{year}"
        / f"despesas_contratadas_candidatos_{year}_BRASIL.csv"
    )
    print(f"  [{year}] Reading {path.name} for CD_CARGO={cargo_cd}...")

    acc: dict[str, dict[str, float]] = defaultdict(
        lambda: {"total": 0.0, "legal": 0.0, "marketing": 0.0,
                 "traditional_marketing": 0.0, "online_marketing": 0.0}
    )
    n_chunks = 0

    for chunk in pd.read_csv(
        path,
        encoding="latin-1",
        sep=";",
        usecols=COLS_NEEDED,
        dtype=str,
        chunksize=CHUNKSIZE,
    ):
        chunk = chunk[chunk["CD_TIPO_ELEICAO"] == "2"]
        chunk = chunk[chunk["CD_CARGO"] == str(cargo_cd)]
        if chunk.empty:
            n_chunks += 1
            continue

        chunk["amount"] = (
            chunk["VR_DESPESA_CONTRATADA"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        chunk["amount"] = pd.to_numeric(chunk["amount"], errors="coerce").fillna(0.0)

        for label, mask in [
            ("total", chunk["DS_ORIGEM_DESPESA"] != "#NULO"),
            ("legal", chunk["DS_ORIGEM_DESPESA"].isin(LEGAL_CATS)),
            ("marketing", chunk["DS_ORIGEM_DESPESA"].isin(MARKETING_CATS)),
            ("traditional_marketing", chunk["DS_ORIGEM_DESPESA"].isin(TRADITIONAL_MARKETING_CATS)),
            ("online_marketing", chunk["DS_ORIGEM_DESPESA"].isin(ONLINE_MARKETING_CATS)),
        ]:
            agg = chunk.loc[mask].groupby("SG_UE")["amount"].sum()
            for muni, val in agg.items():
                acc[muni][label] += val

        n_chunks += 1
        if n_chunks % 20 == 0:
            print(f"    ... {n_chunks * CHUNKSIZE:,} rows processed")

    df = pd.DataFrame.from_dict(acc, orient="index").reset_index(names="municipality_id_tse")
    df["municipality_id_tse"] = df["municipality_id_tse"].str.zfill(5)
    print(f"    Done — {len(df):,} municipalities with spending records")
    return df


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # --- Deflation factors ---
    print("Fetching IPCA from BCB SGS API (series 433)...")
    deflators: dict[int, float] = {}
    for year, ym in ELECTION_YM.items():
        if ym == REF_YM:
            deflators[year] = 1.0
        else:
            deflators[year] = fetch_ipca_deflator(ym, REF_YM)
        print(f"  Deflator {year} -> Nov 2024: {deflators[year]:.4f}x")

    # --- Candidate registry ---
    registry = pd.read_csv(CLEAN_DIR / "office_candidate_outcomes_panel.csv", dtype=str)
    registry.columns = registry.columns.str.lstrip("﻿")
    registry["total_candidates"] = pd.to_numeric(registry["total_candidates"])
    registry["election_year"] = registry["election_year"].astype(int)
    registry["municipality_id_tse"] = registry["municipality_id_tse"].str.zfill(5)

    # --- TSE → IBGE crosswalk ---
    crosswalk = pd.read_csv(RAW_DIR / "bd_municipio_tse_ibge.csv", dtype=str)
    crosswalk["municipality_id_tse"] = crosswalk["id_municipio_tse"].str.zfill(5)
    crosswalk = crosswalk[["municipality_id_tse", "id_municipio"]].rename(
        columns={"id_municipio": "cod_ibge"}
    )

    # --- Process each office ---
    for office_label, cargo_cd in OFFICES:
        print(f"\n{'='*60}")
        print(f"OFFICE: {office_label.upper()} (CD_CARGO={cargo_cd})")
        print("=" * 60)

        frames = []
        for year in [2020, 2024]:
            df = aggregate_year(year, cargo_cd)
            df["election_year"] = year
            for col in ["total", "legal", "marketing", "traditional_marketing", "online_marketing"]:
                df[col] = df[col] * deflators[year]
            frames.append(df)

        long = pd.concat(frames, ignore_index=True)

        # Join candidate counts from registry
        reg_sub = (
            registry[registry["office_group"] == office_label][
                ["municipality_id_tse", "election_year", "total_candidates"]
            ]
            .copy()
        )
        long = long.merge(reg_sub, on=["municipality_id_tse", "election_year"], how="left")

        for col in ["total", "legal", "marketing", "traditional_marketing", "online_marketing"]:
            long[f"{col}_per_cand"] = long[col] / long["total_candidates"]

        # Pivot wide
        val_cols = ["total_per_cand", "legal_per_cand", "marketing_per_cand",
                    "traditional_marketing_per_cand", "online_marketing_per_cand"]
        wide = long.pivot(
            index="municipality_id_tse", columns="election_year", values=val_cols
        )
        wide.columns = [f"{v}_{y}" for v, y in wide.columns]
        wide = wide.reset_index()

        for col in val_cols:
            wide[f"delta_{col}"] = wide[f"{col}_2024"] - wide[f"{col}_2020"]

        # Add IBGE code
        wide = wide.merge(crosswalk, on="municipality_id_tse", how="left")

        out_path = CLEAN_DIR / f"spce_{office_label}.csv"
        wide.to_csv(out_path, index=False)
        print(f"\nSaved -> {out_path}  ({len(wide):,} rows, {len(wide.columns)} cols)")


if __name__ == "__main__":
    main()
