"""
BHJ (2024) checklist item 5 — shift descriptives table.

For each topic k, report:
  - national leave-state-out shift g_k (mean across municipalities, after
    excluding own state)
  - importance weight s_k_bar (mean share across municipalities, after
    RRC+DRAP exclusion and share re-normalisation)
  - contribution to HHI = sum_k s_k_bar^2

Summary: HHI, K_eff = 1/HHI, n positive vs negative shocks.

Inputs:
  data/clean/municipality_bartik_components.csv
  data/estimation/executive_margin_design.csv  (for sample N)

Outputs:
  output/tables/descriptives/shift_descriptives.csv
  output/tables/descriptives/shift_descriptives.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_bartik_components.csv"
DESIGN_PATH     = PROJECT_ROOT / "data" / "estimation" / "executive_margin_design.csv"
OUT_DIR         = PROJECT_ROOT / "output" / "tables" / "descriptives"

EXCLUDE_RRC_DRAP = {"11618", "12044"}


def main() -> None:
    # ---- 1. Load analysis sample to restrict to N=5,560 ----
    design = pd.read_csv(
        DESIGN_PATH,
        dtype={"municipality_id_tse": str},
        low_memory=False,
        usecols=["municipality_id_tse", "bartik_iv_no_rrc_drap"],
    )
    design["municipality_id_tse"] = design["municipality_id_tse"].astype(str).str.zfill(5)
    samp_ids = set(design.dropna(subset=["bartik_iv_no_rrc_drap"])["municipality_id_tse"])
    N = len(samp_ids)
    print(f"Analysis sample: {N:,} municipalities")

    # ---- 2. Load components, apply exclusions, re-normalise shares ----
    comp = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)

    # Keep only rows in sample
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()

    # Exclude RRC and DRAP
    comp = comp[~comp["main_subject_code"].isin(EXCLUDE_RRC_DRAP)].copy()

    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)
    comp["shock"]      = pd.to_numeric(
        comp["shock_log_growth_2020_2024"], errors="coerce"
    ).fillna(0)

    # Re-normalise shares after exclusion
    base_totals = comp.groupby("municipality_id_tse")["n_lawsuits"].transform("sum")
    comp["share"] = comp["n_lawsuits"] / base_totals.replace(0, np.nan)

    topics = sorted(comp["main_subject_code"].unique())
    K = len(topics)
    print(f"Topics after exclusion: {K}")

    # ---- 3. Per-topic statistics ----
    rows = []
    for k in topics:
        sub = comp[comp["main_subject_code"] == k].copy()
        # Drop rows where municipality had 0 total lawsuits (undefined share)
        sub = sub.dropna(subset=["share"])

        n_munis = sub["municipality_id_tse"].nunique()

        # Importance weight: mean share across ALL municipalities in sample
        # (municipalities with 0 lawsuits in topic k have share=0, not NaN,
        #  so we use the full N denominator via pivot later)
        mean_share_local = sub["share"].mean()   # among municipalities that have topic k

        g_mean  = sub["shock"].mean()
        g_sd    = sub["shock"].std()
        g_p10   = sub["shock"].quantile(0.10)
        g_p25   = sub["shock"].quantile(0.25)
        g_p50   = sub["shock"].median()
        g_p75   = sub["shock"].quantile(0.75)
        g_p90   = sub["shock"].quantile(0.90)

        topic_name   = sub["main_subject_name"].iloc[0]
        topic_family = sub["topic_family"].iloc[0] if "topic_family" in sub.columns else ""

        rows.append({
            "topic_code":   k,
            "topic_name":   topic_name,
            "topic_family": topic_family,
            "n_munis":      n_munis,
            "g_mean":       g_mean,
            "g_sd":         g_sd,
            "g_p10":        g_p10,
            "g_p25":        g_p25,
            "g_p50":        g_p50,
            "g_p75":        g_p75,
            "g_p90":        g_p90,
            "mean_share_local": mean_share_local,
        })

    df = pd.DataFrame(rows)

    # ---- 4. Importance weights over all N municipalities ----
    # Build full municipality × topic share matrix (zeros for absent topics)
    pivot = comp.pivot_table(
        index="municipality_id_tse",
        columns="main_subject_code",
        values="share",
        fill_value=0.0,
    ).reindex(list(samp_ids), fill_value=0.0)

    # s_k_bar = mean share across all N municipalities (including those with 0)
    s_k_bar = pivot.mean(axis=0)           # Series indexed by topic code

    # Normalise so sum = 1 (should already be ~1 if shares sum to 1 per municipality)
    s_k_bar_norm = s_k_bar / s_k_bar.sum()

    df["s_k_bar"] = df["topic_code"].map(s_k_bar)
    df["s_k_bar_norm"] = df["topic_code"].map(s_k_bar_norm)
    df["s_k_bar2"] = df["s_k_bar_norm"] ** 2   # contribution to HHI

    hhi    = df["s_k_bar2"].sum()
    k_eff  = 1.0 / hhi
    n_pos  = (df["g_mean"] > 0).sum()
    n_neg  = (df["g_mean"] < 0).sum()
    print(f"\nHHI (importance weights) = {hhi:.4f}  ->  K_eff = {k_eff:.2f}")
    print(f"Topics with positive mean shift: {n_pos} / {K}")
    print(f"Topics with negative mean shift: {n_neg} / {K}")

    # Sort by |s_k_bar_norm| descending
    df = df.sort_values("s_k_bar_norm", ascending=False).reset_index(drop=True)

    # ---- 5. CSV output ----
    out_csv = OUT_DIR / "shift_descriptives.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")

    # ---- 6. Markdown output ----
    md = []
    md.append("# Shift Descriptives — Adversarial-Only (No-RRC, No-DRAP) Bartik IV")
    md.append("")
    md.append("BHJ (2024) checklist item 5: distribution of shifts g_k and importance weights s_k_bar.")
    md.append("")
    md.append(f"**K** = {K} topics | **N** = {N:,} municipalities")
    md.append(f"| HHI (importance) | K_eff | Positive shifts | Negative shifts |")
    md.append(f"| --- | --- | --- | --- |")
    md.append(f"| {hhi:.4f} | {k_eff:.2f} | {n_pos} | {n_neg} |")
    md.append("")
    md.append("## Per-Topic Statistics (sorted by importance weight)")
    md.append("")
    hdr = ["Code", "Topic (truncated)", "Family", "N munis",
           "s̄_k (%)", "g_mean", "g_sd", "g_p10", "g_p50", "g_p90", "HHI contrib"]
    md.append("| " + " | ".join(hdr) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for _, r in df.iterrows():
        md.append("| " + " | ".join([
            r["topic_code"],
            r["topic_name"][:40],
            r["topic_family"][:20] if r["topic_family"] else "",
            str(int(r["n_munis"])),
            f"{r['s_k_bar_norm']*100:.2f}%",
            f"{r['g_mean']:+.3f}",
            f"{r['g_sd']:.3f}",
            f"{r['g_p10']:+.3f}",
            f"{r['g_p50']:+.3f}",
            f"{r['g_p90']:+.3f}",
            f"{r['s_k_bar2']:.4f}",
        ]) + " |")
    md.append("")
    md.append("## Notes")
    md.append("- `s̄_k` = mean share of topic k across all N municipalities (including zeros), re-normalised to sum to 1.")
    md.append("- `g_k` = leave-state-out log growth 2020→2024 for topic k; values vary by municipality (own-state excluded).")
    md.append("  Statistics above are computed across municipalities that have the topic in 2020.")
    md.append("- **HHI** = Σ_k (s̄_k)² — measures concentration of instrument in few topics.")
    md.append("  K_eff = 1/HHI is the effective number of topics driving the Bartik estimate.")
    md.append("- BHJ (2024) criterion: K_eff >> 1 needed for exposure-robust SE asymptotics.")
    md.append(f"  Here K_eff = {k_eff:.2f} → GPS share-exogeneity identification is the primary justification.")

    out_md = OUT_DIR / "shift_descriptives.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
