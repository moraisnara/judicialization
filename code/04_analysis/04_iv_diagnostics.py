"""
04_iv_diagnostics.py — shift-share IV diagnostics for the adversarial Bartik
instrument (merged). Three sections run IN ORDER because each consumes the CSV
the previous one writes:

  [A] rotemberg_weights()   — GPS (2020) Rotemberg-weight decomposition
        tau_IV = sum_k alpha_k * tau_k; per-topic alpha_k, F_k, tau_k.
        -> descriptives/rotemberg_weights.{csv,md}

  [B] gps_balance_tests()   — GPS (2020) Section V.A share-exogeneity tests
        (covariate balance + pre-trend placebo) for top-|alpha| + IE topics.
        reads rotemberg_weights.csv  -> descriptives/gps_balance_tests.{csv,md}

  [C] exposure_robust_se()  — BHJ (2024) / AKM (2019) exposure-robust SEs.
        reads rotemberg_weights.csv + the first-stage / IV regression CSVs
        -> regressions/exposure_robust_se.{csv,md}

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
FS_PATH         = REG_DIR / "executive_margin_first_stage_fixest.csv"
IV_PATH         = REG_DIR / "executive_margin_iv_fixest.csv"
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

    top10 = rw.head(10).copy()
    top10["alpha_pct"] = top10["alpha_pct"].map(lambda x: f"{x:+.1f}%")
    top10["cum_alpha"] = top10["cum_alpha"].map(lambda x: f"{x:.2f}")
    for out in avail_outcomes:
        short = out.replace("delta_", "").replace("_2024_2020", "")
        top10 = top10.rename(columns={f"tau_{out}": short})

    md_rows = ["# Rotemberg Weights — Adversarial Bartik IV", "",
               "GPS (2020) decomposition: tau_IV = sum_k alpha_k * tau_k.", "",
               f"**HHI** = {hhi:.4f} | **Positive-weight topics** = {n_positive} / {len(rw)}",
               "", "## Top 10 Topics by Rotemberg Weight", ""]
    hdr = ["Rank", "Code", "Topic", "alpha (%)", "Cum.", "F_k"] + \
          [o.replace("delta_", "").replace("_2024_2020", "") for o in avail_outcomes]
    md_rows.append("| " + " | ".join(hdr) + " |")
    md_rows.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for i, row in top10.iterrows():
        fk = row.get("f_stat_k", np.nan)
        vals = [str(i + 1), row["topic_code"], row["topic_name"][:45],
                row["alpha_pct"], row["cum_alpha"],
                f"{fk:.1f}" if not np.isnan(fk) else "—"]
        for o in avail_outcomes:
            short = o.replace("delta_", "").replace("_2024_2020", "")
            v = row.get(short, np.nan)
            vals.append(f"{v:.3f}" if not np.isnan(v) else "—")
        md_rows.append("| " + " | ".join(vals) + " |")
    md_rows += [
        "", "## Notes",
        "- `alpha_k = (z_k_tilde' d_tilde) / (Z_tilde' d_tilde)`  where tilde = residual on state FE + 7 baseline controls.",
        "- `tau_k` = just-identified IV using topic k alone as instrument.",
        "- `F_k` = just-identified first-stage F using topic k component as sole instrument (regression through origin on residualised variables, df = N-1).",
        "- HHI < 0.15 → many-shock instrument (Borusyak et al. 2022 criterion).",
    ]
    (DESC_DIR / "rotemberg_weights.md").write_text("\n".join(md_rows), encoding="utf-8")
    print(f"Saved: {(DESC_DIR / 'rotemberg_weights.md').relative_to(PROJECT_ROOT)}")


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

    md = ["# GPS (2020) Balance Tests on Topic Shares", "",
          "Tests share exogeneity for the adversarial-only instrument (no-RRC, no-DRAP).",
          "DRAP (12044) is included as a diagnostic even though excluded from the main spec.",
          "", "## Test 1: Covariate Balance (OLS: s_ik ~ state FE + 7 controls)", "",
          "High R² indicates the share correlates with observables (endogeneity concern).", ""]
    hdr1 = ["Rank", "Code", "Topic", "alpha", "R²", "F", "p"]
    md.append("| " + " | ".join(hdr1) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr1)) + " |")
    for i, r in df.iterrows():
        tag = " *(DRAP)*" if r["is_drap"] else ""
        md.append("| " + " | ".join([
            str(i + 1), r["topic_code"] + tag, r["topic_name"][:40],
            f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
            f"{r['r2_cov_balance']:.3f}", f"{r['f_cov_balance']:.1f}", f"{r['p_cov_balance']:.3f}",
        ]) + " |")

    md += ["", "## Test 2: Pre-trend Balance (OLS: delta_outcome_2016_2020 ~ s_ik | state FE)", "",
           "Under share exogeneity, topic shares should not predict 2016→2020 electoral trends.", ""]
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
                str(i + 1), r["topic_code"] + tag, r["topic_name"][:40],
                f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
                f"{b:+.4f}" if not np.isnan(b) else "—",
                f"{s:.4f}"  if not np.isnan(s) else "—",
                (f"{p:.3f}" if not np.isnan(p) else "—") + sig,
            ]) + " |")
        md.append("")

    ie_df = df[df["is_ie"]].copy()
    md += ["## Information Environment Focus (all 6 topics)", "",
           "The preferred instrument (`bartik_iv_information_environment`) is built from these 6 topics.",
           "Share exogeneity must hold for each individual topic for the family IV to be valid.", ""]
    hdr_ie = ["Code", "Topic", "alpha", "Family", "R²(cov)", "p(cov)", "p(margin)", "p(top1)", "p(ncand)"]
    md.append("| " + " | ".join(hdr_ie) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr_ie)) + " |")
    for _, r in ie_df.iterrows():
        def _p(col):
            v = r.get(col, np.nan)
            if np.isnan(v): return "—"
            return (f"{v:.3f}" + (" *" if v < 0.05 else ""))
        md.append("| " + " | ".join([
            r["topic_code"], r["topic_name"][:45],
            f"{r['alpha']:+.3f}" if not np.isnan(r["alpha"]) else "—",
            r["topic_family"], f"{r['r2_cov_balance']:.3f}",
            _p("p_cov_balance"), _p("p_margin"), _p("p_top1"), _p("p_ncand"),
        ]) + " |")
    md += ["", "(*) significant at 5% — signals potential share endogeneity.", "",
           "## Notes",
           "- All regressions include state fixed effects. State FE are partialled out before the pre-trend regression.",
           "- Pre-trends: delta_margin = margin_top1_top2_2020 - margin_2016; delta_top1 = winner_vote_share_2020 - top1_share_2016; delta_ncand = total_candidates_2020 - n_candidates_2016.",
           "- DRAP (12044) is excluded from the adversarial-only instrument but shown here to evaluate its share exogeneity.",
           "  Low R² and non-significant pre-trend coefficients for DRAP would support its inclusion as an instrument."]
    out_md = DESC_DIR / "gps_balance_tests.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


# ============================================================================
# [C] EXPOSURE-ROBUST SE — BHJ (2024) / AKM (2019)
# ============================================================================
EXP_OUTCOMES = [
    "delta_winner_majority_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_blank_rate_2024_2020",
    "delta_runnerup_vote_share_2024_2020",
]
SPEC    = "baseline"
VARIANT = "adversarial"


def exposure_robust_se() -> None:
    print("\n" + "=" * 70)
    print("[C] Exposure-robust SE (BHJ 2024 / AKM 2019)")
    print("=" * 70)

    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})
    K  = len(rw)
    hhi = (rw["alpha"] ** 2).sum()
    k_eff = 1.0 / hhi
    print(f"K topics = {K}, HHI = {hhi:.4f}, K_eff = {k_eff:.2f}")

    iv_res = pd.read_csv(IV_PATH)
    iv_base = iv_res[(iv_res["spec"] == SPEC) & (iv_res["variant"] == VARIANT)].copy()

    fs_res = pd.read_csv(FS_PATH)
    fs_row = fs_res[(fs_res["spec"] == SPEC) & (fs_res["variant"] == VARIANT)]
    fs_F = fs_row["first_stage_F"].values[0] if len(fs_row) > 0 else np.nan
    print(f"First-stage F ({VARIANT}, {SPEC}) = {fs_F:.2f}" if not np.isnan(fs_F)
          else f"First-stage F ({VARIANT}, {SPEC}) = not found")

    rows = []
    for out in EXP_OUTCOMES:
        tau_col = f"tau_{out}"
        if tau_col not in rw.columns:
            continue
        alpha = rw["alpha"].values
        tau_k = rw[tau_col].values
        tau_2sls_check = np.nansum(alpha * tau_k)

        iv_row = iv_base[iv_base["outcome"] == out]
        if len(iv_row) == 0:
            continue
        b_2sls_conv = iv_row["coef"].values[0]
        se_conv     = iv_row["se"].values[0]
        p_conv      = iv_row["p"].values[0]

        mask = ~np.isnan(tau_k)
        alpha_v = alpha[mask]
        tau_v   = tau_k[mask]
        K_valid = mask.sum()

        residuals_k = alpha_v * (tau_v - tau_2sls_check)
        sum_alpha2  = np.sum(alpha_v ** 2)
        se_bhj = np.sqrt(np.sum(residuals_k ** 2)) / sum_alpha2 if sum_alpha2 > 0 else np.nan
        se_akm = se_bhj * np.sqrt(K_valid / (K_valid - 1)) if K_valid > 1 else np.nan

        tF_cv = 1.96
        if not np.isnan(fs_F) and fs_F < 23.1:
            tF_table_F  = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                                     16, 17, 18, 19, 20, 21, 22, 23.1, 25])
            tF_table_cv = np.array([13.99, 7.13, 5.24, 4.31, 3.78, 3.44, 3.21, 3.02,
                                     2.86,  2.73, 2.62, 2.53, 2.46, 2.39, 2.33, 2.28,
                                     2.24,  2.20, 2.17, 2.14, 2.11, 2.00, 1.96])
            tF_cv = float(np.interp(fs_F, tF_table_F, tF_table_cv))

        rows.append({
            "variant": VARIANT, "spec": SPEC, "outcome": out,
            "tau_2sls": b_2sls_conv, "se_conventional": se_conv, "p_conventional": p_conv,
            "ci_low_conv": b_2sls_conv - 1.96 * se_conv,
            "ci_high_conv": b_2sls_conv + 1.96 * se_conv,
            "se_bhj": se_bhj, "se_akm": se_akm,
            "ci_low_bhj":  b_2sls_conv - 1.96 * se_bhj if not np.isnan(se_bhj) else np.nan,
            "ci_high_bhj": b_2sls_conv + 1.96 * se_bhj if not np.isnan(se_bhj) else np.nan,
            "ci_low_akm":  b_2sls_conv - 1.96 * se_akm if not np.isnan(se_akm) else np.nan,
            "ci_high_akm": b_2sls_conv + 1.96 * se_akm if not np.isnan(se_akm) else np.nan,
            "tF_cv": tF_cv,
            "ci_low_tF":  b_2sls_conv - tF_cv * se_conv,
            "ci_high_tF": b_2sls_conv + tF_cv * se_conv,
            "K_valid": K_valid, "K_eff_rotemberg": k_eff,
        })
        print(f"\n  {out}")
        print(f"    tau_2SLS = {b_2sls_conv:.4f}")
        print(f"    SE: conv={se_conv:.4f}  BHJ={se_bhj:.4f}  AKM={se_akm:.4f}")
        print(f"    tF_cv = {tF_cv:.2f}  |  SE ratio (BHJ/conv) = {se_bhj/se_conv:.2f}")

    df = pd.DataFrame(rows)
    out_csv = REG_DIR / "exposure_robust_se.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")

    md = ["# Exposure-Robust SE — BHJ (2024) / AKM (2019)", "",
          f"Adversarial IV (administrative/procedural excluded at build stage), {SPEC}.",
          f"K = {K} topics | HHI = {hhi:.4f} | K_eff (Rotemberg) = {k_eff:.2f}"]
    tF_cv_display = f"{rows[0]['tF_cv']:.2f}" if rows else "—"
    fs_F_display  = f"{fs_F:.1f}" if not np.isnan(fs_F) else "—"
    md.append(f"First-stage F = {fs_F_display} -> tF critical value (Lee et al. 2022) = {tF_cv_display}")
    md += ["", "**Caveat:** BHJ exposure-robust asymptotics require K_eff >> 1.",
           f"Here K_eff = {k_eff:.2f} (Rotemberg-weight HHI = {hhi:.3f}).",
           "These SEs should be treated as a sensitivity bound, not a replacement",
           "for the conventional municipality-clustered SE.", "",
           "## SE Comparison by Outcome", ""]
    hdr = ["Outcome", "tau_2SLS", "SE_conv", "SE_BHJ", "SE_AKM",
           "SE_BHJ/SE_conv", "tF_cv", "CI95_tF"]
    md.append("| " + " | ".join(hdr) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for _, r in df.iterrows():
        ratio = r["se_bhj"] / r["se_conventional"] if r["se_conventional"] > 0 else np.nan
        md.append("| " + " | ".join([
            r["outcome"].replace("delta_", "").replace("_2024_2020", ""),
            f"{r['tau_2sls']:.4f}", f"{r['se_conventional']:.4f}",
            f"{r['se_bhj']:.4f}" if not np.isnan(r["se_bhj"]) else "—",
            f"{r['se_akm']:.4f}" if not np.isnan(r["se_akm"]) else "—",
            f"{ratio:.2f}" if not np.isnan(ratio) else "—",
            f"{r['tF_cv']:.2f}",
            f"[{r['ci_low_tF']:.4f}, {r['ci_high_tF']:.4f}]",
        ]) + " |")
    md += ["", "## Notes",
           "- **SE_conv**: clustered by principal electoral zone (fixest output).",
           "- **SE_BHJ**: BHJ exposure-robust SE = sqrt(sum_k (alpha_k * (tau_k - tau_2SLS))^2) / sum_k alpha_k^2.",
           "  Valid asymptotically when K_eff -> ∞; here K_eff = {:.2f}.".format(k_eff),
           "- **SE_AKM**: SE_BHJ * sqrt(K/(K-1)) — Adao, Kolesar & Morales (2019) finite-K correction.",
           "- **tF_cv**: Lee et al. (2022) critical value; CIs use tF_cv instead of 1.96.",
           "- The BHJ SE uses residuals from the *shift-level* regression: residual_k = alpha_k * (tau_k - tau_2SLS).",
           "  A large SE_BHJ/SE_conv ratio suggests the Bartik estimate is driven by a few shocks",
           "  (consistent with K_eff = {:.2f}).".format(k_eff)]
    out_md = REG_DIR / "exposure_robust_se.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


def main() -> None:
    rotemberg_weights()   # writes rotemberg_weights.csv (consumed by [B] and [C])
    gps_balance_tests()
    exposure_robust_se()
    print("\nAll IV diagnostics complete.")


if __name__ == "__main__":
    main()
