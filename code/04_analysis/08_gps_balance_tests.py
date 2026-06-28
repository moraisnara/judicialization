"""
GPS (2020) Section V.A balance tests on topic-FAMILY shares.

The shift-share instrument is built at the topic-family level (SIG family
crosswalk, headline rung theme9 = 9 kept families). Shares = municipality 2020
family portfolio (share2020). For each family k we test:

  Test 1 — Covariate balance
    OLS: s_ik ~ state_FE + 7_baseline_controls
    Report R², F-stat, p-value.
    A large R² means the family share correlates with observables
    (endogeneity concern).

  Test 2 — Pre-trend test (placebo)
    OLS: delta_outcome_2016_2020 ~ s_ik | state_FE
    (state FE partialled out of both variables first)
    Pre-period outcomes:
      - delta_margin_2020_2016  = margin_top1_top2_2020 - margin_2016
      - delta_top1_2020_2016    = winner_vote_share_2020 - top1_share_2016
      - delta_ncand_2020_2016   = total_candidates_2020 - n_candidates_2016
    Under share exogeneity (parallel trends), all coefficients should be ~0.

All 9 theme9 families are tested (the build-stage crosswalk already drops the
mandatory-filing classes — RRC/DRAP/prestação de contas — so no share
re-normalisation is needed here).

Inputs:
  data/estimation/act_design.csv
  data/clean/municipality_act_components.csv  (SIG family components, long)
  output/tables/descriptives/rotemberg_weights.csv

Outputs:
  output/tables/descriptives/gps_balance_tests.csv
  output/tables/descriptives/gps_balance_tests.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
DESIGN_PATH     = PROJECT_ROOT / "data" / "estimation" / "act_design.csv"
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_act_components.csv"
RUNG            = "act"   # headline family taxonomy (matches HEADLINE_RUNG)
ROTEMBERG_PATH  = PROJECT_ROOT / "output" / "tables" / "descriptives" / "rotemberg_weights.csv"
OUT_DIR         = PROJECT_ROOT / "output" / "tables" / "descriptives"

FE_COL    = "state"
CONTROLS  = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]

# Pre-trend outcomes: constructed from design matrix columns
# (column_name, label, formula expressed as tuple (col_a, col_b) -> col_a - col_b)
PRETREND_DEFS = [
    ("delta_margin_2020_2016",  "margin_top1_top2_2020", "margin_2016"),
    ("delta_top1_2020_2016",    "winner_vote_share_2020",  "top1_share_2016"),
    ("delta_ncand_2020_2016",   "total_candidates_2020",   "n_candidates_2016"),
]


def ols_stats(y: np.ndarray, X: np.ndarray):
    """
    OLS of y on X (X should be FE-demeaned / include a constant).
    Returns: (coefs, residuals, R2, F, p_F). Homoskedastic F.
    """
    N, K = X.shape
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coef
    resid = y - y_hat
    ss_res = resid @ resid
    ss_tot = (y - y.mean()) @ (y - y.mean())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-20 else 0.0
    df_model = K
    df_res   = N - K
    ms_model = (ss_tot - ss_res) / df_model if df_model > 0 else np.nan
    ms_res   = ss_res / df_res if df_res > 0 else np.nan
    f_stat   = ms_model / ms_res if ms_res and ms_res > 0 else np.nan
    p_f      = 1 - stats.f.cdf(f_stat, df_model, df_res) if not np.isnan(f_stat) else np.nan
    return coef, resid, r2, f_stat, p_f


def main() -> None:
    # ---- 1. Load Rotemberg weights for family alpha map ----
    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})
    alpha_map = rw.set_index("topic_code")["alpha"].to_dict()

    # ---- 2. Load design matrix ----
    design = pd.read_csv(
        DESIGN_PATH,
        dtype={"municipality_id_tse": str},
        low_memory=False,
    )
    design["municipality_id_tse"] = design["municipality_id_tse"].astype(str).str.zfill(5)

    # Construct pre-trend outcomes
    for (new_col, col_a, col_b) in PRETREND_DEFS:
        if col_a in design.columns and col_b in design.columns:
            design[new_col] = pd.to_numeric(design[col_a], errors="coerce") - \
                              pd.to_numeric(design[col_b], errors="coerce")
        else:
            print(f"Warning: could not construct {new_col} ({col_a} or {col_b} missing)")

    pretrend_cols = [d[0] for d in PRETREND_DEFS if d[0] in design.columns]

    needed = (["municipality_id_tse", FE_COL] + CONTROLS + pretrend_cols)
    samp = design[needed].dropna().copy().reset_index(drop=True)
    samp_ids = set(samp["municipality_id_tse"])
    print(f"Sample after dropping NAs: {len(samp):,} municipalities")

    # ---- 3. Load components, build family share matrix (2020 portfolio) ----
    comp = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"id_municipio_tse": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["id_municipio_tse"].str.strip().str.zfill(5)
    comp = comp[comp["rung"] == RUNG].copy()
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()

    # share2020 is the municipality's 2020 family-portfolio share (kept families)
    share_long = (
        comp.drop_duplicates(["municipality_id_tse", "family"])
        .pivot_table(
            index="municipality_id_tse",
            columns="family",
            values="share2020",
            fill_value=0.0,
        )
    )
    families = sorted(share_long.columns)
    share_df = share_long.reindex(samp["municipality_id_tse"].values).fillna(0.0)
    share_df.index = samp.index
    print(f"Testing {len(families)} families: {families}")

    # ---- 4. Build FE dummies and partial-out matrix ----
    fe_dummies = pd.get_dummies(samp[FE_COL], drop_first=True).astype(float).values
    ctrl_mat   = samp[CONTROLS].astype(float).values
    W = np.hstack([fe_dummies, ctrl_mat])  # (N, K_controls)

    # Partial out W from each pretrend outcome once
    pretrend_resid = {}
    for col in pretrend_cols:
        y_raw = samp[col].astype(float).values
        coef, _, _, _ = np.linalg.lstsq(W, y_raw, rcond=None)
        pretrend_resid[col] = y_raw - W @ coef

    # ---- 5. Run tests for each family ----
    rows = []
    for k in families:
        s_raw = share_df[k].values.astype(float)

        # --- Test 1: covariate balance (regress s_ik on controls + FE) ---
        coef_cov, resid_cov, r2_cov, f_cov, p_cov = ols_stats(s_raw, W)

        # --- Partial out FE only for the pre-trend tests ---
        coef_fe_s, _, _, _ = np.linalg.lstsq(fe_dummies, s_raw, rcond=None)
        s_tilde = s_raw - fe_dummies @ coef_fe_s   # share residualised on state FE

        row: dict = {
            "topic_family":   k,
            "alpha":          alpha_map.get(k, np.nan),
            "r2_cov_balance": r2_cov,
            "f_cov_balance":  f_cov,
            "p_cov_balance":  p_cov,
        }

        for col in pretrend_cols:
            y_tilde = pretrend_resid[col]
            N = len(s_tilde)
            sts = s_tilde @ s_tilde
            beta = (s_tilde @ y_tilde) / sts if sts > 1e-20 else np.nan
            resid = y_tilde - beta * s_tilde
            s2    = (resid @ resid) / (N - 1)
            se    = np.sqrt(s2 / sts) if sts > 1e-20 else np.nan
            t     = beta / se if se and se > 0 else np.nan
            p     = 2 * (1 - stats.t.cdf(abs(t), df=N - 1)) if not np.isnan(t) else np.nan
            label = col.replace("delta_", "").replace("_2020_2016", "")
            row[f"beta_{label}"]  = beta
            row[f"se_{label}"]    = se
            row[f"p_{label}"]     = p

        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values("alpha", ascending=False, key=lambda x: x.abs()).reset_index(drop=True)

    # ---- 6. CSV ----
    out_csv = OUT_DIR / "gps_balance_tests.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")
    print(df[["topic_family", "alpha", "r2_cov_balance", "p_cov_balance"]].to_string(index=False))

    # ---- 7. Markdown ----
    md = []
    md.append("# GPS (2020) Balance Tests on Topic-Family Shares")
    md.append("")
    md.append("Tests share exogeneity for the family-level shift-share instrument")
    md.append("(SIG family crosswalk, headline rung theme9 = 9 kept families; mandatory-filing classes dropped at build stage).")
    md.append("")
    md.append("## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)")
    md.append("")
    md.append("High R² indicates the family share correlates with observables (endogeneity concern).")
    md.append("")
    hdr1 = ["Rank", "Family", "alpha", "R²", "F", "p"]
    md.append("| " + " | ".join(hdr1) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr1)) + " |")
    for i, r in df.iterrows():
        md.append("| " + " | ".join([
            str(i + 1),
            r["topic_family"],
            f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
            f"{r['r2_cov_balance']:.3f}",
            f"{r['f_cov_balance']:.1f}",
            f"{r['p_cov_balance']:.3f}",
        ]) + " |")

    md.append("")
    md.append("## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)")
    md.append("")
    md.append("Under share exogeneity, family shares should not predict 2016→2020 electoral trends.")
    md.append("")
    for col in pretrend_cols:
        label = col.replace("delta_", "").replace("_2020_2016", "")
        md.append(f"### Outcome: {col}")
        md.append("")
        hdr2 = ["Rank", "Family", "alpha", "beta", "SE", "p"]
        md.append("| " + " | ".join(hdr2) + " |")
        md.append("| " + " | ".join(["---"] * len(hdr2)) + " |")
        for i, r in df.iterrows():
            b = r.get(f"beta_{label}", np.nan)
            s = r.get(f"se_{label}", np.nan)
            p = r.get(f"p_{label}", np.nan)
            sig = " *" if (not np.isnan(p) and p < 0.05) else ""
            md.append("| " + " | ".join([
                str(i + 1),
                r["topic_family"],
                f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
                f"{b:+.4f}" if not np.isnan(b) else "—",
                f"{s:.4f}"  if not np.isnan(s) else "—",
                (f"{p:.3f}" if not np.isnan(p) else "—") + sig,
            ]) + " |")
        md.append("")

    md.append("## Notes")
    md.append("- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.")
    md.append("- Family shares = baseline_share_2020 (municipality 2020 family portfolio).")
    md.append("- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.")
    md.append("- (*) significant at 5% — signals potential share endogeneity.")

    out_md = OUT_DIR / "gps_balance_tests.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
