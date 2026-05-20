"""
Builds a zona-eleitoral-level panel of lawsuit counts by case class and subject,
covering all four election cycles (2018, 2020, 2022, 2024).

Output: data/clean/zona_lawsuit_panel.csv

Columns:
  election_year                 election year (2018/2020/2022/2024)
  state                         state (from TR field in NR_PROCESSO)
  electoral_zone                electoral zone number (OOOO field in NR_PROCESSO)
  municipality_id_tse           TSE municipality code (from zone->municipality lookup)
  municipality_name             municipality name
  n_municipalities_in_zone      number of municipalities sharing this zone (>1 = multi-mun zone)
  case_class_code               case class code
  case_class_name               case class label
  main_subject_code             main subject code
  main_subject_name             main subject label
  n_lawsuits                    unique NR_PROCESSO count
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
        {"tr": [p[0] for p in parsed], "electoral_zone": [p[1] for p in parsed]},
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
    df = df[df["tr"].notna() & df["electoral_zone"].notna()].copy()

    # Drop TSE-origin cases (TR=00, zone=0): no local zone
    df = df[(df["tr"] != "00") & (df["electoral_zone"] > 0)].copy()

    df["state"] = df["tr"].map(TR_TO_UF)
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

    df["election_year"] = year
    return df


def build_zone_municipality_lookup() -> pd.DataFrame:
    """
    Load the official TSE zone->municipality mapping
    (lista-zonas-municipios-10-07-24.csv, downloaded from TSE).

    Returns one row per (state, electoral_zone, municipality_id_tse) with
    n_municipalities_in_zone. municipality_id_tse is COD_LOCALIDADE zero-padded
    to 5 digits, matching the consulta_cand SG_UE field.

    For zones covering multiple municipalities all municipality rows are kept so
    the caller can decide on allocation. n_municipios_zona flags these zones.
    """
    path = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"
    print(f"  Loading official TSE zone-municipality lookup ({path.name}) ...",
          flush=True)

    lookup = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(columns={
        "UF": "state",
        "ZONA": "electoral_zone",
        "COD_LOCALIDADE": "municipality_id_tse",
        "NOM_LOCALIDADE": "municipality_name",
    })
    # Drop the unnamed index column and the ZZ pseudo-state (overseas)
    lookup = lookup[["state", "electoral_zone", "municipality_id_tse", "municipality_name"]]
    lookup = lookup[lookup["state"] != "ZZ"].copy()

    # Convert zona to int for consistent join
    lookup["electoral_zone"] = pd.to_numeric(lookup["electoral_zone"], errors="coerce")
    lookup = lookup.dropna(subset=["electoral_zone"])
    lookup["electoral_zone"] = lookup["electoral_zone"].astype(int)

    lookup["municipality_id_tse"] = lookup["municipality_id_tse"].str.strip().str.zfill(5)

    # Count municipalities per zone
    mun_count = (
        lookup.groupby(["state", "electoral_zone"])["municipality_id_tse"]
        .nunique()
        .rename("n_municipalities_in_zone")
        .reset_index()
    )
    lookup = lookup.merge(mun_count, on=["state", "electoral_zone"], how="left")
    lookup = lookup.drop_duplicates()

    n_zones = lookup[["state", "electoral_zone"]].drop_duplicates().shape[0]
    n_mun = lookup["municipality_id_tse"].nunique()
    n_multi = (mun_count["n_municipalities_in_zone"] > 1).sum()
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
            ["election_year", "state", "electoral_zone",
             "CD_CLASSE", "DS_CLASSE",
             "CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"],
            as_index=False,
        )
        .agg(n_lawsuits=("NR_PROCESSO", "nunique"))
    )
    panel = panel.rename(columns={
        "CD_CLASSE": "case_class_code",
        "DS_CLASSE": "case_class_name",
        "CD_ASSUNTO_PRINCIPAL": "main_subject_code",
        "DS_ASSUNTO_PRINCIPAL": "main_subject_name",
    })

    # ------------------------------------------------------------------ #
    # 4. Join municipality codes
    # ------------------------------------------------------------------ #
    print("\n[4] Joining municipality codes")

    panel = panel.merge(
        zone_mun,
        on=["state", "electoral_zone"],
        how="left",
    )

    # Rows with no municipality match (zones not observed in 2020 partes)
    n_no_mun = panel["municipality_id_tse"].isna().sum()
    pct_no_mun = n_no_mun / len(panel) * 100
    print(f"  Rows without municipality match: {n_no_mun:,} ({pct_no_mun:.1f}%)")

    # Final column order
    panel = panel[[
        "election_year", "state", "electoral_zone",
        "municipality_id_tse", "municipality_name", "n_municipalities_in_zone",
        "case_class_code", "case_class_name",
        "main_subject_code", "main_subject_name",
        "n_lawsuits",
    ]].sort_values(["election_year", "state", "electoral_zone", "municipality_id_tse",
                    "case_class_code", "main_subject_code"])

    # ------------------------------------------------------------------ #
    # 5. Save
    # ------------------------------------------------------------------ #
    out_path = DERIVED_DIR / "zona_lawsuit_panel.csv"
    panel.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n[5] Saved: {out_path.relative_to(PROJECT_ROOT)}")
    print(f"  Rows: {len(panel):,}")
    print(f"  Unique zones: {panel[['state','electoral_zone']].drop_duplicates().shape[0]:,}")
    print(f"  Unique municipalities (municipality_id_tse): {panel['municipality_id_tse'].nunique():,}")
    print(f"  Years: {sorted(panel['election_year'].unique())}")
    print(f"  Unique (class, subject) combinations: "
          f"{panel[['case_class_code','main_subject_code']].drop_duplicates().shape[0]:,}")

    # Quick cross-tab: total lawsuits by year
    print("\n  Total unique lawsuits by year:")
    year_totals = (
        panel.groupby("election_year")["n_lawsuits"].sum()
    )
    for yr, n in year_totals.items():
        print(f"    {yr}: {n:,.0f}")


if __name__ == "__main__":
    main()
