
"""
Extended heterogeneity analysis: ideology shift, electoral volatility,
incumbent reelection, and female-new-entrant outcomes.

IV specification identical to 08_tighten_executive_margin_analysis.py.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR     = PROJECT_ROOT / "data" / "clean"
REGRESSIONS_DIR = PROJECT_ROOT / "output" / "tables" / "regressions"
COVARIATES_PATH = CLEAN_DIR / "municipal_covariates.csv"
ADMIN_PATH      = CLEAN_DIR / "electoral_admin_outcomes.csv"

# Zucco-Power (2021) left-right scores (1=far left, 10=far right).
# Year-specific because some party codes changed between 2020 and 2024
# (e.g., PODE = 19 in 2020, = 20 in 2024 after PSC became AGIR).
IDEOLOGY_2020: dict[int, float] = {
    50: 1.5,  # PSOL
    65: 2.0,  # PC do B
    13: 3.0,  # PT
    18: 4.0,  # REDE
    40: 4.0,  # PSB
    12: 4.5,  # PDT
    43: 4.5,  # PV
    23: 5.0,  # Cidadania
    15: 5.0,  # MDB
    33: 5.0,  # PMN (now MOBILIZA)
    14: 5.5,  # PTB
    77: 5.5,  # SOLIDARIEDADE
    70: 5.5,  # AVANTE
    90: 5.5,  # PROS
    35: 5.5,  # PMB
    27: 6.0,  # DC
    36: 6.0,  # PTC (now AGIR)
    19: 6.0,  # PODE (code 19 in 2020)
    45: 6.5,  # PSDB
    10: 6.5,  # Republicanos
    55: 6.5,  # PSD
    20: 7.0,  # PSC (code 20 in 2020)
    25: 7.0,  # DEM (code 25 in 2020)
    11: 7.0,  # PP
    51: 7.0,  # PATRIOTA
    17: 7.5,  # PSL (code 17 in 2020, merged into UNIÃO 2022)
    22: 8.0,  # PL
    28: 8.0,  # PRTB
    30: 9.0,  # NOVO
}

IDEOLOGY_2024: dict[int, float] = {
    50: 1.5,  # PSOL
    65: 2.0,  # PC do B
    13: 3.0,  # PT
    18: 4.0,  # REDE
    40: 4.0,  # PSB
    12: 4.5,  # PDT
    43: 4.5,  # PV
    23: 5.0,  # Cidadania
    15: 5.0,  # MDB
    33: 5.0,  # MOBILIZA (formerly PMN)
    77: 5.5,  # SOLIDARIEDADE
    70: 5.5,  # AVANTE
    35: 5.5,  # PMB
    27: 6.0,  # DC
    36: 6.0,  # AGIR (formerly PTC/PSC)
    20: 6.0,  # PODE (code 20 in 2024)
    45: 6.5,  # PSDB
    10: 6.5,  # Republicanos
    55: 6.5,  # PSD
    25: 7.0,  # PRD (formerly DEM, code 25)
    11: 7.0,  # PP
    44: 7.0,  # UNIÃO BRASIL (DEM + PSL merger, 2022)
    22: 8.0,  # PL
    28: 8.0,  # PRTB
    30: 9.0,  # NOVO
}

NEW_OUTCOMES = [
    "delta_winner_ideology_2024_2020",
    "pedersen_volatility",
    "incumbent_candidate_vote_share_2024",
    "incumbent_reelected_share_2024",
    "female_new_entrant_share_2024",
    "female_new_entrant_vote_share_2024",
    # incumbency outcomes from municipal_covariates (not controls)
    "incumbent_ran_2024",
    "incumbent_won_2024",
    "party_switch_2024",
]


# ---------------------------------------------------------------------------
# Data loading (mirrors script 08)
# ---------------------------------------------------------------------------

def load_design() -> pd.DataFrame:
    df = pd.read_csv(
        CLEAN_DIR / "executive_vote_shift_share_design.csv",
        dtype={"SG_UE": str},
        low_memory=False,
    )
    return (
        df.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg({col: "first" for col in df.columns if col not in {"SG_UF", "SG_UE"}})
    )


def load_candidate_panel() -> pd.DataFrame:
    return pd.read_csv(
        CLEAN_DIR / "candidate_vote_panel.csv",
        dtype={"SG_UE": str},
        low_memory=False,
    )


# ---------------------------------------------------------------------------
# Zone-structure and controls (identical to script 08)
# ---------------------------------------------------------------------------

def add_zone_structure(df: pd.DataFrame) -> pd.DataFrame:
    lookup_path = PROJECT_ROOT / "data" / "raw" / "lista-zonas-municipios-10-07-24.csv"
    lookup = pd.read_csv(lookup_path, sep=";", encoding="utf-8-sig", dtype=str)
    lookup.columns = lookup.columns.str.strip()
    lookup = lookup.rename(columns={"UF": "SG_UF", "ZONA": "zona_eleitoral", "COD_LOCALIDADE": "COD_MUN"})
    lookup = lookup[lookup["SG_UF"] != "ZZ"].copy()
    lookup["SG_UE"] = lookup["COD_MUN"].str.strip().str.zfill(5)
    lookup["zona_eleitoral"] = pd.to_numeric(lookup["zona_eleitoral"], errors="coerce")
    zone_info = (
        lookup.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(
            n_zones_in_municipality=("zona_eleitoral", "nunique"),
            principal_zone=("zona_eleitoral", "min"),
        )
    )
    zone_info["principal_zone_id"] = (
        zone_info["SG_UF"].astype(str)
        + "_"
        + zone_info["principal_zone"].astype("Int64").astype(str)
    )
    return df.merge(zone_info, on=["SG_UF", "SG_UE"], how="left", validate="one_to_one")


def add_controls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["total_candidates_2020", "party_count_2020", "coalition_count_2020", "total_valid_votes_2020"]:
        if col in df.columns:
            df[f"log1p_{col}"] = np.log1p(df[col])
    df["log1p_n_zones_in_municipality"] = np.log1p(df["n_zones_in_municipality"].fillna(1))
    return df


def get_control_cols(df: pd.DataFrame) -> list[str]:
    """Baseline controls: 7 variables. Mirrors get_baseline_controls() in script 08."""
    desired = [
        # Census 2010 — predetermined structural
        "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
        # 2016 pre-trend
        "margin_2016",
        # 2020 electoral baseline
        "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
        "log1p_total_candidates_2020",
    ]
    return [col for col in desired if col in df.columns]


def with_state_fe(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    X = df[cols].copy()
    dummies = pd.get_dummies(df["SG_UF"], prefix="uf", drop_first=True, dtype=float)
    return pd.concat([X, dummies], axis=1)


def make_full_rank_exog(exog: pd.DataFrame, endog: pd.Series) -> pd.DataFrame:
    exog = exog.astype(float).copy()
    endog_values = endog.astype(float).to_numpy().reshape(-1, 1)
    selected: list[str] = []
    current_rank = np.linalg.matrix_rank(endog_values)
    for col in exog.columns:
        trial = np.column_stack([endog_values, exog[selected + [col]].to_numpy()])
        if np.linalg.matrix_rank(trial) > current_rank:
            selected.append(col)
            current_rank = np.linalg.matrix_rank(trial)
    return exog[selected]


# ---------------------------------------------------------------------------
# New-variable construction
# ---------------------------------------------------------------------------

def build_ideology_vars(panel: pd.DataFrame) -> pd.DataFrame:
    exec_panel = panel[panel["office_group"] == "executive"].copy()
    winners = exec_panel[exec_panel["is_elected"] == 1].copy()

    for year, mapping in [(2020, IDEOLOGY_2020), (2024, IDEOLOGY_2024)]:
        sub = winners[winners["ANO_ELEICAO"] == year].copy()
        sub["ideology"] = sub["NR_PARTIDO"].map(mapping)
        agg = (
            sub.groupby(["SG_UF", "SG_UE"])["ideology"]
            .first()
            .reset_index()
            .rename(columns={"ideology": f"winner_ideology_{year}"})
        )
        if year == 2020:
            out = agg
        else:
            out = out.merge(agg, on=["SG_UF", "SG_UE"], how="outer")

    out["delta_winner_ideology_2024_2020"] = (
        out["winner_ideology_2024"] - out["winner_ideology_2020"]
    )
    return out[["SG_UF", "SG_UE", "winner_ideology_2020", "winner_ideology_2024",
                "delta_winner_ideology_2024_2020"]]


def build_pedersen_index(panel: pd.DataFrame) -> pd.DataFrame:
    exec_panel = panel[panel["office_group"] == "executive"].copy()

    party_shares = (
        exec_panel.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE", "NR_PARTIDO"])["vote_share"]
        .sum()
        .reset_index()
    )
    wide_2020 = (
        party_shares[party_shares["ANO_ELEICAO"] == 2020]
        .rename(columns={"vote_share": "share_2020"})
        .drop("ANO_ELEICAO", axis=1)
    )
    wide_2024 = (
        party_shares[party_shares["ANO_ELEICAO"] == 2024]
        .rename(columns={"vote_share": "share_2024"})
        .drop("ANO_ELEICAO", axis=1)
    )
    wide = pd.merge(wide_2020, wide_2024, on=["SG_UF", "SG_UE", "NR_PARTIDO"], how="outer").fillna(0)
    wide["abs_diff"] = (wide["share_2024"] - wide["share_2020"]).abs()

    pedersen = (
        wide.groupby(["SG_UF", "SG_UE"])["abs_diff"]
        .sum()
        .div(2)
        .reset_index()
        .rename(columns={"abs_diff": "pedersen_volatility"})
    )
    return pedersen


def build_female_new_entrant(panel: pd.DataFrame) -> pd.DataFrame:
    exec_2024 = panel[
        (panel["office_group"] == "executive") & (panel["ANO_ELEICAO"] == 2024)
    ].copy()
    exec_2024["is_female_new"] = (
        exec_2024["is_female"].astype(bool) & exec_2024["is_new_candidate_vs_2020"].astype(bool)
    )

    total = (
        exec_2024.groupby(["SG_UF", "SG_UE"])["SQ_CANDIDATO"]
        .nunique()
        .reset_index(name="total_candidates_2024")
    )

    fem_new_sub = exec_2024[exec_2024["is_female_new"]]
    fem_new = (
        fem_new_sub.groupby(["SG_UF", "SG_UE"])
        .agg(
            female_new_count=("SQ_CANDIDATO", "nunique"),
            female_new_entrant_vote_share_2024=("vote_share", "sum"),
        )
        .reset_index()
    )

    out = total.merge(fem_new, on=["SG_UF", "SG_UE"], how="left").fillna(0)
    out["female_new_entrant_share_2024"] = (
        out["female_new_count"] / out["total_candidates_2024"].clip(lower=1)
    )
    return out[["SG_UF", "SG_UE", "female_new_entrant_share_2024",
                "female_new_entrant_vote_share_2024"]]


# ---------------------------------------------------------------------------
# IV estimation (identical spec to script 08)
# ---------------------------------------------------------------------------

def run_iv(
    df: pd.DataFrame, outcome_col: str, sample_name: str, family: str
) -> dict[str, float | int | str]:
    exog = with_state_fe(df, get_control_cols(df))
    exog = exog.loc[:, exog.nunique(dropna=False) > 1]
    endog = df["delta_log1p_lawsuits_no_rrc_2024_2020"].astype(float)
    exog = make_full_rank_exog(exog, endog)
    exog = sm.add_constant(exog.astype(float), has_constant="add")
    model = IV2SLS(
        df[outcome_col].astype(float),
        exog,
        endog,
        df["bartik_iv_no_rrc"].astype(float),
    ).fit(cov_type="clustered", clusters=df["cluster_id"])
    endog_name = "delta_log1p_lawsuits_no_rrc_2024_2020"
    return {
        "sample": sample_name,
        "family": family,
        "outcome": outcome_col,
        "coef": float(model.params[endog_name]),
        "se": float(model.std_errors[endog_name]),
        "t": float(model.tstats[endog_name]),
        "p": float(model.pvalues[endog_name]),
        "nobs": int(model.nobs),
        "n_clusters": int(df["cluster_id"].nunique()),
    }


def prepare_samples(df: pd.DataFrame, outcomes: list[str]) -> dict[str, pd.DataFrame]:
    needed = (
        ["bartik_iv_no_rrc", "delta_log1p_lawsuits_no_rrc_2024_2020", "cluster_id"]
        + get_control_cols(df)
        + outcomes
    )
    needed = [c for c in needed if c in df.columns]
    all_sample = df.dropna(subset=needed).copy()
    single_zone = all_sample[all_sample["n_zones_in_municipality"] == 1].copy()
    return {
        "all_principal_zone_cluster": all_sample,
        "single_zone_exact_cluster": single_zone,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    REGRESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    design = add_controls(add_zone_structure(load_design()))
    design["cluster_id"] = design["principal_zone_id"]

    # Rebuild no-RRC treatment/instrument columns (must match script 08 exactly)
    components = pd.read_csv(
        CLEAN_DIR / "municipality_bartik_components.csv",
        dtype={"SG_UE": str, "CD_ASSUNTO_PRINCIPAL": str},
        low_memory=False,
    )
    subject_panel = pd.read_csv(
        CLEAN_DIR / "municipality_competition_subject_panel.csv",
        dtype={"SG_UE": str, "CD_ASSUNTO_PRINCIPAL": str},
        low_memory=False,
    )
    EXCLUDE_RRC = {"11618"}
    comp_alt = components[~components["CD_ASSUNTO_PRINCIPAL"].isin(EXCLUDE_RRC)].copy()
    # Re-normalize shares over the non-RRC topic universe so they sum to 1 per municipality.
    comp_alt["n_lawsuits"] = pd.to_numeric(comp_alt["n_lawsuits"], errors="coerce").fillna(0)
    comp_alt["shock_log_growth_2020_2024"] = pd.to_numeric(comp_alt["shock_log_growth_2020_2024"], errors="coerce").fillna(0)
    base_totals_no_rrc = comp_alt.groupby(["SG_UF", "SG_UE"])["n_lawsuits"].transform("sum")
    comp_alt["baseline_share_no_rrc_2020"] = comp_alt["n_lawsuits"] / base_totals_no_rrc
    comp_alt["bartik_component_no_rrc"] = comp_alt["baseline_share_no_rrc_2020"] * comp_alt["shock_log_growth_2020_2024"]
    bartik_alt = (
        comp_alt.groupby(["SG_UF", "SG_UE"], as_index=False)
        .agg(bartik_iv_no_rrc=("bartik_component_no_rrc", "sum"))
    )
    sp_alt = subject_panel[~subject_panel["CD_ASSUNTO_PRINCIPAL"].isin(EXCLUDE_RRC)]
    totals = (
        sp_alt.groupby(["ANO_ELEICAO", "SG_UF", "SG_UE"], as_index=False)
        .agg(lawsuits=("n_lawsuits", "sum"))
    )
    wide = (
        totals.pivot_table(index=["SG_UF", "SG_UE"], columns="ANO_ELEICAO",
                           values="lawsuits", fill_value=0)
        .rename(columns={2020: "lawsuits_no_rrc_2020", 2024: "lawsuits_no_rrc_2024"})
        .reset_index()
    )
    for col in ["lawsuits_no_rrc_2020", "lawsuits_no_rrc_2024"]:
        if col not in wide.columns:
            wide[col] = 0
    wide["delta_log1p_lawsuits_no_rrc_2024_2020"] = (
        np.log1p(wide["lawsuits_no_rrc_2024"]) - np.log1p(wide["lawsuits_no_rrc_2020"])
    )
    design = (
        design.merge(bartik_alt, on=["SG_UF", "SG_UE"], how="left", suffixes=("", "_y"))
        .merge(wide, on=["SG_UF", "SG_UE"], how="left", suffixes=("", "_y"))
    )
    for col in ["bartik_iv_no_rrc", "delta_log1p_lawsuits_no_rrc_2024_2020"]:
        if col not in design.columns and f"{col}_y" in design.columns:
            design[col] = design[f"{col}_y"]
        design[col] = design[col].fillna(0)

    # Merge new municipal covariates (keep incumbency columns as outcomes, not controls)
    cov = pd.read_csv(COVARIATES_PATH, dtype={"SG_UE": str}, low_memory=False)
    cov["SG_UE"] = cov["SG_UE"].str.zfill(5)
    drop_cov = {"NM_UE", "winner_party_2016", "winner_sq_2016", "winner_name_2016",
                "winner_party_2020"}
    design = design.merge(cov[[c for c in cov.columns if c not in drop_cov]],
                          on=["SG_UF", "SG_UE"], how="left")

    # Merge 2020 voter behavior baseline for controls
    adm = pd.read_csv(ADMIN_PATH, dtype={"SG_UE": str}, low_memory=False)
    adm["SG_UE"] = adm["SG_UE"].str.zfill(5)
    adm["ANO_ELEICAO"] = pd.to_numeric(adm["ANO_ELEICAO"], errors="coerce")
    adm_2020 = adm[adm["ANO_ELEICAO"] == 2020][["SG_UF", "SG_UE",
                                                  "turnout_rate", "null_share", "blank_share"]].copy()
    adm_2020 = adm_2020.rename(columns={"turnout_rate": "turnout_rate_2020",
                                         "null_share": "null_share_2020",
                                         "blank_share": "blank_share_2020"})
    if "turnout_rate_2020" not in design.columns:
        design = design.merge(adm_2020, on=["SG_UF", "SG_UE"], how="left")

    # Build new outcome variables from the candidate panel
    panel = load_candidate_panel()
    ideology = build_ideology_vars(panel)
    pedersen = build_pedersen_index(panel)
    fem_new = build_female_new_entrant(panel)

    design = (
        design
        .merge(ideology, on=["SG_UF", "SG_UE"], how="left")
        .merge(pedersen, on=["SG_UF", "SG_UE"], how="left")
        .merge(fem_new, on=["SG_UF", "SG_UE"], how="left")
    )

    outcomes = [c for c in NEW_OUTCOMES if c in design.columns]
    missing = [c for c in NEW_OUTCOMES if c not in design.columns]
    if missing:
        print(f"WARNING: outcomes not found in design: {missing}")

    iv_rows: list[dict] = []
    for outcome in outcomes:
        samples = prepare_samples(design, [outcome])
        for sample_name, sample_df in samples.items():
            if outcome in ["incumbent_candidate_vote_share_2024",
                           "incumbent_reelected_share_2024",
                           "incumbent_ran_2024", "incumbent_won_2024",
                           "party_switch_2024"]:
                family = "incumbent"
            elif "ideology" in outcome:
                family = "ideology"
            elif "pedersen" in outcome:
                family = "volatility"
            elif "female" in outcome:
                family = "female_entry"
            else:
                family = "other"
            iv_rows.append(run_iv(sample_df, outcome, sample_name, family))

    results = pd.DataFrame(iv_rows)
    results.to_csv(
        REGRESSIONS_DIR / "extended_heterogeneity_iv.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Summary report
    def stars(p: float) -> str:
        if p < 0.01:
            return "***"
        elif p < 0.05:
            return "**"
        elif p < 0.10:
            return "*"
        return ""

    lines = [
        "# Extended Heterogeneity IV Results",
        "",
        "Instrument: bartik_iv_no_rrc (excludes RRC-Candidato lawsuits, subject 11618).",
        "Treatment: delta_log1p_lawsuits_no_rrc_2024_2020.",
        "Clustering: principal electoral zone (all sample) / exact zone (single-zone sample).",
        "",
    ]
    for family in ["ideology", "volatility", "incumbent", "female_entry"]:
        sub = results[results["family"] == family]
        if sub.empty:
            continue
        lines.append(f"## {family}")
        lines.append("")
        lines.append("| outcome | sample | coef | se | t | p | sig | N | clusters |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for _, row in sub.iterrows():
            lines.append(
                f"| {row['outcome']} | {row['sample']} "
                f"| {row['coef']:.4f} | {row['se']:.4f} "
                f"| {row['t']:.3f} | {row['p']:.3f} "
                f"| {stars(row['p'])} "
                f"| {int(row['nobs']):,} | {int(row['n_clusters']):,} |"
            )
        lines.append("")

    (REGRESSIONS_DIR / "extended_heterogeneity_iv.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("Results saved to:")
    print(f"  {REGRESSIONS_DIR / 'extended_heterogeneity_iv.csv'}")
    print(f"  {REGRESSIONS_DIR / 'extended_heterogeneity_iv.md'}")


if __name__ == "__main__":
    main()
