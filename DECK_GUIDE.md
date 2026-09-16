# DECK_GUIDE.md — How the presentation is built

**Status:** convention, adopted 2026-08-12. Single deck since 2026-09-16.
**Governs:** everything under `output/presentation/`.
**Does not govern:** `output/paper/paper.tex` and `output/paper/extended_abstract.tex` —
Nara writes the paper. The deck is the intermediary report.

---

## The deck

There is **one deck**: `slides_report.tex`. It is our view of the paper and the story
the results tell: every result presented, every claim stated at its true confidence
tier. It is read, not presented start to finish.

The 30-minute, 15-minute, and advisor decks were dropped on 2026-09-16 so the
repository has one presentation to keep consistent with the results. They remain in
git history (last present in commit `52065fd`). See "If a talk deck returns" below.

**The deck is an argument, not a history.** A design we abandoned does not get an
appendix frame. A result we stand behind belongs in the deck, however tentative its
tier. Abandoned designs live in git history (the act-family design is tag
`archive/act-redesign-wip`) and in the dated plans under `docs/superpowers/`.

---

## The section spine

The deck carries the paper's macro sections in the paper's order (`WRITING_GUIDE.md`
§5), so the deck and the paper can be read side by side and a section number means
the same thing in both. Subsections and frames change; the spine does not.

> **Status:** §1–§5 and §7 settled 2026-08-12; §6 provisional.

### 1. Introduction — settled 2026-08-12

Subsections in order: **Motivation → This Paper → Literature**.

Literature comes *last* by the standing rule in `WRITING_GUIDE.md` §7 — late and
instrumental, never a standalone review dumped up front. "This Paper" states the
contribution before the literature that positions it, per Evans element 5.

| Subsection | Frames |
|---|---|
| Motivation | `src_motivation`, `src_twofaces` |
| This Paper | `src_thispaper` |
| Literature | `src_literature` |

### 2. Institutional Background — settled 2026-08-12

**Two goals, and both are required.** First, it presents the electoral court —
non-obvious to any non-Brazilian audience, and the paper is unreadable without it.
Second, it lays out the institutional facts identification later leans on: that the
adversarial arena is *horizontal* (candidate sues candidate; voters have no
standing), and that the rule-and-enforcement shifts are *national*, reaching a
municipality only through its own prior exposure.

**These two goals stay separate.** Background *states* the institutional facts; the
identification argument built on them lives in §4, Empirical Strategy.

| Subsection | Frames |
|---|---|
| The Electoral Court | `src_ejustice` |
| The Adversarial Arena | `src_adjudication` |
| *(appendix)* | `app_timeline` |

### 3. Data — settled 2026-08-12

Data says **what exists and what we built from it**; Empirical Strategy says what we
do with it and why it identifies anything. Outcome definitions are therefore *here*,
not in §4 — they are constructed variables, and §4 carries only the equation and the
identifying argument.

`src_variation` opens the section as the bridge out of Background: it states why we
need variation local politics does not manufacture, then hands to the sources.
Outcomes come last, immediately before §4, so the outcome family lands next to the
equation that estimates it.

| Subsection | Frames |
|---|---|
| *(section opener)* | `src_variation` |
| Sources | `src_datasources` |
| What We Keep | `src_adversarialfilter` |
| What We Measure | `src_outcomes` |
| *(appendix)* | `app_recomp` |

### 4. Empirical Strategy — settled 2026-08-12

**Strategy states assumptions; Results shows estimates.** The identification
discussion stays here — the estimating equation, how the instrument is built, and
what has to be true for it to work. The **first stage moves to §5**: it is an
estimate, and an estimate belongs with the estimates.

**The complier population is named here, in the main section.** The first stage lives
entirely on zero-vs-any 2020 litigation — the intensive margin is a real null
(PPML and NegBin, p=.37/.08) — so the estimate is a LATE for **onset compliers**:
municipalities that went from no adversarial contestation to some. That is not a
robustness check, it is what the number means, and leaving it in the appendix
overstates external validity by omission.

