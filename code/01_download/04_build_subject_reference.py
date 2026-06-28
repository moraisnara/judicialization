"""
Build the human-readable subject-code reference document for the full universe
of lawsuit subjects observed in our TSE processual data.

Input:
  data/raw/tpu_assunto_reference.csv   (built by 03_download_tpu_assuntos.py:
                                        official_name + glossary + ancestor path
                                        for every subject code, with our volume)

Output:
  documents/subject_reference_TPU.md   (one section per official TPU branch;
                                        each subject = code + official name +
                                        "what it is" glossary excerpt + volume +
                                        prior disposition)

This is the auditable glossary that grounds the family taxonomy: every code is
shown with its official CNJ name, the legal text that defines it, and where it
sits in the official tree -- so KEEP/DROP and family aggregation decisions can
be read against the official hierarchy rather than hand labels.

Run: python code/01_download/04_build_subject_reference.py
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd


def _ascii(s: str) -> str:
    """Lowercase + strip accents so keyword matching is accent-insensitive."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(s).lower())
        if not unicodedata.combining(c)
    )

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "data" / "raw" / "tpu_assunto_reference.csv"
OUT = ROOT / "documents" / "subject_reference_TPU.md"
OUT.parent.mkdir(parents=True, exist_ok=True)

GLOSS_CHARS = 360  # excerpt length for "what it is"


def section_of(path: str, name: str) -> str:
    """Assign each subject to a high-level thematic section.

    Uses the official ancestor path when the code lives under the electoral
    root (DIREITO ELEITORAL); otherwise buckets by the criminal/procedural
    super-branch so non-electoral codes are visibly separated.
    """
    p = (path or "").strip()
    parts = [x.strip() for x in p.split(">") if x.strip()]
    low = _ascii(p)
    if not parts or _ascii(parts[0]) != "direito eleitoral":
        # codes that resolve outside the electoral root (criminal/civil glossary)
        if "crime" in low:
            return "ZZ. Non-electoral criminal codes (outside electoral root)"
        return "ZZ. Non-electoral / procedural codes (outside electoral root)"

    # within the electoral tree: choose the most informative thematic node
    keymap = [
        ("registro de candidatura", "01. Candidate registration (RRC/DRAP/substitutions)"),
        ("inelegibilidade", "02. Ineligibility"),
        ("condicao de elegibilidade", "03. Eligibility conditions"),
        ("impugnacao", "04. Impugnacao / challenges"),
        ("propaganda", "05. Propaganda (campaign advertising)"),
        ("pesquisa eleitoral", "06. Electoral polls"),
        ("transgressoes eleitorais", "07. Electoral transgressions (abuse/conduct)"),
        ("recursos financeiros", "08. Campaign finance"),
        ("prestacao de contas", "08. Campaign finance"),
        ("alistamento", "09. Voter registration / electoral roll"),
        ("filiacao", "10. Party membership (filiacao/desfiliacao)"),
        ("partido", "11. Party organization"),
        ("coligacao", "11. Party organization"),
        ("cargo", "12. Offices / mandates (cargos)"),
        ("candidat", "13. Candidates (other)"),
        ("resultados", "14. Results / vote count"),
        ("eleicoes", "14. Results / vote count"),
        ("garantias eleitorais", "15. Electoral guarantees / writs"),
        ("direitos politicos", "16. Political rights"),
        ("crimes", "17. Electoral crimes"),
        ("execucao", "18. Enforcement / procedure"),
        ("cautelar", "18. Enforcement / procedure"),
    ]
    for needle, label in keymap:
        if needle in low:
            return label
    return "19. Other electoral matters"


def main() -> None:
    df = pd.read_csv(REF, dtype={"subject_code": str}, encoding="utf-8-sig",
                     keep_default_na=False)
    df["our_volume"] = pd.to_numeric(df["our_volume"], errors="coerce").fillna(0).astype(int)
    df["section"] = [section_of(p, n) for p, n in zip(df["ancestor_path"], df["official_name"])]

    total_vol = df["our_volume"].sum()
    sec_order = (df.groupby("section")["our_volume"].sum()
                 .sort_values(ascending=False).index.tolist())

    lines: list[str] = []
    lines.append("# Subject-code reference (official CNJ/PJe TPU)\n")
    lines.append(
        f"All **{len(df)}** lawsuit subjects observed in the TSE processual data "
        f"(2020 + 2024), totalling **{total_vol:,}** lawsuits. For each: official "
        "CNJ name, the legal-text glossary that defines it (\"what it is\"), our "
        "observed volume, and the prior KEEP/DROP disposition. Grouped by official "
        "TPU branch; sections and subjects sorted by our volume.\n")
    lines.append(
        "_Source: `data/raw/tpu_assunto_reference.csv`, fetched from "
        "`https://gateway.cloud.pje.jus.br/tpu/` (electoral root 11428). "
        "Generated by `code/01_download/04_build_subject_reference.py`._\n")

    for sec in sec_order:
        g = df[df["section"] == sec].sort_values("our_volume", ascending=False)
        lines.append(f"\n## {sec}  \n_{len(g)} codes · {g['our_volume'].sum():,} lawsuits_\n")
        for r in g.itertuples():
            gloss = r.what_it_is.strip()
            if len(gloss) > GLOSS_CHARS:
                gloss = gloss[:GLOSS_CHARS].rsplit(" ", 1)[0] + " […]"
            if not gloss:
                gloss = "_(no official glossary text)_"
            disp = f" · _prev: {r.prev_disposition}_" if r.prev_disposition else ""
            lines.append(
                f"- **`{r.subject_code}`** · {r.our_volume:,} · {r.official_name}{disp}  \n"
                f"  {gloss}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}  ({len(df)} subjects, {len(sec_order)} sections)")
    print("\nSections by volume:")
    for sec in sec_order:
        g = df[df["section"] == sec]
        print(f"  {g['our_volume'].sum():>10,}  {len(g):>3}  {sec}")


if __name__ == "__main__":
    main()
