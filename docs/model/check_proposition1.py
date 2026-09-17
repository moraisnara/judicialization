"""Proposition 1: under mutual 1<->2 attacks the transfer map cannot widen the
top-two margin while preserving the winner.

The closed form in the memo is

    s1 - s2 = (s1 - s2) * kappa,   kappa = 1 - gamma - phi*(2 - alpha)

so kappa < 1 for every phi > 0. This script checks the closed form against a
direct simulation of the support map, and checks the claim on a grid.

Run from the repo root:
    python docs/model/check_proposition1.py
"""
import itertools
import sys

GRID = [i / 20 for i in range(1, 20)]          # 0.05 .. 0.95
SUPPORTS = [(0.45, 0.35, 0.20), (0.50, 0.30, 0.20),
            (0.40, 0.38, 0.22), (0.60, 0.25, 0.15),
            (0.36, 0.34, 0.30)]


def mutual(s1, s2, phi, alpha, gamma, third_attacks_leader):
    """Support after 1<->2 mutual attacks, optionally plus 3 -> 1."""
    a1 = s1 * (1 - phi - gamma) + phi * (1 - alpha) * s2
    a2 = s2 * (1 - phi - gamma) + phi * (1 - alpha) * s1
    if third_attacks_leader:
        a1 -= phi * s1
    return a1, a2


def main():
    bad_closed_form = 0
    widened_with_winner_kept = 0
    n = 0
    for (s1, s2, _s3), phi, alpha, gamma in itertools.product(
            SUPPORTS, GRID, GRID, GRID):
        if phi + gamma > 1:          # a candidate cannot lose more than it has
            continue
        n += 1
        a1, a2 = mutual(s1, s2, phi, alpha, gamma, False)
        kappa = 1 - gamma - phi * (2 - alpha)
        if abs((a1 - a2) - (s1 - s2) * kappa) > 1e-12:
            bad_closed_form += 1
        for third in (False, True):
            b1, b2 = mutual(s1, s2, phi, alpha, gamma, third)
            if b1 <= b2:             # the winner reversed; Prop 1 does not apply
                continue
            if (b1 - b2) > (s1 - s2) + 1e-12:
                widened_with_winner_kept += 1

    print(f"profiles checked: {n}")
    print(f"closed-form mismatches: {bad_closed_form}")
    print(f"margin widened with the winner preserved: {widened_with_winner_kept}")
    if bad_closed_form or widened_with_winner_kept:
        print("PROPOSITION 1 FAILS")
        return 1
    print("Proposition 1 holds on the grid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
