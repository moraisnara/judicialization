"""
Builds a zona-eleitoral-level panel of lawsuit counts by case class and subject,
covering all four election cycles (2018, 2020, 2022, 2024).

Output: data/clean/zona_lawsuit_panel.csv

Columns:
  ANO_ELEICAO           election year (2018/2020/2022/2024)
  SG_UF                 state (from TR field in NR_PROCESSO)
  zona_eleitoral        electoral zone number (OOOO field in NR_PROCESSO)
  SG_UE                 TSE municipality code (from zone->municipality lookup)
  NM_UE                 municipality name
  n_municipios_zona     number of municipalities sharing this zone (>1 = multi-mun zone)
  CD_CLASSE             case class code
  DS_CLASSE             case class label
  CD_ASSUNTO_PRINCIPAL  main subject code
  DS_ASSUNTO_PRINCIPAL  main subject label
  n_lawsuits            unique NR_PROCESSO count
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"

CSV_ENC = "latin-1"
CSV_SEP = ";"
YEARS = [2018, 2020, 2022, 2024]

# First-round election dates: only pre-election cases can affect electoral outcomes.
ELECTION_CUTOFFS: dict[int, pd.Timestamp] = {
    2018: pd.Timestamp("2018-10-07"),
    2020: pd.Timestamp("2020-11-15"),
    2022: pd.Timestamp("2022-10-02"),
    2024: pd.Timestamp("2024-10-06"),
}

# Electoral Justice tribunal code (TR) -> state abbreviation
TR_TO_UF: dict[str, str] = {
    "00": "TSE", "01": "AC", "02": "AL", "03": "AP", "04": "AM",
    "05": "BA", "06": "CE", "07": "DF", "08": "ES", "09": "GO",
    "10": "MA", "11": "MT", "12": "MS", "13": "MG", "14": "PA",
    "15": "PB", "16": "PE", "17": "PI", "18": "RJ", "19": "RN",
    "20": "RS", "21": "RO", "22": "RR", "23": "SC", "24": "SP",
    "25": "SE", "26": "TO", "27": "PR",
}

NR_RE = re.compile(r"^\d{7}-\d{2}\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$")

PROCESSO_COLS = [
    "ANO_ELEICAO", "NR_PROCESSO",
    "NR_INSTANCIA",
    "DT_AUTUACAO",
    "CD_CLASSE", "DS_CLASSE",
    "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL",
]


def parse_nr_processo(series: pd.Series) -> pd.DataFrame:
    """Extract (tr, zona) from NR_PROCESSO. Returns DataFrame aligned with input index."""
    def _parse(nr: str) -> tuple[str | None, int | None]:
        m = NR_RE.match(str(nr).strip())
        if not m:
            return None, None
        tr = m.group(3)
        zona = int(m.group(4))
        return tr, zona

    parsed = series.map(_parse)
    return pd.DataFrame(
        {"tr": [p[0] for p in parsed], "zona_eleitoral": [p[1] for p in parsed]},
        index=series.index,
    )


def load_and_parse_processo(year: int) -> pd.DataFrame:
    path = RAW_DIR / f"processo_eleitoral_{year}" / f"processo_eleitoral_{year}.csv"
    print(f"  Loading {year} ({path.stat().st_size / 1e6:.0f} MB) ...", flush=True)
    df = pd.read_csv(
        path, sep=CSV_SEP, encoding=CSV_ENC,
        usecols=PROCESSO_COLS, dtype=str, low_memory=False,
    )
    parsed = parse_nr_processo(df["NR_PROCESSO"])
    df = pd.concat([df, parsed], axis=1)

    # Drop cases that did not parse (malformed NR_PROCESSO)
    df = df[df["tr"].notna() & df["zona_eleitoral"].notna()].copy()

    # Drop TSE-origin cases (TR=00, zone=0): no local zone
    df = df[(df["tr"] != "00") & (df["zona_eleitoral"] > 0)].copy()

    df["SG_UF"] = df["tr"].map(TR_TO_UF)
    df["NR_INSTANCIA"] = pd.to_numeric(df["NR_INSTANCIA"], errors="coerce")

    # Restrict to first-instance Electoral Zones only.
    # This matches the intended design: local judicialization at the Zona Eleitoral level,
    # excluding appeals and higher-court processing.
    df = df[df["NR_INSTANCIA"] == 1].copy()

    # Keep one row per NR_PROCESSO within first instance
    df = df.sort_values("NR_INSTANCIA", na_position="last")
    df = df.drop_duplicates(subset=["NR_PROCESSO"], keep="first")

    # Restrict to cases filed before first-round election day.
    # Post-election cases (appeals, mandate challenges) cannot affect electoral outcomes
    # and may be endogenous to who won. ~9-10% of competition-relevant cases are post-election.
    cutoff = ELECTION_CUTOFFS.get(year)
    if cutoff is not None:
        df["DT_AUTUACAO"] = pd.to_datetime(df["DT_AUTUACAO"], format="%d/%m/%Y", errors="coerce")
        n_before = len(df)
        df = df[df["DT_AUTUACAO"] < cutoff].copy()
        n_dropped = n_before - len(df)
        pct = (100 * n_dropped / n_before) if n_before > 0 else 0.0
        print(f"    Timing filter: dropped {n_dropped:,} post-election cases "
              f"({pct:.1f}%)", flush=True)

    df["ANO_ELEICAO"] = year
    return df


def build_zone_municipality_lookup() -> pd.DataFrame:
    """
    Load the official TSE zone->municipality mapping
    (lista-zonas-municipios-10-07-24.csv, downloaded from TSE).

    Returns one row per (SG_UF, zona_eleitoral, SG_UE) with n_municipios_zona.
    SG_UE is COD_LOCALIDADE zero-padded to 5 digits, matching the consulta_cand
    SG_UE field.

    For zones covering multiple municipalities all municipality rows are kept so
    the caller can decide on allocation. n_municipios_zona flags these zones.
    """
    path = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"
    print(f"  Loading official TSE zone-municipality lookup ({path.name}) ...",
          flush=True)

    lookup = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(columns={
        "UF": "SG_UF",
        "ZONA": "zona_eleitoral",
        "COD_LOCALIDADE": "COD_MUN",
        "NOM_LOCALIDADE": "NM_UE",
    })
    # Drop the unnamed index column and the ZZ pseudo-state (overseas)
    lookup = lookup[["SG_UF", "zona_eleitoral", "COD_MUN", "NM_UE"]]
    lookup = lookup[lookup["SG_UF"] != "ZZ"].copy()

    # Convert zona to int for consistent join
    lookup["zona_eleitoral"] = pd.to_numeric(lookup["zona_eleitoral"], errors="coerce")
    lookup = lookup.dropna(subset=["zona_eleitoral"])
    lookup["zona_eleitoral"] = lookup["zona_eleitoral"].astype(int)

    # SG_UE = COD_MUN zero-padded to 5 digits (matches consulta_cand SG_UE)
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup = lookup.drop(columns=["COD_MUN"])

    # Count municipalities per zone
    mun_count = (
        lookup.groupby(["SG_UF", "zona_eleitoral"])["SG_UE"]
        .nunique()
        .rename("n_municipios_zona")
        .reset_index()
    )
    lookup = lookup.merge(mun_count, on=["SG_UF", "zona_eleitoral"], how="left")
    lookup = lookup.drop_duplicates()

    n_zones = lookup[["SG_UF", "zona_eleitoral"]].drop_duplicates().shape[0]
    n_mun = lookup["SG_UE"].nunique()
    n_multi = (mun_count["n_municipios_zona"] > 1).sum()
    print(f"    Zones: {n_zones:,}  |  municipalities: {n_mun:,}  "
          f"|  multi-municipality zones: {n_multi:,}", flush=True)
    return lookup


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. Load and parse all four process files
    # ------------------------------------------------------------------ #
    print("\n[1] Loading processo_eleitoral files")
    frames = []
    for year in YEARS:
        df = load_and_parse_processo(year)
        frames.append(df)
        print(f"    {year}: {len(df):,} unique lawsuits with parsed zone")

    all_processes = pd.concat(frames, ignore_index=True)
    print(f"\n  Total across all years: {len(all_processes):,} unique lawsuits")

    # ------------------------------------------------------------------ #
    # 2. Build zone->municipality lookup from 2020
    # ------------------------------------------------------------------ #
    print("\n[2] Zone->municipality lookup")
    zone_mun = build_zone_municipality_lookup()

    # ------------------------------------------------------------------ #
    # 3. Aggregate: count lawsuits by (year, state, zone, class, subject)
    # ------------------------------------------------------------------ #
    print("\n[3] Aggregating by (year, state, zone, class, subject)")

    panel = (
        all_processes
        .groupby(
            ["ANO_ELEICAO", "SG_UF", "zona_eleitoral",
             "CD_CLASSE", "DS_CLASSE",
             "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"],
            as_index=False,
        )
        .agg(n_lawsuits=("NR_PROCESSO", "nunique"))
    )

    # ------------------------------------------------------------------ #
    # 4. Join municipality codes
    # ------------------------------------------------------------------ #
    print("\n[4] Joining municipality codes")

    panel = panel.merge(
        zone_mun,
        on=["SG_UF", "zona_eleitoral"],
        how="left",
    )

    # Rows with no municipality match (zones not observed in 2020 partes)
    n_no_mun = panel["SG_UE"].isna().sum()
    pct_no_mun = n_no_mun / len(panel) * 100
    print(f"  Rows without municipality match: {n_no_mun:,} ({pct_no_mun:.1f}%)")

    # Final column order
    panel = panel[[
        "ANO_ELEICAO", "SG_UF", "zona_eleitoral",
        "SG_UE", "NM_UE", "n_municipios_zona",
        "CD_CLASSE", "DS_CLASSE",
        "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL",
        "n_lawsuits",
    ]].sort_values(["ANO_ELEICAO", "SG_UF", "zona_eleitoral", "SG_UE",
                    "CD_CLASSE", "CD_ASSUNTO_PRINCIPAL"])

    # ------------------------------------------------------------------ #
    # 5. Save
    # ------------------------------------------------------------------ #
    out_path = DERIVED_DIR / "zona_lawsuit_panel.csv"
    panel.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n[5] Saved: {out_path.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(panel):,}")
    print(f"  Unique zones: {panel[['SG_UF','zona_eleitoral']].drop_duplicates().shape[0]:,}")
    print(f"  Unique municipalities (SG_UE): {panel['SG_UE'].nunique():,}")
    print(f"  Years: {sorted(panel['ANO_ELEICAO'].unique())}")
    print(f"  Unique (class, subject) combinations: "
          f"{panel[['CD_CLASSE','CD_ASSUNTO_PRINCIPAL']].drop_duplicates().shape[0]:,}")

    # Quick cross-tab: total lawsuits by year
    print("\n  Total unique lawsuits by year:")
    year_totals = (
        panel.groupby("ANO_ELEICAO")["n_lawsuits"].sum()
    )
    for yr, n in year_totals.items():
        print(f"    {yr}: {n:,.0f}")


if __name__ == "__main__":
    main()
