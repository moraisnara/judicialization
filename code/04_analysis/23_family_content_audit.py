"""
23_family_content_audit.py — systematic family-by-family content audit.

Every time we have read a family's actual (classe, assunto) contents by hand we
have found something misfiled (content_disinfo was three distinct blocks; its
false_content strings were byte-identical to crime_speech, split only by civil-vs-
criminal class). This generalises that manual read to EVERY family, BEFORE any
grouping/estimation decision, so a regrouping must trace to a flag here — never to
a first-stage statistic.

Reads the LIVE crosswalk (data/clean/sig_family_crosswalk.csv — the output of
code/02_build/01_family_crosswalk.py), which already carries n_2020/n_2024/n_total
and the family label under every scheme. Imports 01_family_crosswalk.py only for
`up()` so subject normalisation matches production exactly.

Dumps, per family (subst13 floor + theme9 headline), every distinct member with
volume and 2020->2024 growth (human-readable .md), and auto-flags three
misplacement classes (.csv, for triage — never auto-fixes):
  1. subject_multi_family : same normalised assunto landing in >1 family_micro
       (the false_content/crime_speech case) -> consolidation candidates.
  2. sign_incoherent       : a member whose own national 2020->2024 growth sign
       opposes its family's net growth sign -> cancellation INSIDE a family.
  3. keep_drop_boundary    : high-volume DROPPED subjects, and high-volume members
       sitting in the catch-all/default buckets (prop_placement, crime_other,
       abuse_political) -> both tails of the keep/drop and residual-routing cut.
"""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data/clean"
OUT = ROOT / "output/tables/descriptives"; OUT.mkdir(parents=True, exist_ok=True)

# reuse production normalisation so subject grouping is identical to the routing
spec = importlib.util.spec_from_file_location("fc", ROOT / "code/02_build/01_family_crosswalk.py")
fc = importlib.util.module_from_spec(spec); spec.loader.exec_module(fc)

# volume floors for the flags (absolute lawsuit counts over both years)
SIGN_FLOOR = 200      # a member must carry this much to flag internal cancellation
DROP_FLOOR = 500      # a dropped subject must carry this much to demand a re-look
CATCHALL = {"prop_placement", "crime_other", "abuse_political"}  # default/residual buckets
CATCHALL_FLOOR = 1000
TOPN_MD = 40          # member rows shown per family in the .md

xw = pd.read_csv(CLEAN / "sig_family_crosswalk.csv")
xw["A_norm"] = xw.assunto.map(fc.up)
xw["growth"] = np.where(xw.n_2020 > 0, (xw.n_2024 - xw.n_2020) / xw.n_2020, np.nan)


def fam_growth_sign(df, fam_col):
    """family-level net national growth sign per family on a given rung."""
    g = df.groupby(fam_col)[["n_2020", "n_2024"]].sum()
    g["growth"] = np.where(g.n_2020 > 0, (g.n_2024 - g.n_2020) / g.n_2020, np.nan)
    g["sign"] = np.sign(g.growth)
    return g


# ----------------------------------------------------------------- flag 1: subject in >1 family
multi = (xw.groupby("A_norm")
           .agg(families=("family_micro", lambda s: sorted(set(s))),
                n_fams=("family_micro", lambda s: s.nunique()),
                n_total=("n_total", "sum"))
           .reset_index())
multi = multi[multi.n_fams > 1].sort_values("n_total", ascending=False)
flags1 = []
for _, r in multi.iterrows():
    sub = xw[xw.A_norm == r.A_norm]
    by_fam = sub.groupby("family_micro").n_total.sum().sort_values(ascending=False)
    flags1.append({
        "flag": "subject_multi_family", "assunto": sub.assunto.iloc[0],
        "detail": " | ".join(f"{f}:{int(v):,}" for f, v in by_fam.items()),
        "families": ";".join(r.families), "n_total": int(r.n_total)})
flags1 = pd.DataFrame(flags1)

# ----------------------------------------------------------- flag 2: sign-incoherent member (theme9)
fg9 = fam_growth_sign(xw[xw.fam_theme9 != "drop"], "fam_theme9")
flags2 = []
kept = xw[xw.fam_theme9 != "drop"].copy()
kept["fam_sign"] = kept.fam_theme9.map(fg9["sign"])
kept["mem_sign"] = np.sign(kept.growth)
bad = kept[(kept.n_total >= SIGN_FLOOR) & kept.mem_sign.notna()
           & (kept.mem_sign != 0) & (kept.mem_sign != kept.fam_sign)]
