"""
Candidate and elected pool descriptive statistics by office and election year.

Computes weighted means (weighted by total_candidates per municipality) for
gender, race/ethnicity, education, and age — separately for the candidate pool
and the elected pool — for mayoral (executive) and city council (legislative)
races in 2020 and 2024.

Also computes vote-weighted demographics for the executive race (share of valid
votes cast for female / nonwhite candidates, share of municipalities where the
winner is female).

Inputs:
  data/clean/office_candidate_outcomes_panel.csv
  data/clean/executive_vote_shift_share_design.csv

Outputs:
  output/tables/descriptives/candidate_pool_descriptives.csv
  output/tables/descriptives/candidate_pool_descriptives.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PANEL_CSV    = PROJECT_ROOT / "data" / "clean" / "office_candidate_outcomes_panel.csv"
VOTE_CSV     = PROJECT_ROOT / "data" / "clean" / "executive_vote_shift_share_design.csv"
OUT_DIR      = PROJECT_ROOT / "output" / "tables" / "descriptives"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def weighted_mean(series: pd.Series, weights: pd.Series) -> float:
    mask = series.notna() & weights.notna() & (weights > 0)
    return np.average(series[mask], weights=weights[mask])


def pool_stats(df: pd.DataFrame, office: str, year: int) -> dict:
    sub = df[(df["office_group"] == office) & (df["election_year"] == year)].copy()
    w   = sub["total_candidates"]
    return {
        "office":    office,
        "year":      year,
        "n_municipalities": len(sub),
        # --- candidate pool ---
        "cand_female_share":          weighted_mean(sub["female_share"], w),
        "cand_nonwhite_share":        weighted_mean(sub["nonwhite_share"], w),
        "cand_higher_education_share": weighted_mean(sub["higher_education_share"], w),
        "cand_mean_age":              weighted_mean(sub["mean_age"], w),
        # --- elected pool ---
        "elected_female_share":          weighted_mean(sub["elected_female_share"], w),
        "elected_nonwhite_share":        weighted_mean(sub["elected_nonwhite_share"], w),
        "elected_higher_education_share": weighted_mean(sub["elected_higher_education_share"], w),
        "elected_mean_age":              weighted_mean(sub["elected_mean_age"], w),
        # --- incumbency ---
        "new_candidate_share":       weighted_mean(sub["new_candidate_share"], w),
        "incumbent_candidate_share": weighted_mean(sub["incumbent_candidate_share"], w),
        "incumbent_reelected_share": weighted_mean(sub["incumbent_reelected_share"], w),
    }


def vote_stats(vote: pd.DataFrame, year: int) -> dict:
    return {
        "female_vote_share":   vote[f"female_vote_share_{year}"].mean(),
        "nonwhite_vote_share": vote[f"nonwhite_vote_share_{year}"].mean(),
        "winner_is_female":    vote[f"winner_is_female_{year}"].mean(),
    }


def main() -> None:
    panel = pd.read_csv(PANEL_CSV)
    vote  = pd.read_csv(VOTE_CSV)

    # --- panel stats ---
    rows = []
    for office in ("executive", "legislative"):
        for year in (2020, 2024):
            rows.append(pool_stats(panel, office, year))
    stats = pd.DataFrame(rows)

    # --- vote-weighted stats (executive only) ---
    for year in (2020, 2024):
        vs = vote_stats(vote, year)
        mask = (stats["office"] == "executive") & (stats["year"] == year)
        for col, val in vs.items():
            stats.loc[mask, col] = val

    stats.to_csv(OUT_DIR / "candidate_pool_descriptives.csv", index=False)

    # --- markdown table for quick reference ---
    pct = lambda x: f"{x * 100:.1f}\\%" if pd.notna(x) else "---"
    dec = lambda x: f"{x:.1f}" if pd.notna(x) else "---"

    lines = [
        "# Candidate and Elected Pool Descriptives\n",
        "Weighted by total candidates per municipality.\n",
        "| Statistic | Exec 2020 | Exec 2024 | Leg 2020 | Leg 2024 |",
        "|-----------|-----------|-----------|----------|----------|",
    ]

    def row(label, col, fmt):
        vals = []
        for office, year in [("executive", 2020), ("executive", 2024),
                              ("legislative", 2020), ("legislative", 2024)]:
            mask = (stats["office"] == office) & (stats["year"] == year)
            v = stats.loc[mask, col].values
            vals.append(fmt(v[0]) if len(v) else "---")
        lines.append(f"| {label} | {' | '.join(vals)} |")

    lines.append("| **Candidate pool** | | | | |")
    row("Female share",          "cand_female_share",           pct)
    row("Nonwhite share",        "cand_nonwhite_share",         pct)
    row("Higher education",      "cand_higher_education_share", pct)
    row("Mean age (years)",      "cand_mean_age",               dec)
    lines.append("| **Elected pool** | | | | |")
    row("Female share",          "elected_female_share",          pct)
    row("Nonwhite share",        "elected_nonwhite_share",        pct)
    row("Higher education",      "elected_higher_education_share", pct)
    row("Mean age (years)",      "elected_mean_age",               dec)
    lines.append("| **Vote-weighted (executive only)** | | | | |")
    row("Female vote share",     "female_vote_share",   pct)
    row("Nonwhite vote share",   "nonwhite_vote_share", pct)
    row("Winner is female",      "winner_is_female",    pct)
    lines.append("| **Incumbency (exec 2024 only)** | | | | |")
    row("New candidate share",       "new_candidate_share",       pct)
    row("Incumbent candidate share", "incumbent_candidate_share", pct)
    row("Incumbent reelected share", "incumbent_reelected_share", pct)

    (OUT_DIR / "candidate_pool_descriptives.md").write_text("\n".join(lines), encoding="utf-8")

    print("Saved:")
    print(f"  {OUT_DIR / 'candidate_pool_descriptives.csv'}")
    print(f"  {OUT_DIR / 'candidate_pool_descriptives.md'}")
    print()
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
