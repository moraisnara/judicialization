# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: hardcodes RUNG="theme9" and the old theme9 family label dictionary.
# ===========================================================================
"""
15_report_descriptives.py

Reproducible descriptive numbers + the topic-family/subject table for the
research report (output/presentation/slides_report.tex). Nothing in the report
that comes from data should be typed by hand; this script is the single source.

Writes:
  output/tables/tex/report_descriptives_macros.tex  -- \providecommand/\renewcommand macros
  output/tables/tex/topic_family_subjects.tex       -- longtable: family -> TSE subjects

Run:
  python code/04_analysis/15_report_descriptives.py
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "data" / "estimation" / "executive_margin_design.csv"
TAXONOMY = ROOT / "data" / "clean" / "sig_family_crosswalk.csv"
COMPONENTS = ROOT / "data" / "clean" / "municipality_family_components.csv"
RUNG = "theme9"   # headline family taxonomy (matches HEADLINE_RUNG)
OUT_TEX = ROOT / "output" / "tables" / "tex"
OUT_TEX.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 1. Universe + zone-size distribution (Sample frame)
# ----------------------------------------------------------------------
d = pd.read_csv(DESIGN)
n_munis = len(d)
n_zones = d["principal_zone_id"].nunique()
n_states = d["state"].nunique() if "state" in d.columns else d["SG_UF"].nunique()
munis_per_zone = d.groupby("principal_zone_id").size()
avg_mpz = munis_per_zone.mean()

buckets = {
    "One":       (munis_per_zone == 1),
    "Two":       (munis_per_zone == 2),
    "ThreeFive": (munis_per_zone >= 3) & (munis_per_zone <= 5),
    "Six":       (munis_per_zone >= 6),
}

M = {}
M["NMunisUniverse"] = f"{n_munis:,}"
M["NZonesUniverse"] = f"{n_zones:,}"
M["NStatesUniverse"] = f"{n_states}"
M["AvgMunisPerZone"] = f"{avg_mpz:.1f}"
for name, mask in buckets.items():
    M[f"ZoneDist{name}N"] = f"{int(mask.sum()):,}"
    M[f"ZoneDist{name}Pct"] = f"{100 * mask.mean():.0f}"

# ----------------------------------------------------------------------
# 2. Topic-family taxonomy (family -> subjects), SIG family crosswalk
# ----------------------------------------------------------------------
# Each row of the crosswalk is one distinct (classe, assunto) pair. The instrument
# keeps every family at the headline rung that is not "drop"; the kept subject is
# the assunto (descriptive name). vol = total filings 2020+2024 for the pair.
FAM_COL = f"fam_{RUNG}"
tax = pd.read_csv(TAXONOMY, dtype=str, keep_default_na=False, encoding="utf-8")
keep = tax[tax[FAM_COL] != "drop"].copy()
keep = keep.rename(columns={FAM_COL: "family", "assunto": "main_subject_name"})
keep["vol"] = pd.to_numeric(keep["n_total"], errors="coerce").fillna(0)

# Families that actually enter the instrument (have usable shift cells)
comp = pd.read_csv(COMPONENTS)
comp = comp[comp["rung"] == RUNG]
instrument_families = set(comp["family"].dropna().unique())

n_families_defined = keep["family"].nunique()
n_families_instrument = len(instrument_families)
n_subjects_kept = keep["main_subject_name"].nunique()
M["NFamiliesDefined"] = f"{n_families_defined}"
M["NFamiliesInstrument"] = f"{n_families_instrument}"
M["NSubjectsKept"] = f"{n_subjects_kept}"

# English glosses for the report (families are internal slugs). The 9 substance
# themes of the headline (theme9) scheme; see 01_family_crosswalk.py.
LABEL = {
    "prop_placement":   "Propaganda placement (where the ad ran)",
    "prop_regulatory":  "Propaganda rules \\& airtime limits (HGPE)",
    "prop_timing":      "Premature / out-of-window propaganda",
    "disinformation":   "Disinformation \\& right of reply (false / defamatory content)",
    "electoral_polls":  "Electoral-poll disputes",
    "abuse_power":      "Abuse of economic / political power (AIJE, AIME)",
    "campaign_finance": "Campaign-finance disputes",
    "candidacy":        "Candidacy challenge \\& sham candidacy (ficticia)",
    "criminal":         "Electoral crimes (originating accusations)",
}

# Shorten recurring TSE prefixes so subject cells stay readable
PREFIXES = [
    ("Propaganda Política - Propaganda Eleitoral - ", "Propaganda: "),
    ("Propaganda Política - ", "Propaganda: "),
    ("Registro de Candidatura - ", "Registro: "),
    ("Pesquisa Eleitoral - ", "Pesquisa: "),
    ("Direito Eleitoral - ", ""),
]


def latex_escape(s: str) -> str:
    for a, b in [("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")]:
        s = s.replace(a, b)
    return s


def shorten(s: str) -> str:
    for a, b in PREFIXES:
        if s.startswith(a):
            s = b + s[len(a):]
            break
    return latex_escape(s.strip())


# Order families by total caseload (volume), instrument families first,
# the defined-but-excluded family last with a marker.
fam_vol = keep.groupby("family")["vol"].sum().sort_values(ascending=False)
ordered = [f for f in fam_vol.index if f in instrument_families] + \
          [f for f in fam_vol.index if f not in instrument_families]

rows = []
for fam in ordered:
    subs = keep.loc[keep["family"] == fam].sort_values("vol", ascending=False)
    subj_list = "; ".join(shorten(s) for s in subs["main_subject_name"])
    label = LABEL.get(fam, fam.replace("_", " "))
    marker = "" if fam in instrument_families else r"\,$^{\dagger}$"
    nsub = len(subs)
    rows.append((label + marker, nsub, subj_list))

# longtable body
lines = []
lines.append("% Auto-generated by code/04_analysis/15_report_descriptives.py — do not edit by hand.")
lines.append(r"\begin{longtable}{@{}L{3.9cm}c L{7.7cm}@{}}")
lines.append(r"\toprule")
lines.append(r"\textbf{Topic family} & \textbf{\# subj.} & \textbf{TSE subjects (abbreviated)} \\")
lines.append(r"\midrule")
lines.append(r"\endfirsthead")
lines.append(r"\toprule")
lines.append(r"\textbf{Topic family} & \textbf{\# subj.} & \textbf{TSE subjects (abbreviated)} \\")
lines.append(r"\midrule")
lines.append(r"\endhead")
for label, nsub, subj_list in rows:
    lines.append(f"{label} & {nsub} & {subj_list} \\\\")
    lines.append(r"\addlinespace[2pt]")
lines.append(r"\bottomrule")
lines.append(r"\end{longtable}")
body = "\n".join(lines)

(OUT_TEX / "topic_family_subjects.tex").write_text(body + "\n", encoding="utf-8")

# ----------------------------------------------------------------------
# 3. Write macros
# ----------------------------------------------------------------------
macro_lines = ["% Auto-generated by code/04_analysis/15_report_descriptives.py — do not edit by hand."]
for k, v in M.items():
    macro_lines.append(f"\\providecommand{{\\{k}}}{{}}\\renewcommand{{\\{k}}}{{{v}}}")
(OUT_TEX / "report_descriptives_macros.tex").write_text("\n".join(macro_lines) + "\n", encoding="utf-8")

print("Wrote report_descriptives_macros.tex and topic_family_subjects.tex")
print(f"  universe: {n_munis} munis, {n_zones} zones, {n_states} states, avg {avg_mpz:.2f} munis/zone")
for name, mask in buckets.items():
    print(f"  zone-dist {name}: {int(mask.sum())} ({100*mask.mean():.0f}%)")
print(f"  families: {n_families_defined} defined, {n_families_instrument} in instrument, {n_subjects_kept} subjects")
