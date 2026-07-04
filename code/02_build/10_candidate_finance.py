"""
Builds the municipality-level campaign-finance mechanism panel from TSE SPCE
(Sistema de Prestacao de Contas Eleitorais) contracted-expenses microdata.

Mechanism under test (Phase 3): RESOURCE DRAIN / ATTRITION. If adversarial
litigation drains a challenger's campaign resources faster than the front-runner's,
the front-runner pulls away and the mayoral top-two margin widens WITHOUT the field
or the winner changing (which is exactly the consolidation pattern the IV finds, and
which entry-deterrence -- rejected by compositional neutrality -- cannot explain).

Design (Nara 2026-07-03):
  * MAYORAL race only (CD_CARGO == 11, prefeito).
  * Spending is cut BY VOTE RANK: front-runner (rank 1) vs challenger (rank 2),
    linking SPCE SQ_CANDIDATO -> candidate_vote_panel.candidate_id, ranking on
    candidate_vote_total within municipality x year.
  * Categories: total, marketing (traditional + online), and legal (advocaticios).
  * 2020 values deflated to 2024 R$ (IPCA cumulative 2021-2024).
  * Outputs 2020/2024 levels + delta_log1p, plus the challenger spending SHARE
    (ch / (fr + ch)) whose fall is the sharpest attrition signature.
  The open-seat x contested split is applied downstream in the R estimation using
  open_seat_2024 already carried in the design.

Input : data/raw/spce_candidatos_{2020,2024}/despesas_contratadas_candidatos_*_BRASIL.csv
        data/clean/candidate_vote_panel.csv
Output: data/clean/candidate_finance_panel.csv   (one row per municipality)
Key columns:
  municipality_id_tse
  fr_total_2020/2024, ch_total_2020/2024, muni_total_2020/2024        (real R$, contracted)
  fr_mkt_2020/2024,   ch_mkt_2020/2024                                (marketing R$)
  delta_log1p_fr_total, delta_log1p_ch_total, delta_log1p_muni_total,
  delta_log1p_fr_mkt,   delta_log1p_ch_mkt
  ch_spend_share_2020/2024, delta_ch_spend_share                      (challenger share of top-2 spend)
  n_exec_cand_with_spend_2020/2024
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

YEARS = (2020, 2024)
MAYOR_CARGO = "11"                      # CD_CARGO for prefeito
CHUNK = 500_000

# IBGE IPCA cumulative inflation 2021-2024 (1.1006*1.0579*1.0462*1.0483). Deflates
# 2020 nominal R$ to 2024 price level so the 2020->2024 delta is real. Refine with the
# exact monthly index (campaign window to campaign window) if a level claim needs it.
DEFLATOR_2020_TO_2024 = 1.277

SPCE_COLS = ["CD_CARGO", "DS_ORIGEM_DESPESA", "VR_DESPESA_CONTRATADA", "SQ_CANDIDATO"]


def _norm(s: str) -> str:
    """lower + strip accents, for robust category keyword matching."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().strip()


# marketing = the visible campaign spend litigation would crowd out
_MKT_ONLINE = ("impulsionamento", "paginas na internet", "pagina na internet",
               "criacao e inclusao de paginas")
_MKT_TRAD = ("publicidade", "jingle", "vinheta", "slogan", "programas de radio",
             "comicio", "eventos de promocao")
_LEGAL = ("advocaticio",)


def _categorize(desc_norm: str) -> str:
    if any(k in desc_norm for k in _MKT_ONLINE):
        return "mkt_online"
    if any(k in desc_norm for k in _MKT_TRAD):
        return "mkt_trad"
    if any(k in desc_norm for k in _LEGAL):
        return "legal"
    return "other"


def _parse_brl(series: pd.Series) -> pd.Series:
    """'1.234,56' -> 1234.56 ; blanks/#NULO -> 0."""
    s = series.fillna("").str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def load_candidate_spend(year: int) -> pd.DataFrame:
    """Per-mayoral-candidate contracted spend, by category, for one year."""
    path = (RAW_DIR / f"spce_candidatos_{year}"
            / f"despesas_contratadas_candidatos_{year}_BRASIL.csv")
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, sep=";", encoding="latin-1", usecols=SPCE_COLS,
                             dtype=str, chunksize=CHUNK):
        chunk = chunk[chunk["CD_CARGO"] == MAYOR_CARGO]
        if chunk.empty:
            continue
        chunk = chunk.copy()
        chunk["val"] = _parse_brl(chunk["VR_DESPESA_CONTRATADA"])
        chunk["cat"] = chunk["DS_ORIGEM_DESPESA"].map(_norm).map(_categorize)
        g = (chunk.groupby(["SQ_CANDIDATO", "cat"])["val"].sum().unstack(fill_value=0.0))
        parts.append(g)
    spend = pd.concat(parts).groupby(level=0).sum()
    for c in ("mkt_online", "mkt_trad", "legal", "other"):
        if c not in spend.columns:
            spend[c] = 0.0
    spend["total"] = spend[["mkt_online", "mkt_trad", "legal", "other"]].sum(axis=1)
    spend["mkt"] = spend["mkt_online"] + spend["mkt_trad"]
    spend = spend.reset_index().rename(columns={"SQ_CANDIDATO": "candidate_id"})
    spend["candidate_id"] = spend["candidate_id"].astype(str).str.strip()
    print(f"  {year}: {len(spend):,} mayoral candidates with contracted spend"
          f" | total R$ {spend['total'].sum()/1e6:,.1f}M")
    return spend[["candidate_id", "total", "mkt", "legal"]]


