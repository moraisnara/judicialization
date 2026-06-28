"""
01d_act_family_ivs.py — assemble the ACT-BASED instrument design (data construction).

Builds the act-based 10-family Bartik instrument and its matching endogenous
treatment from the locked crosswalk (code/02_build/01d_act_family_crosswalk.py)
and merges them onto the executive-margin design. NO regressions here — the 2SLS
is run in R (02c_act_iv.R), per the regressions-in-R rule.

Outputs data/estimation/act_design.csv = executive_margin_design.csv + two columns:
  - bartik_iv_act           : sum_k s_ik(2020 share) * g_ik(leave-own-state-out shock)
  - delta_log1p_act_lawsuits: dlog(1 + kept act-family lawsuits), the endogenous treatment

ALSO writes data/clean/municipality_act_components.csv — the long municipality x
family decomposition of the instrument (one row per muni x act family), the single
source for the Rotemberg / shift / balance / leave-one-family-out diagnostics. Its
schema mirrors the retired municipality_family_components.csv so those scripts
repoint with a path + rung swap:
  id_municipio_tse, uf, rung(="act"), family, L2020, L2024, share2020,
  shift_leavestate, bartik_component, delta_log1p_family

See the [[act_family_design_2026-06-26]] design note. Diagnostics: K_eff 6.8, F~26.7.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def build_act_instrument():
    panel = pd.read_csv(f"{ROOT}/data/clean/sig_lawsuits_muni_zona_classe_assunto.csv",
                        dtype={"id_municipio_tse": str})
    xw = pd.read_csv(f"{ROOT}/data/clean/act_family_crosswalk.csv")
    panel = panel.merge(xw[["pair_id", "fam_act10", "kept"]], on="pair_id", how="left")
    panel["id_municipio_tse"] = panel["id_municipio_tse"].str.zfill(5)
    d = panel[panel["kept"] == True].rename(columns={"fam_act10": "fam"}).copy()

    w = (d.groupby(["id_municipio_tse", "uf", "fam", "election_year"])["n_proc"].sum()
         .unstack("election_year", fill_value=0).reset_index())
    w.columns.name = None
    for y in (2020, 2024):
        if y not in w:
            w[y] = 0
    w = w.rename(columns={2020: "n20", 2024: "n24"})
    tot = w.groupby("id_municipio_tse")["n20"].transform("sum")
    w["share"] = np.where(tot > 0, w["n20"] / tot, 0.0)
    nf = w.groupby("fam")[["n20", "n24"]].sum().rename(columns={"n20": "N20", "n24": "N24"})
    sf = w.groupby(["uf", "fam"])[["n20", "n24"]].sum().rename(columns={"n20": "S20", "n24": "S24"})
    w = w.merge(nf, on="fam").merge(sf, on=["uf", "fam"])
    w["g"] = np.log(w["N24"] - w["S24"] + 1) - np.log(w["N20"] - w["S20"] + 1)
    w["comp"] = w["share"] * w["g"]
    B = w.groupby("id_municipio_tse")["comp"].sum().reset_index(name="bartik_iv_act")

    L = (d.groupby(["id_municipio_tse", "election_year"])["n_proc"].sum()
         .unstack("election_year", fill_value=0))
    for y in (2020, 2024):
        if y not in L:
            L[y] = 0
    dY = (np.log1p(L[2024]) - np.log1p(L[2020])).rename("delta_log1p_act_lawsuits").reset_index()

    # long municipality x family components (single source for the diagnostics)
    comp = w.rename(columns={"fam": "family", "n20": "L2020", "n24": "L2024",
                             "share": "share2020", "g": "shift_leavestate",
                             "comp": "bartik_component"}).copy()
    comp["rung"] = "act"
    comp["delta_log1p_family"] = np.log1p(comp["L2024"]) - np.log1p(comp["L2020"])
    comp = comp[["id_municipio_tse", "uf", "rung", "family", "L2020", "L2024",
                 "share2020", "shift_leavestate", "bartik_component",
                 "delta_log1p_family"]]
    return B.merge(dY, on="id_municipio_tse"), comp


def main():
    des = pd.read_csv(f"{ROOT}/data/estimation/executive_margin_design.csv",
                      dtype={"municipality_id_tse": str, "state": str, "cluster_id": str})
    iv, comp = build_act_instrument()
    iv = iv.rename(columns={"id_municipio_tse": "municipality_id_tse"})
    df = des.merge(iv, on="municipality_id_tse", how="left")
    out = f"{ROOT}/data/estimation/act_design.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    comp_out = f"{ROOT}/data/clean/municipality_act_components.csv"
    comp.to_csv(comp_out, index=False, encoding="utf-8")
    n = df["bartik_iv_act"].notna().sum()
    print(f"act_design: {len(df)} municipalities, {n} with instrument")
    print(f"  bartik_iv_act: mean={df['bartik_iv_act'].mean():.4f} sd={df['bartik_iv_act'].std():.4f}")
    print(f"  wrote {out}")
    print(f"  wrote {comp_out} ({len(comp)} muni x family rows, "
          f"{comp['family'].nunique()} families)")


if __name__ == "__main__":
    main()
