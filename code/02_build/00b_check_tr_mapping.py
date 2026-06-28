"""
Validation: TR (tribunal) code -> state mapping in 01_lawsuit_panel.py.

The CNJ case number NR_PROCESSO encodes the originating tribunal in its TR field
and the electoral zone in its OOOO field. Each TRE (state tribunal) has a known,
fixed number of electoral zones. We therefore validate the TR->UF dictionary by
matching, for each TR code, the number of distinct zones observed in the raw
2020 lawsuit file against the true per-state zone count from the official TSE
zona->municipality list. A correct mapping matches within a couple of zones
(a few zones may not appear pre-election, and a handful were renumbered by 2024).

This guards against the bug found 2026-06-17, where codes 16-27 were scrambled,
attributing ~11 states' lawsuits (incl. PR, RS, SC, SP, RJ) to the wrong
municipalities and producing spurious zero-litigation municipalities.

Output: data/clean/tr_mapping_validation.csv
Run:    python code/02_build/00b_check_tr_mapping.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

# Mirror the mapping under test from the build script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module  # noqa: E402

TR_TO_UF = import_module("01_lawsuit_panel").TR_TO_UF

NR_RE = re.compile(r"^\d{7}-\d{2}\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$")


def true_zone_counts() -> pd.Series:
    """Distinct electoral zones per state, from the official TSE list."""
    path = RAW_DIR / "lista-zonas-municipios-10-07-24.csv"
    lk = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    lk.columns = lk.columns.str.strip()
    lk = lk.rename(columns={"UF": "state", "ZONA": "zona"})
    lk = lk[lk["state"] != "ZZ"].copy()
    lk["zona"] = pd.to_numeric(lk["zona"], errors="coerce")
    return lk.groupby("state")["zona"].nunique()


def observed_zone_counts(year: int = 2020) -> pd.Series:
    """Distinct zones per TR code parsed from the raw lawsuit file."""
    path = RAW_DIR / f"processo_eleitoral_{year}" / f"processo_eleitoral_{year}.csv"
    df = pd.read_csv(path, sep=";", encoding="latin-1",
                     usecols=["NR_PROCESSO"], dtype=str, low_memory=False)

    def parse(nr: str) -> tuple[str | None, int | None]:
        m = NR_RE.match(str(nr).strip())
        return (m.group(3), int(m.group(4))) if m else (None, None)

    parsed = df["NR_PROCESSO"].map(parse)
    df["tr"] = [p[0] for p in parsed]
    df["zona"] = [p[1] for p in parsed]
    df = df[(df["zona"].fillna(0) > 0) & df["tr"].notna()]
    return df.groupby("tr")["zona"].nunique()


def main() -> None:
    true = true_zone_counts()
    obs = observed_zone_counts(2020)

    rows = []
    for tr, uf in sorted(TR_TO_UF.items()):
        if uf == "TSE" or tr not in obs.index:
            continue
        o = int(obs[tr])
        t = int(true.get(uf, -1))
        # Observed 2020 zone count should be close to the true (2024-dated) count.
        # Allow modest slack in both directions: a few zones may be absent
        # pre-election, and zones were renumbered/merged between 2020 and 2024
        # (so 2020 can have somewhat more zones than the 2024 list). A gross gap
        # — e.g. the old bug's "SC" = 8 vs true 100 — still flags as MISMATCH.
        ok = (t >= 0) and (0.7 * t - 3 <= o <= 1.25 * t + 3)
        rows.append({"tr": tr, "mapped_uf": uf, "obs_zones": o,
                     "true_zones": t, "match": "OK" if ok else "MISMATCH"})

    res = pd.DataFrame(rows)
    out = CLEAN_DIR / "tr_mapping_validation.csv"
    res.to_csv(out, index=False)

    n_bad = (res["match"] == "MISMATCH").sum()
    print(res.to_string(index=False))
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")
    if n_bad:
        print(f"\nFAIL: {n_bad} TR code(s) mismatch the true zone counts.")
        sys.exit(1)
    print("\nPASS: all TR codes match the official per-state zone counts.")


if __name__ == "__main__":
    main()
