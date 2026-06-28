"""
30_sig_subject_shares.py — exploration (b), step 1: subject composition.

For the SIG municipality lawsuit panel, compute each Assunto's SHARE of lawsuits
at three aggregation levels, so we can see how the litigation portfolio looks and
whether the assunto field is a sensible basis for shift-share families:

  national_share   = sum_muni n_proc(subject) / sum_muni n_proc        (volume-weighted)
  state shares     = same, within each UF -> we report cross-state dispersion
  muni_mean_share  = mean over municipalities of the WITHIN-muni subject share
                     (equal-weights municipalities; municipalities with lawsuits
                      but none of this subject contribute 0). This is the object
                     the shift-share instrument actually uses.

The national vs muni_mean gap measures how concentrated a subject is in big
municipalities. Reads data/clean/sig_lawsuits_muni_zona_assunto.csv.
Run per year; default reports 2020 (the share base year) and writes both.
Output: output/tables/descriptives/sig_subject_shares_{year}.csv
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/clean/sig_lawsuits_muni_zona_assunto.csv"
OUT   = ROOT / "output/tables/descriptives"
OUT.mkdir(parents=True, exist_ok=True)
COUNT = "n_proc"   # could switch to n_proc_orig / n_proc_pre_eleic

def shares_for_year(df, year):
    d = df[df.election_year == year]
    # collapse to muni x subject (sum over zona)
    ms = d.groupby(["id_municipio", "assunto"])[COUNT].sum().reset_index()
    tot_nat = ms[COUNT].sum()

    # national share
    nat = ms.groupby("assunto")[COUNT].sum().rename("nat_n")
    nat_share = (nat / tot_nat).rename("national_share")

    # municipality-mean share (equal weight per muni; zeros included implicitly)
    muni_tot = ms.groupby("id_municipio")[COUNT].sum()
    ms = ms.assign(muni_tot=ms.id_municipio.map(muni_tot))
    ms["w_share"] = ms[COUNT] / ms.muni_tot
    n_munis = muni_tot[muni_tot > 0].size
    # sum of within-muni shares over munis that HAVE the subject, /all munis -> mean incl zeros
    muni_mean = (ms.groupby("assunto")["w_share"].sum() / n_munis).rename("muni_mean_share")
    n_munis_with = ms.groupby("assunto")["id_municipio"].nunique().rename("n_munis_with")

    # state-level shares -> cross-UF dispersion
    dd = d.copy()
    st = dd.groupby(["uf", "assunto"])[COUNT].sum()
    st_tot = dd.groupby("uf")[COUNT].sum()
    st_share = (st / st_tot).rename("st_share").reset_index()
    disp = st_share.groupby("assunto")["st_share"].agg(
        st_mean="mean", st_min="min", st_max="max",
        st_p25=lambda s: s.quantile(.25), st_p75=lambda s: s.quantile(.75)).reset_index()

    out = (pd.concat([nat, nat_share, muni_mean, n_munis_with], axis=1)
             .reset_index().merge(disp, on="assunto", how="left"))
    out["pct_munis_with"] = (out.n_munis_with / n_munis * 100).round(1)
    out = out.sort_values("national_share", ascending=False)
    out.insert(0, "election_year", year)
    return out, n_munis

def main():
    df = pd.read_csv(PANEL, dtype={"id_municipio": str})
    for year in sorted(df.election_year.unique()):
        out, n_munis = shares_for_year(df, year)
        f = OUT / f"sig_subject_shares_{year}.csv"
        out.to_csv(f, index=False)
        print(f"\n================ {year}  ({n_munis} municipalities) ================")
        print(f"distinct subjects: {len(out)} | wrote {f.name}")
        show = out.head(20)[["assunto","national_share","muni_mean_share",
                             "pct_munis_with","st_min","st_max"]].copy()
        for c in ["national_share","muni_mean_share","st_min","st_max"]:
            show[c] = (show[c]*100).round(2)
        show.columns = ["assunto","nat_%","muniMean_%","%munis","st_min_%","st_max_%"]
        with pd.option_context("display.width",160,"display.max_colwidth",46):
            print(show.to_string(index=False))
        topN = out.head(10).national_share.sum()*100
        print(f"top-10 subjects = {topN:.1f}% of all lawsuits")

if __name__ == "__main__":
    main()