| Subsection | Frames |
|---|---|
| What We Estimate | `src_spec` |
| The Instrument | `src_instrument`, `src_instrumentmap` |
| Identification \& Inference | `src_identbrief`, *`src_compliers`* (to build) |
| *(appendix)* | `app_extensive` — the evidence behind the complier claim |

*To build:* `src_compliers.tex`, promoting the core of `app_extensive` into the main
section and pointing to the first stage in §5 as its evidence. `app_extensive` stays
as the backing.

### 5. Results — settled 2026-08-12

**Subsections are substantive, not tiered.** The alternative — grouping frames under
"What Is Robust" and "What Is Tentative" — is harder to misread but destroys the
candidates → voters → outcome spine, and the deck exists to be an argument.

**The rule that replaces it: no frame ships without its confidence tier stated on the
frame.** The tier discipline lives in the prose of every result, not in a heading.
A Results frame that does not say how much weight its estimate carries is unfinished.

| Subsection | Frames |
|---|---|
| The First Stage | `src_firststage` |
| What the Contest Produces | `src_story`, `src_spine1`, `src_gender` |
| Candidates and Voters | `src_favored`, `src_representation`, `src_candidates`, `src_voterballot` |
| Heterogeneity by Seat Type | `src_seathet` |

Frames follow the **outcome layers** defined in `src_outcomes`, not the order they
were written. Layer 3 (how open the contest stays) is *the result*, so the gender
decomposition sits with it — it splits the headline, it does not test an engine.
Layers 1 and 2 (who runs, how voters respond) are *the engines*, so the
representation null and the incumbency descriptive that explains it move there.

The first stage gets its own subsection rather than opening the result because it
carries a reading no other frame does. The coefficient is **positive** (`\FSCoef`),
but it is identified on the extensive margin: municipalities with no adversarial
litigation in 2020 have zero exposure and gain filings, litigating municipalities
lose them, and there is no gradient across nonzero exposure. The positive slope is
litigation *starting* where there was none (onset, or spread), not litigation
amplifying where it already existed, and it cannot be separated from mean reversion.
Miss that and every complier statement in §4 is misread.

(The negative first stage, ψ ≈ −1.08, belongs to the archived act-family design, not
to this instrument.)

### 6. Robustness — provisional 2026-08-12

**Main section: pre-trends only, for now.** The primary results are not final, and
robustness architecture built on top of a moving headline is work that gets redone.
Everything else stays in the appendix until the primary results lock.

| Subsection | Frames |
|---|---|
| *(no subsection)* | `src_robustness`, `src_pretrend` |
| *(appendix, pending promotion)* | `app_exposure`, `app_multiplicity` |
| *(appendix, staying)* | `app_rotemberg`, `app_shares`, `app_inference`, `app_pretrend`, `app_ptrobust`, `app_tdef`, `app_reclass`, `app_fd` |

**The promotion criterion, agreed now so the decision is mechanical later:** a check
earns a main frame if, left unaddressed, a referee stops believing the headline.
Everything else is appendix.

Two checks are queued against that criterion and decided **when the primary results
are final**:

- **BHJ/AKM exposure-robust SEs** — already named as the one binding caveat of the
  ANCOVA decision.
- **Multiplicity** — the answer depends on which p-values are corrected. Over the
  eighteen reduced-form p-values the margin survives Holm and BH at 5% and
  Romano–Wolf at 10% (p_rw = .059). Over the eighteen 2SLS p-values nothing
  survives Holm or BH. A referee will find this unaided, so if it is promoted the
  frame must state both bases, as `src_findings` and `app_multiplicity` already do.

### 7. Conclusion — settled 2026-08-12

**Two frames: Findings → Limitations.** `src_contribution` was **cut** (and its file
deleted 2026-09-16). Under the Evans order locked in §1, "This Paper" states the
contribution before the literature that positions it; restating it at the end was an
artifact of the deck predating that reorder, not a bookend.

