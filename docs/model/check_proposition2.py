"""Proposition 2: the concentration estimates are the top-two margin restated.

Take the estimated reallocation between the top two (winner +dW, runner-up +dR,
others unchanged), apply it to each municipality's observed 2024 share vector,
and recompute the Herfindahl index and the effective number of candidates. If
the implied changes sit inside the confidence intervals of the separately
estimated index regressions, the index regressions add no information.

Run from the repository root:

    python docs/model/check_proposition2.py
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
SHARES = ["winner_vote_share_2024", "runnerup_vote_share_2024",
          "others_vote_share_2024"]


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

    d_win, _, _ = coef(iv, "delta_winner_vote_share_2024_2020")
    d_run, _, _ = coef(iv, "delta_runnerup_vote_share_2024_2020")

    keep = panel[TREAT].notna() & panel[INSTR].notna()
    for col in SHARES:
        keep &= panel[col].notna()
    d = panel.loc[keep, SHARES]

    w = d["winner_vote_share_2024"].to_numpy()
    r = d["runnerup_vote_share_2024"].to_numpy()
    o = d["others_vote_share_2024"].to_numpy()

    hhi_0 = w ** 2 + r ** 2 + o ** 2
    hhi_1 = (w + d_win) ** 2 + (r + d_run) ** 2 + o ** 2
    ok = (hhi_0 > 0) & (hhi_1 > 0)

    implied = {
        "delta_vote_hhi_candidate_2024_2020":
            float(np.mean(hhi_1[ok] - hhi_0[ok])),
        "delta_effective_n_candidates_vote_2024_2020":
            float(np.mean(1.0 / hhi_1[ok] - 1.0 / hhi_0[ok])),
    }

    print(f"reallocation applied: winner {d_win:+.4f}, runner-up {d_run:+.4f}")
    print(f"municipalities used: {int(ok.sum())} "
          f"(dropped {int((~ok).sum())} with a degenerate share vector)")

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
