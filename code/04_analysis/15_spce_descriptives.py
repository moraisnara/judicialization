from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"

CHUNKSIZE = 200_000

LEGAL_CATS = {
    "Servicos advocaticios": "Serviços advocatícios",
    "Multas eleitorais":     "Multas eleitorais",
}

MARKETING_CATS = {
    "Materiais impressos":   "Publicidade por materiais impressos",
    "Adesivos":              "Publicidade por adesivos",
    "Jornais e revistas":    "Publicidade por jornais e revistas",
    "Carros de som":         "Publicidade por carros de som",
    "Jingles e vinhetas":    "Produção de jingles, vinhetas e slogans",
    "Radio e TV":            "Produção de programas de rádio, televisão ou vídeo",
    "Paginas na internet":   "Criação e inclusão de páginas na internet",
    "Impulsionamento":       "Despesa com Impulsionamento de Conteúdos",
}

ALL_CATS = {**LEGAL_CATS, **MARKETING_CATS}
CAT_TO_LABEL = {v: k for k, v in ALL_CATS.items()}
LEGAL_VALUES = set(LEGAL_CATS.values())
MARKETING_VALUES = set(MARKETING_CATS.values())

COLS_NEEDED = ["CD_TIPO_ELEICAO", "DS_ORIGEM_DESPESA", "VR_DESPESA_CONTRATADA"]
NULL_CAT = "#NULO"


def fetch_ipca_deflator(from_ym: tuple[int, int], to_ym: tuple[int, int]) -> float:
    fy, fm = from_ym
    ty, tm = to_ym
    url = (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
        f"?formato=json&dataInicial=01/{fm:02d}/{fy}&dataFinal=01/{tm:02d}/{ty}"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())
    factor = 1.0
    for entry in data[1:]:
        factor *= 1 + float(entry["valor"].replace(",", ".")) / 100
    return factor


def aggregate_categories(year: int) -> tuple[pd.Series, float]:
    """Returns (per-category totals, grand total of all non-null spending)."""
    path = (
        RAW_DIR
        / f"spce_candidatos_{year}"
        / f"despesas_contratadas_candidatos_{year}_BRASIL.csv"
    )
    print(f"  Reading {year}...")
    totals: dict[str, float] = {cat: 0.0 for cat in ALL_CATS.values()}
    grand_total = 0.0

    for chunk in pd.read_csv(
        path, encoding="latin-1", sep=";",
        usecols=COLS_NEEDED, dtype=str, chunksize=CHUNKSIZE,
    ):
        chunk = chunk[chunk["CD_TIPO_ELEICAO"] == "2"]
        if chunk.empty:
            continue

        chunk["amount"] = (
            chunk["VR_DESPESA_CONTRATADA"]
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        chunk["amount"] = pd.to_numeric(chunk["amount"], errors="coerce").fillna(0.0)

        # Grand total — all non-null categories
        grand_total += chunk.loc[chunk["DS_ORIGEM_DESPESA"] != NULL_CAT, "amount"].sum()

        # Sub-category totals
        sub = chunk[chunk["DS_ORIGEM_DESPESA"].isin(ALL_CATS.values())]
        for cat, val in sub.groupby("DS_ORIGEM_DESPESA")["amount"].sum().items():
            if cat in totals:
                totals[cat] += val

    return pd.Series(totals, name=year), grand_total


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching IPCA deflator...")
    deflator_2020 = fetch_ipca_deflator((2020, 11), (2024, 11))
    print(f"  2020 -> Nov 2024: {deflator_2020:.4f}x")

    s2020, grand_2020_nom = aggregate_categories(2020)
    s2024, grand_2024_nom = aggregate_categories(2024)

    # Deflate to Nov 2024 BRL
    grand_2020 = grand_2020_nom * deflator_2020
    grand_2024 = grand_2024_nom

    df = pd.DataFrame({"nominal_2020": s2020, "nominal_2024": s2024})
    df["real_2020"] = df["nominal_2020"] * deflator_2020
    df["real_2024"] = df["nominal_2024"]

    df["bucket"] = df.index.map(lambda x: "legal" if x in LEGAL_VALUES else "marketing")
    df["label"]  = df.index.map(lambda x: CAT_TO_LABEL.get(x, x))

    # Share of GRAND TOTAL for each sub-category
    df["share_of_total_2020"] = df["real_2020"] / grand_2020
    df["share_of_total_2024"] = df["real_2024"] / grand_2024

    # Bucket aggregates
    legal_2020 = df.loc[df["bucket"] == "legal", "real_2020"].sum()
    legal_2024 = df.loc[df["bucket"] == "legal", "real_2024"].sum()
    mktg_2020  = df.loc[df["bucket"] == "marketing", "real_2020"].sum()
    mktg_2024  = df.loc[df["bucket"] == "marketing", "real_2024"].sum()

    df["pct_change_real"] = (df["real_2024"] - df["real_2020"]) / df["real_2020"] * 100

    out = df[["label", "bucket", "real_2020", "real_2024",
              "share_of_total_2020", "share_of_total_2024", "pct_change_real"]].copy()
    out = out.sort_values(["bucket", "share_of_total_2024"], ascending=[True, False])
    out.index.name = "categoria"

    path = OUT_DIR / "spce_category_breakdown.csv"
    out.to_csv(path)
    print(f"\nSaved -> {path}")

    # Console summary
    print(f"\nGrand total (real Nov 2024 BRL):  2020 = R$ {grand_2020/1e9:.2f}B  |  2024 = R$ {grand_2024/1e9:.2f}B  |  chg: {(grand_2024/grand_2020-1)*100:+.1f}%")

    print(f"\n=== LEGAL BUCKET  (share of total: {legal_2020/grand_2020:.2%} -> {legal_2024/grand_2024:.2%}) ===")
    print(f"  Bucket total real:  2020 R$ {legal_2020/1e6:.0f}M  |  2024 R$ {legal_2024/1e6:.0f}M  |  chg: {(legal_2024/legal_2020-1)*100:+.1f}%")
    for _, row in out[out["bucket"] == "legal"].iterrows():
        print(f"  {row['label']:30s}  share of total:  2020={row['share_of_total_2020']:.3%}  2024={row['share_of_total_2024']:.3%}  chg: {row['pct_change_real']:+.1f}%")

    print(f"\n=== MARKETING BUCKET  (share of total: {mktg_2020/grand_2020:.2%} -> {mktg_2024/grand_2024:.2%}) ===")
    print(f"  Bucket total real:  2020 R$ {mktg_2020/1e9:.2f}B  |  2024 R$ {mktg_2024/1e9:.2f}B  |  chg: {(mktg_2024/mktg_2020-1)*100:+.1f}%")
    for _, row in out[out["bucket"] == "marketing"].iterrows():
        print(f"  {row['label']:30s}  share of total:  2020={row['share_of_total_2020']:.3%}  2024={row['share_of_total_2024']:.3%}  chg: {row['pct_change_real']:+.1f}%")


if __name__ == "__main__":
    main()
