"""
31_sig_class_shares.py — exploration (b), step 2: CLASS composition.

Identical metrics to 30_sig_subject_shares.py but on the procedural-CLASS panel,
so assunto vs classe can be compared on the same three aggregation levels:
  national_share (volume-weighted), state shares (cross-UF dispersion),
  muni_mean_share (equal-weights municipalities; the shift-share object).
Reads data/clean/sig_lawsuits_muni_zona_classe.csv.
Output: output/tables/descriptives/sig_class_shares_{year}.csv
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/clean/sig_lawsuits_muni_zona_classe.csv"
OUT   = ROOT / "output/tables/descriptives"
OUT.mkdir(parents=True, exist_ok=True)
COUNT, DIM = "n_proc", "classe"

def shares_for_year(df, year):
    d = df[df.election_year == year]
    ms = d.groupby(["id_municipio", DIM])[COUNT].sum().reset_index()
    tot_nat = ms[COUNT].sum()
    nat = ms.groupby(DIM)[COUNT].sum().rename("nat_n")
    nat_share = (nat / tot_nat).rename("national_share")
    muni_tot = ms.groupby("id_municipio")[COUNT].sum()
    ms = ms.assign(muni_tot=ms.id_municipio.map(muni_tot))
    ms["w_share"] = ms[COUNT] / ms.muni_tot
    n_munis = muni_tot[muni_tot > 0].size
    muni_mean = (ms.groupby(DIM)["w_share"].sum() / n_munis).rename("muni_mean_share")
    n_munis_with = ms.groupby(DIM)["id_municipio"].nunique().rename("n_munis_with")
    st = d.groupby(["uf", DIM])[COUNT].sum()
    st_tot = d.groupby("uf")[COUNT].sum()
    st_share = (st / st_tot).rename("st_share").reset_index()
    disp = st_share.groupby(DIM)["st_share"].agg(
        st_mean="mean", st_min="min", st_max="max",
        st_p25=lambda s: s.quantile(.25), st_p75=lambda s: s.quantile(.75)).reset_index()
    out = (pd.concat([nat, nat_share, muni_mean, n_munis_with], axis=1)
             .reset_index().merge(disp, on=DIM, how="left"))
    out["pct_munis_with"] = (out.n_munis_with / n_munis * 100).round(1)
    out = out.sort_values("national_share", ascending=False)
    out.insert(0, "election_year", year)
    return out, n_munis

def main():
    df = pd.read_csv(PANEL, dtype={"id_municipio": str})
    for year in sorted(df.election_year.unique()):
        out, n_munis = shares_for_year(df, year)
        f = OUT / f"sig_class_shares_{year}.csv"
        out.to_csv(f, index=False)
        print(f"\n================ {year}  ({n_munis} municipalities) ================")
        print(f"distinct classes: {len(out)} | wrote {f.name}")
        show = out.head(18)[[DIM,"national_share","muni_mean_share",
                             "pct_munis_with","st_min","st_max"]].copy()
        for c in ["national_share","muni_mean_share","st_min","st_max"]:
            show[c] = (show[c]*100).round(2)
        show.columns = ["classe","nat_%","muniMean_%","%munis","st_min_%","st_max_%"]
        with pd.option_context("display.width",170,"display.max_colwidth",52):
            print(show.to_string(index=False))
        print(f"top-10 classes = {out.head(10).national_share.sum()*100:.1f}% of all lawsuits")

if __name__ == "__main__":
    main()
