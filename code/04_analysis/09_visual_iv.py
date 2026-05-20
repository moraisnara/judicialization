"""
GPS (2020) Figure 1 — Visual IV graph.

For each topic k, plot:
  x = F_k  (just-identified first-stage F using topic k component)
  y = tau_k (just-identified IV estimate using topic k)
  size  proportional to |alpha_k|
  color = sign(alpha_k): blue=positive, red=negative

Horizontal line at tau_2SLS = sum_k alpha_k * tau_k.

Interpretation: if high-weight topics scatter near tau_2SLS, the Bartik
estimate is robust. Outliers in tau_k signal that the estimate depends
heavily on a single topic's shock and its exogeneity.

Produces one panel per outcome in OUTCOMES.

Input:
  output/tables/descriptives/rotemberg_weights.csv  (must include f_stat_k)

Outputs:
  output/figures/visual_iv_{outcome_short}.pdf  (one per outcome)
  output/figures/visual_iv_grid.pdf             (2×2 grid of all outcomes)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
ROTEMBERG_PATH = PROJECT_ROOT / "output" / "tables" / "descriptives" / "rotemberg_weights.csv"
OUT_DIR        = PROJECT_ROOT / "output" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTCOMES = [
    "delta_winner_majority_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_blank_rate_2024_2020",
]
OUTCOME_LABELS = {
    "delta_winner_majority_2024_2020":  r"$\Delta$ Winner majority (binary)",
    "delta_margin_top1_top2_2024_2020": r"$\Delta$ Electoral margin (top-1 vs top-2)",
    "delta_winner_vote_share_2024_2020":r"$\Delta$ Winner vote share",
    "delta_blank_rate_2024_2020":       r"$\Delta$ Blank vote rate",
}

# Minimum marker size (points^2)
MIN_SIZE = 30
MAX_SIZE = 600

# Label topics with |alpha| > this threshold
LABEL_THRESHOLD = 0.05


def size_map(alpha: np.ndarray) -> np.ndarray:
    """Map |alpha| to marker areas in [MIN_SIZE, MAX_SIZE]."""
    a = np.abs(alpha)
    a_min, a_max = a.min(), a.max()
    if a_max == a_min:
        return np.full_like(a, (MIN_SIZE + MAX_SIZE) / 2)
    return MIN_SIZE + (MAX_SIZE - MIN_SIZE) * (a - a_min) / (a_max - a_min)


def short_label(name: str, max_len: int = 28) -> str:
    """Abbreviate topic name for figure annotations."""
    name = name.replace("Propaganda Política - Propaganda Eleitoral - ", "Prop. ")
    name = name.replace("Registro de Candidatura - ", "Reg.Cand. - ")
    name = name.replace("Inelegibilidade - ", "Inelegib. - ")
    name = name.replace("Conduta Vedada ao Agente Público", "Conduta Vedada")
    name = name.replace("Autorização de Divulgação de Publicidade Institucional",
                        "Pub. Institucional")
    return name[:max_len]


def plot_panel(ax, rw: pd.DataFrame, outcome_col: str, tau_2sls: float,
               title: str) -> None:
    tau_col = f"tau_{outcome_col}"
    if tau_col not in rw.columns:
        ax.set_visible(False)
        return

    df = rw.dropna(subset=[tau_col, "f_stat_k", "alpha"]).copy()
    pos = df["alpha"] > 0
    neg = df["alpha"] <= 0

    sizes = size_map(df["alpha"].values)

    # Scatter: positive alpha = steelblue, negative = tomato
    ax.scatter(
        df.loc[pos, "f_stat_k"], df.loc[pos, tau_col],
        s=sizes[pos.values], c="steelblue", alpha=0.75, edgecolors="white",
        linewidths=0.4, zorder=3, label=r"$\alpha_k > 0$",
    )
    ax.scatter(
        df.loc[neg, "f_stat_k"], df.loc[neg, tau_col],
        s=sizes[neg.values], c="tomato", alpha=0.75, edgecolors="white",
        linewidths=0.4, zorder=3, label=r"$\alpha_k \leq 0$",
    )

    # tau_2SLS horizontal reference line
    ax.axhline(tau_2sls, color="black", linestyle="--", linewidth=1.2,
               zorder=2, label=rf"$\tau_{{2SLS}} = {tau_2sls:.3f}$")

    # Weak instrument F thresholds
    ax.axvline(10, color="gray", linestyle=":", linewidth=0.8, zorder=1)
    ax.text(10.3, ax.get_ylim()[1] if ax.get_ylim()[1] != 0 else 0.1,
            "F=10", fontsize=6, color="gray", va="top")

    # Label high-alpha topics
    for _, row in df[df["alpha"].abs() > LABEL_THRESHOLD].iterrows():
        ax.annotate(
            short_label(str(row.get("topic_name", row["topic_code"]))),
            xy=(row["f_stat_k"], row[tau_col]),
            xytext=(6, 3), textcoords="offset points",
            fontsize=5.5, color="black",
            arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
        )

    ax.set_xlabel(r"First-stage $F_k$ (just-identified)", fontsize=8)
    ax.set_ylabel(r"$\tau_k$ (just-identified IV)", fontsize=8)
    ax.set_title(title, fontsize=8)
    ax.legend(fontsize=6, loc="upper right")
    ax.tick_params(labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})

    # Verify f_stat_k column exists
    if "f_stat_k" not in rw.columns:
        raise ValueError(
            "rotemberg_weights.csv is missing 'f_stat_k'. "
            "Run 05_rotemberg_weights.py first."
        )

    avail = [o for o in OUTCOMES if f"tau_{o}" in rw.columns]
    print(f"Available outcomes: {avail}")

    # ---- Individual panels ----
    for out in avail:
        tau_col = f"tau_{out}"
        tau_2sls = (rw["alpha"] * rw[tau_col]).sum()
        label = OUTCOME_LABELS.get(out, out)
        short = out.replace("delta_", "").replace("_2024_2020", "")

        fig, ax = plt.subplots(figsize=(5.5, 4.2))
        plot_panel(ax, rw, out, tau_2sls, label)
        fig.tight_layout()
        out_path = OUT_DIR / f"visual_iv_{short}.pdf"
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out_path.relative_to(PROJECT_ROOT)}")

    # ---- 2x2 grid ----
    if len(avail) >= 2:
        ncols = 2
        nrows = (len(avail) + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(10, 4 * nrows))
        axes_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

        for idx, out in enumerate(avail):
            tau_col = f"tau_{out}"
            tau_2sls = (rw["alpha"] * rw[tau_col]).sum()
            label = OUTCOME_LABELS.get(out, out)
            plot_panel(axes_flat[idx], rw, out, tau_2sls, label)

        # Hide any unused axes
        for ax in axes_flat[len(avail):]:
            ax.set_visible(False)

        # Size legend (manual)
        legend_alphas = [0.05, 0.15, 0.40]
        legend_sizes  = size_map(np.array(legend_alphas))
        legend_handles = [
            mpatches.Circle((0, 0), radius=np.sqrt(s / np.pi) / 10,
                            color="gray", alpha=0.6,
                            label=rf"$|\alpha_k|={a:.2f}$")
            for s, a in zip(legend_sizes, legend_alphas)
        ]
        fig.legend(
            handles=legend_handles,
            title=r"Bubble size $\propto |\alpha_k|$",
            loc="lower center", ncol=3, fontsize=7, title_fontsize=7,
            bbox_to_anchor=(0.5, -0.02),
        )

        fig.suptitle(
            "GPS (2020) Visual IV — Adversarial-Only Bartik IV\n"
            r"$\tau_k$ vs $F_k$ per topic; bubble area $\propto |\alpha_k|$",
            fontsize=9,
        )
        fig.tight_layout(rect=[0, 0.04, 1, 0.96])
        grid_path = OUT_DIR / "visual_iv_grid.pdf"
        fig.savefig(grid_path, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {grid_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
