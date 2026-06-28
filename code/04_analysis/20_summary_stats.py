r"""
20_summary_stats.py

Summary-statistics frame for the report: treatment + instrument, outcome
variables (split into candidate-related and voter-related, matching the two
analyses), and pre-determined controls. Computed on the BASELINE estimation
sample (complete cases on the instrument, endogenous, cluster and baseline
controls) so the N matches the regressions.

Min/max for the OUTCOME variables are shown at the 1st/99th percentile to keep
single-municipality outliers from dominating the display (footnoted); treatment
and controls show true min/max.

Source:
  data/estimation/act_design.csv

Writes:
  output/tables/descriptives/summary_stats.csv
  output/tables/tex/summary_stats_frame.tex
"""

import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / "output" / "tables" / "tex"
DESC = ROOT / "output" / "tables" / "descriptives"
TEX.mkdir(parents=True, exist_ok=True)
DESC.mkdir(parents=True, exist_ok=True)

d = pd.read_csv(ROOT / "data" / "estimation" / "act_design.csv")

INSTRUMENT = "bartik_iv_act"
ENDOG = "delta_log1p_act_lawsuits"
BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]

# Baseline estimation sample: complete cases on instrument + endogenous + cluster
# + baseline controls (mirrors build_sample() in 02_iv_main.R for the baseline).
req = [INSTRUMENT, ENDOG, "cluster_id"] + BASELINE_CONTROLS
req = [c for c in req if c in d.columns]
samp = d.dropna(subset=req).reset_index(drop=True)
N = len(samp)

# Each row: (column, label, decimals, winsorize_minmax)
SECTIONS = [
    ("Treatment and instrument", [
        (ENDOG, r"$\Delta\log(1+\text{adversarial lawsuits})$", 3, False),
        (INSTRUMENT, r"Bartik IV ($Z_m$, adversarial filter)", 3, False),
    ]),
    (r"Outcome variables --- \textit{candidate-related}", [
        ("delta_runnerup_vote_share_2024_2020",            r"$\Delta$ Runner-up vote share", 3, True),
        ("delta_margin_top1_top2_2024_2020",               r"$\Delta$ Margin (winner$-$runner-up)", 3, True),
        ("delta_winner_vote_share_2024_2020",              r"$\Delta$ Winner vote share", 3, True),
        ("delta_winner_majority_2024_2020",                r"$\Delta$ Winner majority (P50)", 3, True),
        ("delta_others_vote_share_2024_2020",              r"$\Delta$ Other-candidates vote share", 3, True),
        ("delta_log1p_n_candidates_with_votes_2024_2020",  r"$\Delta$ Log candidates", 3, True),
        ("delta_female_vote_share_2024_2020",              r"$\Delta$ Female vote share", 3, True),
        ("delta_female_share_2024_2020",                   r"$\Delta$ Female candidate share", 3, True),
        ("delta_nonwhite_vote_share_2024_2020",            r"$\Delta$ Non-white vote share", 3, True),
        ("delta_new_candidate_vote_share_2024_2020",       r"$\Delta$ New-candidate vote share", 3, True),
        ("delta_incumbent_candidate_vote_share_2024_2020", r"$\Delta$ Incumbent vote share", 3, True),
        ("delta_winner_is_female_2024_2020",               r"$\Delta$ Winner is female", 3, True),
        ("delta_winner_is_new_vs_2020_2024_2020",          r"$\Delta$ Winner is new entrant", 3, True),
        ("delta_share_first_time_candidates_2024_2020",    r"$\Delta$ First-time-candidate share", 3, True),
        ("delta_share_serial_challenger_2024_2020",        r"$\Delta$ Serial-challenger share", 3, True),
        ("delta_share_cross_cycle_returner_2024_2020",     r"$\Delta$ Cross-cycle returner share", 3, True),
    ]),
    (r"Outcome variables --- \textit{voter-related}", [
        ("delta_turnout_rate_2024_2020",    r"$\Delta$ Turnout rate", 3, True),
        ("delta_blank_rate_2024_2020",      r"$\Delta$ Blank vote rate", 3, True),
        ("delta_null_rate_2024_2020",       r"$\Delta$ Null vote rate", 3, True),
        ("delta_valid_vote_rate_2024_2020", r"$\Delta$ Valid vote rate", 3, True),
    ]),
    (r"Outcome variables --- \textit{competition structure}", [
        ("delta_effective_n_candidates_vote_2024_2020",     r"$\Delta$ Eff.\ N candidates (votes)", 3, True),
        ("delta_effective_party_count_candidates_2024_2020", r"$\Delta$ Eff.\ N parties (candidates)", 3, True),
        ("delta_vote_hhi_candidate_2024_2020",              r"$\Delta$ Vote HHI (candidate)", 3, True),
        ("delta_top2_vote_share_2024_2020",                 r"$\Delta$ Top-two vote share", 3, True),
    ]),
    ("Pre-determined controls", [
        ("log_pop_2010",                 r"Log population (2010)", 2, False),
        ("urban_share_2010",             r"Urban share (2010)", 3, False),
        ("log_income_pc_2010",           r"Log income per capita (2010)", 3, False),
        ("margin_2016",                  r"Margin 2016 (pp)", 1, False),
        ("log1p_total_valid_votes_2020", r"Log valid votes (2020)", 2, False),
        ("margin_top1_top2_2020",        r"Top-two margin (2020)", 3, False),
        ("log1p_total_candidates_2020",  r"Log candidates (2020)", 2, False),
    ]),
]