What a conclusion adds that an introduction cannot is the conditions under which the
paper fails. **Limitations is therefore the load-bearing frame**, and it has one
specific job: name what would overturn the tentative face-assignment. The ballot
assigns the face and that assignment is tentative — the conclusion says what evidence
would flip it.

| Subsection | Frames |
|---|---|
| Findings | `src_findings` |
| Limitations | `src_limitations` |

### Appendix and References

Not spine sections. **Appendix** collects every `app_` frame the deck reaches by
button, in the order of the main sections that point into it. **References** is one
frame, `src_references`, last.

---

## The frame library

Every frame is one file under `output/presentation/frames/`. The deck is a thin driver
that `\input`s the frames in order.

```
output/presentation/
  slides_report.tex            driver: sectioning + one \input per frame
  slides_preamble.tex          theme, colors, commands, number macros
  check_links.py               every button resolves; no unused frame files
  DECK_WORKPLAN.md             frame-by-frame review and open items
  biblio.bib
  frames/
    src_motivation.tex
    src_twofaces.tex
    ...
    app_rotemberg.tex
    ...
```

**Naming.** The filename is the frame's navigation target with the colon replaced by an
underscore: `\hypertarget{src:seathet}` lives in `frames/src_seathet.tex`. `src_` is a
main-section frame; `app_` is an appendix frame reached by button. Every frame has a
target, and no two frames share one.

**A frame file contains only its frame.** No `\section{}`, no `\subsection{}`, no
`\input` of another frame. Sectioning lives in the driver, so moving a frame between
sections is a one-line edit.

**A dangling button compiles.** A `\hyperlink` to a target the driver never `\input`s
still builds — the button just goes nowhere. `check_links.py` checks that every
`\hyperlink` resolves and flags any frame file the driver does not `\input`; a frame
the deck no longer uses is deleted, not kept in the library.

**Adding a frame:** write `frames/<prefix>_<id>.tex`, add one `\input` line to
`slides_report.tex`, run `python check_links.py`.

---

## Standing rules the deck inherits

These predate this guide and are not negotiable by it.

1. **Never hardcode a number.** Every estimate comes from
   `../tables/tex/abstract_macros.tex`, auto-generated by
   `code/04_analysis/06_abstract_macros.py`. Re-run that script after any estimation
   change and recompile. A number typed into a frame is a bug, because it survives the
   estimate it was copied from.
2. **Figures carry no baked-in titles, footnotes, or captions.** Those live on the
   Beamer frame. Producing scripts source `code/utils/figure_style.R`.
3. **Framing is locked in `FRAMING.md`.** The vocabulary lock, the confidence tiers,
   and the Leveling/Barrier dichotomy govern the deck. American spelling throughout.
4. **Claims sit at their true tier.** The headline finding (consolidation) is robust;
   its interpretation (which face) rests on the ballot and is tentative. A deck that
   blurs those has drifted.

---

## House prose style

**The audience is academic.** These frames are read by economists and political
scientists, and prose that performs its own cleverness reads as unserious to them —
or, since 2026, as machine-written. Adopted 2026-08-12 after Nara flagged the decks
as "too AI-look-alike."

**Titles.** Setup frames (Introduction, Background, Data, Empirical Strategy) take
**declarative noun phrases** — "Outcomes: Three Layers of the Contest." Results frames
take **claim-titles** — "Adversarial Litigation Consolidates the Mayoral Race" — which
are standard in economics seminars and are what a referee expects over an estimate.
**No rhetorical questions, and no colon-plus-tagline.** "What We're Measuring: Level
the Field, or Raise the Bar?" is both.

**Eight tells to remove on sight.**

1. Rhetorical-question titles and tagline subtitles.
2. Bold-label lead-ins — "**The lever.**", "**Why it matters for identification:**".
3. Emphasis as rhythm. Bold and italics mark **terms of art on first use**, nothing
   else. Emphasis sprinkled to make a sentence land is the single loudest tell.