def rank_candidates(year: int) -> pd.DataFrame:
    """Front-runner / challenger flags per municipality for the mayoral race."""
    vp = pd.read_csv(CLEAN_DIR / "candidate_vote_panel.csv", encoding="utf-8-sig",
                     dtype={"municipality_id_tse": str, "candidate_id": str})
    vp = vp[(vp["office_group"] == "executive") & (vp["election_year"] == year)].copy()
    vp["municipality_id_tse"] = vp["municipality_id_tse"].str.strip().str.zfill(5)
    vp["candidate_id"] = vp["candidate_id"].str.strip()
    vp["candidate_vote_total"] = pd.to_numeric(vp["candidate_vote_total"], errors="coerce")
    vp = vp.sort_values(["municipality_id_tse", "candidate_vote_total"],
                        ascending=[True, False])
    vp["vote_rank"] = vp.groupby("municipality_id_tse").cumcount() + 1
    return vp[["municipality_id_tse", "candidate_id", "vote_rank"]]


def build_year(year: int) -> pd.DataFrame:
    """Municipality-wide spend for front-runner, challenger, and whole field."""
    spend = load_candidate_spend(year)
    ranks = rank_candidates(year)
    df = ranks.merge(spend, on="candidate_id", how="left")
    matched = df["total"].notna().mean()
    print(f"  {year}: {matched:5.1%} of ranked mayoral candidates matched to SPCE spend")
    for c in ("total", "mkt", "legal"):
        df[c] = df[c].fillna(0.0)
        if year == 2020:
            df[c] *= DEFLATOR_2020_TO_2024

    muni_total = df.groupby("municipality_id_tse")["total"].sum().rename(f"muni_total_{year}")
    n_cand = (df[df["total"] > 0].groupby("municipality_id_tse")["candidate_id"].size()
              .rename(f"n_exec_cand_with_spend_{year}"))
    fr = (df[df["vote_rank"] == 1].set_index("municipality_id_tse")[["total", "mkt"]]
          .rename(columns={"total": f"fr_total_{year}", "mkt": f"fr_mkt_{year}"}))
    ch = (df[df["vote_rank"] == 2].set_index("municipality_id_tse")[["total", "mkt"]]
          .rename(columns={"total": f"ch_total_{year}", "mkt": f"ch_mkt_{year}"}))
    out = pd.concat([muni_total, n_cand, fr, ch], axis=1).reset_index()
    return out


def main() -> None:
    print("Building candidate campaign-finance mechanism panel (SPCE contracted expenses)")
    yr = {y: build_year(y) for y in YEARS}
    panel = yr[2020].merge(yr[2024], on="municipality_id_tse", how="outer")

    lvl_cols = [c for c in panel.columns if c != "municipality_id_tse"
                and not c.startswith("n_exec_cand")]
    panel[lvl_cols] = panel[lvl_cols].fillna(0.0)

    for stub in ("fr_total", "ch_total", "muni_total", "fr_mkt", "ch_mkt"):
        panel[f"delta_log1p_{stub}"] = (
            np.log1p(panel[f"{stub}_2024"]) - np.log1p(panel[f"{stub}_2020"]))

    for y in YEARS:
        denom = panel[f"fr_total_{y}"] + panel[f"ch_total_{y}"]
        panel[f"ch_spend_share_{y}"] = np.where(denom > 0,
                                                panel[f"ch_total_{y}"] / denom, np.nan)
    panel["delta_ch_spend_share"] = (panel["ch_spend_share_2024"]
                                     - panel["ch_spend_share_2020"])

    out_path = CLEAN_DIR / "candidate_finance_panel.csv"
    panel.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}  ({len(panel):,} municipalities, {panel.shape[1]} cols)")
    print("  challenger spend-share 2020 -> 2024 (median): "
          f"{panel['ch_spend_share_2020'].median():.3f} -> "
          f"{panel['ch_spend_share_2024'].median():.3f}")
    print("  median delta_log1p challenger total: "
          f"{panel['delta_log1p_ch_total'].median():.3f} | front-runner: "
          f"{panel['delta_log1p_fr_total'].median():.3f}")


if __name__ == "__main__":
    main()
