# Repo reorganization — paper pipeline vs exploration

**Date:** 2026-08-12 · **Branch:** `framing-application` · **Status:** design, approved by Nara

## The rule

> Scripts in the main folders must generate inputs or results for the paper. Exploration
> that did not reach the paper, but is important enough to survive an easy drop, moves to
> a separate archive location.

Two clarifications settled before drafting:

- **"The paper" includes `slides_report.tex`.** The Beamer report *is* the research report
  and `paper.tex` is drafted from it, so a deck-only script has reached the paper's evidence
  base. (Standing rule: "presentation is a report".)
- **The archive is `exploration/` inside this repo**, mirroring the stage folders — not a
  fourth GitHub repo. Two facts force this: every script resolves the project root as
  exactly two levels up from itself (`parents[2]` in Python, `file.path(SCRIPT_DIR, "..", "..")`
  in R), and `*.csv` is globally gitignored so the data never leaves this repo. A depth-2
  `exploration/<stage>/` layout keeps every archived script runnable with zero path edits;
  a separate repo would need the root resolution rewritten in every moved file and would
  have no `data/clean/` to read.

This modifies the standing cleanup rule ("drop orphan scripts on sight, never archive").
Orphan *scripts* now have a sanctioned home. Orphan *outputs* are still deleted — an output
is regenerable by its producing script, so once the script is safe the stale asset carries
no information.

## Operationalizing the rule: three tests

A script stays in `code/` if **any** test passes:

1. **Direct consumption** — a document `\input`s or `\includegraphics`es one of its outputs.
   Documents = `slides_report.tex`, `slides_advisor.tex`, `paper.tex`,
   `extended_abstract.tex`, `estimating_equations.tex`.
2. **Macro consumption** — `04_analysis/06_abstract_macros.py` reads one of its CSVs. The
   macro hub converts CSVs into `\ARMarginP`-style macros consumed by deck *and* paper, so
   a script can reach both documents without ever emitting a `.tex`.
3. **Transitive data dependency** — it writes a `data/` artifact that a script passing (1)
   or (2) reads, directly or through a chain.

Test 2 is not optional bookkeeping. Four scripts pass *only* test 2 —
`06_wild_bootstrap_ar.R` (headline AR-WCR inference), `07_multiplicity.R` (Holm/BH),
`04_iv_diagnostics.py` (Rotemberg), `07_exposure_robust_se.R` (BHJ/AKM exposure-robust SE).
A classification built on `\input` evidence alone would archive the paper's headline
inference and its one binding caveat.

## Classification result

**45 of 49 script files stay.** The download and build layers pass test 3 (with the two
exceptions below); the estimation and analysis layers pass 1 or 2; `code/utils/` holds
three sourced helpers that emit nothing. The pipeline was already close to paper-only; this
is a trim, not a restructure.

### Explicit exception: verification gates

`01_download/00_verify_raw_data.py` and `02_build/00_verify_lawsuits.py` fail all three
tests — their manifests are read by nothing. They **stay** as pipeline infrastructure: both
are wired into `run_all.py` (lines 32 and 41) as integrity gates that run before the stage
they guard. The rule is about *research* dead ends, not about the machinery that makes the
paper's pipeline runnable. Any future script that only verifies or reports on the pipeline
inherits this exception; the auditor lists them under a separate "infrastructure" heading
rather than as archive candidates.

### Moving to `exploration/`

| File | Destination | Why it fails all three tests |
|---|---|---|
| `code/03_estimation/03_family_iv.R` | `exploration/03_estimation/` | `family_iv_results.csv` is not `\input`, not read by the macro hub, and no deck frame presents family-split IV results. Superseded by `13_reclassification_robustness.R` (family-level Z) and `11_summary_indices.R` |
| `code/03_estimation/08_mean_reversion.R` | `exploration/03_estimation/` | Split-sample first-stage falsification. Its only asset, `firststage_splitsample.pdf`, is already recorded in README as shown on **nothing** |
| `code/04_analysis/05_validation.R` | `exploration/04_analysis/` | FD-vs-ANCOVA comparison + ANCOVA falsification gate. See the caveat below |
| `code/04_analysis/11_lawsuit_topic_selection.py` | `exploration/04_analysis/` | Topic selector for the `tse-shift-share` redesign. No script reads `lawsuit_topic_selection_worksheet.csv` — it is a decision ledger for Nara, not a pipeline step |
| `SPECIFICATION.md` (untracked) | `exploration/SPECIFICATION_tse_shift_share.md` | Its own header states it specifies the redesign and that "the committed propaganda-Bartik/ANCOVA design on `main` is the preserved fallback". Committing it at repo root would advertise it as the paper's spec |

**Caveat on `05_validation.R`.** Its section [A] is the evidence behind the deck's "Why
ANCOVA, not first differences" (`src:fd`, `slides_report.tex:428`). But the table the deck
actually displays is `appendix_first_difference.tex`, written by `02_iv_main.R`, and its
section [B] duplicates falsifications that `05_pretrend_balance.R` and
`04_placebo_nonadversarial.R` already produce for the deck. It is decision-evidence for a
locked estimator choice, not a paper asset — exactly the "important enough to survive"
category. `exploration/README.md` must record that it answers a referee asking "why ANCOVA?".

The last two rows travel together: they are one artifact pair from the `tse-shift-share`
redesign lane. This also resolves the open question of whether
`11_lawsuit_topic_selection.py` belonged in the mainline `run_all.py` — it does not.

