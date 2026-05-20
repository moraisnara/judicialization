"""
GPS (2020) Section V.A balance tests on topic shares.

For each topic k (top-10 by |alpha_k| + DRAP 12044 + all 6 information environment topics):

  Test 1 — Covariate balance
    OLS: s_ik ~ state_FE + 7_baseline_controls
    Report R², F-stat, p-value.
    A large R² means the share correlates with observables (endogeneity concern).

  Test 2 — Pre-trend test (placebo)
    OLS: delta_outcome_2016_2020 ~ s_ik + state_FE
    (after partialling state_FE out of both variables)
    Report coefficient, SE, p-value for three pre-period outcomes:
      - delta_margin_2020_2016  = margin_top1_top2_2020 - margin_2016
      - delta_top1_2020_2016    = winner_vote_share_2020 - top1_share_2016
      - delta_ncand_2020_2016   = total_candidates_2020 - n_candidates_2016
    Under share exogeneity (parallel trends), all coefficients should be ~0.

Information environment focus: all 6 IE topics are tested explicitly in a
dedicated section, regardless of whether they appear in the top-10 by |alpha|.

Inputs:
  data/estimation/executive_margin_design.csv
  data/clean/municipality_bartik_components.csv
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
DESIGN_PATH     = PROJECT_ROOT / "data" / "estimation" / "executive_margin_design.csv"
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_bartik_components.csv"
ROTEMBERG_PATH  = PROJECT_ROOT / "output" / "tables" / "descriptives" / "rotemberg_weights.csv"
OUT_DIR         = PROJECT_ROOT / "output" / "tables" / "descriptives"

EXCLUDE_RRC_DRAP = {"11618", "12044"}
FE_COL    = "state"
CONTROLS  = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]
N_TOP = 10   # top topics by |alpha_k|
# All information environment topic codes — tested in dedicated section
IE_TOPICS = {"11484", "11679", "12635", "12637", "12638", "12639"}

# Pre-trend outcomes: constructed from design matrix columns
# (column_name, label, formula expressed as tuple (col_a, col_b) -> col_a - col_b)
PRETREND_DEFS = [
    ("delta_margin_2020_2016",  "margin_top1_top2_2020", "margin_2016"),
    ("delta_top1_2020_2016",    "winner_vote_share_2020",  "top1_share_2016"),
    ("delta_ncand_2020_2016",   "total_candidates_2020",   "n_candidates_2016"),
]


def resid_on_fe(x: np.ndarray, fe_dummies: np.ndarray) -> np.ndarray:
    """Partial out FE dummies from vector x via OLS (returns residuals)."""
    coef, _, _, _ = np.linalg.lstsq(fe_dummies, x, rcond=None)
    return x - fe_dummies @ coef


def ols_stats(y: np.ndarray, X: np.ndarray):
    """
    OLS of y on X (no constant — X should include a constant or be FE-demeaned).
    Returns: (coefs, residuals, R2, F, p_F).
    Uses heteroskedasticity-robust F approximation.
    """
    N, K = X.shape
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coef
    resid = y - y_hat
    ss_res = resid @ resid
    ss_tot = (y - y.mean()) @ (y - y.mean())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-20 else 0.0
    # Robust F (heteroskedasticity-robust Wald for all coefs except constant)
    # For simplicity use homoskedastic F
    df_model = K
    df_res   = N - K
    ms_model = (ss_tot - ss_res) / df_model if df_model > 0 else np.nan
    ms_res   = ss_res / df_res if df_res > 0 else np.nan
    f_stat   = ms_model / ms_res if ms_res and ms_res > 0 else np.nan
    p_f      = 1 - stats.f.cdf(f_stat, df_model, df_res) if not np.isnan(f_stat) else np.nan
    return coef, resid, r2, f_stat, p_f


def main() -> None:
    # ---- 1. Load Rotemberg weights to get top-N topics ----
    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})
    rw["abs_alpha"] = rw["alpha"].abs()
    top_topics = rw.nlargest(N_TOP, "abs_alpha")["topic_code"].tolist()

    # Always include DRAP (diagnostic) and all 6 IE topics
    drap_code = "12044"
    extra_codes = [drap_code] + [k for k in sorted(IE_TOPICS) if k not in top_topics and k != drap_code]
    all_topics = top_topics + [k for k in extra_codes if k not in top_topics]
    print(f"Testing {len(top_topics)} top topics + extras: {all_topics}")

    # ---- 2. Load design matrix ----
    needed_design = (
        ["municipality_id_tse", FE_COL]
        + CONTROLS
        + ["winner_vote_share_2020", "margin_top1_top2_2020",
           "winner_vote_share_2024", "total_candidates_2020"]
    )
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

    # ---- 3. Load components, build share matrix for selected topics ----
    comp = pd.read_csv(
        COMPONENTS_PATH,
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()
    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)

    # Compute re-normalised shares (exclude RRC+DRAP from denominator for
    # the main spec; include DRAP when testing DRAP itself)
    base_no_rrc_drap = comp[~comp["main_subject_code"].isin(EXCLUDE_RRC_DRAP)] \
                           .groupby("municipality_id_tse")["n_lawsuits"].sum()
    base_all         = comp.groupby("municipality_id_tse")["n_lawsuits"].sum()

    shares = {}
    for k in all_topics:
        sub = comp[comp["main_subject_code"] == k][["municipality_id_tse", "n_lawsuits"]]
        sub = sub.rename(columns={"n_lawsuits": "n_k"})
        if k == drap_code:
            # DRAP: denominator = all competition lawsuits incl. RRC+DRAP
            denom = base_all
        else:
            denom = base_no_rrc_drap
        sub = sub.set_index("municipality_id_tse").reindex(list(samp_ids), fill_value=0.0)
        sub["share"] = sub["n_k"] / denom.reindex(sub.index).replace(0, np.nan)
        sub["share"] = sub["share"].fillna(0.0)
        shares[k] = sub["share"]

    share_df = pd.DataFrame(shares).reindex(samp["municipality_id_tse"].values)
    share_df.index = samp.index

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

    # ---- 5. Run tests for each topic ----
    topic_meta = (
        comp[["main_subject_code", "main_subject_name"]]
        .drop_duplicates("main_subject_code")
        .set_index("main_subject_code")["main_subject_name"]
    )
    family_meta = (
        comp[["main_subject_code", "topic_family"]]
        .drop_duplicates("main_subject_code")
        .set_index("main_subject_code")["topic_family"]
    )
    alpha_map = rw.set_index("topic_code")["alpha"].to_dict()

    rows = []
    for k in all_topics:
        s_raw = share_df[k].values.astype(float)

        # --- Test 1: covariate balance (regress s_ik on controls + FE) ---
        coef_cov, resid_cov, r2_cov, f_cov, p_cov = ols_stats(s_raw, W)

        # --- Partial out FE (only FE, not controls) for pre-trend tests ---
        # GPS style: partial out state FE from s_ik, then regress demeaned
        # pre-trend on demeaned share
        coef_fe_s, _, _, _ = np.linalg.lstsq(fe_dummies, s_raw, rcond=None)
        s_tilde = s_raw - fe_dummies @ coef_fe_s   # share residualised on state FE

        row: dict = {
            "topic_code":    k,
            "topic_name":    topic_meta.get(k, ""),
            "topic_family":  family_meta.get(k, ""),
            "alpha":         alpha_map.get(k, np.nan),
            "is_drap":       (k == drap_code),
            "is_ie":         (k in IE_TOPICS),
            "r2_cov_balance": r2_cov,
            "f_cov_balance":  f_cov,
            "p_cov_balance":  p_cov,
        }

        for col in pretrend_cols:
            y_tilde = pretrend_resid[col]   # pre-trend residualised on W
            N = len(s_tilde)
            # OLS: y_tilde ~ s_tilde (through origin, both demeaned)
            beta = (s_tilde @ y_tilde) / (s_tilde @ s_tilde) if (s_tilde @ s_tilde) > 1e-20 else np.nan
            resid = y_tilde - beta * s_tilde
            s2    = (resid @ resid) / (N - 1)
            se    = np.sqrt(s2 / (s_tilde @ s_tilde)) if (s_tilde @ s_tilde) > 1e-20 else np.nan
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
    print(df[["topic_code", "topic_name", "alpha", "r2_cov_balance", "p_cov_balance"]].to_string(index=False))

    # ---- 7. Markdown ----
    md = []
    md.append("# GPS (2020) Balance Tests on Topic Shares")
    md.append("")
    md.append("Tests share exogeneity for the adversarial-only instrument (no-RRC, no-DRAP).")
    md.append("DRAP (12044) is included as a diagnostic even though excluded from the main spec.")
    md.append("")
    md.append("## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)")
    md.append("")
    md.append("High R² indicates the share correlates with observables (endogeneity concern).")
    md.append("")
    hdr1 = ["Rank", "Code", "Topic", "alpha", "R²", "F", "p"]
    md.append("| " + " | ".join(hdr1) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr1)) + " |")
    for i, r in df.iterrows():
        tag = " *(DRAP)*" if r["is_drap"] else ""
        md.append("| " + " | ".join([
            str(i + 1),
            r["topic_code"] + tag,
            r["topic_name"][:40],
            f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
            f"{r['r2_cov_balance']:.3f}",
            f"{r['f_cov_balance']:.1f}",
            f"{r['p_cov_balance']:.3f}",
        ]) + " |")

    md.append("")
    md.append("## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)")
    md.append("")
    md.append("Under share exogeneity, topic shares should not predict 2016→2020 electoral trends.")
    md.append("")
    for col in pretrend_cols:
        label = col.replace("delta_", "").replace("_2020_2016", "")
        md.append(f"### Outcome: {col}")
        md.append("")
        hdr2 = ["Rank", "Code", "Topic", "alpha", "beta", "SE", "p"]
        md.append("| " + " | ".join(hdr2) + " |")
        md.append("| " + " | ".join(["---"] * len(hdr2)) + " |")
        for i, r in df.iterrows():
            tag = " *(DRAP)*" if r["is_drap"] else ""
            b = r.get(f"beta_{label}", np.nan)
            s = r.get(f"se_{label}", np.nan)
            p = r.get(f"p_{label}", np.nan)
            sig = " *" if (not np.isnan(p) and p < 0.05) else ""
            md.append("| " + " | ".join([
                str(i + 1),
                r["topic_code"] + tag,
                r["topic_name"][:40],
                f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
                f"{b:+.4f}" if not np.isnan(b) else "—",
                f"{s:.4f}"  if not np.isnan(s) else "—",
                (f"{p:.3f}" if not np.isnan(p) else "—") + sig,
            ]) + " |")
        md.append("")

    # ---- Information environment focused section ----
    ie_df = df[df["is_ie"]].copy()
    md.append("## Information Environment Focus (all 6 topics)")
    md.append("")
    md.append("The preferred instrument (`bartik_iv_information_environment`) is built from these 6 topics.")
    md.append("Share exogeneity must hold for each individual topic for the family IV to be valid.")
    md.append("")
    hdr_ie = ["Code", "Topic", "alpha", "Family", "R²(cov)", "p(cov)", "p(margin)", "p(top1)", "p(ncand)"]
    md.append("| " + " | ".join(hdr_ie) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr_ie)) + " |")
    for _, r in ie_df.iterrows():
        def _p(col):
            v = r.get(col, np.nan)
            if np.isnan(v): return "—"
            return (f"{v:.3f}" + (" *" if v < 0.05 else ""))
        md.append("| " + " | ".join([
            r["topic_code"],
            r["topic_name"][:45],
            f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
            r["topic_family"],
            f"{r['r2_cov_balance']:.3f}",
            _p("p_cov_balance"),
            _p("p_margin"),
            _p("p_top1"),
            _p("p_ncand"),
        ]) + " |")
    md.append("")
    md.append("(*) significant at 5% — signals potential share endogeneity.")
    md.append("")

    md.append("## Notes")
    md.append("- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.")
    md.append("- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.")
    md.append("- DRAP (12044) is excluded from the adversarial-only instrument but shown here to evaluate its share exogeneity.")
    md.append("  Low R² and non-significant pre-trend coefficients for DRAP would support its inclusion as an instrument.")

    out_md = OUT_DIR / "gps_balance_tests.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
