"""Audit the pipeline: which scripts earn their place in code/, which outputs are orphans.

A script stays in code/ if ANY of three tests passes:
  1. Direct consumption   -- a document \\inputs or \\includegraphics one of its outputs
  2. Macro consumption    -- 04_analysis/06_abstract_macros.py reads one of its CSVs
  3. Transitive data dep  -- it writes a data/ artifact a passing script reads

Test 2 is not bookkeeping. Four scripts pass ONLY test 2 (wild bootstrap AR,
multiplicity, IV diagnostics, exposure-robust SE); an \\input-only rule would
archive the paper's headline inference.

Report only -- always exits 0. Run: python code/utils/audit_pipeline.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "code"
MACRO_HUB = CODE / "04_analysis" / "06_abstract_macros.py"

# Scripts that verify or report on the pipeline rather than producing a paper
# asset. They fail all three tests by design and are listed separately.
INFRASTRUCTURE = {
    "01_download/00_verify_raw_data.py",
    "02_build/00_verify_lawsuits.py",
    "run_all.py",
    "utils/audit_pipeline.py",
}

WRITE = r"(to_csv|write_csv|fwrite|write\.csv|savefig|ggsave|write_parquet|writeLines|write_text|urlretrieve|extractall)"
READ = r"(read_csv|fread|read\.csv|read_parquet|read_excel)"


def script_files() -> dict[str, str]:
    """Relative path -> full text, for every script under code/ (never exploration/)."""
    out = {}
    for p in sorted(list(CODE.rglob("*.py")) + list(CODE.rglob("*.R"))):
        rel = str(p.relative_to(CODE)).replace("\\", "/")
        out[rel] = p.read_text(encoding="utf-8", errors="replace")
    return out


def documents() -> str:
    """Concatenated text of every document that can consume an asset."""
    docs = list((ROOT / "output/presentation").glob("*.tex"))
    docs += list((ROOT / "output/paper").glob("*.tex"))
    return "\n".join(d.read_text(encoding="utf-8", errors="replace") for d in docs)


def aliases(text: str, name: str) -> set[str]:
    """Variables assigned a path containing `name`."""
    return {m.group(1) for m in
            re.finditer(rf"^\s*([A-Za-z_][\w.]*)\s*(?:<-|=)\s*[^\n]*{re.escape(name)}", text, re.M)}


def roles(text: str, name: str) -> tuple[bool, bool]:
    """(writes, reads) for a filename.

    Must resolve path constants, not scan nearby lines. Scripts bind a path to a
    variable at the top and use the verb hundreds of lines later:
        OUT_CSV <- file.path(ROOT, ".../x.csv")   # line 43
        fwrite(res, OUT_CSV)                      # line 210
    A context window scores line 43 as 'mentioned, verb unknown'. Treating that as
    a read hid four of seventeen orphan CSVs when this audit was first run by hand.
    """
    alt = "|".join([re.escape(name)] + [re.escape(a) for a in aliases(text, name)])
    writes = bool(re.search(rf"{WRITE}\s*\([^)]*({alt})", text, re.S)) or \
             bool(re.search(rf"({alt})[^\n]*{WRITE}", text))
    reads = bool(re.search(rf"{READ}\s*\([^)]*({alt})", text, re.S)) or \
            bool(re.search(rf"({alt})[^\n]*{READ}", text))
    return writes, reads


def referenced(stem: str, blob: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(stem)}(?![\w-])", blob) is not None


def main() -> None:
    scripts = script_files()
    blob = documents()
    macro_src = MACRO_HUB.read_text(encoding="utf-8", errors="replace")

    assets = list((ROOT / "output/figures").glob("*.pdf"))
    assets += list((ROOT / "output/tables/tex").glob("*.tex"))

    # --- which script emits which asset, and does a document use it? -------------
    emitters: dict[str, set[str]] = {}
    for a in assets:
        for rel, text in scripts.items():
            if a.name in text and roles(text, a.name)[0]:
                emitters.setdefault(rel, set()).add(a.name)

    orphan_assets = [a for a in assets if not referenced(a.stem, blob)]

    # --- test 1 and test 2 -------------------------------------------------------
    passes: dict[str, str] = {}
    for rel, text in scripts.items():
        if rel in INFRASTRUCTURE:
            continue
        if any(referenced(Path(n).stem, blob) for n in emitters.get(rel, ())):
            passes[rel] = "direct"
            continue
        csvs = {Path(c).name for c in re.findall(r"[\w./-]+\.csv", text)}
        if any(c in macro_src for c in csvs):
            passes[rel] = "macro"

    # --- test 3: transitive data dependency, and sourced helpers -----------------
    # A helper under utils/ emits nothing, so it fails tests 1-3 by construction.
    # It earns its place by being source()d/imported by a script that passes.
    changed = True
    while changed:
        changed = False
        for rel, text in scripts.items():
            if rel in INFRASTRUCTURE or rel in passes:
                continue
            written = {Path(m).name for m in re.findall(r"[\w./-]+\.(?:csv|parquet)", text)
                       if roles(text, Path(m).name)[0]}
            for other, other_text in scripts.items():
                if other not in passes:
                    continue
                if any(roles(other_text, w)[1] for w in written):
                    passes[rel] = "transitive"
                    changed = True
                    break
                if Path(rel).name in other_text:
                    passes[rel] = f"sourced by {other}"
                    changed = True
                    break

    candidates = [r for r in scripts if r not in passes and r not in INFRASTRUCTURE]

    # --- unreferenced CSVs: a question, never a deletion candidate ----------------
    unref_csv = []
    for sub in ("output/tables/regressions", "output/tables/descriptives"):
        for p in sorted((ROOT / sub).glob("*.csv")):
            read_by = [rel for rel, text in scripts.items()
                       if p.name in text and roles(text, p.name)[1] and not roles(text, p.name)[0]]
            if not read_by and not referenced(p.stem, blob):
                unref_csv.append(f"{sub}/{p.name}")

    # --- documents pointing at assets that are not on disk ------------------------
    on_disk = {a.stem for a in assets}
    breakers = []
    for d in list((ROOT / "output/presentation").glob("*.tex")) + list((ROOT / "output/paper").glob("*.tex")):
        txt = d.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\\(?:input|includegraphics)\s*(?:\[[^\]]*\])?\{([^}]+)\}", txt):
            stem = Path(m.group(1).strip()).stem
            if stem in on_disk or stem == "slides_preamble":
                continue
            if not (ROOT / "output/presentation" / f"{stem}.tex").exists():
                breakers.append(f"{d.name} -> {m.group(1)}")

    def section(title: str, rows: list[str], note: str = "") -> None:
        print(f"\n=== {title}: {len(rows)} ===")
        if note and rows:
            print(f"    {note}")
        for r in rows:
            print(f"    {r}")

    print(f"Audited {len(scripts)} scripts under code/ against {len(assets)} committed assets.")
    section("ARCHIVE CANDIDATES (fail all three tests)", candidates,
            "move to exploration/<stage>/ -- see docs/superpowers/specs/2026-08-12-repo-reorganization-design.md")
    section("ORPHAN OUTPUTS (no document references them)", [a.name for a in orphan_assets],
            "delete the file AND strip the block that emits it")
    section("BUILD BREAKERS (document references a missing asset)", breakers)
    section("UNREFERENCED CSVs (a question, not a defect)", unref_csv,
            "csv = source of truth: a record behind a shown result is fine here")
    section("INFRASTRUCTURE (exempt by design)", sorted(INFRASTRUCTURE))


if __name__ == "__main__":
    main()
