"""
Goldsmith-Pinkham, Sorkin & Swift (2020, AER) Rotemberg-weight decomposition
for the adversarial Bartik shift-share IV (administrative and procedural
classes/subjects excluded at build stage).

For each topic k, the Rotemberg weight alpha_k and the just-identified
IV estimate tau_k are computed so that tau_IV = sum_k alpha_k * tau_k.

Inputs:
  data/estimation/executive_margin_design.csv
  data/clean/municipality_bartik_components.csv

Output:
  output/tables/descriptives/rotemberg_weights.csv
  output/tables/descriptives/rotemberg_weights.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
DESIGN_PATH     = PROJECT_ROOT / "data" / "estimation" / "executive_margin_design.csv"
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_bartik_components.csv"
OUT_DIR         = PROJECT_ROOT / "output" / "tables" / "descriptives"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENDOGENOUS = "delta_log1p_competition_lawsuits_2024_2020"
INSTRUMENT = "bartik_iv_2020_2024"
FE_COL     = "state"

BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]

# Outcomes to decompose (significant and primary)
OUTCOMES = [
    "delta_winner_majority_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_blank_rate_2024_2020",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def partial_out(
    df: pd.DataFrame,
    cols: list[str],
    controls: list[str],
    fe_col: str,
) -> pd.DataFrame:
    """
    Return residuals after projecting each column in `cols` onto
    state FE dummies + `controls` via OLS.
    """
    fe_dummies = pd.get_dummies(df[fe_col], drop_first=True).astype(float)
    ctrl_vals  = df[controls].astype(float)
    W = np.hstack([fe_dummies.values, ctrl_vals.values])  # (N, K)

    WtW_inv_Wt = np.linalg.lstsq(W, np.eye(len(df)), rcond=None)[0]  # (K, N)
    proj = W @ WtW_inv_Wt                                              # (N, N)
    M    = np.eye(len(df)) - proj                                      # annihilator

    data_mat = df[cols].astype(float).values                           # (N, C)
    resids   = M @ data_mat                                            # (N, C)
    return pd.DataFrame(resids, index=df.index, columns=cols)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- 1. Load design ----
    design = pd.read_csv(
        DESIGN_PATH,
        dtype={"municipality_id_tse": str},
        low_memory=False,
    )

    need = [ENDOGENOUS, INSTRUMENT, FE_COL] + BASELINE_CONTROLS
    avail_outcomes = [o for o in OUTCOMES if o in design.columns]
    need += avail_outcomes

    samp = design[need].dropna().copy().reset_index(drop=True)
    samp["municipality_id_tse"] = samp["municipality_id_tse"].str.zfill(5) \
        if "municipality_id_tse" in samp.columns else samp.index.astype(str)

    # municipality_id_tse is a column or index — handle both cases
    if "municipality_id_tse" not in samp.columns:
        samp = design[["municipality_id_tse"] + need].dropna().copy().reset_index(drop=True)
    else:
        samp = design[["municipality_id_tse"] + need].dropna().copy().reset_index(drop=True)

    samp["municipality_id_tse"] = samp["municipality_id_tse"].astype(str).str.zfill(5)
    print(f"Analysis sample: {len(samp):,} municipalities")

    # ---- 2. Load components, build no-RRC Bartik matrix ----
    comp = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)

    # Shares already reflect adversarial filter applied at build stage
    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)
    comp["shock"]      = pd.to_numeric(
        comp["shock_log_growth_2020_2024"], errors="coerce"
    ).fillna(0)
    base_totals = comp.groupby("municipality_id_tse")["n_lawsuits"].transform("sum")
    comp["share"] = comp["n_lawsuits"] / base_totals.replace(0, np.nan)
    comp["z_component"] = comp["share"] * comp["shock"]

    # Keep only municipalities in the analysis sample
    samp_ids = set(samp["municipality_id_tse"])
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()

    # ---- 3. Pivot to municipality × topic matrix ----
    pivot = comp.pivot_table(
        index="municipality_id_tse",
        columns="main_subject_code",
        values="z_component",
        fill_value=0.0,
    )
    pivot = pivot.reindex(samp["municipality_id_tse"]).fillna(0.0)
    topic_codes = list(pivot.columns)
    print(f"Topics in adversarial instrument: {len(topic_codes)}")

    # ---- 4. Assemble combined frame and partial out ----
    samp_indexed = samp.set_index("municipality_id_tse")
    pivot.index.name = "municipality_id_tse"
    combined = samp_indexed.join(pivot, how="inner")

    scalar_cols = [ENDOGENOUS, INSTRUMENT] + avail_outcomes
    all_cols    = scalar_cols + topic_codes

    print("Partialling out controls and state FE …")
    resid_df = partial_out(combined, all_cols, BASELINE_CONTROLS, FE_COL)

    d_tilde  = resid_df[ENDOGENOUS].values          # (N,)  residualised endog

    # GPS (2020) correct alpha_k:
    # alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)
    # Z_tilde = sum_k z_k_tilde (exact by linearity of M), so sum_k alpha_k = 1.
    # Use the sum of topic columns as denominator — not the design's bartik_iv —
    # to avoid any mismatch in share normalization between the two sources.
    Z_sum_tilde = resid_df[topic_codes].values.sum(axis=1)  # exact by construction
    Zd = Z_sum_tilde @ d_tilde                              # denominator for weights

    # ---- 5. Rotemberg weights and just-identified IV estimates ----
    topic_names = (
        comp[["main_subject_code", "main_subject_name"]]
        .drop_duplicates("main_subject_code")
        .set_index("main_subject_code")["main_subject_name"]
    )

    N = len(d_tilde)
    rows = []
    for k in topic_codes:
        zk   = resid_df[k].values         # residualised topic component
        zk_D = zk @ d_tilde               # first-stage numerator for topic k
        zk_zk = zk @ zk                   # sum of squares of instrument

        alpha_k = zk_D / Zd               # GPS Rotemberg weight

        # Just-identified first-stage F_k (regression through origin, df = N-1)
        if zk_zk > 1e-20:
            beta_k  = zk_D / zk_zk
            ssr_k   = d_tilde @ d_tilde - zk_D ** 2 / zk_zk
            s2_k    = ssr_k / (N - 1)
            f_k     = beta_k ** 2 * zk_zk / s2_k
        else:
            f_k = np.nan

        row: dict = {
            "topic_code": k,
            "topic_name": topic_names.get(k, ""),
            "alpha":      alpha_k,
            "f_stat_k":   f_k,
        }
        for out in avail_outcomes:
            y_tilde = resid_df[out].values
            zk_Y    = zk @ y_tilde
            row[f"tau_{out}"] = zk_Y / zk_D if abs(zk_D) > 1e-12 else np.nan

        rows.append(row)

    rw = pd.DataFrame(rows)
    print(f"\nSum of alpha_k: {rw['alpha'].sum():.6f}  (should be 1.0)")

    # Verify: tau_2SLS = sum_k alpha_k * tau_k
    for out in avail_outcomes:
        tau_col  = f"tau_{out}"
        tau_check = (rw["alpha"] * rw[tau_col]).sum()
        print(f"  {out}: IV check = {tau_check:.4f}")

    # ---- 6. Sort, summarise, save ----
    rw = rw.sort_values("alpha", ascending=False).reset_index(drop=True)
    rw["alpha_pct"]    = rw["alpha"] * 100
    rw["cum_alpha"]    = rw["alpha"].cumsum()

    hhi = (rw["alpha"] ** 2).sum()
    n_positive = (rw["alpha"] > 0).sum()
    print(f"\nHHI of Rotemberg weights: {hhi:.4f}")
    print(f"Number of topics with positive weight: {n_positive} / {len(rw)}")
    print(f"\nTop 10 topics by Rotemberg weight:")
    display_cols = ["topic_code", "topic_name", "alpha_pct", "cum_alpha", "f_stat_k"] + \
                   [f"tau_{o}" for o in avail_outcomes]
    print(rw[display_cols].head(10).to_string(index=False))

    # ---- 7. Write CSV ----
    out_csv = OUT_DIR / "rotemberg_weights.csv"
    rw.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")

    # ---- 8. Write markdown summary ----
    top10 = rw.head(10).copy()
    top10["alpha_pct"]  = top10["alpha_pct"].map(lambda x: f"{x:+.1f}%")
    top10["cum_alpha"]  = top10["cum_alpha"].map(lambda x: f"{x:.2f}")
    for out in avail_outcomes:
        col = f"tau_{out}"
        short = out.replace("delta_", "").replace("_2024_2020", "")
        top10 = top10.rename(columns={col: short})

    md_rows = []
    md_rows.append(f"# Rotemberg Weights — Adversarial Bartik IV")
    md_rows.append(f"")
    md_rows.append(f"GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.")
    md_rows.append(f"")
    md_rows.append(f"**HHI** = {hhi:.4f} | "
                   f"**Positive-weight topics** = {n_positive} / {len(rw)}")
    md_rows.append(f"")
    md_rows.append(f"## Top 10 Topics by Rotemberg Weight")
    md_rows.append(f"")

    hdr = ["Rank", "Code", "Topic", "alpha (%)", "Cum.", "F_k"] + \
          [o.replace("delta_","").replace("_2024_2020","") for o in avail_outcomes]
    md_rows.append("| " + " | ".join(hdr) + " |")
    md_rows.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for i, row in top10.iterrows():
        fk = row.get("f_stat_k", np.nan)
        vals = [
            str(i + 1),
            row["topic_code"],
            row["topic_name"][:45],
            row["alpha_pct"],
            row["cum_alpha"],
            f"{fk:.1f}" if not np.isnan(fk) else "—",
        ]
        for o in avail_outcomes:
            short = o.replace("delta_", "").replace("_2024_2020", "")
            v = row.get(short, np.nan)
            vals.append(f"{v:.3f}" if not np.isnan(v) else "—")
        md_rows.append("| " + " | ".join(vals) + " |")

    md_rows += [
        "",
        "## Notes",
        "- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.",
        "- `tau_k` = just-identified IV using topic k alone as instrument.",
        "- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).",
        "- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).",
    ]

    out_md = OUT_DIR / "rotemberg_weights.md"
    out_md.write_text("\n".join(md_rows), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
