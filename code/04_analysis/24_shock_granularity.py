"""
24_shock_granularity.py — how many EFFECTIVE shocks does the act instrument have,
and what happens to that count (and the instrument) under a FINER shock partition?

Motivation: under the shift-exogeneity (BHJ) defense, consistency/inference are
driven by the EFFECTIVE NUMBER OF SHOCKS, not by the 5,009 municipalities. The
act design aggregates lawsuits into 10 families, which concentrates the Rotemberg
weights on ~3 shocks. This script:

  (1) reports the effective number of shocks for the CURRENT 10-family design two
      ways — exposure-based (BHJ inverse-HHI of mean exposure shares) and
      Rotemberg-based (inverse-HHI of |alpha|, which governs the point estimate);
  (2) rebuilds the leave-own-state-out Bartik instrument at three granularities
      — act10 (current), subject (cod_assunto), pair (class x subject) — and
      reports K, K_eff, and instrument summary for each.

It writes data/clean/shock_granularity_instruments.csv (muni x the three
instruments) so 24b_shock_granularity_fstage.R can run the on-spec first stage
for each. NO regressions here (regressions-in-R rule); only instrument
construction + share-concentration descriptives.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLEAN = os.path.join(ROOT, "data", "clean")


def inv_hhi(weights: np.ndarray) -> float:
    """Effective count = 1 / HHI of |weights| normalized to sum 1."""
    w = np.abs(weights)
    w = w[w > 0]
    if w.sum() == 0:
        return float("nan")
    p = w / w.sum()
    return 1.0 / np.sum(p ** 2)


def build_instrument(panel: pd.DataFrame, cell: str):
    """Leave-own-state-out Bartik at the granularity given by column `cell`.
    Returns (instrument_df, mean_exposure_shares, K)."""
    d = panel.copy()
    w = (d.groupby(["id_municipio_tse", "uf", cell, "election_year"])["n_proc"].sum()
         .unstack("election_year", fill_value=0).reset_index())
    w.columns.name = None
    for y in (2020, 2024):
        if y not in w:
            w[y] = 0
    w = w.rename(columns={2020: "n20", 2024: "n24"})
    tot = w.groupby("id_municipio_tse")["n20"].transform("sum")
    w["share"] = np.where(tot > 0, w["n20"] / tot, 0.0)
    nf = w.groupby(cell)[["n20", "n24"]].sum().rename(columns={"n20": "N20", "n24": "N24"})
    sf = w.groupby(["uf", cell])[["n20", "n24"]].sum().rename(columns={"n20": "S20", "n24": "S24"})
    w = w.merge(nf, on=cell).merge(sf, on=["uf", cell])
    w["g"] = np.log(w["N24"] - w["S24"] + 1) - np.log(w["N20"] - w["S20"] + 1)
    w["comp"] = w["share"] * w["g"]
    B = w.groupby("id_municipio_tse")["comp"].sum().reset_index(name="iv")

    # mean exposure share per cell (BHJ importance weight), over munis with any 2020 activity
    sbar = w.groupby(cell)["share"].mean()
    K = int((nf["N20"] > 0).sum())     # cells with national 2020 activity
    return B, sbar.values, K


def main():
    panel = pd.read_csv(os.path.join(CLEAN, "sig_lawsuits_muni_zona_classe_assunto.csv"),
                        dtype={"id_municipio_tse": str})
    xw = pd.read_csv(os.path.join(CLEAN, "act_family_crosswalk.csv"), dtype=str)
    xw["kept"] = xw["kept"].map({"True": True, "False": False})
    panel["pair_id"] = panel["pair_id"].astype(str)
    xw["pair_id"] = xw["pair_id"].astype(str)
    panel = panel.merge(xw[["pair_id", "cod_assunto", "fam_act10", "kept"]],
                        on="pair_id", how="left")
    panel["id_municipio_tse"] = panel["id_municipio_tse"].str.zfill(5)
    panel = panel[panel["kept"] == True].copy()

    # ---- (1) effective shock count for the CURRENT 10-family design ----------
    print("=== current 10-family design: effective number of shocks ===")
    shift = pd.read_csv(os.path.join(ROOT, "output", "tables", "descriptives",
                                     "shift_descriptives.csv"))
    keff_expo = 1.0 / np.sum((shift["s_k_bar_norm"]) ** 2)
    print(f"  exposure-based  K_eff = 1/HHI(mean shares)      = {keff_expo:.2f}")
    rot = pd.read_csv(os.path.join(ROOT, "output", "tables", "descriptives",
                                   "rotemberg_weights.csv"))
    keff_rot = inv_hhi(rot["alpha"].values)
    n_pos = (rot["alpha"] > 0).sum()
    top3 = rot.reindex(rot["alpha"].abs().sort_values(ascending=False).index).head(3)
    print(f"  Rotemberg-based K_eff = 1/HHI(|alpha|)          = {keff_rot:.2f}")
    print(f"  (10 nominal families; {n_pos} positive-weight; "
          f"top-3 by |alpha|: {', '.join(top3['topic_code'])})")

    # ---- (2) rebuild instrument at three granularities -----------------------
    GRAINS = [("act10", "fam_act10"), ("subject", "cod_assunto"), ("pair", "pair_id")]
    print("\n=== instrument under finer shock partitions ===")
    print(f"{'grain':10s} {'K cells':>8s} {'K_eff':>7s} {'iv mean':>9s} {'iv sd':>8s}")
    out = None
    for name, col in GRAINS:
        sub = panel[panel[col].notna()].copy()
        B, sbar, K = build_instrument(sub, col)
        keff = inv_hhi(sbar)
        print(f"{name:10s} {K:8d} {keff:7.2f} {B['iv'].mean():9.4f} {B['iv'].std():8.4f}")
        B = B.rename(columns={"iv": f"biv_{name}"})
        out = B if out is None else out.merge(B, on="id_municipio_tse", how="outer")

    out = out.rename(columns={"id_municipio_tse": "municipality_id_tse"})
    dst = os.path.join(CLEAN, "shock_granularity_instruments.csv")
    out.to_csv(dst, index=False, encoding="utf-8")
    print(f"\nWrote {dst}  ({len(out)} munis, instruments: "
          f"{', '.join('biv_'+g[0] for g in GRAINS)})")


if __name__ == "__main__":
    main()
