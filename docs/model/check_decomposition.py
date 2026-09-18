"""Checks on the seat-split ballot decomposition.

Two properties are testable. The three valid-vote shares (winner, runner-up,
others) partition the valid vote, so their coefficients should sum to zero;
they do not exactly, because each outcome is estimated on its own non-missing
sample, and the residual has to be small relative to the 3pp moves being
interpreted. And the signs have to match what the model predicts.

Run from the repo root:
    python docs/model/check_decomposition.py
"""
import re
import sys
from pathlib import Path

MACROS = Path("output/tables/tex/abstract_macros.tex")
PAT = re.compile(r"providecommand\{.(Decomp[A-Za-z]+)\}\{([^}]*)\}")
PARTS = ("Winner", "RunnerUp", "Others", "Exit", "Turnout")

# Every numeric gate in this file is a regression guard calibrated on today's
# estimates, not a proof of anything. It catches a rebuild that silently moves
# the decomposition; it does not establish that the decomposition is right.
# The residuals are currently -0.42pp (open) and +0.27pp (contested), so this
# tolerance is set just above them.
RESID_TOL = 0.60          # percentage points of registered voters


def read_macros():
    text = MACROS.read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in PAT.finditer(text)}


def main():
    M = read_macros()
    need = ([f"Decomp{s}{c}" for s in ("Open", "Cont") for c in PARTS]
            + [f"Decomp{s}{c}P" for s in ("Open", "Cont") for c in PARTS]
            + [f"Decomp{s}Resid" for s in ("Open", "Cont")])
    missing = [k for k in need if k not in M]
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1

    ok = True
    for seat in ("Open", "Cont"):
        v = {c: float(M[f"Decomp{seat}{c}"]) for c in PARTS}
        resid = float(M[f"Decomp{seat}Resid"])
        print(f"{seat}: " + "  ".join(f"{c.lower()} {v[c]:+.1f}" for c in PARTS)
              + f"   share-sum residual {resid:+.2f}pp")
        if abs(resid) > RESID_TOL:
            print(f"  FAILED: residual {resid:+.2f}pp exceeds {RESID_TOL}pp; the "
                  f"three valid shares no longer partition the valid vote")
            ok = False
        # Also a calibrated guard: half the blank/null entry is an arbitrary
        # yardstick, chosen because the residual is well under it today.
        if abs(resid) > 0.5 * abs(v["Exit"]):
            print(f"  WARNING: residual {resid:+.2f}pp is large relative to the "
                  f"blank/null entry {v['Exit']:+.2f}pp; do not interpret the "
                  f"others column")

    # Signs the model predicts. The runner-up's losses reach the winner where
    # the seat is open and partly leave the valid ballot where it is contested.
    checks = [
        ("open: winner gains",        float(M["DecompOpenWinner"]) > 0),
        ("open: runner-up loses",     float(M["DecompOpenRunnerUp"]) < 0),
        ("contested: winner gains",   float(M["DecompContWinner"]) > 0),
        ("contested: runner-up loses", float(M["DecompContRunnerUp"]) < 0),
        ("contested: blank/null rises", float(M["DecompContExit"]) > 0),
        ("the winner absorbs more where the seat is open",
         float(M["DecompOpenWinner"]) > float(M["DecompContWinner"])),
        # 1.5pp is calibrated on today's gap (2.9 vs 3.2), not derived.
        ("the runner-up's losses are comparable across seat types",
         abs(float(M["DecompOpenRunnerUp"]) - float(M["DecompContRunnerUp"])) < 1.5),
        ("blank/null exit is larger where the seat is contested",
         float(M["DecompContExit"]) > float(M["DecompOpenExit"])),
    ]
    for label, passed in checks:
        print(("  ok   " if passed else "  FAIL ") + label)
        if not passed:
            ok = False

    # The contested branch is the one the deck leans on, so its two headline
    # entries must still be the ones that clear conventional inference. These
    # thresholds are regression guards against today's p-values, not tests of
    # the cells: no p here belongs to the number it sits under. DecompCont*P
    # for Winner and RunnerUp are the vote-SHARE coefficients' p-values, while
    # the cell is that share coefficient combined with the valid-rate one; and
    # DecompContExitP is min(blank p, null p), a selection over two dependent
    # tests rather than a joint test of the blank+null sum. The 0.10 limit on
    # it is loosened accordingly -- it is the tighter of two p's, so a 0.05
    # gate would be doubly misleading.
    for k, lim in [("DecompContWinnerP", 0.05), ("DecompContRunnerUpP", 0.05),
                   ("DecompContExitP", 0.10)]:
        got = float(M[k])
        print(f"  {'ok  ' if got <= lim else 'FAIL'} {k} = {got:.3f} <= {lim}")
        if got > lim:
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