def stat_row(col, label, dec, winsor):
    x = pd.to_numeric(samp[col], errors="coerce").dropna()
    mean, sd = x.mean(), x.std()
    lo, hi = (np.percentile(x, 1), np.percentile(x, 99)) if winsor else (x.min(), x.max())
    f = lambda v: f"{v:.{dec}f}"
    return f"  {label} & {f(mean)} & {f(sd)} & {f(lo)} & {f(hi)} \\\\", \
           (col, label, mean, sd, lo, hi)


records = []


def render_section(title, rows):
    out = [rf"  \addlinespace[2pt]\textit{{{title}}} \\"]
    for col, label, dec, winsor in rows:
        if col not in samp.columns:
            continue
        tex, rec = stat_row(col, label, dec, winsor)
        out.append(tex)
        records.append(rec)
    return out


def make_frame(subtitle, section_idxs, footnote):
    body = "\n".join(l for i in section_idxs
                     for l in render_section(SECTIONS[i][0], SECTIONS[i][1]))
    return rf"""\begin{{frame}}{{Summary Statistics --- {subtitle}}}
\centering
\scriptsize
\setlength{{\tabcolsep}}{{5pt}}
\renewcommand{{\arraystretch}}{{0.98}}
\begin{{tabular}}{{l r r r r}}
  \toprule
  Variable & \multicolumn{{1}}{{c}}{{Mean}} & \multicolumn{{1}}{{c}}{{SD}}
   & \multicolumn{{1}}{{c}}{{Min}} & \multicolumn{{1}}{{c}}{{Max}} \\
  \midrule
{body}
  \bottomrule
\end{{tabular}}

\vspace{{3pt}}
{{\scriptsize {footnote}}}
\end{{frame}}"""


# Three frames so the full set fits: (1) treatment + candidate outcomes,
# (2) voter outcomes + competition structure, (3) pre-determined controls.
ofoot = (rf"$N={N:,}$ municipalities (baseline estimation sample). Outcome "
         r"min/max at the 1st/99th percentile; treatment shows true min/max.")
vfoot = (rf"$N={N:,}$ municipalities. Outcome min/max at the 1st/99th percentile.")
cfoot = (rf"$N={N:,}$ municipalities. Controls show true min/max.")
frame = (make_frame("Treatment and Candidate Outcomes", [0, 1], ofoot)
         + "\n\n"
         + make_frame("Voter Outcomes and Competition Structure", [2, 3], vfoot)
         + "\n\n"
         + make_frame("Pre-determined Controls", [4], cfoot))

(TEX / "summary_stats_frame.tex").write_text(
    "% Auto-generated by code/04_analysis/20_summary_stats.py — do not edit by hand.\n"
    + frame + "\n", encoding="utf-8")

pd.DataFrame(records, columns=["variable", "label", "mean", "sd", "min", "max"]).to_csv(
    DESC / "summary_stats.csv", index=False)

# ----------------------------------------------------------------------
# Instrument-distribution macros for the report's frame-17 figure captions
# (histogram + binscatter). These previously came from the now-archived
# 12_abstract_numbers.py; sourced here so they track the current G8rh design.
#   \BartikZMeanRaw   raw mean of the instrument
#   \BartikZSDResid   SD after partialling out state fixed effects
#   \FSCoef           baseline first-stage slope (from voter_first_stage.csv)
# ----------------------------------------------------------------------
state_col = "state" if "state" in samp.columns else "SG_UF"
z = samp[INSTRUMENT]
z_resid = z - samp.groupby(state_col)[INSTRUMENT].transform("mean")
IM = {
    "BartikZMeanRaw": f"{z.mean():.3f}",
    "BartikZSDResid": f"{z_resid.std():.3f}",
}
fs_path = ROOT / "output" / "tables" / "regressions" / "voter_first_stage.csv"
if fs_path.exists():
    fs = pd.read_csv(fs_path)
    base = fs.loc[fs["spec"] == "baseline", "coef"]
    if len(base):
        IM["FSCoef"] = f"{float(base.iloc[0]):.3f}"
im_lines = ["% Auto-generated by code/04_analysis/20_summary_stats.py — do not edit by hand."]
for k, val in IM.items():
    im_lines.append(f"\\providecommand{{\\{k}}}{{}}\\renewcommand{{\\{k}}}{{{val}}}")
(TEX / "instrument_dist_macros.tex").write_text("\n".join(im_lines) + "\n", encoding="utf-8")
print("Wrote instrument_dist_macros.tex:", IM)

print(f"N = {N:,}")
print(f"{'variable':48s} {'mean':>9s} {'sd':>9s} {'min':>9s} {'max':>9s}")
for col, label, m, sd, lo, hi in records:
    print(f"{col:48s} {m:9.3f} {sd:9.3f} {lo:9.3f} {hi:9.3f}")
print(f"\nWrote {TEX / 'summary_stats_frame.tex'}")
print(f"Wrote {DESC / 'summary_stats.csv'}")
