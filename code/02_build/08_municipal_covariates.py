"""
Builds the municipal covariates master table by merging:
  1. Census 2010 covariates (log_pop, urban_share, log_income_pc)
  2. 2016 electoral controls (n_candidates, margin, hhi, enp, winner info)
  3. Candidate experience panel, 2020 wave
  4. Electoral admin outcomes, 2020 wave (turnout, null/blank share)

The incumbency flag (incumbent_ran_2024, incumbent_won_2024) is built here
by cross-referencing the 2020 mayoral winner with the 2024 candidate list.

All covariates are pre-determined relative to 2024 (the outcome year).

Output: data/clean/municipal_covariates.csv
Key columns:
  SG_UF, SG_UE, NM_UE              municipality identifiers
  log_pop_2010                      Census 2010 log population
  urban_share_2010                  Census 2010 urban share
  log_income_pc_2010                Census 2010 log income per capita
  n_candidates_2016                 2016 number of mayoral candidates
  margin_2016                       2016 winner-runnerup margin
  hhi_2016                          2016 HHI
  enp_2016                          2016 effective number of candidates
  share_first_time_candidates_2020  candidate experience (2020)
  mean_prior_candidacies_2020       candidate experience (2020)
  share_career_politicians_2020     candidate experience (2020)
  turnout_rate_2020                 electoral admin (2020)
  null_share_2020                   electoral admin (2020)
  blank_share_2020                  electoral admin (2020)
  incumbent_ran_2024                1 if 2020 winner appeared as 2024 candidate
  incumbent_won_2024                1 if 2020 winner also won in 2024
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DERIVED_DIR = PROJECT_ROOT / "data" / "clean"


def normalize(s: object) -> str:
    t = "" if pd.isna(s) else str(s).strip().upper()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return " ".join(t.split())


def load_consulta_cand(year: int) -> pd.DataFrame:
    folder = RAW_DIR / f"consulta_cand_{year}"
    files = sorted(folder.glob(f"consulta_cand_{year}_BRASIL.csv"))
    if not files:
        files = sorted(folder.glob(f"consulta_cand_{year}_*.csv"))
        files = [f for f in files if "leiame" not in f.name.lower()]
    if not files:
        return pd.DataFrame()

    frames = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath, sep=";", encoding="latin-1",
                             usecols=lambda c: c in [
                                 "ANO_ELEICAO", "SG_UF", "SG_UE", "NM_UE",
                                 "DS_CARGO", "CD_TIPO_ELEICAO", "NR_TURNO",
                                 "NR_TITULO_ELEITORAL_CANDIDATO",
                                 "NM_CANDIDATO", "DT_NASCIMENTO",
                                 "DS_SIT_TOT_TURNO", "SG_PARTIDO",
                             ],
                             dtype=str, low_memory=False)
            frames.append(df)
        except Exception as e:
            print(f"  WARNING: {fpath.name}: {e}", flush=True)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    if "CD_TIPO_ELEICAO" in df.columns:
        df = df[df["CD_TIPO_ELEICAO"] == "2"].copy()
    if "NR_TURNO" in df.columns:
        df = df[df["NR_TURNO"] == "1"].copy()
    if "DS_CARGO" in df.columns:
        df = df[df["DS_CARGO"].str.upper().str.contains("PREFEITO", na=False)].copy()

    df["ANO_ELEICAO"] = year
    df["title_key"] = df["NR_TITULO_ELEITORAL_CANDIDATO"].fillna("").str.strip()
    df["title_key"] = df["title_key"].replace({"#NULO#": "", "-4": "", "-1": ""})
    df["NM_CANDIDATO_norm"] = df["NM_CANDIDATO"].map(normalize)
    df["DT_NASC_norm"] = pd.to_datetime(
        df.get("DT_NASCIMENTO", ""), format="%d/%m/%Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d").fillna("")
    df["person_key"] = df["title_key"].where(
        df["title_key"].str.len() > 3,
        df["NM_CANDIDATO_norm"] + "|" + df["DT_NASC_norm"],
    )

    ELECTED = {"ELEITO", "ELEITO POR QP", "ELEITO POR MÉDIA",
               "ELEITO POR MEDIA", "ELEITO POR MÉ DIA"}
    df["is_elected"] = (
        df["DS_SIT_TOT_TURNO"].str.upper().str.strip().isin(ELECTED)
    ).astype(int)

    return df


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. Census 2010
    # ------------------------------------------------------------------ #
    print("[1] Loading Census 2010 covariates", flush=True)
    censo = pd.read_csv(DERIVED_DIR / "censo2010_municipal_ibge.csv", dtype=str)
    censo["code_muni_6"] = censo["code_muni"].str[:6]
    print(f"    {len(censo):,} municipalities", flush=True)

    # ------------------------------------------------------------------ #
    # 2. 2016 electoral controls
    # ------------------------------------------------------------------ #
    print("[2] Loading 2016 electoral controls", flush=True)
    ctrl2016 = pd.read_csv(DERIVED_DIR / "electoral_controls_2016.csv", dtype=str)
    ctrl2016["SG_UE"] = ctrl2016["SG_UE"].str.zfill(5)
    for col in ["n_candidates_2016", "top1_share_2016", "margin_2016",
                "hhi_2016", "enp_2016"]:
        ctrl2016[col] = pd.to_numeric(ctrl2016[col], errors="coerce")
    print(f"    {len(ctrl2016):,} municipalities", flush=True)

    # ------------------------------------------------------------------ #
    # 3. Candidate experience — 2020 wave
    # ------------------------------------------------------------------ #
    print("[3] Loading candidate experience panel (2020 wave)", flush=True)
    cexp = pd.read_csv(DERIVED_DIR / "candidate_experience_panel.csv", dtype=str)
    cexp["ANO_ELEICAO"] = pd.to_numeric(cexp["ANO_ELEICAO"], errors="coerce")
    cexp_2020 = cexp[cexp["ANO_ELEICAO"] == 2020].copy()
    cexp_2020["SG_UE"] = cexp_2020["SG_UE"].str.zfill(5)
    for col in ["share_first_time_candidates", "mean_prior_candidacies",
                "share_prior_winners", "share_career_politicians", "n_candidates"]:
        cexp_2020[col] = pd.to_numeric(cexp_2020[col], errors="coerce")
    cexp_2020 = cexp_2020.rename(columns={
        "share_first_time_candidates": "share_first_time_candidates_2020",
        "mean_prior_candidacies":      "mean_prior_candidacies_2020",
        "share_prior_winners":         "share_prior_winners_2020",
        "share_career_politicians":    "share_career_politicians_2020",
        "n_candidates":                "n_candidates_experience_2020",
    })
    print(f"    {len(cexp_2020):,} municipalities", flush=True)

    # ------------------------------------------------------------------ #
    # 4. Electoral admin outcomes — 2020 wave
    # ------------------------------------------------------------------ #
    print("[4] Loading electoral admin outcomes (2020 wave)", flush=True)
    adm = pd.read_csv(DERIVED_DIR / "electoral_admin_outcomes.csv", dtype=str)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")
    adm_2020 = adm[adm["ANO_ELEICAO"] == 2020].copy()
    adm_2020["SG_UE"] = adm_2020["SG_UE"].str.zfill(5)
    for col in ["turnout_rate", "abstention_rate", "blank_share", "null_share"]:
        adm_2020[col] = pd.to_numeric(adm_2020[col], errors="coerce")
    adm_2020 = adm_2020.rename(columns={
        "turnout_rate":    "turnout_rate_2020",
        "abstention_rate": "abstention_rate_2020",
        "blank_share":     "blank_share_2020",
        "null_share":      "null_share_2020",
    })
    print(f"    {len(adm_2020):,} municipalities", flush=True)

    # ------------------------------------------------------------------ #
    # 5. Incumbency flags: 2020 winner appeared / won in 2024
    # ------------------------------------------------------------------ #
    print("[5] Building incumbency flags", flush=True)
    cand_2020 = load_consulta_cand(2020)
    cand_2024 = load_consulta_cand(2024)

    if not cand_2020.empty and not cand_2024.empty:
        winners_2020 = (
            cand_2020[cand_2020["is_elected"] == 1]
            .drop_duplicates(subset=["SG_UF", "SG_UE"])
            [["SG_UF", "SG_UE", "person_key", "SG_PARTIDO"]]
            .rename(columns={"person_key": "winner_key_2020",
                             "SG_PARTIDO": "winner_party_2020"})
        )
        winners_2020["SG_UE"] = winners_2020["SG_UE"].str.zfill(5)

        cands_2024_keys = (
            cand_2024[["SG_UF", "SG_UE", "person_key", "is_elected", "SG_PARTIDO"]]
            .copy()
        )
        cands_2024_keys["SG_UE"] = cands_2024_keys["SG_UE"].str.zfill(5)
        cands_2024_keys["SG_PARTIDO"] = cands_2024_keys["SG_PARTIDO"].fillna("")

        # Did the 2020 winner run in 2024?
        ran = (
            cands_2024_keys.groupby(["SG_UF", "SG_UE"])["person_key"]
            .apply(set)
            .reset_index()
            .rename(columns={"person_key": "keys_2024"})
        )
        won_2024 = (
            cands_2024_keys[cands_2024_keys["is_elected"] == 1]
            .drop_duplicates(subset=["SG_UF", "SG_UE"])
            [["SG_UF", "SG_UE", "person_key", "SG_PARTIDO"]]
            .rename(columns={"person_key": "winner_key_2024",
                             "SG_PARTIDO": "winner_party_2024"})
        )
        won_2024["SG_UE"] = won_2024["SG_UE"].str.zfill(5)

        incumbency = winners_2020.merge(ran, on=["SG_UF", "SG_UE"], how="left")
        incumbency["incumbent_ran_2024"] = incumbency.apply(
            lambda r: int(r["winner_key_2020"] in r["keys_2024"])
            if isinstance(r["keys_2024"], set) else 0,
            axis=1,
        )
        incumbency = incumbency.merge(won_2024, on=["SG_UF", "SG_UE"], how="left")
        incumbency["incumbent_won_2024"] = (
            incumbency["winner_key_2020"] == incumbency["winner_key_2024"]
        ).astype(int)
        incumbency["party_switch_2024"] = (
            (incumbency["winner_party_2020"].fillna("") !=
             incumbency["winner_party_2024"].fillna("")) &
            incumbency["winner_party_2024"].notna()
        ).astype(int)

        incumbency = incumbency[["SG_UF", "SG_UE",
                                 "incumbent_ran_2024", "incumbent_won_2024",
                                 "party_switch_2024"]]
        print(f"    2020 winners matched: {len(incumbency):,}", flush=True)
        print(f"    incumbent_ran_2024 mean: {incumbency['incumbent_ran_2024'].mean():.3f}",
              flush=True)
        print(f"    incumbent_won_2024 mean: {incumbency['incumbent_won_2024'].mean():.3f}",
              flush=True)
    else:
        print("    WARNING: consulta_cand files not available; incumbency skipped.", flush=True)
        incumbency = pd.DataFrame(columns=["SG_UF", "SG_UE",
                                           "incumbent_ran_2024", "incumbent_won_2024",
                                           "party_switch_2024"])

    # ------------------------------------------------------------------ #
    # 6. Assemble on (SG_UF, SG_UE)
    # ------------------------------------------------------------------ #
    print("\n[6] Assembling final covariate table", flush=True)

    # Base: 2016 controls define the municipality universe
    base = ctrl2016[["SG_UF", "SG_UE", "NM_UE",
                     "n_candidates_2016", "top1_share_2016",
                     "margin_2016", "hhi_2016", "enp_2016",
                     "winner_party_2016", "winner_sq_2016", "winner_name_2016"]].copy()

    def merge_on_ue(left, right, suffix=""):
        cols = [c for c in right.columns if c not in ("SG_UF", "SG_UE", "NM_UE",
                                                        "ANO_ELEICAO")]
        return left.merge(
            right[["SG_UF", "SG_UE"] + cols],
            on=["SG_UF", "SG_UE"], how="left"
        )

    # Join Census: censobr uses IBGE numeric state codes and municipality names.
    # TSE uses state abbreviations (SG_UF) and NM_UE. Match on state+name.
    IBGE_STATE_TO_UF = {
        11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
        21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE",
        27: "AL", 28: "SE", 29: "BA",
        31: "MG", 32: "ES", 33: "RJ", 35: "SP",
        41: "PR", 42: "SC", 43: "RS",
        50: "MS", 51: "MT", 52: "GO", 53: "DF",
    }
    censo_merge = censo[["abbrev_state", "name_muni", "code_micro", "name_micro",
                          "log_pop_2010", "urban_share_2010",
                          "log_income_pc_2010"]].copy()
    for col in ["log_pop_2010", "urban_share_2010", "log_income_pc_2010"]:
        censo_merge[col] = pd.to_numeric(censo_merge[col], errors="coerce")
    censo_merge["SG_UF"] = (
        pd.to_numeric(censo_merge["abbrev_state"], errors="coerce")
        .map(IBGE_STATE_TO_UF)
    )
    censo_merge["name_muni_norm"] = censo_merge["name_muni"].map(normalize)
    censo_merge = censo_merge.drop(columns=["abbrev_state", "name_muni"])

    base["name_muni_norm"] = base["NM_UE"].map(normalize)
    base = base.merge(
        censo_merge,
        on=["SG_UF", "name_muni_norm"],
        how="left",
    )
    base = base.drop(columns=["name_muni_norm"])

    n_matched = base["log_pop_2010"].notna().sum()
    print(f"  Census matched: {n_matched:,}/{len(base):,} municipalities "
          f"({100*n_matched/len(base):.1f}%)", flush=True)

    base = merge_on_ue(base, cexp_2020[[
        "SG_UF", "SG_UE",
        "share_first_time_candidates_2020", "mean_prior_candidacies_2020",
        "share_prior_winners_2020", "share_career_politicians_2020",
    ]])

    base = merge_on_ue(base, adm_2020[[
        "SG_UF", "SG_UE",
        "turnout_rate_2020", "abstention_rate_2020",
        "blank_share_2020", "null_share_2020",
    ]])

    if not incumbency.empty:
        base = merge_on_ue(base, incumbency)

    print(f"  Final rows: {len(base):,}", flush=True)

    # Report merge rates
    for col in ["log_pop_2010", "margin_2016",
                "share_first_time_candidates_2020",
                "turnout_rate_2020", "incumbent_ran_2024"]:
        if col in base.columns:
            n_miss = base[col].isna().sum()
            pct = 100 * n_miss / len(base)
            print(f"  {col}: {n_miss:,} missing ({pct:.1f}%)", flush=True)

    out = DERIVED_DIR / "municipal_covariates.csv"
    base.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
