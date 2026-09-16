"""Derive the 30- and 15-minute decks from the frame library.

A talk includes only some frames, so buttons pointing at excluded frames would
dangle. For each such frame we emit a <id>_talk.tex with the dangling buttons
stripped -- the divergence is a visible file, per DECK_GUIDE.md.
"""
import re
from pathlib import Path

PRES = Path(__file__).resolve().parent
FR = PRES / "frames"
BS = chr(92)

# Both talks carry THE SPINE (DECK_GUIDE.md): the same macro sections in the
# same order as slides_report.tex and the paper. A short deck may GLUE adjacent
# sections; it may never reorder, drop, or invent one. Only the subsections and
# the frames inside them differ.
#
# Frame SELECTION is deliberately unchanged from the pre-spine talks -- which
# results a talk shows is a Results decision, deferred until the primary results
# lock. What moved here is only what the spine moved: src_outcomes into Data,
# src_firststage into Results.

TALK30 = [
    ("Introduction", ["src_motivation", "src_twofaces", "src_thispaper"]),
    ("Institutional Background", ["src_ejustice", "src_adjudication"]),
    ("Data", ["src_variation", "src_adversarialfilter", "app_recomp",
              "src_outcomes"]),
    ("Empirical Strategy", ["src_spec", "src_instrument", "src_identbrief"]),
    ("Results", ["src_firststage", "src_story", "src_spine1", "src_favored",
                 "src_representation", "src_gender", "src_candidates",
                 "src_voterballot", "src_seathet"]),
    ("Robustness", ["src_robustness", "src_pretrend"]),
    ("Conclusion", ["src_findings", "src_limitations"]),
    ("References", ["src_references"]),
]

# The 15-minute deck glues Sec. 2-4 (Institutional Background + Data + Empirical
# Strategy) into one heading that names the job. src_ejustice is added because
# Sec. 2 must appear under the spine, and because the electoral court is not
# obvious to a non-Brazilian audience -- which is the audience a conference talk
# has. The pre-spine 15-minute deck had no institutional frame at all.
TALK15 = [
    ("Introduction", ["src_motivation", "src_twofaces", "src_thispaper"]),
    ("Setting and Design", ["src_ejustice", "src_variation", "src_spec"]),
    ("Results", ["src_firststage", "src_story", "src_spine1",
                 "src_representation", "src_candidates", "src_voterballot",
                 "src_seathet"]),
    ("Conclusion", ["src_findings"]),
    ("References", ["src_references"]),
]

HYPER = re.compile(re.escape(BS + "hypertarget{") + r"([^}]+)}")
LINK = re.compile(re.escape(BS + "hyperlink{") + r"([^}]+)}")
# a whole button: \hyperlink{tgt}{\beamergotobutton{label}} (or beamerreturnbutton)
BUTTON = re.compile(
    re.escape(BS + "hyperlink{") + r"(?P<t>[^}]+)}"
    + re.escape("{" + BS) + r"beamer(?:goto|return)button\{[^}]*\}\}")
# separators left behind once a button is removed
LEFTOVER = re.compile(
    r"^(?:" + re.escape(BS) + r"(?:centerline|hfill|quad|,|;|:|!|par|smallskip|"
    r"medskip|bigskip|space|;)|[{}\s,]|" + re.escape(BS) + r"footnotesize)*$")


def targets_of(fid):
    return set(HYPER.findall((FR / f"{fid}.tex").read_text(encoding="utf-8")))


# spacing commands left stranded at end of line once the button they positioned is gone
TRAILING = re.compile(r"(?:" + re.escape(BS) + r"(?:hfill|quad|qquad|,|;|:|!| )|\s)+$")
# "...)  ." -> "...)." : a space orphaned in front of punctuation
ORPHAN_PUNCT = re.compile(r"([)}])\s+([.,;:])")


def strip_buttons(text, keep):
    """Remove buttons whose target is not in `keep`; tidy what they leave behind."""
    out = []
    for line in text.splitlines():
        new = BUTTON.sub(lambda m: "" if m.group("t") not in keep else m.group(0), line)
        if new == line:
            out.append(line)
            continue
        if LEFTOVER.match(new.strip()):
            continue  # the line existed only to carry the buttons
        new = ORPHAN_PUNCT.sub(r"\1\2", TRAILING.sub("", new))
        out.append(new)
    return "\r\n".join(out) + "\r\n"


def build(name, spec, title, subtitle):
    included = [f for _, fs in spec for f in fs]
    # Talks carry no appendix, so they carry no navigation buttons at all
    # (DECK_GUIDE.md, talk-deck minimalism). One button-free variant per frame,
    # shared by both talks -- so the two decks never fight over the same file.
    keep = set()

    driver = [
        "% " + "=" * 58,
        f"% {title} --- derived deck",
        "% Generated from the frame library; see DECK_GUIDE.md.",
        "% Frames come from frames/. A frame needing different prose for this talk",
        "% gets its own frames/<id>_talk.tex, listed here instead of the original.",
        "% The macro sections below are THE SPINE, shared with slides_report.tex",
        "% and the paper. A short deck may GLUE adjacent sections; it may never",
        "% reorder, drop, or invent one.",
        "% " + "=" * 58,
        "",
        BS + "documentclass[aspectratio=169,10pt]{beamer}",
        BS + "input{slides_preamble.tex}",
        "",
        BS + "title{When It Gets to Court: The Electoral Costs of Judicialization}",
        BS + "subtitle{" + subtitle + "}",
        BS + "author{Nara Morais}",
        BS + "institute{FEA--USP}",
        BS + "date{" + BS + "today}",
        "",
        BS + "begin{document}",
        "",
        BS + "maketitle",
        "",
    ]
    made = []
    for section, frames in spec:
        driver.append("% " + "-" * 58)
        driver.append(BS + "section{" + section + "}")
        for f in frames:
            src = (FR / f"{f}.tex").read_text(encoding="utf-8")
            dangling = {t for t in LINK.findall(src)} - keep
            if dangling:
                stripped = strip_buttons(src, keep)
                (FR / f"{f}_talk.tex").write_text(stripped, encoding="utf-8", newline="")
                made.append((f, sorted(dangling)))
                driver.append(BS + "input{frames/" + f + "_talk.tex}")
            else:
                driver.append(BS + "input{frames/" + f + ".tex}")
        driver.append("")
    driver += [BS + "end{document}", ""]
    (PRES / name).write_text("\r\n".join(driver), encoding="utf-8", newline="")

    print(f"\n{name}: {len(included)} frames, {len(made)} _talk variants")
    for f, d in made:
        print(f"   {f}_talk.tex  (dropped buttons -> {', '.join(d)})")
    # nothing may still dangle
    bad = []
    for f in included:
        p = FR / (f + "_talk.tex")
        if not p.exists():
            p = FR / (f + ".tex")
        for t in LINK.findall(p.read_text(encoding="utf-8")):
            if t not in keep:
                bad.append((p.name, t))
    print(f"   residual dangling links: {bad if bad else 'none'}")


build("slides_30min.tex", TALK30, "30-minute seminar", "Seminar --- 30 minutes")
build("slides_15min.tex", TALK15, "15-minute talk", "Conference talk --- 15 minutes")