## Orphan outputs

Nine committed assets are consumed by no document. Only one belongs to a departing script;
the other eight are emitted by scripts that stay, so deleting the files alone is futile —
the next `run_all.py` regenerates them. **Decision: delete the files and remove the emitting
blocks**, so a core script emits only paper assets.

| Asset | Emitted by | Action |
|---|---|---|
| `firststage_splitsample.pdf` | `03_estimation/08_mean_reversion.R` | Delete; producer departs, emit block stays with it |
| `litigation_timing_{count,rate,share}.pdf` | `04_analysis/02_descriptive_figures.R` | Delete + strip emit. Only `litigation_timing_shape.pdf` is used |
| `firststage_binscatter.pdf` | `04_analysis/03_result_figures.R` | Delete + strip emit. `firststage_linear.pdf` is the one the deck shows |
| `nonadversarial_placebo_rf.tex` | `03_estimation/04_placebo_nonadversarial.R` | Delete + strip emit |
| `open_seat_blank_rate.tex` | `03_estimation/02_iv_main.R` | Delete + strip emit |
| `pretrend_balance_{consolidation,voterbehavior}.tex` | `03_estimation/05_pretrend_balance.R` | Delete + strip emit. `pretrend_coefplot.pdf` from the same script IS used and stays |

Each strip must remove only the block that writes the named asset, leaving every consumed
output of that script byte-identical. Verified by re-running the pipeline stage and diffing.

## Output routing for archived scripts

Moved scripts currently write into `output/`. Repoint each to `exploration/output/` so
`output/` means "paper assets only". Four edits; `PROJECT_ROOT` resolution is unchanged
because depth 2 is preserved.

## The auditor

`code/utils/audit_pipeline.py` implements the three tests as a re-runnable check. It reports:

- scripts failing all three tests (archive candidates),
- committed outputs referenced by no document (deletion candidates),
- documents referencing assets absent from disk (build breakers).

It is a report, not a gate — it prints findings and exits 0. Rationale: the classification
will drift as scripts are added, and the alternative is redoing this analysis by hand.

## Wiring and documentation updates

- `code/run_all.py` — drop the four moved calls.
- `README.md` — stage tables for 03/04; the `output/figures/` and `output/tables/tex/`
  tables lose their orphan rows; "known wrinkles" items 3, 6 and 8 are resolved or restated.
- `CLAUDE.md` — record the `exploration/` lane and the three tests under the naming rules.
- `exploration/README.md` — new: per-script entry giving what it was, what it produced, and
  why it stopped short of the paper.

## Sequencing

The reorg is step 3. Steps 1–2 clear the ground so it lands as a reviewable diff.

1. **Commit the working tree** (~36 files, pending for weeks). Split: new analysis
   outputs+scripts · estimation changes+regenerated outputs · docs · the two deletions.
   Urgent independent of the reorg: all 12 untracked figures/fragments are referenced by
   the committed decks and `run_all.py` calls three untracked scripts, so a clean checkout
   of `main` today cannot build the decks or run the pipeline.
2. **Close the FRAMING plan record** — `docs/superpowers/plans/2026-08-11-framing-application.md`
   has 69 unchecked boxes for work that shipped.
3. **The reorganization** as specified above.
4. **Merge `framing-application` → `main` and push** (main is also 5 commits unpushed).
5. **Verify** — `run_all.py` completes; both decks compile at 67 / 11 pages; the auditor
   reports zero archive candidates and zero orphan outputs.

## Flagged for Nara — not in scope

- `extended_abstract.tex` references `../figures/forest_voter_behavior.pdf`, which is not on
  disk, so that document cannot compile. The figure was renamed to `voterbehavior_forest.pdf`
  and then deleted. Fixing it means either restoring a figure or editing the paper file —
  a paper-side call.
- `FRAMING.md` uses "concentration" for the top-two margin in its own D4 header and D5 table
  column, which the vocabulary lock reserves for *consolidation*. Recorded in the FRAMING
  application record; still open.
- Three R scripts hard-code an absolute `ROOT` path (`"c:/Users/naral/..."`) instead of
  deriving it from `SCRIPT_DIR`. Pre-existing portability defect, untouched here.
- `data/clean/zona_eleitoral_lookup.csv` is read by no script and written by no script, so
  deleting it is not undoable by re-running the pipeline. Left alone.

## Risks

| Risk | Mitigation |
|---|---|
| A stripped emit block silently changes a consumed output | Re-run the stage, diff every surviving asset; only the named file may disappear |
| A moved script is later found to back a deck claim | Nothing is deleted — `exploration/` keeps it runnable at the same depth, and its README says what it backed |
| The big working-tree commit hides a regression | Commit in four themed chunks before the reorg, so the reorg diff contains only moves and strips |

## Done when

- `code/` contains only scripts passing one of the three tests; the four named scripts and
  `SPECIFICATION.md` are under `exploration/` with a README explaining each.
- The nine orphan assets are gone and no surviving script regenerates them.
- `code/utils/audit_pipeline.py` reports zero archive candidates, zero orphan outputs, the
  two verification gates under "infrastructure", and one known build breaker (the
  `extended_abstract.tex` figure, flagged above).
- `run_all.py` completes without referencing a moved script.
- Both decks compile at their baseline page counts (67 / 11).
- `git status` is clean and `main` is pushed.
