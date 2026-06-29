"""
Turns the disaggregated turnout panel (comparecimento_disaggregated.csv) into
WIDE municipality outcomes for the act 2SLS voter-behaviour block.

Rationale: under compulsory voting the aggregate turnout rate is structurally
floored, so its IV null is near-mechanical. The ELASTIC margins -- facultative
voters (16-17, 70+, illiterate) and low-education voters -- are where a real
voter-engagement effect of judicialization would surface. This builds those
margins as outcomes plus their 2020 levels (lagged DV).

Turnout for a group = sum(comparecimento over the group's cells) / sum(aptos),
computed per municipality x year, then pivoted to _2020 / _2024 and differenced.
Aggregating COUNTS (not averaging rates) keeps the rate population-weighted.

Groups built:
  facultative / compulsory      (dimension compulsory_status)
  low_ed   = ANALFABETO + LE E ESCREVE + ENSINO FUNDAMENTAL INCOMPLETO
  high_ed  = SUPERIOR COMPLETO + SUPERIOR INCOMPLETO
  analfabeto                    (sharpest low-education cell)
  female / male                 (dimension sex)

Output: data/clean/voter_disaggregated_outcomes.csv  (one row per municipality)
  municipality_id_tse,
  <group>_turnout_2020, <group>_turnout_2024,
  delta_<group>_turnout_2024_2020,
  plus delta_education_turnout_gap and delta_sex_turnout_gap (high-low / female-male).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

LOW_ED = {"ANALFABETO", "LÊ E ESCREVE", "ENSINO FUNDAMENTAL INCOMPLETO"}
HIGH_ED = {"SUPERIOR COMPLETO", "SUPERIOR INCOMPLETO"}


def group_turnout(df: pd.DataFrame, dim: str, cats: set[str] | None,
                  name: str) -> pd.DataFrame:
    """Population-weighted turnout for a set of categories, per muni x year."""
    sub = df[df["dimension"] == dim]
    if cats is not None:
        sub = sub[sub["category"].isin(cats)]
    g = (sub.groupby(["municipality_id_tse", "election_year"], as_index=False)
            [["comparecimento", "aptos"]].sum())
    g[name] = g["comparecimento"] / g["aptos"].replace(0, float("nan"))
    wide = g.pivot_table(index="municipality_id_tse", columns="election_year",
                         values=name)
    wide.columns = [f"{name}_{int(c)}" for c in wide.columns]
    return wide


def main() -> None:
    src = CLEAN_DIR / "comparecimento_disaggregated.csv"
    df = pd.read_csv(src, dtype={"municipality_id_tse": str})
    df["municipality_id_tse"] = df["municipality_id_tse"].str.zfill(5)

    specs = [
        ("compulsory_status", {"facultative"}, "facultative_turnout"),
        ("compulsory_status", {"compulsory"}, "compulsory_turnout"),
        ("education", LOW_ED, "low_ed_turnout"),
        ("education", HIGH_ED, "high_ed_turnout"),
        ("education", {"ANALFABETO"}, "analfabeto_turnout"),
        ("sex", {"FEMININO"}, "female_turnout"),
        ("sex", {"MASCULINO"}, "male_turnout"),
    ]

    out = None
    for dim, cats, name in specs:
        w = group_turnout(df, dim, cats, name)
        out = w if out is None else out.join(w, how="outer")

    out = out.reset_index()

    # deltas (2024 - 2020) + within-cycle gaps
    for _, _, name in specs:
        c20, c24 = f"{name}_2020", f"{name}_2024"
        if c20 in out.columns and c24 in out.columns:
            out[f"delta_{name}_2024_2020"] = out[c24] - out[c20]

    # education gap (high - low) and sex gap (female - male), level + delta
    for yr in (2020, 2024):
        out[f"education_turnout_gap_{yr}"] = (
            out[f"high_ed_turnout_{yr}"] - out[f"low_ed_turnout_{yr}"])
        out[f"sex_turnout_gap_{yr}"] = (
            out[f"female_turnout_{yr}"] - out[f"male_turnout_{yr}"])
    out["delta_education_turnout_gap_2024_2020"] = (
        out["education_turnout_gap_2024"] - out["education_turnout_gap_2020"])
    out["delta_sex_turnout_gap_2024_2020"] = (
        out["sex_turnout_gap_2024"] - out["sex_turnout_gap_2020"])

    dst = CLEAN_DIR / "voter_disaggregated_outcomes.csv"
    out.to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"Saved: {dst.relative_to(PROJECT_ROOT)}  ({len(out):,} municipalities)")
    delta_cols = [c for c in out.columns if c.startswith("delta_")]
    print("\nDelta outcomes (mean / sd / n):")
    for c in delta_cols:
        s = out[c].dropna()
        print(f"  {c:42s} {s.mean():+.4f}  sd {s.std():.4f}  n {len(s):,}")


if __name__ == "__main__":
    main()
