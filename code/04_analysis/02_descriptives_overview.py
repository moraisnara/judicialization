"""
Overview descriptive statistics: lawsuits, voters, and candidates.

Computes counts, totals, and derived ratios (lawsuits/candidate,
lawsuits/voter) for 2020 and 2024 municipal elections. These numbers
feed the two "scale of the phenomenon" slides in the presentation.

Inputs:
  data/clean/zona_lawsuit_panel.csv            — all lawsuits by zone×year×subject
  data/estimation/act_design.csv  — adversarial lawsuit counts
  data/clean/electoral_admin_outcomes.csv      — registered voters, turnout, blank, null
  data/clean/office_candidate_outcomes_panel.csv — candidates and elected

Outputs:
  output/tables/descriptives/overview_lawsuits.csv
  output/tables/descriptives/overview_voters.csv
  output/tables/descriptives/overview_candidates.csv
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN        = PROJECT_ROOT / "data" / "clean"
ESTIMATION   = PROJECT_ROOT / "data" / "estimation"
OUT_DIR      = PROJECT_ROOT / "output" / "tables" / "descriptives"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2020, 2024]

# ── load ──────────────────────────────────────────────────────────────────────
print("Loading data...")

panel = pd.read_csv(
    CLEAN / "zona_lawsuit_panel.csv",
    dtype={"case_class_code": str},
    low_memory=False,
)
design = pd.read_csv(
    ESTIMATION / "act_design.csv",
    usecols=["municipality_id_tse", "competition_lawsuits_2020", "competition_lawsuits_2024"],
)
adm = pd.read_csv(CLEAN / "electoral_admin_outcomes.csv")
cand = pd.read_csv(CLEAN / "office_candidate_outcomes_panel.csv")

# ── 1. LAWSUITS ───────────────────────────────────────────────────────────────
print("\n[1] Lawsuits...")

# total lawsuits (all classes) per year, from zona panel
all_by_year = (
    panel[panel.election_year.isin(YEARS)]
    .groupby("election_year")
    .agg(
        total_lawsuits      = ("n_lawsuits",           "sum"),
        n_munis_any_lawsuit = ("municipality_id_tse",  "nunique"),
    )
    .reset_index()
)

# adversarial (competition-relevant) from design file
adv = pd.DataFrame({
    "election_year":        [2020,                                    2024],
    "adversarial_lawsuits": [design["competition_lawsuits_2020"].sum(),
                             design["competition_lawsuits_2024"].sum()],
    "n_munis_adversarial":  [(design["competition_lawsuits_2020"] > 0).sum(),
                             (design["competition_lawsuits_2024"] > 0).sum()],
})

# voter and candidate denominators (computed below; merge after)
voters_by_year = (
    adm[adm.election_year.isin(YEARS)]
    .groupby("election_year")
    .agg(
        registered_voters = ("registered_voters", "sum"),
        turnout_count     = ("turnout_count",      "sum"),
    )
    .reset_index()
)

cand_totals = (
    cand[cand.election_year.isin(YEARS)]
    .groupby("election_year")["total_candidates"]
    .sum()
    .reset_index()
    .rename(columns={"total_candidates": "total_candidates_all"})
)

lawsuits = (
    all_by_year
    .merge(adv,           on="election_year")
    .merge(voters_by_year, on="election_year")
    .merge(cand_totals,    on="election_year")
)

lawsuits["share_adversarial_pct"]        = lawsuits["adversarial_lawsuits"] / lawsuits["total_lawsuits"] * 100
lawsuits["share_munis_exposed_pct"]      = lawsuits["n_munis_adversarial"]  / 5570 * 100
lawsuits["all_lawsuits_per_candidate"]   = lawsuits["total_lawsuits"]       / lawsuits["total_candidates_all"]
lawsuits["adv_lawsuits_per_candidate"]   = lawsuits["adversarial_lawsuits"] / lawsuits["total_candidates_all"]
lawsuits["adv_per_registered_voter"]     = lawsuits["adversarial_lawsuits"] / lawsuits["registered_voters"]
lawsuits["adv_per_voter_who_voted"]      = lawsuits["adversarial_lawsuits"] / lawsuits["turnout_count"]
lawsuits["registered_voters_per_adv"]    = lawsuits["registered_voters"]    / lawsuits["adversarial_lawsuits"]
lawsuits["voters_voted_per_adv"]         = lawsuits["turnout_count"]        / lawsuits["adversarial_lawsuits"]

# drop helper columns that belong to other tables
lawsuits = lawsuits.drop(columns=["registered_voters", "turnout_count", "total_candidates_all"])
lawsuits.to_csv(OUT_DIR / "overview_lawsuits.csv", index=False)
print(lawsuits.to_string(index=False))

# ── 2. VOTERS ─────────────────────────────────────────────────────────────────
print("\n[2] Voters...")

voters = (
    adm[adm.election_year.isin(YEARS)]
    .groupby("election_year")
    .agg(
        registered_voters = ("registered_voters", "sum"),
        turnout_count     = ("turnout_count",      "sum"),
        abstentions_count = ("abstentions_count",  "sum"),
        blank_votes       = ("blank_votes",         "sum"),
        null_votes        = ("null_votes",           "sum"),
        valid_votes       = ("valid_votes",          "sum"),
        n_munis           = ("municipality_id_tse",  "nunique"),
    )
    .reset_index()
)

voters["turnout_rate_pct"]     = voters["turnout_count"]     / voters["registered_voters"] * 100
voters["abstention_rate_pct"]  = voters["abstentions_count"] / voters["registered_voters"] * 100
voters["blank_rate_pct"]       = voters["blank_votes"]       / voters["turnout_count"]      * 100
voters["null_rate_pct"]        = voters["null_votes"]        / voters["turnout_count"]      * 100
voters["valid_rate_pct"]       = voters["valid_votes"]       / voters["turnout_count"]      * 100

voters.to_csv(OUT_DIR / "overview_voters.csv", index=False)
print(voters.to_string(index=False))

# ── 3. CANDIDATES ─────────────────────────────────────────────────────────────
print("\n[3] Candidates...")

candidates = (
    cand[cand.election_year.isin(YEARS)]
    .groupby(["election_year", "office_group"])
    .apply(lambda g: pd.Series({
        "total_candidates":   g["total_candidates"].sum(),
        "elected_candidates": g["elected_candidates"].sum(),
        "female_share_pct":   (
            (g["female_share"] * g["total_candidates"]).sum()
            / g["total_candidates"].sum() * 100
        ),
        "nonwhite_share_pct": (
            (g["nonwhite_share"] * g["total_candidates"]).sum()
            / g["total_candidates"].sum() * 100
        ),
        "higher_ed_share_pct": (
            (g["higher_education_share"] * g["total_candidates"]).sum()
            / g["total_candidates"].sum() * 100
        ),
        "n_munis": g["municipality_id_tse"].nunique(),
    }), include_groups=False)
    .reset_index()
)

candidates["elected_rate_pct"] = (
    candidates["elected_candidates"] / candidates["total_candidates"] * 100
)

candidates.to_csv(OUT_DIR / "overview_candidates.csv", index=False)
print(candidates.to_string(index=False))

print("\nDone. Outputs saved to:", OUT_DIR)
