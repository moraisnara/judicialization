"""
SP electoral-lawsuit CLASS COMPOSITION across 2016 -> 2020 -> 2024 (appendix descriptive).

Purpose. Extend the "expanded role, not a volume wave" framing to a PRE-SAMPLE
(2016) baseline using an independent TRE-SP source, and show the mandatory core
dominates every cycle. This is the only place a 2016 litigation snapshot enters.

Sources & the compatibility boundary (stated honestly on the slide):
  * 2016   = data/raw/SAC-JE_769756-...xlsx (TRE-SP, "Eleicao 2016" sheet):
             zona x classe counts, COMPLETE SP (425 zonas, 142k cases).
  * 2020/24 = data/clean/zona_lawsuit_panel.csv (SIG): zona x classe x subject.
  Zone IDs do NOT align (2016 spans zones 1-427; the SIG panel only carries
  zone-codes 1-107), so this is a STATE-LEVEL composition comparison, never a
  zone-by-zone one. Because the source changes (SAC-JE -> SIG), only SHARES
  WITHIN a source are read -- raw counts are never trended across sources
  (the coverage-artifact rule). The class dictionary also evolved: 2016 had no
  propaganda-specific class (those filed as Representacao), so the internal
  Representacao<->Propaganda split across 2016 vs 2020/24 is confounded by
  reclassification and is flagged, not over-read.

Outputs:
  output/tables/descriptives/lawsuit_composition_sp.csv   (bucket shares, %)
  output/tables/tex/lawsuit_composition_sp.tex            (deck fragment)
"""
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/SAC-JE_769756-Distribuicao_de_casos_novos_por_eleicao.xlsx"
PANEL = ROOT / "data/clean/zona_lawsuit_panel.csv"
CSV_OUT = ROOT / "output/tables/descriptives/lawsuit_composition_sp.csv"
TEX_OUT = ROOT / "output/tables/tex/lawsuit_composition_sp.tex"


def norm(s):
    if pd.isna(s):
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.upper().strip()


# stable buckets keyed on normalized class name (substring, first hit wins)
BUCKETS = [
    ("Registration (RCAND)",      ["REGISTRO DE CANDIDATURA"]),
    ("Accounts (contas)",         ["PRESTACAO DE CONTAS"]),
    ("Representacao (core adv.)", ["REPRESENTACAO ESPECIAL", "REPRESENTACAO CRIMINAL",
                                   "REPRESENTACAO"]),
    ("Propaganda (adv.)",         ["PROPAGANDA", "DIREITO DE RESPOSTA"]),
    ("AIJE (adv.)",               ["INVESTIGACAO JUDICIAL"]),
    ("AIME (adv.)",               ["IMPUGNACAO DE MANDATO"]),
    ("Criminal (adv.)",           ["ACAO PENAL", "NOTICIA DE CRIME", "INQUERITO"]),
    ("Poll-station admin",        ["MESA RECEPTORA", "APURACAO DE ELEICAO", "JUNTA"]),
    ("Party/registration admin",  ["FILIACAO", "PROCESSO ADMINISTRATIVO", "PARTIDO",
                                   "APOIAMENTO", "DUPLICIDADE", "INSCRICAO", "ELEITOR"]),
    ("Petitions / civil",         ["PETICAO", "CARTAS", "MANDADO DE SEGURANCA",
                                   "CAUTELAR", "EXCECOES"]),
    ("Enforcement",               ["CUMPRIMENTO DE SENTENCA", "EXECUCAO", "EMBARGOS",
                                   "EXECUCAO DA PENA"]),
]
ADVERSARIAL = {"Representacao (core adv.)", "Propaganda (adv.)", "AIJE (adv.)",
               "AIME (adv.)", "Criminal (adv.)"}


def bucket(name):
    n = norm(name)
    for label, keys in BUCKETS:
        if any(k in n for k in keys):
            return label
    return "Other"