for _, r in bad.sort_values("n_total", ascending=False).iterrows():
    flags2.append({
        "flag": "sign_incoherent", "family_theme9": r.fam_theme9,
        "classe": r.classe, "assunto": r.assunto, "n_total": int(r.n_total),
        "member_growth": round(r.growth, 3),
        "family_growth": round(fg9.loc[r.fam_theme9, "growth"], 3)})
flags2 = pd.DataFrame(flags2)

# ----------------------------------------------------- flag 3: keep/drop & catch-all boundary
flags3 = []
dropped = xw[(xw.family_micro == "drop") & (xw.n_total >= DROP_FLOOR)]
for _, r in dropped.sort_values("n_total", ascending=False).iterrows():
    flags3.append({"flag": "drop_highvol", "family_micro": "drop",
                   "classe": r.classe, "assunto": r.assunto, "n_total": int(r.n_total)})
catch = xw[xw.family_micro.isin(CATCHALL) & (xw.n_total >= CATCHALL_FLOOR)]
for _, r in catch.sort_values("n_total", ascending=False).iterrows():
    flags3.append({"flag": "catchall_highvol", "family_micro": r.family_micro,
                   "classe": r.classe, "assunto": r.assunto, "n_total": int(r.n_total)})
flags3 = pd.DataFrame(flags3)

# ----------------------------------------------------------------------------- write flags csv
allflags = pd.concat([flags1, flags2, flags3], ignore_index=True)
allflags.to_csv(OUT / "family_content_audit_flags.csv", index=False)

# ---------------------------------------------------------------------------- write member dump
def member_table(df):
    t = (df.groupby(["classe", "assunto"], as_index=False)
           .agg(n_2020=("n_2020", "sum"), n_2024=("n_2024", "sum"), n_total=("n_total", "sum"))
           .sort_values("n_total", ascending=False))
    t["growth"] = np.where(t.n_2020 > 0, (t.n_2024 - t.n_2020) / t.n_2020, np.nan)
    return t


lines = ["# Family content audit\n",
         "Per-family `(classe, assunto)` members with volume and 2020->2024 national "
         "growth. Read each family to confirm it aggregates what we intend. Flags in "
         "`family_content_audit_flags.csv`.\n"]
lines.append(f"- subject-in-multiple-families flags: **{len(flags1)}**")
lines.append(f"- sign-incoherent members (theme9, n>={SIGN_FLOOR}): **{len(flags2)}**")
lines.append(f"- keep/drop & catch-all boundary flags: **{len(flags3)}**\n")

for rung, col, title in [("subst13", "fam_subst13", "subst13 (floor)"),
                         ("theme9", "fam_theme9", "theme9 (headline)")]:
    lines.append(f"\n---\n\n## {title}\n")
    fg = fam_growth_sign(xw[xw[col] != "drop"], col)
    fams = sorted([f for f in xw[col].unique() if f != "drop"],
                  key=lambda f: -xw[xw[col] == f].n_total.sum())
    for fam in fams:
        sub = xw[xw[col] == fam]
        t = member_table(sub)
        gr = fg.loc[fam, "growth"]
        lines.append(f"\n### {fam} — {int(t.n_total.sum()):,} lawsuits, "
                     f"{len(t)} distinct (classe,assunto), net growth {gr:+.1%}\n")
        head = t.head(TOPN_MD)
        lines.append("| classe | assunto | n_2020 | n_2024 | growth |")
        lines.append("|---|---|---:|---:|---:|")
        for _, r in head.iterrows():
            g = "" if pd.isna(r.growth) else f"{r.growth:+.0%}"
            lines.append(f"| {r.classe} | {r.assunto} | {int(r.n_2020):,} | "
                         f"{int(r.n_2024):,} | {g} |")
        if len(t) > TOPN_MD:
            lines.append(f"| … | _{len(t) - TOPN_MD} more_ | | | |")

(OUT / "family_content_audit.md").write_text("\n".join(lines), encoding="utf-8")

print(f"wrote {OUT/'family_content_audit.md'}")
print(f"wrote {OUT/'family_content_audit_flags.csv'}  ({len(allflags)} flags)")
print(f"  subject_multi_family={len(flags1)}  sign_incoherent={len(flags2)}  "
      f"keep_drop_boundary={len(flags3)}")
