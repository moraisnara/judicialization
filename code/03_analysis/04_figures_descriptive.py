from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"


def shorten(text: str, width: int = 34) -> str:
    return "\n".join(textwrap.wrap(str(text), width=width))


def make_family_composition() -> None:
    df = pd.read_csv(DERIVED_DIR / "shift_share_family_summary.csv")
    df = df[df["ANO_ELEICAO"].isin([2020, 2024])].copy()
    df = df[~df["topic_family"].isin(["unmapped"])].copy()
    order = [
        "eligibility_ballot_access",
        "administrative_compliance",
        "party_organization",
        "campaign_conduct",
        "information_environment",
        "abuse_misuse_office",
        "electoral_administration_results",
    ]
    colors = {
        "eligibility_ballot_access": "#0b6e4f",
        "administrative_compliance": "#5d6d7e",
        "party_organization": "#b9770e",
        "campaign_conduct": "#c0392b",
        "information_environment": "#2471a3",
        "abuse_misuse_office": "#7d3c98",
        "electoral_administration_results": "#7f8c8d",
    }

    pivot = (
        df.pivot(index="ANO_ELEICAO", columns="topic_family", values="share_of_year")
        .reindex(columns=order)
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bottom = pd.Series(0, index=pivot.index, dtype=float)
    for family in order:
        vals = pivot[family]
        ax.bar(
            pivot.index.astype(str),
            vals,
            bottom=bottom,
            color=colors[family],
            label=family.replace("_", " "),
            width=0.6,
        )
        bottom += vals
    ax.set_ylabel("Share of competition-related panel mass")
    ax.set_xlabel("Municipal election year")
    ax.set_ylim(0, 1)
    ax.set_title("Judicialization mass is dominated by eligibility and compliance")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "family_composition_2020_2024.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_instrument_concentration() -> None:
    df = pd.read_csv(DERIVED_DIR / "prefeito_bartik_variant_concentration.csv")
    metrics = ["top_5_share", "top_10_share", "hhi"]
    labels = ["Top 5 share", "Top 10 share", "HHI"]
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    x = range(len(metrics))
    width = 0.35
    full = df[df["variant"] == "full"].iloc[0]
    excl = df[df["variant"] == "exclude_rrc"].iloc[0]
    ax.bar([i - width / 2 for i in x], [full[m] for m in metrics], width=width, label="Full", color="#c0392b")
    ax.bar([i + width / 2 for i in x], [excl[m] for m in metrics], width=width, label="Exclude RRC", color="#0b6e4f")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Concentration")
    ax.set_title("Dropping RRC makes the Bartik much less concentrated")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "instrument_concentration_compare.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_tightened_iv_plot() -> None:
    df = pd.read_csv(DERIVED_DIR / "executive_margin_iv_clustered.csv")
    df["label"] = df["sample"].map(
        {
            "all_principal_zone_cluster": "All municipalities\nprincipal-zone cluster",
            "single_zone_exact_cluster": "Single-zone municipalities\nexact-zone cluster",
        }
    )
    outcome_map = {
        "delta_runnerup_vote_share_2024_2020": "Runner-up vote share",
        "delta_margin_top1_top2_2024_2020": "Winner-runner-up margin",
        "delta_winner_vote_share_2024_2020": "Winner vote share",
    }
    df["outcome_label"] = df["outcome"].map(outcome_map)
    ordered = [
        ("Runner-up vote share", "All municipalities\nprincipal-zone cluster"),
        ("Runner-up vote share", "Single-zone municipalities\nexact-zone cluster"),
        ("Winner-runner-up margin", "All municipalities\nprincipal-zone cluster"),
        ("Winner-runner-up margin", "Single-zone municipalities\nexact-zone cluster"),
        ("Winner vote share", "All municipalities\nprincipal-zone cluster"),
        ("Winner vote share", "Single-zone municipalities\nexact-zone cluster"),
    ]
    rows = []
    for outcome_label, label in ordered:
        rows.append(df[(df["outcome_label"] == outcome_label) & (df["label"] == label)].iloc[0])
    plot_df = pd.DataFrame(rows).reset_index(drop=True)
    plot_df["lower"] = plot_df["coef"] - 1.96 * plot_df["se"]
    plot_df["upper"] = plot_df["coef"] + 1.96 * plot_df["se"]

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    y = list(range(len(plot_df)))[::-1]
    colors = ["#0b6e4f" if fam == "primary" else "#7f8c8d" for fam in plot_df["family"]]
    for yi, coef, se, color in zip(y, plot_df["coef"], plot_df["se"], colors):
        ax.errorbar(
            coef,
            yi,
            xerr=1.96 * se,
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=2,
            capsize=3,
            markersize=5,
        )
    ax.axvline(0, color="#555555", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{o}\n{s}" for o, s in zip(plot_df["outcome_label"], plot_df["label"])])
    ax.set_xlabel("IV coefficient")
    ax.set_title("Executive vote-margin result survives clustered inference")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "executive_margin_iv_plot.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    make_family_composition()
    make_instrument_concentration()
    make_tightened_iv_plot()
    print("Wrote presentation figures.")


if __name__ == "__main__":
    main()
