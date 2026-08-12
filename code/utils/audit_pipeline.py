"""Audit the pipeline: which scripts earn their place in code/, which outputs are orphans.

A script stays in code/ if ANY of three tests passes:
  1. Direct consumption   -- a document \\inputs or \\includegraphics one of its outputs
  2. Macro consumption    -- 04_analysis/06_abstract_macros.py reads one of its CSVs
  3. Transitive data dep  -- it writes a data/ artifact a passing script reads

Test 2 is not bookkeeping. Four scripts pass ONLY test 2 (wild bootstrap AR,
multiplicity, IV diagnostics, exposure-robust SE); an \\input-only rule would
archive the paper's headline inference. It requires the script to WRITE the CSV
the hub reads: merely naming (reading) a hub CSV passes for a reason that is not
true and hides the real one -- the same failure mode already fixed in sources().

Documented limit -- writes through a user-defined wrapper. roles() pairs a write
verb with a filename literal in the same expression, so a write that happens
inside a helper which receives the path as a parameter is invisible: the literal
sits at the call site, the verb inside the helper body. The WRITE `write[\\w.]+`
alternative covers the common case, where the wrapper is itself *named*
`write_...` (e.g. write_tex() in 03_estimation/10_mechanism_finance.R, whose
inner writeLines() never sees the filename). A wrapper named `emit_fragment`
would still be missed, and would have to be renamed or added to WRITE by hand.

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

# One `write[\w.]+` alternative subsumes write_csv / write.csv / write_parquet /
# writeLines / write_text / write_tex and any future write_* wrapper (see the
# module docstring's wrapper limit). The trailing `+` (not `*`) requires a
# suffix, which excludes the bare file-object method `f.write(...)`: roles()
# matches an alias as an unanchored substring, so scoring `f.write` as a path
# write let two-letter aliases (`ar` for the wild-bootstrap table, `er` for the
# exposure-robust one) hit inside the LaTeX string literals the hub writes, and
# flipped three of the hub's reads into writes. No script here calls a bare
# `write(`; the one real open-then-write is caught by the open() alternative.
# That open() is MODE-AWARE on purpose: a bare `open` would score every read-open
# as a write, so it only fires when the argument list also carries a "w"/"a"
# mode string. The zero-width lookahead leaves the "(" unconsumed, so both
# roles() compositions still line the verb up with the path.
WRITE = (r"(write[\w.]+|to_csv|fwrite|savefig|ggsave|urlretrieve|extractall"
         r"|open(?=\s*\([^)\n]*[\"'][wa][bt+]*[\"']))")
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
    """Variables assigned a path containing `name`.

    Binding is file-wide and reassignment-blind: once a variable is matched to
    `name` anywhere in the file, it is treated as an alias for `name` across
    the whole text, even where it is later reassigned to something unrelated.
    Every caller (roles(), writes_raw_lane()) inherits this.
    """
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


def raw_dir_vars(text: str) -> set[str]:
    """Variables bound to a path literal under data/raw, e.g. RAW_DIR = ROOT/"data"/"raw"."""
    return {m.group(1) for m in re.finditer(
        r'^\s*([A-Za-z_][\w.]*)\s*(?:<-|=)\s*[^\n]*["\']data["\'][^\n]*["\']raw["\']',
        text, re.M)}


def sources(other_text: str, rel: str) -> bool:
    """True if `other_text` actually loads the script `rel`, not merely names it.

    A bare `name in other_text` mention is not a dependency: scripts here refer
    to each other in docstrings ("re-run 01_lawsuits.py to refresh the cache")
    and in FileNotFoundError messages telling a human which step to run. Those
    read as sourcing to a substring match and let a script pass for a reason
    that is not true, which is worse than failing -- it hides the real one.
    So require a load construct: source() in R, an import or exec(open()) in
    Python.

    Two documented limits, neither live today (all five real source() calls in
    the repo are single-line literals): a call split across lines, or one that
    builds the filename from parts, is missed; and a commented-out source()
    still matches, since the pattern does not exclude # lines.
    """
    name = Path(rel).name
    if re.search(rf"source\s*\([^\n]*{re.escape(name)}", other_text):
        return True
    if name.endswith(".py"):
        stem = re.escape(name[:-3])
        if re.search(rf"^\s*(?:from|import)\s+[\w.]*\b{stem}\b", other_text, re.M):
            return True
        if re.search(rf"exec\s*\([^\n]*{re.escape(name)}", other_text):
            return True
    return False


def writes_raw_lane(text: str) -> bool:
    """True if the script writes anywhere under a data/raw path constant.

    Word-boundary anchored, unlike roles()'s unanchored substring match: a
    generic alias such as `path` would otherwise false-match inside an
    unrelated variable like `out_path` elsewhere in the same file. Scoped
    narrowly to this one check rather than tightening roles() itself, since
    roles() is shared by tests 1-3 and its behavior there is already validated.

    Inherits aliases()'s file-wide, reassignment-blind binding (see its
    docstring): a script that reads from data/raw/ into a variable and then
    reuses that same name for an unrelated write elsewhere in the file would
    pass here as a raw-lane producer. Latent today -- no script in the repo
    reuses a name that way -- but a real failure mode, which is why every
    raw-lane pass is named in the auditor's report output rather than folded
    silently into the pass count.
    """
    for root in raw_dir_vars(text):
        names = [root] + sorted(aliases(text, root))
        alt = "|".join(rf"\b{re.escape(n)}\b" for n in names)
        if re.search(rf"{WRITE}\s*\([^)]*({alt})", text, re.S):
            return True
        if re.search(rf"({alt})[^\n]*{WRITE}", text):
            return True
    return False


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
        # Test 2 requires the script to WRITE the CSV the hub reads. Every
        # estimation script names executive_margin_design.csv (it reads it), and
        # the hub names it too, so a mention-only test passed a dozen scripts for
        # a reason that was not theirs.
        csvs = {Path(c).name for c in re.findall(r"[\w./-]+\.csv", text)}
        if any(c in macro_src and roles(text, c)[0] for c in csvs):
            passes[rel] = "macro"

    # --- test 3: transitive data dependency, and sourced helpers -----------------
    # A helper under utils/ emits nothing, so it fails tests 1-3 by construction.
    # It earns its place by being source()d/imported by a script that passes.
    def spread_transitive() -> None:
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
                    if sources(other_text, rel):
                        passes[rel] = f"sourced by {other}"
                        changed = True
                        break

    spread_transitive()

    # --- last resort: the data/raw directory-level edge ---------------------------
    # Download scripts extract whole folders into data/raw/ with names built at
    # runtime (e.g. f"consulta_cand_{year}"), so there is no output filename
    # literal for tests 1-3 to match against. The raw lane is consumed by the
    # build stage by construction, so this directory-level edge stands in for the
    # missing filename. It runs LAST, after every filename-level test has had its
    # chance: a script that can pass on a real filename match should be recorded
    # that way, so the RAW-LANE section names only scripts that genuinely depend
    # on the heuristic.
    for rel, text in scripts.items():
        if rel in INFRASTRUCTURE or rel in passes:
            continue
        if writes_raw_lane(text):
            passes[rel] = "raw-lane"
    spread_transitive()   # a raw-lane passer may unlock transitives behind it

    candidates = [r for r in scripts if r not in passes and r not in INFRASTRUCTURE]
    raw_lane_producers = sorted(r for r, why in passes.items() if why == "raw-lane")

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
    section("RAW-LANE PRODUCERS (directory-level edge, not filename-verified)", raw_lane_producers,
            "passed via writes_raw_lane(), not a filename-level test -- see its docstring for the reassignment gap")
    section("ORPHAN OUTPUTS (no document references them)", [a.name for a in orphan_assets],
            "delete the file AND strip the block that emits it")
    section("BUILD BREAKERS (document references a missing asset)", breakers)
    section("UNREFERENCED CSVs (a question, not a defect)", unref_csv,
            "csv = source of truth: a record behind a shown result is fine here")
    section("INFRASTRUCTURE (exempt by design)", sorted(INFRASTRUCTURE))


if __name__ == "__main__":
    main()