def compute_shares():
    # 2016 from SAC-JE (SP-complete)
    d16 = pd.read_excel(RAW, sheet_name="Eleição 2016", header=1)
    d16.columns = ["zona", "classe", "n"]
    d16 = d16.dropna(subset=["classe"])
    d16["n"] = pd.to_numeric(d16["n"], errors="coerce")
    d16["bucket"] = d16["classe"].map(bucket)
    b16 = d16.groupby("bucket")["n"].sum()

    # 2020/2024 from SIG zona panel (SP)
    z = pd.read_csv(PANEL, dtype=str)
    z["n_lawsuits"] = pd.to_numeric(z["n_lawsuits"], errors="coerce")
    z = z[(z.state == "SP") & (z.election_year.isin(["2020", "2024"]))]
    z["bucket"] = z["case_class_name"].map(bucket)
    b = z.groupby(["election_year", "bucket"])["n_lawsuits"].sum().unstack(0)

    tab = pd.DataFrame({"2016": b16, "2020": b["2020"], "2024": b["2024"]}).fillna(0)
    order = [lbl for lbl, _ in BUCKETS] + ["Other"]
    tab = tab.reindex([o for o in order if o in tab.index])
    shares = tab.div(tab.sum(), axis=1) * 100.0
    return tab, shares


def row(label, vals, dec, bold=False):
    fmt = "%.{}f".format(dec)
    if bold:
        cells = " & ".join("\\textbf{%s}" % (fmt % v) for v in vals)
        return "\\textbf{%s} & %s \\\\" % (label, cells)
    cells = " & ".join(fmt % v for v in vals)
    return "%s & %s \\\\" % (label, cells)


def write_tex(shares):
    yrs = ["2016", "2020", "2024"]
    s = shares[yrs]

    def g(bkt):
        return [s.loc[bkt, y] if bkt in s.index else 0.0 for y in yrs]

    core = [sum(x) for x in zip(g("Registration (RCAND)"), g("Accounts (contas)"))]
    other_adv = [sum(x) for x in zip(g("AIJE (adv.)"), g("AIME (adv.)"), g("Criminal (adv.)"))]
    adversarial = [sum(x) for x in zip(
        g("Representacao (core adv.)"), g("Propaganda (adv.)"), other_adv)]
    admin = [sum(x) for x in zip(
        g("Poll-station admin"), g("Party/registration admin"),
        g("Petitions / civil"), g("Enforcement"),
        [s.loc["Other", y] if "Other" in s.index else 0.0 for y in yrs])]

    lines = [
        "% Auto-generated by code/04_analysis/08_lawsuit_composition_sp.py",
        "% Do not edit manually -- rerun the generating script to update",
        "",
        "\\begin{tabular}{lccc}",
        "\\toprule\\toprule",
        " & \\textbf{2016} & \\textbf{2020} & \\textbf{2024} \\\\",
        " & \\scriptsize{TRE-SP} & \\scriptsize{SIG} & \\scriptsize{SIG} \\\\",
        "\\midrule",
        "\\multicolumn{4}{l}{\\textit{Mandatory / ancillary filings}} \\\\",
        row("\\quad Candidacy registration", g("Registration (RCAND)"), 1),
        row("\\quad Campaign accounts", g("Accounts (contas)"), 1),
        "\\rowcolor{mylight}",
        row("Mandatory core", core, 1, bold=True),
        "\\midrule",
        "\\multicolumn{4}{l}{\\textit{Adversarial filings}} \\\\",
        row("\\quad Representa\\c{c}\\~{a}o", g("Representacao (core adv.)"), 2),
        row("\\quad Propaganda$^{\\dagger}$", g("Propaganda (adv.)"), 2),
        row("\\quad AIJE / AIME / criminal", other_adv, 2),
        "\\rowcolor{mylight}",
        row("Adversarial", adversarial, 2, bold=True),
        "\\midrule",
        row("Administrative \\& other", admin, 1),
        "\\bottomrule\\bottomrule",
        "\\end{tabular}",
    ]
    TEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    tab, shares = compute_shares()
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    shares.round(3).to_csv(CSV_OUT)
    write_tex(shares)

    tot = {c: int(tab[c].sum()) for c in ["2016", "2020", "2024"]}
    adv = shares.loc[[b for b in shares.index if b in ADVERSARIAL], ["2016", "2020", "2024"]].sum()
    print("SP lawsuit-class composition written.")
    print("  captured cases:", tot)
    print("  adversarial share (%):", {y: round(adv[y], 2) for y in adv.index})
    print("  ->", CSV_OUT.relative_to(ROOT))
    print("  ->", TEX_OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
