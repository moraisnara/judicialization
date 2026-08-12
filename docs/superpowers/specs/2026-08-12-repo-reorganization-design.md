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

## Orphan CSVs under `output/tables/`

Seventeen CSVs under `output/tables/{regressions,descriptives}/` are read by no script and
cited by no document. **They are not treated like the orphan figures above**, for two reasons:

- **`csv = source of truth`** (standing convention, 2026-07-02): the CSV is the saved numeric
  record of a regression that was actually run; the `.tex` is only its deck rendering. A CSV
  that no document `\input`s can still be the record behind a figure the deck *does* show.
- **Every CSV here is gitignored** (`*.csv` is the last rule in `.gitignore`, overriding the
  earlier `!output/tables/` whitelist). Nothing under `output/tables/` is tracked, so deleting
  one changes no committed content. This is local hygiene, not a repo change.

So the reference test used for figures ("no document names it") over-fires on CSVs. The test
here is **does the result it records appear anywhere** — as a figure, a fragment, a macro, or
a prose claim in the deck.

**A — travel with a departing script (6).** No separate decision; they move to
`exploration/output/` with their producer.

| CSV | Producer (moving) |
|---|---|
| `regressions/ancova_validation.csv` | `04_analysis/05_validation.R` |
| `regressions/fd_vs_ancova_comparison.csv` | `04_analysis/05_validation.R` |
| `regressions/family_iv_results.csv` | `03_estimation/03_family_iv.R` |
| `regressions/mean_reversion_splitsample.csv` | `03_estimation/08_mean_reversion.R` |
| `regressions/mean_reversion_splitsample_summary.csv` | `03_estimation/08_mean_reversion.R` |
| `descriptives/lawsuit_topic_selection_worksheet.csv` | `04_analysis/11_lawsuit_topic_selection.py` |

**B — record CSVs; keep (9).** The producing script also emits a consumed asset covering the
same result, so the CSV is that result's source of truth. No action.

| CSV | The result it records, and where it appears |
|---|---|
| `regressions/pretrend_balance.csv` | Numbers behind `pretrend_coefplot.pdf` (`src:pretrend`) |
| `regressions/summary_indices_fixest.csv` | Behind `summary_indices.tex` (`app:multiplicity`) |
| `regressions/mechanism_finance_fixest.csv` | Behind the mechanism fragment |
| `regressions/exposure_robust_akm.csv` | AKM variant of `exposure_robust_se.csv`, which the macro hub reads |
| `regressions/legislative_first_stage_fixest.csv` | The legislative first stage the deck reports |
| `regressions/extensive_margin_decomposition.csv` | Behind `extensive_margin_macros.tex` (`app:extensive`) |
| `regressions/zero_exposure_robustness.csv` | Zero-exposure check from the same script |
| `descriptives/candidate_pool_descriptives.csv` | Candidate-pool descriptives |
| `descriptives/litigation_family_shares.csv` | Within-adversarial family composition |

**C — genuine dead end; delete + strip (1).**

| CSV | Producer (stays) | Why |
|---|---|---|
| `regressions/liml_comparison.csv` | `03_estimation/02_iv_main.R` | Zero mentions of LIML in *any* document. With `K=1` the estimator is 2SLS ≡ LIML by construction, so the check confirms a mechanical identity. Delete the file, strip the emit block, and remove its row from the CLAUDE.md "Output tables" quick reference |

**D — flagged, not resolved here (1).** `descriptives/gps_balance_tests.csv`
(`04_analysis/04_iv_diagnostics.py`) is **not** a delete candidate and **not** a clean record.
It holds the share-covariate balance test — a different test from the R pre-trend balance in
category B — and the deck asserts that defense in prose (`slides_report.tex:989`, "we defend
the design on the exogeneity of the shares — balance, pre-trend, and a placebo shifter")
without citing a number from it. Two live problems, both pre-existing (README wrinkle #3):
the deck's balance claim shows no figures, and the test is computed in Python, which the
"regressions in R only" rule bars for anything reaching a slide. Resolving it means porting
the test to R and wiring it to the macro hub, or dropping the claim — a scope decision for
Nara, out of scope for this reorg.

Net effect on the reorg: one file deleted, one emit block stripped, one CLAUDE.md row removed.

## Output routing for archived scripts

Moved scripts currently write into `output/`. Repoint each to `exploration/output/` so
`output/` means "paper assets only". Four edits; `PROJECT_ROOT` resolution is unchanged
because depth 2 is preserved.

## The auditor

`code/utils/audit_pipeline.py` implements the three tests as a re-runnable check. It reports:

- scripts failing all three tests (archive candidates),
- committed outputs referenced by no document (deletion candidates),
- documents referencing assets absent from disk (build breakers),
- unreferenced CSVs under `output/tables/`, listed **separately** and never as deletion
  candidates — under `csv = source of truth` an unreferenced CSV is a question ("is this
  result shown anywhere?"), not a defect.

**Detection must resolve path constants, not scan nearby lines.** Scripts bind a path to a
variable and use the verb far away — `OUT_CSV <- file.path(ROOT, ".../x.csv")` in a constant
block at the top, `fwrite(res, OUT_CSV)` two hundred lines down. Two weaker heuristics were
tried and both undercounted: a same-line regex misread writers as readers, and a ±4-line
context window scored constant-block declarations as "mentioned, verb unknown" and silently
treated them as read — hiding four of the seventeen orphans (both `mean_reversion_*` and
both `09_extensive_margin.R` outputs). The auditor must find the variable a path literal is
assigned to, then look for read/write verbs applied to *that variable* anywhere in the file.

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
- **The share-balance defense shows no numbers.** See category D above: the deck claims share
  exogeneity is defended on "balance", but the only balance table (`gps_balance_tests.csv`) is
  cited nowhere and is computed in Python. Port to R and cite, or drop the claim.
- **`output/tables/` is the declared source of truth but is entirely untracked.** `*.csv` is
  gitignored repo-wide, so a clean checkout has no saved regression records at all — they
  exist only on this machine, recoverable only by re-running the pipeline. Consistent with
  "data never leaves this repo", but worth a deliberate decision rather than a side effect.

## Risks

| Risk | Mitigation |
|---|---|
| A stripped emit block silently changes a consumed output | Re-run the stage, diff every surviving asset; only the named file may disappear |
| A moved script is later found to back a deck claim | Nothing is deleted — `exploration/` keeps it runnable at the same depth, and its README says what it backed |
| The big working-tree commit hides a regression | Commit in four themed chunks before the reorg, so the reorg diff contains only moves and strips |

## Done when

- `code/` contains only scripts passing one of the three tests; the four named scripts and
  `SPECIFICATION.md` are under `exploration/` with a README explaining each.
- The nine orphan assets and `liml_comparison.csv` are gone, and no surviving script
  regenerates them.
- `code/utils/audit_pipeline.py` reports zero archive candidates, zero orphan outputs, the
  two verification gates under "infrastructure", one known build breaker (the
  `extended_abstract.tex` figure, flagged above), and the unreferenced-CSV list down to ten —
  the nine record CSVs plus `gps_balance_tests.csv`.
- `run_all.py` completes without referencing a moved script.
- Both decks compile at their baseline page counts (67 / 11).
- `git status` is clean and `main` is pushed.
