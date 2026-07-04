"""
04_iv_diagnostics.py — shift-share IV diagnostics for the adversarial Bartik
instrument (merged). Two sections run IN ORDER because the second consumes the
CSV the first writes:

  [A] rotemberg_weights()   — GPS (2020) Rotemberg-weight decomposition
        tau_IV = sum_k alpha_k * tau_k; per-topic alpha_k, F_k, tau_k.
        -> descriptives/rotemberg_weights.csv

  [B] gps_balance_tests()   — GPS (2020) Section V.A share-exogeneity tests
        (covariate balance + pre-trend placebo) for top-|alpha| + IE topics.
        reads rotemberg_weights.csv  -> descriptives/gps_balance_tests.csv

Exposure-robust (AKM 2019 / BHJ 2022) SEs are computed separately, in R, by
code/04_analysis/07_exposure_robust_se.R (regressions-in-R rule). The former
Python [C] heuristic here measured per-topic IV-coefficient dispersion rather
than sampling variance and has been removed.

Inputs:
  data/estimation/executive_margin_design.csv
  data/clean/municipality_bartik_components.csv
  output/tables/regressions/executive_margin_first_stage_fixest.csv
  output/tables/regressions/executive_margin_iv_fixest.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
DESIGN_PATH     = PROJECT_ROOT / "data" / "estimation" / "executive_margin_design.csv"
COMPONENTS_PATH = PROJECT_ROOT / "data" / "clean" / "municipality_bartik_components.csv"
DESC_DIR        = PROJECT_ROOT / "output" / "tables" / "descriptives"
REG_DIR         = PROJECT_ROOT / "output" / "tables" / "regressions"
ROTEMBERG_PATH  = DESC_DIR / "rotemberg_weights.csv"
DESC_DIR.mkdir(parents=True, exist_ok=True)
REG_DIR.mkdir(parents=True, exist_ok=True)

ENDOGENOUS = "delta_log1p_competition_lawsuits_2024_2020"
INSTRUMENT = "bartik_iv_2020_2024"
FE_COL     = "state"
BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]


# ============================================================================
# [A] ROTEMBERG WEIGHTS — GPS (2020) decomposition
# ============================================================================
ROT_OUTCOMES = [
    "delta_winner_majority_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_blank_rate_2024_2020",
]
# Headline = ANCOVA on the 2016 pre-window baseline: the decomposed dependent
# variable is the 2024 LEVEL, residualised on controls PLUS its own 2016 level.
# The Rotemberg WEIGHTS (alpha_k, K_eff) are first-stage objects — unchanged by
# the outcome form — so only the per-topic outcome estimates tau_k use ANCOVA.
ANCOVA_LEVEL = {
    "delta_winner_majority_2024_2020":   ("winner_majority_2024",   "winner_majority_2016"),
    "delta_margin_top1_top2_2024_2020":  ("margin_top1_top2_2024",  "margin_top1_top2_2016"),
    "delta_winner_vote_share_2024_2020": ("winner_vote_share_2024", "winner_vote_share_2016"),
    "delta_blank_rate_2024_2020":        ("blank_rate_2024",        "blank_rate_2016"),
}


def partial_out(df: pd.DataFrame, cols: list[str], controls: list[str],
                fe_col: str) -> pd.DataFrame:
    """Residuals after projecting each column in `cols` onto state FE + controls."""
    fe_dummies = pd.get_dummies(df[fe_col], drop_first=True).astype(float)
    ctrl_vals  = df[controls].astype(float)
    W = np.hstack([fe_dummies.values, ctrl_vals.values])            # (N, K)
    WtW_inv_Wt = np.linalg.lstsq(W, np.eye(len(df)), rcond=None)[0]  # (K, N)
    proj = W @ WtW_inv_Wt                                            # (N, N)
    M    = np.eye(len(df)) - proj                                    # annihilator
    data_mat = df[cols].astype(float).values                        # (N, C)
    resids   = M @ data_mat                                         # (N, C)
    return pd.DataFrame(resids, index=df.index, columns=cols)


def rotemberg_weights() -> None:
    print("=" * 70)
    print("[A] Rotemberg weights (GPS 2020 decomposition)")
    print("=" * 70)

    design = pd.read_csv(DESIGN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)

    need = [ENDOGENOUS, INSTRUMENT, FE_COL] + BASELINE_CONTROLS
    avail_outcomes = [o for o in ROT_OUTCOMES
                      if all(c in design.columns for c in ANCOVA_LEVEL.get(o, ("", "")))]
    for o in avail_outcomes:
        lvl, lag = ANCOVA_LEVEL[o]
        need += [lvl, lag]

    samp = design[["municipality_id_tse"] + need].dropna().copy().reset_index(drop=True)
    samp["municipality_id_tse"] = samp["municipality_id_tse"].astype(str).str.zfill(5)
    print(f"Analysis sample: {len(samp):,} municipalities")

    comp = pd.read_csv(COMPONENTS_PATH,
                       dtype={"municipality_id_tse": str, "main_subject_code": str},
                       low_memory=False)
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)
    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)
    comp["shock"]      = pd.to_numeric(comp["shock_log_growth_2020_2024"],
                                       errors="coerce").fillna(0)
    base_totals = comp.groupby("municipality_id_tse")["n_lawsuits"].transform("sum")
    comp["share"] = comp["n_lawsuits"] / base_totals.replace(0, np.nan)
    comp["z_component"] = comp["share"] * comp["shock"]

    samp_ids = set(samp["municipality_id_tse"])
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()

    pivot = comp.pivot_table(index="municipality_id_tse", columns="main_subject_code",
                             values="z_component", fill_value=0.0)
    pivot = pivot.reindex(samp["municipality_id_tse"]).fillna(0.0)
    topic_codes = list(pivot.columns)
    print(f"Topics in adversarial instrument: {len(topic_codes)}")

    samp_indexed = samp.set_index("municipality_id_tse")
    pivot.index.name = "municipality_id_tse"
    combined = samp_indexed.join(pivot, how="inner")

    scalar_cols = [ENDOGENOUS, INSTRUMENT]
    all_cols    = scalar_cols + topic_codes

    print("Partialling out controls and state FE ...")
    resid_df = partial_out(combined, all_cols, BASELINE_CONTROLS, FE_COL)

    outcome_resid = {}
    for o in avail_outcomes:
        lvl, lag = ANCOVA_LEVEL[o]
        rr = partial_out(combined, [lvl], BASELINE_CONTROLS + [lag], FE_COL)
        outcome_resid[o] = rr[lvl].values

    d_tilde = resid_df[ENDOGENOUS].values
    Z_sum_tilde = resid_df[topic_codes].values.sum(axis=1)
    Zd = Z_sum_tilde @ d_tilde

    topic_names = (comp[["main_subject_code", "main_subject_name"]]
                   .drop_duplicates("main_subject_code")
                   .set_index("main_subject_code")["main_subject_name"])

    N = len(d_tilde)
    rows = []
    for k in topic_codes:
        zk    = resid_df[k].values
        zk_D  = zk @ d_tilde
        zk_zk = zk @ zk
        alpha_k = zk_D / Zd
        if zk_zk > 1e-20:
            beta_k = zk_D / zk_zk
            ssr_k  = d_tilde @ d_tilde - zk_D ** 2 / zk_zk
            s2_k   = ssr_k / (N - 1)
            f_k    = beta_k ** 2 * zk_zk / s2_k
        else:
            f_k = np.nan
        row: dict = {"topic_code": k, "topic_name": topic_names.get(k, ""),
                     "alpha": alpha_k, "f_stat_k": f_k}
        for out in avail_outcomes:
            y_tilde = outcome_resid[out]
            zk_Y    = zk @ y_tilde
            row[f"tau_{out}"] = zk_Y / zk_D if abs(zk_D) > 1e-12 else np.nan
        rows.append(row)

    rw = pd.DataFrame(rows)
    print(f"\nSum of alpha_k: {rw['alpha'].sum():.6f}  (should be 1.0)")
    for out in avail_outcomes:
        tau_check = (rw["alpha"] * rw[f"tau_{out}"]).sum()
        print(f"  {out}: IV check = {tau_check:.4f}")

    rw = rw.sort_values("alpha", ascending=False).reset_index(drop=True)
    rw["alpha_pct"] = rw["alpha"] * 100
    rw["cum_alpha"] = rw["alpha"].cumsum()

    hhi = (rw["alpha"] ** 2).sum()
    n_positive = (rw["alpha"] > 0).sum()
    print(f"\nHHI of Rotemberg weights: {hhi:.4f}")
    print(f"Number of topics with positive weight: {n_positive} / {len(rw)}")

    rw.to_csv(ROTEMBERG_PATH, index=False, encoding="utf-8-sig")
    print(f"Saved: {ROTEMBERG_PATH.relative_to(PROJECT_ROOT)}")


# ============================================================================
# [B] GPS BALANCE TESTS — share exogeneity
# ============================================================================
EXCLUDE_RRC_DRAP = {"11618", "12044"}
N_TOP = 10
IE_TOPICS = {"11484", "11679", "12635", "12637", "12638", "12639"}
PRETREND_DEFS = [
    ("delta_margin_2020_2016",  "margin_top1_top2_2020", "margin_2016"),
    ("delta_top1_2020_2016",    "winner_vote_share_2020",  "top1_share_2016"),
    ("delta_ncand_2020_2016",   "total_candidates_2020",   "n_candidates_2016"),
]


def ols_stats(y: np.ndarray, X: np.ndarray):
    """OLS of y on X (X should be FE-demeaned / include constant). Returns
    (coefs, residuals, R2, F, p_F) with homoskedastic F."""
    N, K = X.shape
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
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


def gps_balance_tests() -> None:
    print("\n" + "=" * 70)
    print("[B] GPS (2020) balance tests on topic shares")
    print("=" * 70)

    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})
    rw["abs_alpha"] = rw["alpha"].abs()
    top_topics = rw.nlargest(N_TOP, "abs_alpha")["topic_code"].tolist()

    drap_code = "12044"
    extra_codes = [drap_code] + [k for k in sorted(IE_TOPICS)
                                 if k not in top_topics and k != drap_code]
    all_topics = top_topics + [k for k in extra_codes if k not in top_topics]
    print(f"Testing {len(top_topics)} top topics + extras: {all_topics}")

    design = pd.read_csv(DESIGN_PATH, dtype={"municipality_id_tse": str}, low_memory=False)
    design["municipality_id_tse"] = design["municipality_id_tse"].astype(str).str.zfill(5)

    for (new_col, col_a, col_b) in PRETREND_DEFS:
        if col_a in design.columns and col_b in design.columns:
            design[new_col] = pd.to_numeric(design[col_a], errors="coerce") - \
                              pd.to_numeric(design[col_b], errors="coerce")
        else:
            print(f"Warning: could not construct {new_col} ({col_a} or {col_b} missing)")
    pretrend_cols = [d[0] for d in PRETREND_DEFS if d[0] in design.columns]

    needed = (["municipality_id_tse", FE_COL] + BASELINE_CONTROLS + pretrend_cols)
    samp = design[needed].dropna().copy().reset_index(drop=True)
    samp_ids = set(samp["municipality_id_tse"])
    print(f"Sample after dropping NAs: {len(samp):,} municipalities")

    comp = pd.read_csv(COMPONENTS_PATH,
                       dtype={"municipality_id_tse": str, "main_subject_code": str},
                       low_memory=False)
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()
    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)

    base_no_rrc_drap = comp[~comp["main_subject_code"].isin(EXCLUDE_RRC_DRAP)] \
                           .groupby("municipality_id_tse")["n_lawsuits"].sum()
    base_all = comp.groupby("municipality_id_tse")["n_lawsuits"].sum()

    shares = {}
    for k in all_topics:
        sub = comp[comp["main_subject_code"] == k][["municipality_id_tse", "n_lawsuits"]]
        sub = sub.rename(columns={"n_lawsuits": "n_k"})
        denom = base_all if k == drap_code else base_no_rrc_drap
        sub = sub.set_index("municipality_id_tse").reindex(list(samp_ids), fill_value=0.0)
        sub["share"] = sub["n_k"] / denom.reindex(sub.index).replace(0, np.nan)
        sub["share"] = sub["share"].fillna(0.0)
        shares[k] = sub["share"]

    share_df = pd.DataFrame(shares).reindex(samp["municipality_id_tse"].values)
    share_df.index = samp.index

    fe_dummies = pd.get_dummies(samp[FE_COL], drop_first=True).astype(float).values
    ctrl_mat   = samp[BASELINE_CONTROLS].astype(float).values
    W = np.hstack([fe_dummies, ctrl_mat])

    pretrend_resid = {}
    for col in pretrend_cols:
        y_raw = samp[col].astype(float).values
        coef, _, _, _ = np.linalg.lstsq(W, y_raw, rcond=None)
        pretrend_resid[col] = y_raw - W @ coef

    topic_meta = (comp[["main_subject_code", "main_subject_name"]]
                  .drop_duplicates("main_subject_code")
                  .set_index("main_subject_code")["main_subject_name"])
    family_meta = (comp[["main_subject_code", "topic_family"]]
                   .drop_duplicates("main_subject_code")
                   .set_index("main_subject_code")["topic_family"])
    alpha_map = rw.set_index("topic_code")["alpha"].to_dict()

    rows = []
    for k in all_topics:
        s_raw = share_df[k].values.astype(float)
        coef_cov, resid_cov, r2_cov, f_cov, p_cov = ols_stats(s_raw, W)
        coef_fe_s, _, _, _ = np.linalg.lstsq(fe_dummies, s_raw, rcond=None)
        s_tilde = s_raw - fe_dummies @ coef_fe_s
        row: dict = {
            "topic_code": k, "topic_name": topic_meta.get(k, ""),
            "topic_family": family_meta.get(k, ""), "alpha": alpha_map.get(k, np.nan),
            "is_drap": (k == drap_code), "is_ie": (k in IE_TOPICS),
            "r2_cov_balance": r2_cov, "f_cov_balance": f_cov, "p_cov_balance": p_cov,
        }
        for col in pretrend_cols:
            y_tilde = pretrend_resid[col]
            N = len(s_tilde)
            beta = (s_tilde @ y_tilde) / (s_tilde @ s_tilde) if (s_tilde @ s_tilde) > 1e-20 else np.nan
            resid = y_tilde - beta * s_tilde
            s2    = (resid @ resid) / (N - 1)
            se    = np.sqrt(s2 / (s_tilde @ s_tilde)) if (s_tilde @ s_tilde) > 1e-20 else np.nan
            t     = beta / se if se and se > 0 else np.nan
            p     = 2 * (1 - stats.t.cdf(abs(t), df=N - 1)) if not np.isnan(t) else np.nan
            label = col.replace("delta_", "").replace("_2020_2016", "")
            row[f"beta_{label}"] = beta
            row[f"se_{label}"]   = se
            row[f"p_{label}"]    = p
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values("alpha", ascending=False, key=lambda x: x.abs()).reset_index(drop=True)

    out_csv = DESC_DIR / "gps_balance_tests.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"Saved: {out_csv.relative_to(PROJECT_ROOT)}")
    print(df[["topic_code", "topic_name", "alpha", "r2_cov_balance", "p_cov_balance"]].to_string(index=False))


def main() -> None:
    rotemberg_weights()   # writes rotemberg_weights.csv (consumed by [B] + R script)
    gps_balance_tests()
    # Exposure-robust (AKM 2019 / BHJ 2022) SEs are produced in R by
    # code/04_analysis/07_exposure_robust_se.R. The old Python heuristic that
    # lived here measured per-topic IV-coefficient dispersion, not sampling
    # variance (it spuriously inflated SEs ~11x), and has been deleted.
    print("\nAll IV diagnostics complete.")


if __name__ == "__main__":
    main()
