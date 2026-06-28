"""
Poll-coverage report for the executive-race estimation panel.

Documents poll coverage of the 5,571 panel municipalities for TWO sources, and
for each tests whether covered municipalities differ from uncovered ones on
pre-treatment covariates (2010 census + 2016 electoral baseline):

  A. TSE poll registry  — metadata of every registered mayoral poll. Flags:
     polled_2020 / polled_2024 (near-universal coverage of larger munis).
  B. Poder360 compilation — carries actual vote intentions but only covers a
     handful of (mostly capital) municipalities. No IBGE code, so coverage is
     name-matched (sigla_uf + nome_municipio) to the panel.

For each source we produce one four-category coverage map (both cycles / only
2020 / only 2024 / never) and one balance table (covered-either vs not).

Also produces a Poder360 trajectory summary (polls per municipality, time span)
for the beamer exploration slide.

Inputs:
  data/estimation/act_design.csv     (panel keys)
  data/clean/poll_activity_design.csv              (TSE poll activity, wide)
  data/clean/municipal_covariates.csv              (pre-treatment covariates)
  data/clean/poder360_prefeito_muni_year.csv       (Poder360 prefeito muni-year)
  geobr municipality geometries (2020, cached)

Outputs:
  output/tables/descriptives/poll_coverage_summary.csv
  output/tables/descriptives/poll_coverage_balance.{csv,tex}          (TSE)
  output/tables/descriptives/poder360_coverage_balance.{csv,tex}      (Poder360)
  output/tables/descriptives/poder360_trajectory_summary.tex          (trajectory)
  output/figures/poll_coverage_map_tse.png
  output/figures/poll_coverage_map_poder360.png
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN = PROJECT_ROOT / "data" / "clean"
EST = PROJECT_ROOT / "data" / "estimation"
FIG = PROJECT_ROOT / "output" / "figures"
TAB = PROJECT_ROOT / "output" / "tables" / "descriptives"

# Pre-treatment covariates to balance on: label -> (column, log?)
BAL_VARS = [
    ("Population (2010)",            "pop_2010",               True),
    ("Urban share (2010)",          "urban_share_2010",       False),
    ("Income per capita (2010)",    "income_pc_2010",         False),
    ("Higher-educ. share (2010)",   "higher_educ_share_2010", False),
    ("N candidates (2016)",         "n_candidates_2016",      False),
    ("Win margin (2016)",           "margin_2016",            False),
    ("Eff. n. parties (2016)",      "enp_2016",               False),
    ("Turnout rate (2020)",         "turnout_rate_2020",      False),
    ("Blank rate (2020)",           "blank_rate_2020",        False),
]

# Four-category colors (sequential blues + grey for "never").
CAT_COLORS = {
    "both":  "#08519c",
    "2020":  "#6baed6",
    "2024":  "#fd8d3c",
    "never": "#e0e0e0",
}
CAT_LABELS = {
    "both":  "Both cycles",
    "2020":  "Only 2020",
    "2024":  "Only 2024",
    "never": "Neither cycle",
}


def _norm(s: pd.Series) -> pd.Series:
    """Normalize municipality names for matching: upper, strip accents/punct."""
    def f(x: str) -> str:
        x = unicodedata.normalize("NFKD", str(x))
        x = "".join(c for c in x if not unicodedata.combining(c))
        return "".join(c for c in x.upper() if c.isalnum() or c == " ").strip()
    return s.map(f)


def attach_poder360(pan: pd.DataFrame) -> pd.DataFrame:
    """Name-match Poder360 prefeito coverage onto the panel (no IBGE code)."""
    pan["poder360_2020"] = 0
    pan["poder360_2024"] = 0
    f = CLEAN / "poder360_prefeito_muni_year.csv"
    if not f.exists():
        print(f"  [warn] {f.name} not found — Poder360 flags left at 0")
        return pan
    p = pd.read_csv(f)
    p["mkey"] = p["sigla_uf"].str.upper().str.strip() + "|" + _norm(p["nome_municipio"])
    pan["mkey"] = pan["state"].str.upper().str.strip() + "|" + _norm(pan["municipality_name"])
    for yr in (2020, 2024):
        covered = set(p.loc[p["ano"] == yr, "mkey"])
        pan[f"poder360_{yr}"] = pan["mkey"].isin(covered).astype(int)
    matched = pan[["poder360_2020", "poder360_2024"]].max(axis=1).sum()
    p_keys = set(p["mkey"])
    print(f"  Poder360: {p['nome_municipio'].nunique()} distinct names, "
          f"{len(p_keys)} uf-name keys; matched {matched} panel municipalities "
          f"({len(p_keys - set(pan['mkey']))} keys unmatched)")
    return pan


def build_panel() -> pd.DataFrame:
    pan = pd.read_csv(EST / "act_design.csv",
                      usecols=["municipality_id_tse", "municipality_id_ibge",
                               "municipality_name", "state"])
    polls = pd.read_csv(CLEAN / "poll_activity_design.csv")
    cov = pd.read_csv(CLEAN / "municipal_covariates.csv")

    for df in (pan, polls):
        df["k"] = df["municipality_id_tse"].astype(str).str.lstrip("0")
    flags = ["polled_2020", "polled_2024", "polled_either", "polled_both",
             "n_polls_2020", "n_polls_2024"]
    pan = pan.merge(polls[["k"] + flags], on="k", how="left")
    for c in flags:
        pan[c] = pan[c].fillna(0).astype(int if c.startswith("polled") else float)

    cov["k"] = cov["municipality_id_tse"].astype(str).str.lstrip("0")
    cov_cols = ["k"] + [v[1] for v in BAL_VARS if v[1] in cov.columns]
    cov = cov.drop_duplicates(subset="k")
    pan = pan.merge(cov[cov_cols], on="k", how="left")
    assert pan["k"].is_unique, "panel keys not unique after merge"

    pan = attach_poder360(pan)
    return pan


def coverage_summary(pan: pd.DataFrame) -> pd.DataFrame:
    n = len(pan)
    p360_either = ((pan.poder360_2020 == 1) | (pan.poder360_2024 == 1)).astype(int)
    rows = [
        ("Panel municipalities",          n,                          1.0),
        ("TSE: polled 2020",              int(pan.polled_2020.sum()), pan.polled_2020.mean()),
        ("TSE: polled 2024",              int(pan.polled_2024.sum()), pan.polled_2024.mean()),
        ("TSE: polled both",              int(pan.polled_both.sum()), pan.polled_both.mean()),
        ("TSE: polled either",            int(pan.polled_either.sum()), pan.polled_either.mean()),
        ("Poder360: covered 2020",        int(pan.poder360_2020.sum()), pan.poder360_2020.mean()),
        ("Poder360: covered 2024",        int(pan.poder360_2024.sum()), pan.poder360_2024.mean()),
        ("Poder360: covered either",      int(p360_either.sum()),     p360_either.mean()),
    ]
    out = pd.DataFrame(rows, columns=["group", "n", "share"])
    out["share"] = out["share"].round(3)
    return out


def balance_table(pan: pd.DataFrame, flag: str) -> pd.DataFrame:
    """Covered (flag==1) vs uncovered (flag==0) on BAL_VARS."""
    from scipy import stats
    rows = []
    for label, col, logit in BAL_VARS:
        if col not in pan.columns:
            continue
        x = np.log1p(pan[col]) if logit else pan[col]
        a = x[pan[flag] == 1].dropna()
        b = x[pan[flag] == 0].dropna()
        if len(a) < 2 or len(b) < 2:
            continue
        m1, m0 = a.mean(), b.mean()
        sd_pool = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        smd = (m1 - m0) / sd_pool if sd_pool else np.nan
        t, p = stats.ttest_ind(a, b, equal_var=False)
        rows.append({"variable": label,
                     "mean_covered": round(m1, 3),
                     "mean_uncovered": round(m0, 3),
                     "std_diff": round(smd, 3),
                     "p_value": round(p, 4)})
    return pd.DataFrame(rows)


def write_balance_tex(bal: pd.DataFrame, path: Path,
                      head_covered="Covered", head_uncovered="Uncovered") -> None:
    lines = [
        f"% {path.name} - auto-generated by 13_poll_coverage_report.py",
        "\\begin{tabular}{lrrrr}",
        "  \\toprule",
        f"  Covariate & {head_covered} & {head_uncovered} & Std.\\ diff. & $p$ \\\\",
        "  \\midrule",
    ]
    for _, r in bal.iterrows():
        lines.append(f"  {r.variable} & {r.mean_covered:g} & {r.mean_uncovered:g} "
                     f"& {r.std_diff:+.3f} & {r.p_value:.3f} \\\\")
    lines += ["  \\bottomrule", "\\end{tabular}"]
    path.write_text("\n".join(lines), encoding="utf-8")


def _category(pan: pd.DataFrame, f2020: str, f2024: str) -> pd.Series:
    both = (pan[f2020] == 1) & (pan[f2024] == 1)
    only20 = (pan[f2020] == 1) & (pan[f2024] == 0)
    only24 = (pan[f2020] == 0) & (pan[f2024] == 1)
    cat = pd.Series("never", index=pan.index)
    cat[both] = "both"
    cat[only20] = "2020"
    cat[only24] = "2024"
    return cat


def make_category_map(pan: pd.DataFrame, f2020: str, f2024: str,
                      title: str, fname: str, geo) -> None:
    pan = pan.copy()
    pan["cat"] = _category(pan, f2020, f2024)
    pan["code_muni"] = pan["municipality_id_ibge"].astype("Int64").astype(str)
    g = geo.merge(pan[["code_muni", "cat"]], on="code_muni", how="left")
    in_panel = g["cat"].notna()

    fig, ax = plt.subplots(figsize=(7, 7))
    g[~in_panel].plot(ax=ax, color="#f7f7f7", linewidth=0)
    for key in ("never", "2020", "2024", "both"):
        sub = g[in_panel & (g["cat"] == key)]
        if len(sub):
            sub.plot(ax=ax, color=CAT_COLORS[key], linewidth=0)
    counts = pan["cat"].value_counts()
    ax.set_title(title, fontsize=13)
    ax.axis("off")
    ax.legend(handles=[
        Patch(facecolor=CAT_COLORS[k],
              label=f"{CAT_LABELS[k]} ({int(counts.get(k, 0))})")
        for k in ("both", "2020", "2024", "never")
    ], loc="lower left", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {fname}")


def poder360_trajectory_summary() -> pd.DataFrame:
    """Summary of Poder360 prefeito observations by year (munis, polls, depth)."""
    f = CLEAN / "poder360_prefeito_muni_year.csv"
    p = pd.read_csv(f)
    p = p[p["ano"].isin([2020, 2024])]
    rows = []
    for yr, g in p.groupby("ano"):
        n_munis = g["nome_municipio"].nunique()
        n_polls = int(g["n_polls"].sum())
        n_ge3   = int((g["n_polls"] >= 3).sum())
        n_ge10  = int((g["n_polls"] >= 10).sum())
        max_polls = int(g["n_polls"].max())
        med_polls = float(g["n_polls"].median())
        rows.append({"year": yr, "n_munis": n_munis, "n_polls": n_polls,
                     "n_munis_ge3": n_ge3, "n_munis_ge10": n_ge10,
                     "max_polls": max_polls, "med_polls": med_polls})
    df = pd.DataFrame(rows)
    # Add total row
    both = set(p[p["ano"] == 2020]["sigla_uf"].astype(str) + "|" + p[p["ano"] == 2020]["nome_municipio"].astype(str)) & \
           set(p[p["ano"] == 2024]["sigla_uf"].astype(str) + "|" + p[p["ano"] == 2024]["nome_municipio"].astype(str))
    tot = {"year": "Both cycles", "n_munis": len(both), "n_polls": int(p["n_polls"].sum()),
           "n_munis_ge3": "", "n_munis_ge10": "", "max_polls": "", "med_polls": ""}
    df = pd.concat([df, pd.DataFrame([tot])], ignore_index=True)
    return df


def write_poder360_trajectory_tex(df: pd.DataFrame, path: Path) -> None:
    lines = [
        f"% {path.name} - auto-generated by 13_poll_coverage_report.py",
        "\\begin{tabular}{lrrrrrr}",
        "  \\toprule",
        "  Year & Municipalities & Total polls & $\\geq$3 polls & $\\geq$10 polls"
        " & Max polls & Median polls \\\\",
        "  \\midrule",
    ]
    for _, r in df.iterrows():
        def fmt(v):
            if v == "" or (isinstance(v, float) and np.isnan(v)):
                return "---"
            if isinstance(v, float):
                return f"{v:.1f}"
            return str(int(v)) if isinstance(v, (int, np.integer)) else str(v)
        lines.append(
            f"  {r['year']} & {fmt(r['n_munis'])} & {fmt(r['n_polls'])} & "
            f"{fmt(r['n_munis_ge3'])} & {fmt(r['n_munis_ge10'])} & "
            f"{fmt(r['max_polls'])} & {fmt(r['med_polls'])} \\\\"
        )
    lines += ["  \\bottomrule", "\\end{tabular}"]
    path.write_text("\n".join(lines), encoding="utf-8")


def make_maps(pan: pd.DataFrame) -> None:
    import geobr
    geo = geobr.read_municipality(code_muni="all", year=2020, simplified=True)
    geo["code_muni"] = geo["code_muni"].astype(float).astype("Int64").astype(str)

    make_category_map(pan, "polled_2020", "polled_2024",
                      "TSE registry: mayoral-poll coverage",
                      "poll_coverage_map_tse.png", geo)
    make_category_map(pan, "poder360_2020", "poder360_2024",
                      "Poder360: mayoral-poll coverage",
                      "poll_coverage_map_poder360.png", geo)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    pan = build_panel()

    summ = coverage_summary(pan)
    summ.to_csv(TAB / "poll_coverage_summary.csv", index=False)
    print("\n=== Coverage summary ===")
    print(summ.to_string(index=False))

    # TSE balance: polled-either vs not.
    bal = balance_table(pan, "polled_either")
    bal.to_csv(TAB / "poll_coverage_balance.csv", index=False)
    write_balance_tex(bal, TAB / "poll_coverage_balance.tex",
                      head_covered="Polled", head_uncovered="Unpolled")
    print("\n=== TSE balance: polled (either) vs unpolled ===")
    print(bal.to_string(index=False))

    # Poder360 balance: covered-either vs not.
    pan["poder360_either"] = (((pan.poder360_2020 == 1) |
                               (pan.poder360_2024 == 1)).astype(int))
    bal360 = balance_table(pan, "poder360_either")
    bal360.to_csv(TAB / "poder360_coverage_balance.csv", index=False)
    write_balance_tex(bal360, TAB / "poder360_coverage_balance.tex",
                      head_covered="Covered", head_uncovered="Not covered")
    print("\n=== Poder360 balance: covered (either) vs not ===")
    print(bal360.to_string(index=False))

    # Poder360 trajectory summary.
    print("\n=== Poder360 trajectory summary ===")
    traj = poder360_trajectory_summary()
    print(traj.to_string(index=False))
    write_poder360_trajectory_tex(traj, TAB / "poder360_trajectory_summary.tex")
    print(f"  saved poder360_trajectory_summary.tex")

    print("\n=== Maps ===")
    make_maps(pan)


if __name__ == "__main__":
    main()
