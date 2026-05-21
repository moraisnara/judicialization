from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
DERIVED_DIR    = PROJECT_ROOT / "data" / "clean"
FIGURES_DIR    = PROJECT_ROOT / "output" / "figures"
COMPONENTS_CSV = DERIVED_DIR / "municipality_bartik_components.csv"
PANEL_CSV      = DERIVED_DIR / "zona_lawsuit_panel.csv"
CROSSWALK_CSV  = DERIVED_DIR / "shift_share_subject_crosswalk.csv"

# Adversarial filter — keep in sync with 02_bartik_inputs.py
DROP_CLASSES: set[str] = {
    "11532", "12193", "12554", "11530", "12550", "12560", "1298",
    "12549", "12633", "12729", "386", "XXXJ", "12551", "11546",
    "1303", "1308", "12557", "12562",
    "156", "241", "261", "258", "278", "157", "355", "1727", "12060",
    "12248", "12121", "1116", "193", "326", "83", "10980", "335",
    "221", "325", "228", "1463", "11793", "333",
}
DROP_SUBJECTS: set[str] = {
    "12366", "11778", "12362", "11651", "12599", "12598", "11753",
    "11767", "11579", "11756", "11648", "11592", "11589", "11782",
    "11783", "11428", "-1",
    "11628", "11629", "11630", "11631", "11632", "11633", "11634",
    "11637", "11638", "11640", "11641",
    "11584", "12600", "12601",
}

FAMILY_ORDER = [
    "eligibility_ballot_access",
    "campaign_conduct",
    "information_environment",
    "abuse_misuse_office",
    "party_organization",
    "administrative_compliance",
    "electoral_administration_results",
]
FAMILY_COLORS = {
    "eligibility_ballot_access":          "#0b6e4f",
    "administrative_compliance":          "#5d6d7e",
    "party_organization":                 "#b9770e",
    "campaign_conduct":                   "#c0392b",
    "information_environment":            "#2471a3",
    "abuse_misuse_office":                "#7d3c98",
    "electoral_administration_results":   "#7f8c8d",
}


def _load_subject_family_map() -> pd.Series:
    comp = pd.read_csv(
        COMPONENTS_CSV,
        dtype={"main_subject_code": str},
        usecols=["main_subject_code", "topic_family"],
        low_memory=False,
    )
    return comp.drop_duplicates("main_subject_code").set_index("main_subject_code")["topic_family"]


def make_family_composition() -> None:
    xw = _load_subject_family_map()

    panel = pd.read_csv(
        PANEL_CSV,
        dtype={"case_class_code": str, "main_subject_code": str},
        low_memory=False,
    )
    panel = panel[panel["election_year"].isin([2020, 2024])].copy()
    panel = panel[
        ~panel["case_class_code"].isin(DROP_CLASSES) &
        ~panel["main_subject_code"].isin(DROP_SUBJECTS)
    ].copy()

    panel["topic_family"] = panel["main_subject_code"].map(xw).fillna("unmapped")
    panel["n_lawsuits"]   = pd.to_numeric(panel["n_lawsuits"], errors="coerce").fillna(0)

    grouped = (
        panel.groupby(["election_year", "topic_family"])["n_lawsuits"]
        .sum()
        .reset_index()
    )
    totals = grouped.groupby("election_year")["n_lawsuits"].transform("sum")
    grouped["share_of_year"] = grouped["n_lawsuits"] / totals.replace(0, np.nan)

    grouped = grouped[grouped["topic_family"] != "unmapped"]

    pivot = grouped.pivot(
        index="election_year", columns="topic_family", values="share_of_year"
    ).reindex(columns=[f for f in FAMILY_ORDER if f in grouped["topic_family"].unique()]).fillna(0)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    bottom = pd.Series(0.0, index=pivot.index)
    for family in pivot.columns:
        vals = pivot[family]
        ax.bar(
            pivot.index.astype(str),
            vals,
            bottom=bottom,
            color=FAMILY_COLORS.get(family, "#aaaaaa"),
            label=family.replace("_", " "),
            width=0.6,
        )
        bottom += vals

    ax.set_ylabel("Share of adversarial cases")
    ax.set_xlabel("Municipal election year")
    ax.set_ylim(0, 1)
    ax.set_title("Composition of adversarial electoral judicialization, 2020–2024")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "family_composition_2020_2024.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved: family_composition_2020_2024.png")


def make_topic_herfindahl() -> None:
    comp = pd.read_csv(COMPONENTS_CSV, dtype={"main_subject_code": str})
    comp["n_lawsuits"]   = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)

    # Importance weight per topic: mean share across municipalities
    totals = comp.groupby("municipality_id_tse")["n_lawsuits"].transform("sum")
    comp["share"] = comp["n_lawsuits"] / totals.replace(0, np.nan)
    mean_share = comp.groupby("main_subject_code")["share"].mean()

    # HHI by topic_family
    family_map = comp.drop_duplicates("main_subject_code").set_index("main_subject_code")["topic_family"]
    mean_share_df = mean_share.reset_index()
    mean_share_df["topic_family"] = mean_share_df["main_subject_code"].map(family_map)
    mean_share_df = mean_share_df[mean_share_df["topic_family"] != "unmapped"]

    total_share = mean_share_df["share"].sum()
    mean_share_df["share_norm"] = mean_share_df["share"] / total_share

    family_hhi = (
        mean_share_df.groupby("topic_family")["share_norm"]
        .apply(lambda v: (v ** 2).sum())
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    families = [f for f in FAMILY_ORDER if f in family_hhi.index]
    ax.barh(
        [f.replace("_", " ") for f in families],
        [family_hhi[f] for f in families],
        color=[FAMILY_COLORS[f] for f in families],
    )
    ax.set_xlabel("Contribution to HHI (importance-weight concentration)")
    ax.set_title("Instrument concentration by topic family (2020 shares)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "topic_family_hhi.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved: topic_family_hhi.png")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    make_family_composition()
    make_topic_herfindahl()
    print("Wrote descriptive figures.")


if __name__ == "__main__":
    main()
