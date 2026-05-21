"""
BHJ (2024) / AKM (2019) exposure-robust standard errors.

The Bartik 2SLS estimator can be expressed as a shift-level weighted regression:
    tau_2SLS = sum_k alpha_k * tau_k  (GPS Rotemberg decomposition)
where tau_k = just-identified IV estimate for topic k.

Exposure-robust SE (BHJ Section III.B):
  Regress alpha_k * tau_k on 1 (constant), weighting by 1.
  The OLS SE from this shift-level regression, treating topics as the unit of
  observation, gives the "exposure-robust" SE that is valid when:
    K_eff >> 1  (BHJ requirement: many relevant shocks)

AKM (2019, QJE) finite-K correction:
  Scale up SE by sqrt(K / (K - 1)) to account for finite number of shocks.

Comparison:
  - Conventional (municipality-clustered) SE: standard fixest output
  - Exposure-robust (shift-level) SE: BHJ approach
  - AKM-corrected SE: multiply exposure-robust SE by sqrt(K/(K-1))

CAVEAT: K_eff (Rotemberg) = 1/HHI ≈ 2.6 for adversarial-only spec.
  BHJ requires K_eff -> ∞ for consistency; 2.6 is very small.
  Results should be interpreted as a sensitivity bound, not a replacement
  for the conventional SE.

Inputs:
  output/tables/descriptives/rotemberg_weights.csv  (with f_stat_k column)
  output/tables/regressions/executive_margin_first_stage_fixest.csv
  output/tables/regressions/executive_margin_iv_fixest.csv  (baseline spec)

Output:
  output/tables/regressions/exposure_robust_se.csv
  output/tables/regressions/exposure_robust_se.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
ROTEMBERG_PATH  = PROJECT_ROOT / "output" / "tables" / "descriptives" / "rotemberg_weights.csv"
FS_PATH         = PROJECT_ROOT / "output" / "tables" / "regressions" / "executive_margin_first_stage_fixest.csv"
IV_PATH         = PROJECT_ROOT / "output" / "tables" / "regressions" / "executive_margin_iv_fixest.csv"
OUT_DIR         = PROJECT_ROOT / "output" / "tables" / "regressions"

OUTCOMES = [
    "delta_winner_majority_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_blank_rate_2024_2020",
    "delta_runnerup_vote_share_2024_2020",
]
SPEC    = "baseline_state_fe"
VARIANT = "adversarial"


def main() -> None:
    # ---- 1. Load Rotemberg weights ----
    rw = pd.read_csv(ROTEMBERG_PATH, dtype={"topic_code": str})
    K  = len(rw)
    hhi = (rw["alpha"] ** 2).sum()
    k_eff = 1.0 / hhi
    print(f"K topics = {K}, HHI = {hhi:.4f}, K_eff = {k_eff:.2f}")

    # ---- 2. Load conventional SE from IV results ----
    iv_res = pd.read_csv(IV_PATH)
    iv_base = iv_res[
        (iv_res["spec"] == SPEC) & (iv_res["variant"] == VARIANT)
    ].copy()

    # ---- 3. Load first-stage F ----
    fs_res = pd.read_csv(FS_PATH)
    fs_row = fs_res[
        (fs_res["spec"] == SPEC) & (fs_res["variant"] == VARIANT)
    ]
    fs_F  = fs_row["first_stage_F"].values[0] if len(fs_row) > 0 else np.nan
    print(f"First-stage F ({VARIANT}, {SPEC}) = {fs_F:.2f}" if not np.isnan(fs_F) else f"First-stage F ({VARIANT}, {SPEC}) = not found")

    # ---- 4. Exposure-robust SE for each outcome ----
    # tau_k values are in Rotemberg CSV as tau_{outcome}
    rows = []
    for out in OUTCOMES:
        tau_col = f"tau_{out}"
        if tau_col not in rw.columns:
            continue

        alpha   = rw["alpha"].values
        tau_k   = rw[tau_col].values

        # tau_2SLS = sum_k alpha_k * tau_k (verify)
        tau_2sls_check = np.nansum(alpha * tau_k)

        # Get conventional SE from IV CSV
        iv_row = iv_base[iv_base["outcome"] == out]
        if len(iv_row) == 0:
            continue
        b_2sls_conv = iv_row["coef"].values[0]
        se_conv      = iv_row["se"].values[0]
        p_conv       = iv_row["p"].values[0]

        # Exposure-robust SE (BHJ shift-level regression):
        # Treat the K topics as observations.
        # Regress (alpha_k * tau_k) on alpha_k (with no constant, since
        # sum_k alpha_k * tau_k = tau_2SLS = sum_k alpha_k * tau_2SLS is the
        # WLS moment condition).
        # The slope = tau_2SLS, and the SE comes from the residual variation
        # across k: residual_k = alpha_k * (tau_k - tau_2SLS)
        # SE_bhj^2 = sum_k [alpha_k * (tau_k - tau_2SLS)]^2 / (sum_k alpha_k^2)^2

        # Keep only topics with valid tau_k
        mask = ~np.isnan(tau_k)
        alpha_v = alpha[mask]
        tau_v   = tau_k[mask]
        K_valid = mask.sum()

        tau_w = np.nansum(alpha_v * tau_v) / np.nansum(alpha_v ** 2) \
                if np.nansum(alpha_v ** 2) > 1e-20 else np.nan

        # BHJ exposure-robust SE (eq. 21 in BHJ 2024):
        # Numerator: sum_k (alpha_k * (tau_k - tau_2SLS))^2 = Var of shift-level residuals
        residuals_k = alpha_v * (tau_v - tau_2sls_check)
        sum_alpha2   = np.sum(alpha_v ** 2)
        se_bhj = np.sqrt(np.sum(residuals_k ** 2)) / sum_alpha2 if sum_alpha2 > 0 else np.nan

        # AKM (2019) finite-K correction: multiply by sqrt(K / (K-1))
        se_akm = se_bhj * np.sqrt(K_valid / (K_valid - 1)) if K_valid > 1 else np.nan

        # tF correction: use the first-stage F from the main spec
        tF_cv = 1.96
        if not np.isnan(fs_F) and fs_F < 23.1:
            # Linear interpolation from lookup table (same as R script)
            tF_table_F  = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                                     16, 17, 18, 19, 20, 21, 22, 23.1, 25])
            tF_table_cv = np.array([13.99, 7.13, 5.24, 4.31, 3.78, 3.44, 3.21, 3.02,
                                     2.86,  2.73, 2.62, 2.53, 2.46, 2.39, 2.33, 2.28,
                                     2.24,  2.20, 2.17, 2.14, 2.11, 2.00, 1.96])
            tF_cv = float(np.interp(fs_F, tF_table_F, tF_table_cv))

        rows.append({
            "variant":         VARIANT,
            "spec":            SPEC,
            "outcome":         out,
            "tau_2sls":        b_2sls_conv,
            "se_conventional": se_conv,
            "p_conventional":  p_conv,
            "ci_low_conv":     b_2sls_conv - 1.96 * se_conv,
            "ci_high_conv":    b_2sls_conv + 1.96 * se_conv,
            "se_bhj":          se_bhj,
            "se_akm":          se_akm,
            "ci_low_bhj":      b_2sls_conv - 1.96 * se_bhj  if not np.isnan(se_bhj) else np.nan,
            "ci_high_bhj":     b_2sls_conv + 1.96 * se_bhj  if not np.isnan(se_bhj) else np.nan,
            "ci_low_akm":      b_2sls_conv - 1.96 * se_akm  if not np.isnan(se_akm) else np.nan,
            "ci_high_akm":     b_2sls_conv + 1.96 * se_akm  if not np.isnan(se_akm) else np.nan,
            "tF_cv":           tF_cv,
            "ci_low_tF":       b_2sls_conv - tF_cv * se_conv,
            "ci_high_tF":      b_2sls_conv + tF_cv * se_conv,
            "K_valid":         K_valid,
            "K_eff_rotemberg": k_eff,
        })

        print(f"\n  {out}")
        print(f"    tau_2SLS = {b_2sls_conv:.4f}")
        print(f"    SE: conv={se_conv:.4f}  BHJ={se_bhj:.4f}  AKM={se_akm:.4f}")
        print(f"    tF_cv = {tF_cv:.2f}  |  SE ratio (BHJ/conv) = {se_bhj/se_conv:.2f}")

    df = pd.DataFrame(rows)

    # ---- 5. CSV ----
    out_csv = OUT_DIR / "exposure_robust_se.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out_csv.relative_to(PROJECT_ROOT)}")

    # ---- 6. Markdown ----
    md = []
    md.append("# Exposure-Robust SE — BHJ (2024) / AKM (2019)")
    md.append("")
    md.append(f"Adversarial IV (administrative/procedural excluded at build stage), {SPEC}.")
    md.append(f"K = {K} topics | HHI = {hhi:.4f} | K_eff (Rotemberg) = {k_eff:.2f}")
    tF_cv_display = f"{rows[0]['tF_cv']:.2f}" if rows else "—"
    fs_F_display  = f"{fs_F:.1f}" if not np.isnan(fs_F) else "—"
    md.append(f"First-stage F = {fs_F_display} -> tF critical value (Lee et al. 2022) = {tF_cv_display}")
    md.append("")
    md.append("**Caveat:** BHJ exposure-robust asymptotics require K_eff >> 1.")
    md.append(f"Here K_eff = {k_eff:.2f} (Rotemberg-weight HHI = {hhi:.3f}).")
    md.append("These SEs should be treated as a sensitivity bound, not a replacement")
    md.append("for the conventional municipality-clustered SE.")
    md.append("")
    md.append("## SE Comparison by Outcome")
    md.append("")
    hdr = ["Outcome", "tau_2SLS", "SE_conv", "SE_BHJ", "SE_AKM",
           "SE_BHJ/SE_conv", "tF_cv", "CI95_tF"]
    md.append("| " + " | ".join(hdr) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for _, r in df.iterrows():
        ratio = r["se_bhj"] / r["se_conventional"] if r["se_conventional"] > 0 else np.nan
        md.append("| " + " | ".join([
            r["outcome"].replace("delta_", "").replace("_2024_2020", ""),
            f"{r['tau_2sls']:.4f}",
            f"{r['se_conventional']:.4f}",
            f"{r['se_bhj']:.4f}" if not np.isnan(r["se_bhj"]) else "—",
            f"{r['se_akm']:.4f}" if not np.isnan(r["se_akm"]) else "—",
            f"{ratio:.2f}"       if not np.isnan(ratio)         else "—",
            f"{r['tF_cv']:.2f}",
            f"[{r['ci_low_tF']:.4f}, {r['ci_high_tF']:.4f}]",
        ]) + " |")

    md += [
        "",
        "## Notes",
        "- **SE_conv**: clustered by principal electoral zone (fixest output).",
        "- **SE_BHJ**: BHJ exposure-robust SE = sqrt(sum_k (alpha_k * (tau_k - tau_2SLS))^2) / sum_k alpha_k^2.",
        "  Valid asymptotically when K_eff -> ∞; here K_eff = {:.2f}.".format(k_eff),
        "- **SE_AKM**: SE_BHJ * sqrt(K/(K-1)) — Adao, Kolesar & Morales (2019) finite-K correction.",
        "- **tF_cv**: Lee et al. (2022) critical value; CIs use tF_cv instead of 1.96.",
        "- The BHJ SE uses residuals from the *shift-level* regression: residual_k = alpha_k * (tau_k - tau_2SLS).",
        "  A large SE_BHJ/SE_conv ratio suggests the Bartik estimate is driven by a few shocks",
        "  (consistent with K_eff = {:.2f}).".format(k_eff),
    ]

    out_md = OUT_DIR / "exposure_robust_se.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Saved: {out_md.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