4. Aphorisms — "The arena does not grow, it rearranges."
5. "Not X, but Y" constructions and rules of three.
6. The em-dash aside as default connector. A period usually works.
7. Deck self-narration — "Next, the equation, then the instrument behind it." The
   frame order already says this; saying it too is padding.
8. Metaphor scaffolding — lever, engine, spine, arena. Say the mechanism.

**What replaces them:** declarative sentences, terms defined once, and the estimate
doing the work. Two to four sentences of prose per frame is usually enough.

**The vocabulary lock is not style and is not negotiable here.** `FRAMING.md` fixes
one word per concept — consolidation vs. concentration, withdrawal, decisiveness,
open vs. contested, weaponization never "lawfare." Rewriting for register must not
drift a locked term, and rewriting is a good moment to *catch* drift: the calibration
pass on `src_outcomes` found "victory margin" where the lock requires the top-two
margin be called **consolidation**.

---

## If a talk deck returns

Rules already learned, so a new talk does not relearn them:

- **Same spine, glued not reordered.** A short deck may present adjacent sections
  under one heading; it may not reorder the spine or invent a section.
- **A talk is a driver over the same frame library.** Where it needs different prose,
  that is a separate file beside the original, never a conditional inside a shared
  frame. The deck's inputs change; the report's frames do not.
- **Talk-deck minimalism**, from Nara's edits to the 2026-08 advisor deck: evidence
  only (no methods footlines on results frames), at most one button per frame and
  only to its own full-table backup, defensive and robustness backups deleted rather
  than demoted, single-sentence framing without qualifier chains. The report is
  exempt.
- Extend `check_links.py` to the new driver before presenting it.

---

## Building

From `output/presentation/`. Citations come from `biblio.bib` through BibTeX, so a deck
whose citations show as `(?)` has simply not had its `bibtex` pass:

```bash
pdflatex -interaction=nonstopmode slides_report.tex
bibtex   slides_report
pdflatex -interaction=nonstopmode slides_report.tex
pdflatex -interaction=nonstopmode slides_report.tex
```

Once the `.bbl` exists, day-to-day edits need only the two `pdflatex` passes; re-run
`bibtex` when citations change.

**Fragment overflow is silent.** A table that runs past the bottom of a frame produces
no warning — it is simply cut off in the PDF. After changing a frame that carries a
`\resizebox`ed fragment, rasterize the page and look at it. Do not trust a clean
compile.

The deck currently reports **30 overfull `\vbox`es** (2026-09-16, after the citation
audit; every flagged page was rasterized and nothing is cut off) — a standing condition,
not a regression. Because of it you cannot use "no overfull warnings" as your safety
check; compare the count against the last known-good build instead, and investigate
only a count that *rose*.

**A negative `\vspace` right after `\end{columns}` overlaps the next paragraph.** The
column box is tall, so the interline glue falls back to `\lineskip` (1pt) and the
negative space pulls the text into the columns. Use zero or positive space there.
Likewise, a `\beamergotobutton` on its own line inside a `p{}` table cell overlaps the
line above; start that line with `\par\vspace{3pt}`.

**Check the page count after any structural edit.** A driver that lost an `\input`
still compiles perfectly; the frame is just gone. Known-good (2026-09-16): **63
frames, 68 pages** (the reference list runs to more pages since the citation audit).
`python check_links.py` must exit 0.

**When restructuring rather than editing prose, prove the output did not move.** Dump the
text layer before and after and diff it:

```bash
pdftotext slides_report.pdf before.txt   # ...restructure...
pdftotext slides_report.pdf after.txt
diff before.txt after.txt                # must be empty
```

An empty diff plus an unchanged page count is what makes a structural change safe to
commit. PDF bytes are not a valid check — `ggsave` and pdfTeX both stamp creation times,
so the files differ even when nothing did.
