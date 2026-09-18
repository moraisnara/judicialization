"""Proposition 3: the concentration estimates are the top-two margin restated.

Take the estimated reallocation between the top two (winner +dW, runner-up +dR,
others unchanged), apply it to each municipality's observed 2024 share vector,
and recompute the Herfindahl index and the effective number of candidates. If
the implied changes sit inside the confidence intervals of the separately
estimated index regressions, the index regressions add no information.

The baseline Herfindahl index is the municipality's own candidate-level index
(vote_hhi_candidate_2024), which is what effective_n_candidates_vote inverts.
Reconstructing it from the three top-two-plus-others shares would lump every
non-top-two candidate into a single bin and understate the index.

Run from the repository root:

    python docs/model/check_proposition3.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IV = ROOT / "output" / "tables" / "regressions" / "executive_margin_iv_fixest.csv"
PANEL = ROOT / "data" / "estimation" / "executive_margin_design.csv"

TREAT = "delta_log1p_competition_lawsuits_2024_2020"
INSTR = "bartik_iv_2020_2024"
HHI = "vote_hhi_candidate_2024"
SHARES = ["winner_vote_share_2024", "runnerup_vote_share_2024"]


def coef(iv, outcome):
    """The baseline adversarial 2SLS coefficient, its SE, and its p-value."""
    rows = iv[(iv["spec"] == "baseline") & (iv["variant"] == "adversarial")
              & (iv["outcome"] == outcome)]
    if len(rows) != 1:
        raise SystemExit(f"expected one row for {outcome}, got {len(rows)}")
    row = rows.iloc[0]
    return float(row["coef"]), float(row["se"]), float(row["p"])


def main():
    iv = pd.read_csv(IV)
    panel = pd.read_csv(PANEL)

    # The two estimates do not sum to zero (d_win + d_run = -0.0009), so the
    # applied shift is not literally the zero-sum one-parameter reallocation
    # Proposition 3 hypothesizes. These are the estimates; they stand as they
    # are, and the residual is three orders of magnitude below either leg.
    d_win, _, _ = coef(iv, "delta_winner_vote_share_2024_2020")
    d_run, _, _ = coef(iv, "delta_runnerup_vote_share_2024_2020")

    # Exclusions, stage by stage, so the estimation sample is legible.
    n_all = len(panel)
    keep = panel[TREAT].notna() & panel[INSTR].notna()
    n_design = int(keep.sum())
    for col in SHARES + [HHI]:
        keep &= panel[col].notna()
    n_obs = int(keep.sum())

    d = panel.loc[keep, SHARES + [HHI]]
    w = d[SHARES[0]].to_numpy()
    r = d[SHARES[1]].to_numpy()

    hhi_0 = d[HHI].to_numpy()
    hhi_1 = hhi_0 + (w + d_win) ** 2 - w ** 2 + (r + d_run) ** 2 - r ** 2
    ok = (hhi_0 > 0) & (hhi_1 > 0)
    n_used = int(ok.sum())

    implied = {
        "delta_vote_hhi_candidate_2024_2020":
            float(np.mean(hhi_1[ok] - hhi_0[ok])),
        "delta_effective_n_candidates_vote_2024_2020":
            float(np.mean(1.0 / hhi_1[ok] - 1.0 / hhi_0[ok])),
    }

    print(f"reallocation applied: winner {d_win:+.4f}, runner-up {d_run:+.4f} "
          f"(sum {d_win + d_run:+.4f}, not zero -- these are the estimates)")
    print(f"rows in the design file: {n_all}")
    print(f"    with the treatment and the instrument: {n_design} "
          f"(dropped {n_all - n_design})")
    print(f"    with the top-two shares and the candidate HHI: {n_obs} "
          f"(dropped {n_design - n_obs} for missing values)")
    print(f"    with a non-degenerate share vector: {n_used} "
          f"(dropped {n_obs - n_used})")

    outside = 0
    for outcome, imp in implied.items():
        est, se, _ = coef(iv, outcome)
        lo, hi = est - 1.96 * se, est + 1.96 * se
        inside = lo <= imp <= hi
        outside += 0 if inside else 1
        print(f"{outcome}\n"
              f"    implied {imp:+.4f}   estimated {est:+.4f} "
              f"({se:.3f})   95% CI [{lo:+.4f}, {hi:+.4f}]   "
              f"{'inside' if inside else 'OUTSIDE'}")

    print(f"implied values outside the estimated CI: {outside}")
    return 0 if outside == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
