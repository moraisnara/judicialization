"""
Topic-selection worksheet for the normatively-selected shift-share instrument
(branch: tse-shift-share, Architecture B).

Purpose: give a per-subtopic decision sheet for building the first-instance
lawsuit-flow Bartik. Each row is ONE leaf subject (CD_ASSUNTO_PRINCIPAL, NOT
rolled up), carrying the signals needed to decide keep / drop / roll-up:

  - national first-instance adversarial COUNT per cycle (2018/2020/2022/2024)
  - share within the treated municipal cycles (2020, 2024) and its movement
  - TPU family (depth-2 ancestor) so sparse leaves can be rolled up by family
  - normative-salience flags (K*): is this subtopic / its family on the TSE's
    normative agenda (Consulta + Instrucao corpus, primary + secondary subjects)?
  - COVID-suspect and sparse flags to separate substantive shifts from artifacts

Design rationale lives in memory: amv-tse-shift-share-redesign. The leaf level
(K_eff ~30) preserves the differential subtopic movement that a depth-2 roll-up
cancels out; normative salience is the principled selector that ends the
grouping saga.

Output: output/tables/descriptives/lawsuit_topic_selection_worksheet.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "exploration" / "output" / "tables" / "descriptives"

YEARS = [2018, 2020, 2022, 2024]           # normative-agenda selector uses all cycles
# 2018 processual file is appeals-only (instances 2 & 3, no zona-level first instance),
# so the first-instance FLOW panel is 2020/2022/2024; treated municipal cycles = 2020, 2024.
FIRST_INSTANCE_YEARS = [2020, 2022, 2024]
MUNI_CYCLES = [2020, 2024]                  # the treated cycles (municipal elections)
CSV_ENC, CSV_SEP = "latin-1", ";"

# Classes that are mandatory administrative filings (every candidate must file):
# dropped so the universe is adversarial litigation only. Matches 01_lawsuit_panel.
MANDATORY_CLASS_PREFIXES = (
    "REGISTRO DE CANDIDATURA",
    "PRESTA",                        # PRESTACAO DE CONTAS ...
    "REQUERIMENTO DE REGULARIZA",    # regularizacao de omissao de contas
)

SPARSE_MAX = 50          # a leaf whose largest single-cycle count is below this is "sparse" -> roll up
# In-person / gathering campaigning: pandemic-distorted in 2020, so 2020->2024 moves are suspect.
COVID_SUSPECT_TOKENS = ("comício", "showmício", "carreata", "passeata", "alto-falante", "amplifica")
# Procedural / administrative / office-composition subjects: NOT substantive electoral-conduct
# shocks. Flagged so they can be dropped even when their TPU family is on the normative agenda.
PROCEDURAL_TOKENS = (
    "execução", "cumprimento de sentença", "requerimento", "cargo -", "cargos",
    "filiação partidária", "matéria administrativa", "minuta de resolução",
    "meios processuais", "diplomação", "resultados", "composição de mesa",
    "alistamento eleitoral", "trabalhos eleitorais", "prestação de contas",
    "administração da justiça", "designação", "magistrado", "servidor",
    "estrutura orgânica", "petição", "cautelar", "medida cautelar",
)


def unmojibake(s: str) -> str:
    """Raw TSE files are utf-8 bytes mis-read as latin-1; round-trip to recover accents."""
    try:
        return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
    except (AttributeError, UnicodeError):
        return s


# --------------------------------------------------------------------------- #
# TPU tree: parent chain, family (depth-2), depth, clean utf-8 names
# --------------------------------------------------------------------------- #
def load_tpu() -> tuple[dict, dict]:
    tree = json.loads((RAW_DIR / "tpu_eleitoral_tree.json").read_text(encoding="utf-8"))
    pai, name = {}, {}
    for x in tree:
        c = int(x["cod_item"])
        pai[c] = int(x["cod_item_pai"]) if x["cod_item_pai"] is not None else None
        name[c] = x["nome"]
    return pai, name


def make_helpers(pai: dict):
    def chain(code) -> list[int]:
        try:
            c = int(float(code))
        except (TypeError, ValueError):
            return []
        path, seen = [], set()
        while c is not None and c in pai and c not in seen:
            seen.add(c)
            path.append(c)
            c = pai.get(c)
        return path[::-1]              # root-first

    def family(code, depth=2):
        p = chain(code)
        return p[min(depth, len(p) - 1)] if p else None

    def depth_of(code):
        p = chain(code)
        return len(p) if p else np.nan

    return chain, family, depth_of


# --------------------------------------------------------------------------- #
# Corpora
# --------------------------------------------------------------------------- #
def load_processo(year: int, cols: list[str]) -> pd.DataFrame:
    path = RAW_DIR / f"processo_eleitoral_{year}" / f"processo_eleitoral_{year}.csv"
    return pd.read_csv(path, sep=CSV_SEP, encoding=CSV_ENC, dtype=str,
                       low_memory=False, usecols=cols)


def first_instance_adversarial(year: int) -> pd.Series:
    """National first-instance adversarial counts by leaf subject for one cycle."""
    df = load_processo(year, ["NR_INSTANCIA", "DS_CLASSE",
                              "CD_ASSUNTO_PRINCIPAL", "NR_PROCESSO"])
    df = df[df["NR_INSTANCIA"] == "1"].drop_duplicates("NR_PROCESSO")
    cl = df["DS_CLASSE"].str.upper()
    df = df[~cl.str.startswith(MANDATORY_CLASS_PREFIXES)]
    return df["CD_ASSUNTO_PRINCIPAL"].value_counts()


def build_name_map() -> dict:
    """Clean code -> subject-name map, sourced from the raw files. These are plain
    latin-1, so reading with CSV_ENC already yields correct accents (unlike the
    mojibake TPU tree). Covers primary + secondary subjects."""
    nm: dict = {}
    for year in YEARS:
        p = RAW_DIR / f"processo_eleitoral_{year}" / f"processo_eleitoral_{year}.csv"
        if p.exists():
            df = load_processo(year, ["CD_ASSUNTO_PRINCIPAL", "DS_ASSUNTO_PRINCIPAL"]).dropna()
            for c, n in zip(df["CD_ASSUNTO_PRINCIPAL"], df["DS_ASSUNTO_PRINCIPAL"]):
                nm.setdefault(c, n)
        a = RAW_DIR / f"assuntos_{year}" / f"processos_eleitorais_assuntos_{year}.csv"
        if a.exists():
            df = pd.read_csv(a, sep=CSV_SEP, encoding=CSV_ENC, dtype=str, low_memory=False,
                             usecols=["CD_ASSUNTO", "DS_ASSUNTO"]).dropna()
            for c, n in zip(df["CD_ASSUNTO"], df["DS_ASSUNTO"]):
                nm.setdefault(c, n)
    return nm


def normative_subject_set() -> set:
    """
    K* selector: subjects the TSE normatively works on. Corpus = CONSULTA +
    INSTRUCAO processos (excl AGRAVO), pooled across all four cycles, using
    BOTH primary (from processo file) and secondary subjects (from the Assuntos
    multi-subject file). Returns (leaf codes, family codes, family->name).
    """
    leaf_codes: set = set()
    for year in YEARS:
        # normative processos + their primary subject
        df = load_processo(year, ["DS_CLASSE", "CD_ASSUNTO_PRINCIPAL", "NR_PROCESSO"])
        cl = df["DS_CLASSE"].str.upper()
        norm = df[(cl.str.contains("CONSULTA") | cl.str.startswith("INSTRU"))
                  & ~cl.str.contains("AGRAVO")].drop_duplicates("NR_PROCESSO")
        norm_ids = set(norm["NR_PROCESSO"])
        leaf_codes |= set(norm["CD_ASSUNTO_PRINCIPAL"].dropna())

        # secondary subjects of those same processos (Assuntos file)
        assuntos_path = (RAW_DIR / f"assuntos_{year}" /
                         f"processos_eleitorais_assuntos_{year}.csv")
        if assuntos_path.exists():
            a = pd.read_csv(assuntos_path, sep=CSV_SEP, encoding=CSV_ENC, dtype=str,
                            low_memory=False, usecols=["NR_PROCESSO", "CD_ASSUNTO"])
            leaf_codes |= set(a[a["NR_PROCESSO"].isin(norm_ids)]["CD_ASSUNTO"].dropna())
    return leaf_codes


# --------------------------------------------------------------------------- #
# Build worksheet
# --------------------------------------------------------------------------- #
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pai, tree_name = load_tpu()
    chain, family, depth_of = make_helpers(pai)
    name_map = build_name_map()

    def clean_name(code) -> str:
        if code in name_map:
            return name_map[code]
        try:
            return unmojibake(tree_name.get(int(float(code)), str(code)))
        except (TypeError, ValueError):
            return str(code)

    print("[1] First-instance adversarial counts by leaf subject, per cycle")
    counts = {y: first_instance_adversarial(y) for y in FIRST_INSTANCE_YEARS}
    for y in FIRST_INSTANCE_YEARS:
        print(f"    {y}: {counts[y].sum():>8,} lawsuits | {len(counts[y]):>4} leaf subtopics")

    print("[2] Normative K* selector (Consulta/Instrucao, primary + secondary subjects)")
    norm_leaf = normative_subject_set()
    norm_family = {family(c) for c in norm_leaf} - {None}
    print(f"    normative leaf subjects: {len(norm_leaf)} | families touched: {len(norm_family)}")

    all_codes = sorted(set().union(*[set(counts[y].index) for y in FIRST_INSTANCE_YEARS]))
    muni_tot = {y: counts[y].sum() for y in MUNI_CYCLES}
    rows = []
    for code in all_codes:
        fam = family(code)
        n = {y: int(counts[y].get(code, 0)) for y in FIRST_INSTANCE_YEARS}
        sh20 = 100 * n[2020] / muni_tot[2020] if muni_tot[2020] else 0.0
        sh24 = 100 * n[2024] / muni_tot[2024] if muni_tot[2024] else 0.0
        nm = clean_name(code)
        low = nm.lower()
        is_sparse = max(n[2020], n[2024]) < SPARSE_MAX
        is_proc = any(t in low for t in PROCEDURAL_TOKENS)
        is_covid = any(t in low for t in COVID_SUSPECT_TOKENS)
        in_norm_fam = fam in norm_family
        rows.append({
            "cd_assunto": code,
            "ds_assunto": nm,
            "tpu_family": clean_name(fam) if fam else "",
            "tpu_depth": depth_of(code),
            "n_2020": n[2020], "n_2022": n[2022], "n_2024": n[2024],
            "share_2020_pct": round(sh20, 3),
            "share_2024_pct": round(sh24, 3),
            "delta_share_pp": round(sh24 - sh20, 3),
            "pct_change_muni": (round(100 * (n[2024] - n[2020]) / n[2020], 1)
                                if n[2020] else np.nan),
            "in_normative_leaf": code in norm_leaf,
            "in_normative_family": in_norm_fam,
            "flag_sparse": is_sparse,
            "flag_procedural": is_proc,
            "flag_covid_suspect": is_covid,
            # starter suggestion (override freely): substantive, salient, trustworthy
            "keep_suggestion": bool(in_norm_fam and not is_sparse and not is_proc and not is_covid),
            "muni_total": n[2020] + n[2024],
        })

    ws = pd.DataFrame(rows).sort_values("muni_total", ascending=False)
    ws = ws.drop(columns="muni_total")

    out_path = OUT_DIR / "lawsuit_topic_selection_worksheet.csv"
    ws.to_csv(out_path, index=False, encoding="utf-8-sig")

    # ------------------------------------------------------------------ #
    # summary
    # ------------------------------------------------------------------ #
    def keff(s):
        s = s[s > 0].astype(float)
        p = s / s.sum()
        return 1 / (p ** 2).sum()

    print(f"\n[3] Saved: {out_path.relative_to(PROJECT_ROOT)}")
    print(f"    rows (leaf subtopics): {len(ws)}")
    kept = ws[ws["in_normative_family"] & ~ws["flag_sparse"]]
    print(f"    normatively-salient & non-sparse: {len(kept)} subtopics")
    print(f"    K_eff(2020 leaf, all adversarial):   {keff(counts[2020]):.1f}")
    print(f"    K_eff(2024 leaf, all adversarial):   {keff(counts[2024]):.1f}")
    print("\n    Top 12 movers (|delta share|) among normatively-salient non-sparse:")
    top = kept.reindex(kept["delta_share_pp"].abs().sort_values(ascending=False).index).head(12)
    for _, r in top.iterrows():
        print(f"      {r['delta_share_pp']:+6.2f}pp  {r['n_2020']:>6,} -> {r['n_2024']:>6,}"
              f"  {r['ds_assunto'][:52]}")


if __name__ == "__main__":
    main()
