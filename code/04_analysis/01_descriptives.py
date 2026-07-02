"""
01_descriptives.py — descriptive statistics for the deck (merged).

PURPOSE: all descriptive TABLES describing the data (candidates, voters,
lawsuits, and the shift-share ingredients). Figures live in the R figure
scripts (02_descriptive_figures.R, 03_result_figures.R); this file only writes
CSV/MD tables. Three sections, each self-contained:

  [A] candidate_pool_descriptives()  — weighted candidate/elected pool means by
        office × year (+ vote-weighted executive demographics).
        -> descriptives/candidate_pool_descriptives.{csv,md}

  [B] overview_stats()               — lawsuit / voter / candidate "scale of the
        phenomenon" counts and ratios (feed the deck macros via 06_abstract_macros.py).
        -> descriptives/overview_{lawsuits,voters,candidates}.csv

  [C] shift_descriptives()           — BHJ (2024) checklist item 5: per-topic
        shifts g_k, importance weights s_k_bar, HHI / K_eff.
        -> descriptives/shift_descriptives.{csv,md}

Inputs:
  data/clean/office_candidate_outcomes_panel.csv
  data/clean/executive_vote_shift_share_design.csv
  data/clean/electoral_admin_outcomes.csv
  data/clean/municipality_bartik_components.csv
  data/estimation/executive_margin_design.csv

LAWSUIT SOURCE: all lawsuit counts (total / adversarial / non-adversarial) come
from the SIG-derived estimation panel (municipality-resolved). The Portal de
Dados Abertos `processo_eleitoral` files are RETIRED as a statistical source —
no paper number may come from them; only the text->code label bridge (a code
dictionary, in the builder) is a permitted Portal dependency. See memory:
sig_undercaptures_2024_coverage, framing_expanded_role_not_volume.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN        = PROJECT_ROOT / "data" / "clean"
ESTIMATION   = PROJECT_ROOT / "data" / "estimation"
OUT_DIR      = PROJECT_ROOT / "output" / "tables" / "descriptives"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2020, 2024]


# ============================================================================
# [A] CANDIDATE / ELECTED POOL DESCRIPTIVES
# ----------------------------------------------------------------------------
# Weighted means (weighted by total_candidates per municipality) for gender,
# race/ethnicity, education, and age — candidate pool and elected pool — for
# executive and legislative races in 2020 and 2024, plus vote-weighted
# executive demographics.
# ============================================================================
def _weighted_mean(series: pd.Series, weights: pd.Series) -> float:
    mask = series.notna() & weights.notna() & (weights > 0)
    return np.average(series[mask], weights=weights[mask])


def _pool_stats(df: pd.DataFrame, office: str, year: int) -> dict:
    sub = df[(df["office_group"] == office) & (df["election_year"] == year)].copy()
    w   = sub["total_candidates"]
    return {
        "office":    office,
        "year":      year,
        "n_municipalities": len(sub),
        # --- candidate pool ---
        "cand_female_share":          _weighted_mean(sub["female_share"], w),
        "cand_nonwhite_share":        _weighted_mean(sub["nonwhite_share"], w),
        "cand_higher_education_share": _weighted_mean(sub["higher_education_share"], w),
        "cand_mean_age":              _weighted_mean(sub["mean_age"], w),
        # --- elected pool ---
        "elected_female_share":          _weighted_mean(sub["elected_female_share"], w),
        "elected_nonwhite_share":        _weighted_mean(sub["elected_nonwhite_share"], w),
        "elected_higher_education_share": _weighted_mean(sub["elected_higher_education_share"], w),
        "elected_mean_age":              _weighted_mean(sub["elected_mean_age"], w),
        # --- incumbency ---
        "new_candidate_share":       _weighted_mean(sub["new_candidate_share"], w),
        "incumbent_candidate_share": _weighted_mean(sub["incumbent_candidate_share"], w),
        "incumbent_reelected_share": _weighted_mean(sub["incumbent_reelected_share"], w),
    }


def _vote_stats(vote: pd.DataFrame, year: int) -> dict:
    return {
        "female_vote_share":   vote[f"female_vote_share_{year}"].mean(),
        "nonwhite_vote_share": vote[f"nonwhite_vote_share_{year}"].mean(),
        "winner_is_female":    vote[f"winner_is_female_{year}"].mean(),
    }


def candidate_pool_descriptives() -> None:
    print("[A] Candidate / elected pool descriptives...")
    panel = pd.read_csv(CLEAN / "office_candidate_outcomes_panel.csv")
    vote  = pd.read_csv(CLEAN / "executive_vote_shift_share_design.csv")

    rows = []
    for office in ("executive", "legislative"):
        for year in (2020, 2024):
            rows.append(_pool_stats(panel, office, year))
    stats = pd.DataFrame(rows)

    for year in (2020, 2024):
        vs = _vote_stats(vote, year)
        mask = (stats["office"] == "executive") & (stats["year"] == year)
        for col, val in vs.items():
            stats.loc[mask, col] = val

    stats.to_csv(OUT_DIR / "candidate_pool_descriptives.csv", index=False)

    pct = lambda x: f"{x * 100:.1f}\\%" if pd.notna(x) else "---"
    dec = lambda x: f"{x:.1f}" if pd.notna(x) else "---"

    lines = [
        "# Candidate and Elected Pool Descriptives\n",
        "Weighted by total candidates per municipality.\n",
        "| Statistic | Exec 2020 | Exec 2024 | Leg 2020 | Leg 2024 |",
        "|-----------|-----------|-----------|----------|----------|",
    ]

    def row(label, col, fmt):
        vals = []
        for office, year in [("executive", 2020), ("executive", 2024),
                             ("legislative", 2020), ("legislative", 2024)]:
            mask = (stats["office"] == office) & (stats["year"] == year)
            v = stats.loc[mask, col].values
            vals.append(fmt(v[0]) if len(v) else "---")
        lines.append(f"| {label} | {' | '.join(vals)} |")

    lines.append("| **Candidate pool** | | | | |")
    row("Female share",          "cand_female_share",           pct)
    row("Nonwhite share",        "cand_nonwhite_share",         pct)
    row("Higher education",      "cand_higher_education_share", pct)
    row("Mean age (years)",      "cand_mean_age",               dec)
    lines.append("| **Elected pool** | | | | |")
    row("Female share",          "elected_female_share",          pct)
    row("Nonwhite share",        "elected_nonwhite_share",        pct)
    row("Higher education",      "elected_higher_education_share", pct)
    row("Mean age (years)",      "elected_mean_age",               dec)
    lines.append("| **Vote-weighted (executive only)** | | | | |")
    row("Female vote share",     "female_vote_share",   pct)
    row("Nonwhite vote share",   "nonwhite_vote_share", pct)
    row("Winner is female",      "winner_is_female",    pct)
    lines.append("| **Incumbency (exec 2024 only)** | | | | |")
    row("New candidate share",       "new_candidate_share",       pct)
    row("Incumbent candidate share", "incumbent_candidate_share", pct)
    row("Incumbent reelected share", "incumbent_reelected_share", pct)

    (OUT_DIR / "candidate_pool_descriptives.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  Saved candidate_pool_descriptives.{{csv,md}}")


# ============================================================================
# [B] OVERVIEW — lawsuits, voters, candidates ("scale of the phenomenon")
# ----------------------------------------------------------------------------
# Counts, totals, and derived ratios (lawsuits/candidate, lawsuits/voter) for
# 2020 and 2024. These feed the two "scale" slides via the deck macros.
# ============================================================================
def overview_stats() -> None:
    print("\n[B] Overview: lawsuits, voters, candidates...")

    # Lawsuit counts come ENTIRELY from the SIG-derived estimation panel
    # (municipality-resolved). total = adversarial (competition) + non-adversarial.
    # The Portal `zona_lawsuit_panel.csv` is retired (see module docstring).
    design = pd.read_csv(
        ESTIMATION / "executive_margin_design.csv",
        dtype={"municipality_id_tse": str},
        usecols=["municipality_id_tse",
                 "competition_lawsuits_2020",     "competition_lawsuits_2024",
                 "nonadversarial_lawsuits_2020",  "nonadversarial_lawsuits_2024"],
    )
    design["municipality_id_tse"] = design["municipality_id_tse"].str.zfill(5)
    adm  = pd.read_csv(CLEAN / "electoral_admin_outcomes.csv")
    cand = pd.read_csv(CLEAN / "office_candidate_outcomes_panel.csv",
                       dtype={"municipality_id_tse": str})
    cand["municipality_id_tse"] = cand["municipality_id_tse"].str.zfill(5)

    # -- 1. lawsuits (all from SIG) --
    # Candidate totals are election-SPECIFIC (2020 divides by 2020 candidates,
    # 2024 by 2024) and count ALL municipal candidates (mayor+vice+councillor).
    cand_by_muni = (
        cand[cand.election_year.isin(YEARS)]
        .groupby(["election_year", "municipality_id_tse"])["total_candidates"].sum()
    )
    rows = []
    for y in YEARS:
        adv_col, nad_col = f"competition_lawsuits_{y}", f"nonadversarial_lawsuits_{y}"
        adv_tot = float(design[adv_col].sum())
        nad_tot = float(design[nad_col].sum())
        # municipality-unit adversarial intensity (per 1,000 candidates), over
        # municipalities that fielded >=1 candidate in year y. This is the
        # paper's UNIT; the national ratio below is size-weighted (big-city heavy).
        cby = cand_by_muni.loc[y]
        adv_muni = design.set_index("municipality_id_tse")[adv_col].reindex(cby.index).fillna(0.0)
        contested = cby > 0
        per1000 = (adv_muni[contested] / cby[contested] * 1000)
        rows.append({
            "election_year":            y,
            "total_lawsuits":           adv_tot + nad_tot,
            "adversarial_lawsuits":     adv_tot,
            "nonadversarial_lawsuits":  nad_tot,
            "n_munis_any_lawsuit":      int(((design[adv_col] + design[nad_col]) > 0).sum()),
            "n_munis_adversarial":      int((design[adv_col] > 0).sum()),
            # municipality-unit distribution
            "adv_per_1000cand_muni_mean":   float(per1000.mean()),
            "adv_per_1000cand_muni_median": float(per1000.median()),
            "share_munis_with_adv_pct":     float((adv_muni[contested] > 0).mean() * 100),
        })
    lawsuits = pd.DataFrame(rows)

    voters_by_year = (
        adm[adm.election_year.isin(YEARS)]
        .groupby("election_year")
        .agg(
            registered_voters = ("registered_voters", "sum"),
            turnout_count     = ("turnout_count",      "sum"),
        )
        .reset_index()
    )
    cand_totals = (
        cand[cand.election_year.isin(YEARS)]
        .groupby("election_year")["total_candidates"]
        .sum()
        .reset_index()
        .rename(columns={"total_candidates": "total_candidates_all"})
    )

    lawsuits = (
        lawsuits
        .merge(voters_by_year, on="election_year")
        .merge(cand_totals,    on="election_year")
    )
    lawsuits["share_adversarial_pct"]      = lawsuits["adversarial_lawsuits"] / lawsuits["total_lawsuits"] * 100
    lawsuits["share_munis_exposed_pct"]    = lawsuits["n_munis_adversarial"]  / 5570 * 100
    lawsuits["all_lawsuits_per_candidate"] = lawsuits["total_lawsuits"]       / lawsuits["total_candidates_all"]
    lawsuits["adv_lawsuits_per_candidate"] = lawsuits["adversarial_lawsuits"] / lawsuits["total_candidates_all"]
    # national (size-weighted) adversarial per 1,000 candidates
    lawsuits["adv_per_1000cand_national"]  = lawsuits["adv_lawsuits_per_candidate"] * 1000
    lawsuits["adv_per_registered_voter"]   = lawsuits["adversarial_lawsuits"] / lawsuits["registered_voters"]
    lawsuits["adv_per_voter_who_voted"]    = lawsuits["adversarial_lawsuits"] / lawsuits["turnout_count"]
    lawsuits["registered_voters_per_adv"]  = lawsuits["registered_voters"]    / lawsuits["adversarial_lawsuits"]
    lawsuits["voters_voted_per_adv"]       = lawsuits["turnout_count"]        / lawsuits["adversarial_lawsuits"]
    lawsuits = lawsuits.drop(columns=["registered_voters", "turnout_count", "total_candidates_all"])
    lawsuits.to_csv(OUT_DIR / "overview_lawsuits.csv", index=False)
    print(lawsuits.to_string(index=False))

    # -- 2. voters --
    voters = (
        adm[adm.election_year.isin(YEARS)]
        .groupby("election_year")
        .agg(
            registered_voters = ("registered_voters", "sum"),
            turnout_count     = ("turnout_count",      "sum"),
            abstentions_count = ("abstentions_count",  "sum"),
            blank_votes       = ("blank_votes",         "sum"),
            null_votes        = ("null_votes",           "sum"),
            valid_votes       = ("valid_votes",          "sum"),
            n_munis           = ("municipality_id_tse",  "nunique"),
        )
        .reset_index()
    )
    voters["turnout_rate_pct"]    = voters["turnout_count"]     / voters["registered_voters"] * 100
    voters["abstention_rate_pct"] = voters["abstentions_count"] / voters["registered_voters"] * 100
    voters["blank_rate_pct"]      = voters["blank_votes"]       / voters["turnout_count"]      * 100
    voters["null_rate_pct"]       = voters["null_votes"]        / voters["turnout_count"]      * 100
    voters["valid_rate_pct"]      = voters["valid_votes"]       / voters["turnout_count"]      * 100
    voters.to_csv(OUT_DIR / "overview_voters.csv", index=False)
    print(voters.to_string(index=False))

    # -- 3. candidates --
    candidates = (
        cand[cand.election_year.isin(YEARS)]
        .groupby(["election_year", "office_group"])
        .apply(lambda g: pd.Series({
            "total_candidates":   g["total_candidates"].sum(),
            "elected_candidates": g["elected_candidates"].sum(),
            "female_share_pct":   (
                (g["female_share"] * g["total_candidates"]).sum()
                / g["total_candidates"].sum() * 100
            ),
            "nonwhite_share_pct": (
                (g["nonwhite_share"] * g["total_candidates"]).sum()
                / g["total_candidates"].sum() * 100
            ),
            "higher_ed_share_pct": (
                (g["higher_education_share"] * g["total_candidates"]).sum()
                / g["total_candidates"].sum() * 100
            ),
            "n_munis": g["municipality_id_tse"].nunique(),
        }), include_groups=False)
        .reset_index()
    )
    candidates["elected_rate_pct"] = (
        candidates["elected_candidates"] / candidates["total_candidates"] * 100
    )
    candidates.to_csv(OUT_DIR / "overview_candidates.csv", index=False)
    print(candidates.to_string(index=False))


# ============================================================================
# [B2] LITIGATION COMPOSITION — coverage-robust "change of composition" facts
# ----------------------------------------------------------------------------
# The SIG count level is contaminated by a 2024 coverage artifact (see memory
# sig_undercaptures_2024_coverage), so we do NOT report a count trend. Volume is
# flat; the story is RECOMPOSITION. This table reports only coverage-robust
# ratios/shares that survive the artifact:
#   (1) WHEN  — post-election share of adversarial filings (timing shift)
#   (2) HOW FAR — appeal escalation rate (recursal / originario)
#   (3) WHAT — within-adversarial composition by topic family
# Computed from raw SIG via the builder's own helpers, so the adversarial
# universe is byte-identical to the instrument.
# ============================================================================
def _load_builder():
    """Import the SIG builder module (filename starts with a digit)."""
    path = PROJECT_ROOT / "code" / "02_build" / "02_shift_share_design.py"
    spec = importlib.util.spec_from_file_location("ss_builder", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def litigation_composition() -> None:
    print("\n[B2] Litigation composition (coverage-robust, from SIG)...")
    m = _load_builder()
    class_map, subject_map, _ = m.build_label_code_bridges()
    crosswalk = m.load_crosswalk()
    fam_map = dict(zip(crosswalk["CD_ASSUNTO_PRINCIPAL"], crosswalk["topic_family"]))

    sig = m.load_sig_lawsuits()
    sig["qt_proc"] = pd.to_numeric(sig["qt_proc"], errors="coerce").fillna(0.0)
    sig["dt_dist"] = pd.to_datetime(sig["data_dist"], errors="coerce")
    sig["CD_CLASSE"]             = sig["classe"].map(m.norm_label).map(class_map)
    sig["CD_ASSUNTO_PRINCIPAL"]  = sig["assunto"].map(m.norm_label).map(subject_map)
    sig["orig"]     = sig["tipo_origem"].str.startswith("Origin", na=False)
    sig["recursal"] = sig["tipo_origem"].str.startswith("Recurs", na=False)
    sig["pre"]      = sig["dt_dist"] < sig["election_year"].map(m.SIG_ELECTION_DAY)
    sig["bridged"]  = sig["CD_CLASSE"].notna() & sig["CD_ASSUNTO_PRINCIPAL"].notna()
    sig["adv"]      = sig["bridged"] & ~(sig["CD_CLASSE"].isin(m.DROP_CLASSES)
                                         | sig["CD_ASSUNTO_PRINCIPAL"].isin(m.DROP_SUBJECTS))
    sig["family"]   = sig["CD_ASSUNTO_PRINCIPAL"].map(fam_map)

    cand = pd.read_csv(CLEAN / "office_candidate_outcomes_panel.csv",
                       usecols=["election_year", "total_candidates"])
    cand_tot = cand.groupby("election_year")["total_candidates"].sum()

    V = lambda d: float(d["qt_proc"].sum())

    # (1)+(2) year-level coverage-robust ratios ------------------------------------
    advo = sig[sig["orig"] & sig["adv"]]                       # adversarial, originario
    rows = []
    for y in YEARS:
        d      = advo[advo["election_year"] == y]
        pre, post = V(d[d["pre"]]), V(d[~d["pre"]])
        orig_all = V(sig[(sig["election_year"] == y) & sig["orig"] & sig["bridged"]])
        rec_all  = V(sig[(sig["election_year"] == y) & sig["recursal"] & sig["bridged"]])
        rec_adv  = V(sig[(sig["election_year"] == y) & sig["recursal"] & sig["adv"]])
        rows.append({
            "election_year":            y,
            "post_election_share_adv":  post / (pre + post) if (pre + post) else np.nan,
            "appeal_escalation_rate":   rec_all / orig_all if orig_all else np.nan,
            "adv_appeals":              rec_adv,
            "adv_appeals_per_1000cand": rec_adv / cand_tot[y] * 1000,
        })
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT_DIR / "litigation_composition.csv", index=False)
    print(comp.to_string(index=False))

    # timing panel for 02_descriptive_figures.R (the label bridge stays HERE in
    # Python; R only plots). Daily aggregation of ALL originário filings, with a
    # total and an adversarial count, and days relative to the first-round vote.
    tim = sig[sig["orig"] & sig["bridged"]].copy()
    tim["days_rel"] = (tim["dt_dist"] - tim["election_year"].map(m.SIG_ELECTION_DAY)).dt.days
    tim = tim.dropna(subset=["days_rel"])
    tim["days_rel"] = tim["days_rel"].astype(int)
    tim["adv_qt"]   = tim["qt_proc"].where(tim["adv"], 0.0)
    timagg = (tim.groupby(["election_year", "days_rel"])
                 .agg(total_qt=("qt_proc", "sum"), adv_qt=("adv_qt", "sum"))
                 .reset_index())
    timagg.to_csv(OUT_DIR / "litigation_timing_panel.csv", index=False)
    print(f"  Saved litigation_timing_panel.csv ({len(timagg):,} day-year rows)")

    # (3) within-adversarial family composition (share of adversarial) -------------
    fam = (advo[advo["pre"]].groupby(["election_year", "family"])["qt_proc"].sum()
           .unstack("election_year", fill_value=0.0))
    for y in YEARS:
        if y not in fam.columns:
            fam[y] = 0.0
    for y in YEARS:
        fam[f"share_{y}"] = fam[y] / fam[y].sum()
    fam = fam.sort_values(2024, ascending=False).reset_index()
    fam.to_csv(OUT_DIR / "litigation_family_shares.csv", index=False)

    # markdown summary -------------------------------------------------------------
    c20 = comp[comp.election_year == 2020].iloc[0]
    c24 = comp[comp.election_year == 2024].iloc[0]
    pp = lambda a, b: f"{(b - a) * 100:+.1f} pp"
    md = [
        "# Litigation Composition — coverage-robust facts (SIG)\n",
        "Volume is flat (no count trend reported — SIG 2024 under-captures; see",
        "`sig_undercaptures_2024_coverage`). The change is in COMPOSITION.\n",
        "| Coverage-robust ratio | 2020 | 2024 | Change |",
        "|---|---|---|---|",
        f"| Post-election share of adversarial | {c20['post_election_share_adv']*100:.1f}\\% "
        f"| {c24['post_election_share_adv']*100:.1f}\\% | {pp(c20['post_election_share_adv'], c24['post_election_share_adv'])} |",
        f"| Appeal escalation (recursal/originário) | {c20['appeal_escalation_rate']*100:.2f}\\% "
        f"| {c24['appeal_escalation_rate']*100:.2f}\\% | {pp(c20['appeal_escalation_rate'], c24['appeal_escalation_rate'])} |",
        f"| Adversarial appeals per 1,000 cand. | {c20['adv_appeals_per_1000cand']:.1f} "
        f"| {c24['adv_appeals_per_1000cand']:.1f} | {c24['adv_appeals_per_1000cand']/c20['adv_appeals_per_1000cand']-1:+.1%} |",
        "",
        "## Within-adversarial composition by family (share of adversarial)",
        "",
        "| Family | 2020 | 2024 | Change |",
        "|---|---|---|---|",
    ]
    for _, r in fam.iterrows():
        md.append(f"| {r['family']} | {r['share_2020']*100:.1f}\\% | {r['share_2024']*100:.1f}\\% "
                  f"| {pp(r['share_2020'], r['share_2024'])} |")
    (OUT_DIR / "litigation_composition.md").write_text("\n".join(md), encoding="utf-8")
    print("  Saved litigation_composition.{csv,md} + litigation_family_shares.csv")


# ============================================================================
# [C] SHIFT DESCRIPTIVES — BHJ (2024) checklist item 5
# ----------------------------------------------------------------------------
# Per-topic shift g_k, importance weight s_k_bar, HHI contribution; summary
# HHI / K_eff / n positive vs negative shocks.
# ============================================================================
def shift_descriptives() -> None:
    print("\n[C] Shift descriptives (BHJ item 5)...")

    design = pd.read_csv(
        ESTIMATION / "executive_margin_design.csv",
        dtype={"municipality_id_tse": str},
        low_memory=False,
        usecols=["municipality_id_tse", "bartik_iv_2020_2024"],
    )
    design["municipality_id_tse"] = design["municipality_id_tse"].astype(str).str.zfill(5)
    samp_ids = set(design.dropna(subset=["bartik_iv_2020_2024"])["municipality_id_tse"])
    N = len(samp_ids)
    print(f"  Analysis sample: {N:,} municipalities")

    comp = pd.read_csv(
        CLEAN / "municipality_bartik_components.csv",
        dtype={"municipality_id_tse": str, "main_subject_code": str},
        low_memory=False,
    )
    comp["municipality_id_tse"] = comp["municipality_id_tse"].str.zfill(5)
    comp = comp[comp["municipality_id_tse"].isin(samp_ids)].copy()

    comp["n_lawsuits"] = pd.to_numeric(comp["n_lawsuits"], errors="coerce").fillna(0)
    comp["shock"]      = pd.to_numeric(
        comp["shock_log_growth_2020_2024"], errors="coerce"
    ).fillna(0)

    base_totals = comp.groupby("municipality_id_tse")["n_lawsuits"].transform("sum")
    comp["share"] = comp["n_lawsuits"] / base_totals.replace(0, np.nan)

    topics = sorted(comp["main_subject_code"].unique())
    K = len(topics)
    print(f"  Topics after exclusion: {K}")

    rows = []
    for k in topics:
        sub = comp[comp["main_subject_code"] == k].copy()
        sub = sub.dropna(subset=["share"])
        n_munis = sub["municipality_id_tse"].nunique()
        mean_share_local = sub["share"].mean()
        g_mean = sub["shock"].mean()
        g_sd   = sub["shock"].std()
        g_p10  = sub["shock"].quantile(0.10)
        g_p25  = sub["shock"].quantile(0.25)
        g_p50  = sub["shock"].median()
        g_p75  = sub["shock"].quantile(0.75)
        g_p90  = sub["shock"].quantile(0.90)
        topic_name   = sub["main_subject_name"].iloc[0]
        topic_family = sub["topic_family"].iloc[0] if "topic_family" in sub.columns else ""
        rows.append({
            "topic_code":   k,
            "topic_name":   topic_name,
            "topic_family": topic_family,
            "n_munis":      n_munis,
            "g_mean":       g_mean, "g_sd": g_sd,
            "g_p10": g_p10, "g_p25": g_p25, "g_p50": g_p50, "g_p75": g_p75, "g_p90": g_p90,
            "mean_share_local": mean_share_local,
        })
    df = pd.DataFrame(rows)

    pivot = comp.pivot_table(
        index="municipality_id_tse", columns="main_subject_code",
        values="share", fill_value=0.0,
    ).reindex(list(samp_ids), fill_value=0.0)
    s_k_bar = pivot.mean(axis=0)
    s_k_bar_norm = s_k_bar / s_k_bar.sum()

    df["s_k_bar"]      = df["topic_code"].map(s_k_bar)
    df["s_k_bar_norm"] = df["topic_code"].map(s_k_bar_norm)
    df["s_k_bar2"]     = df["s_k_bar_norm"] ** 2

    hhi   = df["s_k_bar2"].sum()
    k_eff = 1.0 / hhi
    n_pos = (df["g_mean"] > 0).sum()
    n_neg = (df["g_mean"] < 0).sum()
    print(f"  HHI = {hhi:.4f}  ->  K_eff = {k_eff:.2f}  (pos {n_pos}, neg {n_neg} of {K})")

    df = df.sort_values("s_k_bar_norm", ascending=False).reset_index(drop=True)
    df.to_csv(OUT_DIR / "shift_descriptives.csv", index=False, encoding="utf-8-sig")

    md = []
    md.append("# Shift Descriptives — Adversarial Bartik IV")
    md.append("")
    md.append("BHJ (2024) checklist item 5: distribution of shifts g_k and importance weights s_k_bar.")
    md.append("")
    md.append(f"**K** = {K} topics | **N** = {N:,} municipalities")
    md.append(f"| HHI (importance) | K_eff | Positive shifts | Negative shifts |")
    md.append(f"| --- | --- | --- | --- |")
    md.append(f"| {hhi:.4f} | {k_eff:.2f} | {n_pos} | {n_neg} |")
    md.append("")
    md.append("## Per-Topic Statistics (sorted by importance weight)")
    md.append("")
    hdr = ["Code", "Topic (truncated)", "Family", "N munis",
           "s̄_k (%)", "g_mean", "g_sd", "g_p10", "g_p50", "g_p90", "HHI contrib"]
    md.append("| " + " | ".join(hdr) + " |")
    md.append("| " + " | ".join(["---"] * len(hdr)) + " |")
    for _, r in df.iterrows():
        md.append("| " + " | ".join([
            r["topic_code"],
            r["topic_name"][:40],
            r["topic_family"][:20] if r["topic_family"] else "",
            str(int(r["n_munis"])),
            f"{r['s_k_bar_norm']*100:.2f}%",
            f"{r['g_mean']:+.3f}",
            f"{r['g_sd']:.3f}",
            f"{r['g_p10']:+.3f}",
            f"{r['g_p50']:+.3f}",
            f"{r['g_p90']:+.3f}",
            f"{r['s_k_bar2']:.4f}",
        ]) + " |")
    md.append("")
    md.append("## Notes")
    md.append("- `s̄_k` = mean share of topic k across all N municipalities (including zeros), re-normalised to sum to 1.")
    md.append("- `g_k` = leave-state-out log growth 2020→2024 for topic k; values vary by municipality (own-state excluded).")
    md.append("  Statistics above are computed across municipalities that have the topic in 2020.")
    md.append("- **HHI** = Σ_k (s̄_k)² — measures concentration of instrument in few topics.")
    md.append("  K_eff = 1/HHI is the effective number of topics driving the Bartik estimate.")
    md.append("- BHJ (2024) criterion: K_eff >> 1 needed for exposure-robust SE asymptotics.")
    md.append(f"  Here K_eff = {k_eff:.2f} → GPS share-exogeneity identification is the primary justification.")
    (OUT_DIR / "shift_descriptives.md").write_text("\n".join(md), encoding="utf-8")
    print(f"  Saved shift_descriptives.{{csv,md}}")


def main() -> None:
    candidate_pool_descriptives()
    overview_stats()
    litigation_composition()
    shift_descriptives()
    print("\nDone. Outputs saved to:", OUT_DIR)


if __name__ == "__main__":
    main()
