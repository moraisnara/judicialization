# Repo Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `code/` contain only scripts that produce paper/deck assets, move four exploration scripts to a runnable `exploration/` lane, delete the orphan outputs, and land it all on `main`.

**Architecture:** Three phases that must run in order. First the ~36-file working tree is committed in four themed chunks, so the reorg lands as a reviewable diff containing only moves and deletions. Then the reorg itself: move scripts, strip the emit blocks that regenerate orphan assets, add a re-runnable auditor. Finally verification (pipeline runs, decks compile) and merge to `main`.

**Tech Stack:** Python 3.13 (`C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe`), R 4.6.0 (`C:\Program Files\R\R-4.6.0\bin\Rscript.exe`, not on PATH — call explicitly), `fixest`, `ggplot2`, pdflatex, git. Shell is PowerShell; the Bash tool is available for POSIX scripts.

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-08-12-repo-reorganization-design.md`. Every classification decision comes from there; do not re-derive it.
- **Never add `Co-Authored-By: Claude`** or any Claude authorship trailer to a commit.
- **Never write prose into `output/paper/paper.tex` or `output/paper/extended_abstract.tex`.** Nara writes the paper. This plan touches neither file.
- **Regressions run in R/fixest only.** No task may compute a coefficient, SE, or F in Python.
- **Depth-2 root resolution is load-bearing.** Every script resolves the project root as exactly two levels up (`Path(__file__).resolve().parents[2]`, `normalizePath(file.path(SCRIPT_DIR, "..", ".."))`). Archived scripts go to `exploration/<stage>/script.ext` — same depth, zero path edits.
- **`*.csv` is gitignored repo-wide** (last rule in `.gitignore`). Nothing under `output/tables/` is tracked. Deleting a CSV changes no committed content.
- **Working directory** is `C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization` for every command. Branch is `framing-application`.
- **Two files must NOT be committed at repo root:** `SPECIFICATION.md` and `code/04_analysis/11_lawsuit_topic_selection.py`. They are untracked today and move into `exploration/` in Task 3. Never `git add` them from their current paths.
- **Baseline page counts:** `slides_report.tex` = 67 pages, `slides_advisor.tex` = 11 pages. Any change to these is a regression.

---

### Task 1: Commit the working tree in four themed chunks

A clean checkout of `main` today cannot build: 12 untracked figures/fragments are referenced by the committed decks, and `run_all.py` calls three untracked scripts. This is urgent independent of the reorg.

**Files:**
- Commit (no content edits in this task): the 36 paths listed in the steps below
- Deliberately left uncommitted: `SPECIFICATION.md`, `code/04_analysis/11_lawsuit_topic_selection.py`

**Interfaces:**
- Consumes: nothing
- Produces: a `git status` whose only untracked entries are `SPECIFICATION.md` and `code/04_analysis/11_lawsuit_topic_selection.py`

- [ ] **Step 1: Confirm the starting state matches this plan**

```bash
git status --porcelain
```

Expected: 36 entries. If the set differs from the four chunks below, STOP and report the difference rather than improvising a chunk assignment.

- [ ] **Step 2: Commit chunk A — estimation and build changes plus the fragments they regenerate**

```bash
git add code/02_build/03_vote_outcomes.py \
        code/03_estimation/02_iv_main.R \
        code/03_estimation/02b_iv_legislative.R \
        code/03_estimation/09_extensive_margin.R \
        output/tables/tex/extensive_margin_macros.tex \
        output/tables/tex/legislative_iv_candidate_pool.tex \
        output/tables/tex/executive_iv_ballot_council.tex \
        output/tables/tex/executive_iv_ballot_mayoral.tex \
        output/tables/tex/executive_iv_gender_consolidation.tex \
        output/tables/tex/executive_iv_gender_gap.tex \
        output/tables/tex/executive_iv_heterogeneity_seat.tex
git rm --cached output/tables/tex/executive_iv_ballot_panel.tex
git commit -m "estimation: split the ballot panel by office and add the gender and seat cuts

The single executive_iv_ballot_panel table is replaced by per-office tables
(mayoral, council), and the gender-consolidation, gender-gap and seat
heterogeneity cuts get their own fragments. Legislative candidate-pool and
extensive-margin fragments regenerate off the same run."
```

- [ ] **Step 3: Commit chunk B — new analysis scripts, figures, and the runner**

```bash
git add code/04_analysis/09_summary_statistics.R \
        code/04_analysis/10_candidate_rank_profile.py \
        code/04_analysis/03_result_figures.R \
        code/run_all.py \
        output/tables/tex/sample_summary_statistics.tex \
        output/tables/tex/candidate_rank_profile.tex \
        output/figures/entrant_coefplot.pdf \
        output/figures/firststage_binscatter.pdf \
        output/figures/firststage_linear.pdf \
        output/figures/representation_coefplot.pdf \
        output/figures/turnout_coefplot.pdf \
        output/figures/candidate_supply_coefplot.pdf \
        output/figures/gender_consolidation_coefplot.pdf \
        output/figures/heterogeneity_seat_coefplot.pdf \
        output/figures/legislative_coefplot.pdf \
        output/figures/voterbehavior_seat_coefplot.pdf
git rm --cached output/figures/voterbehavior_forest.pdf
git commit -m "analysis: add summary statistics and candidate rank profile, retire the forest plot

09_summary_statistics.R and 10_candidate_rank_profile.py join the pipeline.
The voter-behavior forest plot is replaced by voterbehavior_seat_coefplot,
which carries the office x seat-type split the deck now shows."
```

- [ ] **Step 4: Commit chunk C — the macro hub**

```bash
git add code/04_analysis/06_abstract_macros.py output/tables/tex/abstract_macros.tex
git commit -m "macros: regenerate abstract macros for the new office and seat cuts"
```

- [ ] **Step 5: Commit chunk D — documentation**

```bash
git add CLAUDE.md README.md output/paper/estimating_equations.tex
git commit -m "docs: record the estimating equations and refresh the conventions"
```

- [ ] **Step 6: Verify only the two deliberate holdouts remain**

```bash
git status --porcelain
```

Expected output, exactly two lines:

```
?? SPECIFICATION.md
?? code/04_analysis/11_lawsuit_topic_selection.py
```

If any other path is still uncommitted, add it to the chunk it belongs to and amend that commit.

- [ ] **Step 7: Verify a clean checkout can now build**

```bash
git stash list
git ls-files output/figures/ | wc -l
git ls-files output/tables/tex/ | wc -l
```

Expected: every figure and fragment the decks reference is now tracked. Cross-check with the auditor in Task 5; for now confirm `voterbehavior_seat_coefplot.pdf` and `sample_summary_statistics.tex` appear in `git ls-files`.

---

### Task 2: Close the FRAMING plan record

`docs/superpowers/plans/2026-08-11-framing-application.md` has 69 unchecked boxes for work that shipped in commits `210aaa7` through `771c8cf`. The record is misleading as written.

**Files:**
- Modify: `docs/superpowers/plans/2026-08-11-framing-application.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing consumed by later tasks

- [ ] **Step 1: Confirm the box count**

```bash
grep -c "^- \[ \]" docs/superpowers/plans/2026-08-11-framing-application.md
grep -c "^- \[x\]" docs/superpowers/plans/2026-08-11-framing-application.md
```

Expected: `69` and `0`.

- [ ] **Step 2: Tick every box**

```bash
sed -i 's/^- \[ \]/- [x]/' docs/superpowers/plans/2026-08-11-framing-application.md
grep -c "^- \[ \]" docs/superpowers/plans/2026-08-11-framing-application.md
```

Expected final count: `0`.

- [ ] **Step 3: Add the closing note at the top of the file**

Insert immediately after the plan's H1 title line:

```markdown
> **Status: CLOSED 2026-08-12.** Every step shipped in commits `210aaa7`..`771c8cf`
> on branch `framing-application`. One item remains open and was moved to the
> reorganization spec's "Flagged for Nara" list: `FRAMING.md` still uses
> "concentration" for the top-two margin in its D4 header and D5 table column,
> which the vocabulary lock reserves for *consolidation*.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-08-11-framing-application.md
git commit -m "plans: close the FRAMING application record

All 69 steps shipped in 210aaa7..771c8cf. The one open item -- FRAMING.md's
'concentration' wording in D4/D5 -- moves to the reorganization spec's flagged
list so it is tracked in exactly one place."
```

---

### Task 3: Create `exploration/` and move the four scripts

**Files:**
- Create: `exploration/README.md`
- Move: `code/03_estimation/03_family_iv.R` → `exploration/03_estimation/03_family_iv.R`
- Move: `code/03_estimation/08_mean_reversion.R` → `exploration/03_estimation/08_mean_reversion.R`
- Move: `code/04_analysis/05_validation.R` → `exploration/04_analysis/05_validation.R`
- Move: `code/04_analysis/11_lawsuit_topic_selection.py` → `exploration/04_analysis/11_lawsuit_topic_selection.py`
- Move: `SPECIFICATION.md` → `exploration/SPECIFICATION_tse_shift_share.md`
- Modify: `code/run_all.py` (drop lines 62, 67, 79, 84)
- Modify: each moved script's output directory constant

**Interfaces:**
- Consumes: a clean working tree from Task 1
- Produces: `exploration/` tree; `code/run_all.py` with no reference to a moved script. Task 5's auditor asserts `exploration/` scripts are excluded from its scan.

- [ ] **Step 1: Create the directory structure and move the files**

```bash
mkdir -p exploration/03_estimation exploration/04_analysis exploration/output
git mv code/03_estimation/03_family_iv.R      exploration/03_estimation/03_family_iv.R
git mv code/03_estimation/08_mean_reversion.R exploration/03_estimation/08_mean_reversion.R
git mv code/04_analysis/05_validation.R       exploration/04_analysis/05_validation.R
mv code/04_analysis/11_lawsuit_topic_selection.py exploration/04_analysis/11_lawsuit_topic_selection.py
mv SPECIFICATION.md exploration/SPECIFICATION_tse_shift_share.md
```

The last two use plain `mv`: both files are untracked, so `git mv` would fail with "not under version control".

- [ ] **Step 2: Verify depth-2 root resolution still holds**

```bash
grep -n "parents\[2\]\|SCRIPT_DIR" exploration/03_estimation/*.R exploration/04_analysis/*
```

Expected: each file still resolves the root two levels up. `exploration/03_estimation/x.R` is the same depth as `code/03_estimation/x.R`, so **no edit is required**. If any file resolves a different number of levels, STOP and report — the archive layout assumption is wrong.

- [ ] **Step 3: Repoint each moved script's output directory to `exploration/output/`**

Four exact edits, one per script.

`exploration/03_estimation/03_family_iv.R` line 34:

```r
# before
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
# after
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "exploration", "output", "tables", "regressions")
```

`exploration/03_estimation/08_mean_reversion.R` lines 43–45. Note this script hard-codes an absolute `ROOT` at line 40 (`"c:/Users/naral/Desktop/..."`), so the move does not affect its root resolution or its `source(file.path(ROOT, "code/utils/figure_style.R"))` at line 47 — leave both alone:

```r
# before
OUT_CSV <- file.path(ROOT, "output/tables/regressions/mean_reversion_splitsample.csv")
OUT_SUM <- file.path(ROOT, "output/tables/regressions/mean_reversion_splitsample_summary.csv")
OUT_FIG <- file.path(ROOT, "output/figures/firststage_splitsample.pdf")
# after
OUT_CSV <- file.path(ROOT, "exploration/output/tables/regressions/mean_reversion_splitsample.csv")
OUT_SUM <- file.path(ROOT, "exploration/output/tables/regressions/mean_reversion_splitsample_summary.csv")
OUT_FIG <- file.path(ROOT, "exploration/output/figures/firststage_splitsample.pdf")
```

`exploration/04_analysis/05_validation.R` line 35:

```r
# before
OUT_DIR     <- file.path(ROOT, "output", "tables", "regressions")
# after
OUT_DIR     <- file.path(ROOT, "exploration", "output", "tables", "regressions")
```

`exploration/04_analysis/11_lawsuit_topic_selection.py` line 33:

```python
# before
OUT_DIR = PROJECT_ROOT / "output" / "tables" / "descriptives"
# after
OUT_DIR = PROJECT_ROOT / "exploration" / "output" / "tables" / "descriptives"
```

Then create the target directories, since none of these scripts makes its own:

```bash
mkdir -p exploration/output/tables/regressions exploration/output/tables/descriptives exploration/output/figures
```

Finally, move the six CSVs these scripts already produced (spec category A) out of `output/`:

```bash
mv output/tables/regressions/ancova_validation.csv \
   output/tables/regressions/fd_vs_ancova_comparison.csv \
   output/tables/regressions/family_iv_results.csv \
   output/tables/regressions/mean_reversion_splitsample.csv \
   output/tables/regressions/mean_reversion_splitsample_summary.csv \
   exploration/output/tables/regressions/
mv output/tables/descriptives/lawsuit_topic_selection_worksheet.csv \
   exploration/output/tables/descriptives/
```

Plain `mv`, not `git mv`: `*.csv` is gitignored repo-wide, so none of these is tracked.

Verify the edits took:

```bash
grep -n "\"output\"\|output/tables\|output/figures" exploration/03_estimation/*.R exploration/04_analysis/*
```

Expected: every path now contains `exploration`. A bare `output/` in any of these four files is a miss.

- [ ] **Step 4: Drop the four calls from `code/run_all.py`**

Delete these four lines (line numbers as of Task 1's commit; match on text, not number):

```python
    run_r("code/03_estimation/03_family_iv.R")
    run_r("code/03_estimation/08_mean_reversion.R")              # split-sample first-stage falsification (audit #10)
    run_r("code/04_analysis/05_validation.R")               # FD-vs-ANCOVA + ANCOVA validation
    run_py("code/04_analysis/11_lawsuit_topic_selection.py")  # which adversarial topics the instrument selects on
```

Then add this comment immediately after the `print("\n=== 04 Analysis ===")` line:

```python
    # Exploration scripts (family IV, mean reversion, FD-vs-ANCOVA validation,
    # topic selection) live in exploration/ and are run by hand, not here.
    # See exploration/README.md.
```

- [ ] **Step 5: Verify no reference to a moved script survives in `code/`**

```bash
grep -rn "03_family_iv\|08_mean_reversion\|05_validation\|11_lawsuit_topic_selection" code/
```

Expected: no output. Any hit is a broken reference that must be fixed before committing.

- [ ] **Step 6: Write `exploration/README.md`**

```markdown
# exploration/

Analysis that was run, is worth keeping, and did **not** reach the paper or the
report deck.

The rule for `code/`: a script there must generate an input or a result for the
paper. A script that fails that test but is important enough to survive an easy
drop lives here instead. Nothing in this folder is deleted, and nothing here is
called by `code/run_all.py` — run these by hand.

Layout mirrors the pipeline stages so the depth-2 project-root resolution every
script uses (`parents[2]` in Python, `file.path(SCRIPT_DIR, "..", "..")` in R)
keeps working unchanged. Outputs land in `exploration/output/`, never in
`output/`, so `output/` means "paper assets only".

## What is here and why it stopped short

| Script | What it did | Why it is not in `code/` |
|---|---|---|
| `03_estimation/03_family_iv.R` | IV split by lawsuit family (4 families x outcomes) | `family_iv_results.csv` is cited by no document and read by no script. Superseded by `13_reclassification_robustness.R` (family-level Z) and `11_summary_indices.R` |
| `03_estimation/08_mean_reversion.R` | Split-sample first-stage falsification | Its only asset, `firststage_splitsample.pdf`, was shown on nothing |
| `04_analysis/05_validation.R` | FD-vs-ANCOVA comparison and the ANCOVA falsification gate | **Answers a referee asking "why ANCOVA, not first differences?"** The deck makes that argument (`src:fd`), but from `appendix_first_difference.tex`, which `02_iv_main.R` writes. Section [B] duplicates falsifications that `05_pretrend_balance.R` and `04_placebo_nonadversarial.R` already produce. Decision-evidence for a locked estimator choice, not a paper asset |
| `04_analysis/11_lawsuit_topic_selection.py` | Which adversarial topics the instrument selects on | Decision ledger for the `tse-shift-share` redesign, not a pipeline step |
| `SPECIFICATION_tse_shift_share.md` | Spec for the TSE shift-share redesign | Specifies the *redesign*, not the paper's design. Its own header names the committed propaganda-Bartik/ANCOVA design on `main` as the preserved fallback. At repo root it would advertise itself as the paper's spec |

The last two are one artifact pair from the `tse-shift-share` redesign lane and
travel together.

## Removed diagnostics

The LIML-vs-2SLS comparison was removed from `code/03_estimation/02_iv_main.R`
rather than archived: with `K=1` the estimator is 2SLS ≡ LIML by construction, so
the check confirmed a mechanical identity, and no document ever cited it. If a
referee asks, recover it from git history — it was removed in the commit that
follows `<PRE_STRIP_SHA>`.
```

Replace `<PRE_STRIP_SHA>` in Task 4, Step 8, once the pre-strip SHA is known.

- [ ] **Step 7: Commit**

```bash
git add exploration/ code/run_all.py
git add -u code/
git commit -m "reorg: move exploration scripts out of the paper pipeline

code/ now holds only scripts that generate an input or a result for the paper
or the report deck. Four scripts that fail that test move to exploration/,
which mirrors the stage layout so depth-2 project-root resolution keeps working
with no path edits. Their outputs are repointed to exploration/output/ so
output/ means paper assets only.

SPECIFICATION.md moves with the topic-selection script: both belong to the
tse-shift-share redesign lane, not to the committed design."
```

---

### Task 4: Delete the orphan assets and strip the blocks that regenerate them

Nine committed assets plus `liml_comparison.csv` are consumed by nothing. Deleting files alone is futile — the next `run_all.py` recreates them — so each emitting block goes too.

**Files:**
- Modify: `code/03_estimation/02_iv_main.R` (two strips: LIML machinery, section 9f)
- Modify: `code/03_estimation/04_placebo_nonadversarial.R`
- Modify: `code/03_estimation/05_pretrend_balance.R`
- Modify: `code/04_analysis/02_descriptive_figures.R`
- Modify: `code/04_analysis/03_result_figures.R`
- Delete: 9 assets under `output/` plus `output/tables/regressions/liml_comparison.csv`

**Interfaces:**
- Consumes: `exploration/README.md` from Task 3 (Step 8 fills in its `<PRE_STRIP_SHA>` placeholder)
- Produces: scripts whose surviving outputs are unchanged. Task 7 verifies via deck compilation.

- [ ] **Step 1: Record the pre-strip SHA and snapshot the fragments**

```bash
git rev-parse --short HEAD > .superpowers/sdd/2026-08-12-repo-reorganization/pre_strip_sha.txt
cat .superpowers/sdd/2026-08-12-repo-reorganization/pre_strip_sha.txt
mkdir -p .superpowers/sdd/2026-08-12-repo-reorganization/frag_before
cp output/tables/tex/*.tex .superpowers/sdd/2026-08-12-repo-reorganization/frag_before/
ls .superpowers/sdd/2026-08-12-repo-reorganization/frag_before | wc -l
```

`.tex` fragments are deterministic text, so a byte-diff is a valid regression test for them. PDFs are **not** — `ggsave` embeds a creation timestamp, so PDF checksums differ on every run. Figures are verified by page count and deck compilation instead.

- [ ] **Step 2: Strip the binscatter from `code/04_analysis/03_result_figures.R`**

Remove lines 90–108 — `set.seed(42)` through the `cat` — but **keep line 88**. `bs_df` is reused by the linear first stage at lines 127–133; deleting it breaks section [B].

Delete exactly this, leaving `bs_df <- data.frame(x = resid_instr, y = resid_endog)` in place:

```r
set.seed(42)
bs <- binsreg(y = bs_df$y, x = bs_df$x, nbins = 30,
              line = c(3, 3), ci = c(3, 3), cb = NULL,
              plotxrange = quantile(bs_df$x, c(0.01, 0.99)))
bin_df  <- bs$data.plot$`Group Full Sample`$data.dots
line_df <- bs$data.plot$`Group Full Sample`$data.line

p_bin <- ggplot() +
  geom_ribbon(data = bs$data.plot$`Group Full Sample`$data.ci,
              aes(x = x, ymin = ci.l, ymax = ci.r), fill = COL_BLUE, alpha = 0.15) +
  geom_line(data = line_df, aes(x = x, y = fit), color = COL_BLUE, linewidth = 0.9) +
  geom_point(data = bin_df, aes(x = x, y = fit), color = COL_BLUE, size = 2.2) +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  labs(x = "Bartik IV (residualised on 7 controls + state FE)",
       y = expression(Delta*log(1 + lawsuits) ~ " (residualised)")) +
  theme_report()
ggsave(file.path(FIG_DIR, "firststage_binscatter.pdf"), p_bin, width = 7, height = 4.5)
cat("  Saved firststage_binscatter.pdf\n")
```

`binsreg` is now unused. Remove `library(binsreg)` at line 28 and drop `binsreg` from the `# Requires:` comment at line 22. Update the header comment at line 6 that lists `firststage_binscatter.pdf` as an output.

- [ ] **Step 3: Verify the binscatter strip left no dangling reference**

```bash
grep -n "binsreg\|bin_df\|line_df\|p_bin\|firststage_binscatter" code/04_analysis/03_result_figures.R
grep -n "bs_df" code/04_analysis/03_result_figures.R
```

Expected: the first command prints nothing. The second still shows `bs_df` at its definition and at the lines that build the linear first stage.

- [ ] **Step 4: Strip the three timing figures from `code/04_analysis/02_descriptive_figures.R`**

Remove the `p_count`, `p_rate` and `p_share` blocks (lines 123–151), each running from its `# (n) ...` comment through its `cat("  Saved ...")`. **Keep** `timing_base`, `agg`, and the `p_shape` block that follows at line 153 — `litigation_timing_shape.pdf` is the figure the deck shows.

Then update the header comment at lines 6–8, which lists all three as outputs:

```r
# before
#   [A] Litigation timing        -> litigation_timing_count.pdf
#                                   litigation_timing_rate.pdf
#                                   litigation_timing_share.pdf
# after
#   [A] Litigation timing        -> litigation_timing_shape.pdf
```

- [ ] **Step 5: Strip the two pre-trend fragments from `code/03_estimation/05_pretrend_balance.R`**

Remove the two calls at lines 300–305:

```r
write_pretrend_tex(names(CONSOL), file.path(TEX_DIR, "pretrend_balance_consolidation.tex"),
                   "consolidation ladder")
write_pretrend_tex(c(names(VOTERB), names(TURN)),
                   file.path(TEX_DIR, "pretrend_balance_voterbehavior.tex"),
                   "voter-disengagement outcomes + turnout")
```

Those were its only two call sites, so remove the `write_pretrend_tex` function definition too (starts line 264, ends at the closing brace before line 300). Remove the two output lines from the header comment at lines 63–64. **Keep** everything from section 5 onward — `pretrend_coefplot.pdf` is used by the deck, and `pretrend_balance.csv` is its source-of-truth record.

- [ ] **Step 6: Strip the placebo fragment from `code/03_estimation/04_placebo_nonadversarial.R`**

Remove the block at lines 271–278, comment through closing brace:

```r
{
  mods <- label_mods(plac_rf_fits, FOCUS_OUTCOMES, OUTCOME_LABELS)
  out <- do.call(etable, c(list(
    mods, keep = "Placebo Bartik", fitstat = ~ n + r2
  ), etab_base))
  write_frag(out, file.path(TEX_DIR, "nonadversarial_placebo_rf.tex"),
             "code/03_estimation/04_placebo_nonadversarial.R")
}
```

Keep the `# ---- 5a.` explanatory comment above it only if section 5b's comment does not already carry the context; otherwise remove it with the block. Remove the output line from the header comment at line 27. **Keep** section 5b — `nonadversarial_robustness.tex` is used.

- [ ] **Step 7: Strip section 9f and the LIML machinery from `code/03_estimation/02_iv_main.R`**

Two independent removals.

(a) Section 9f at lines 1400–1408, comment through closing brace:

```r
# ---- 9f. Blank Rate — open-seat heterogeneity (cols = subgroup specs) ----
{
  sub_labels <- c(
    baseline      = "All municipalities",
    open_seat     = "Open seat",
    contested_seat = "Contested seat"
  )
  mods <- label_mods(tex_blank_sub_fits, BLANK_SUBGROUP_SPECS, sub_labels)
  iv_etable(mods, file.path(TEX_DIR, "open_seat_blank_rate.tex"))
}
```

(b) The LIML machinery, which is self-contained across three sites — `liml_rows` appears only at lines 497, 639, 718 and 719:

1. Line 497: delete `liml_rows <- list()`
2. Lines 615–646: delete this entire `if (spec_name == "baseline")` block. It sits inside the per-spec loop, immediately after the 2SLS `tryCatch` closes. Delete from the comment through the block's closing brace — leave the two `}` that close the enclosing loops:

```r
    # LIML for baseline spec (K=1 instrument — no eigenvalue issue)
    if (spec_name == "baseline") {
      for (y in ALL_OUTCOMES) {
        if (!(y %in% names(samp))) next
        if (sum(!is.na(samp[[y]])) < 20L) next
        family <- if (y %in% PRIMARY_OUTCOMES)          "primary"
                  else if (y %in% SECONDARY_OUTCOMES)  "secondary"
                  else if (y %in% COMPOSITION_OUTCOMES) "composition"
                  else if (y %in% CANDIDATE_SUPPLY_OUTCOMES) "candidate_supply"
                  else if (y %in% ENTRY_OUTCOMES)       "entry"
                  else if (y %in% CONCENTRATION_OUTCOMES) "concentration"
                  else if (y %in% PRETREND_OUTCOMES)    "pretrend"
                  else                                  "voter_behavior"
        tryCatch({
          controls_y <- if (y %in% PRETREND_OUTCOMES)
                          intersect(controls, PREDET_CONTROLS) else controls
          r_l        <- resolve_lhs(y, form, samp)
          ctrls_l    <- avail(c(controls_y, r_l$lag), samp)
          ctrl_rhs_l <- if (length(ctrls_l) > 0) paste(ctrls_l, collapse = " + ") else "1"
          fml_l      <- as.formula(sprintf(
            "%s ~ %s | %s | %s ~ %s", r_l$lhs, ctrl_rhs_l, fe_col, endogenous, instrument
          ))
          liml_fit <- feols(fml_l, data = samp, cluster = ~cluster_id,
                            estimator = "liml", warn = FALSE, notes = FALSE)
          liml_rows[[length(liml_rows) + 1]] <- extract_iv_row(
            liml_fit, var_name, spec_name, family, y, n_obs, n_cl, endogenous,
            estimator = "liml"
          )
        }, error = function(e)
          message("  LIML error [", y, "]: ", conditionMessage(e)))
      }
    }
```

3. Lines 713–751: delete section 8 in full, from the `# 8. LIML vs 2SLS COMPARISON` banner through the closing `}` of the `else` branch that prints "No LIML results collected."

Removing this also drops one `feols` fit per outcome from the baseline loop, so the script gets faster. It must not change any coefficient — Step 10's fragment diff is what proves that.

- [ ] **Step 8: Verify the LIML strip is complete and fill in the archive note**

```bash
grep -n "liml\|LIML" code/03_estimation/02_iv_main.R
grep -n "BLANK_SUBGROUP_SPECS\|tex_blank_sub_fits\|open_seat_blank_rate" code/03_estimation/02_iv_main.R
```

Expected: the first prints nothing. For the second, `BLANK_SUBGROUP_SPECS` and `tex_blank_sub_fits` may legitimately survive if another section uses them — check each hit; if they are now unused, remove their definitions too.

Then replace `<PRE_STRIP_SHA>` in `exploration/README.md` with the SHA recorded in Step 1:

```bash
sed -i "s/<PRE_STRIP_SHA>/$(cat .superpowers/sdd/2026-08-12-repo-reorganization/pre_strip_sha.txt)/" exploration/README.md
grep -n "PRE_STRIP_SHA\|recover it from git history" exploration/README.md
```

Expected: the placeholder is gone and a real short SHA is in its place.

- [ ] **Step 9: Delete the ten orphan files**

```bash
git rm output/figures/firststage_splitsample.pdf \
       output/figures/litigation_timing_count.pdf \
       output/figures/litigation_timing_rate.pdf \
       output/figures/litigation_timing_share.pdf \
       output/figures/firststage_binscatter.pdf \
       output/tables/tex/nonadversarial_placebo_rf.tex \
       output/tables/tex/open_seat_blank_rate.tex \
       output/tables/tex/pretrend_balance_consolidation.tex \
       output/tables/tex/pretrend_balance_voterbehavior.tex
rm -f output/tables/regressions/liml_comparison.csv
```

`liml_comparison.csv` uses plain `rm`: it is gitignored, so `git rm` fails with "did not match any files".

- [ ] **Step 10: Re-run the two affected stages and diff every surviving fragment**

```bash
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/02_iv_main.R
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/04_placebo_nonadversarial.R
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/05_pretrend_balance.R
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/04_analysis/02_descriptive_figures.R
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/04_analysis/03_result_figures.R
diff -rq .superpowers/sdd/2026-08-12-repo-reorganization/frag_before output/tables/tex/
```

Expected `diff` output: exactly four "Only in .superpowers/sdd/2026-08-12-repo-reorganization/frag_before" lines, for `nonadversarial_placebo_rf.tex`, `open_seat_blank_rate.tex`, `pretrend_balance_consolidation.tex`, `pretrend_balance_voterbehavior.tex`. **Any "differ" line is a regression** — a strip changed a surviving output. Investigate before continuing; do not commit.

- [ ] **Step 11: Confirm the deleted assets were not recreated**

```bash
ls output/figures/firststage_binscatter.pdf output/figures/litigation_timing_count.pdf 2>&1
ls output/tables/regressions/liml_comparison.csv 2>&1
```

Expected: "No such file or directory" for each. If any reappeared, its emit block was not fully stripped.

- [ ] **Step 12: Commit**

```bash
git add -u
git add exploration/README.md
git commit -m "reorg: delete orphan outputs and the blocks that regenerate them

Nine committed assets were consumed by no document, and eight came from scripts
that stay -- so deleting the files alone would have been undone by the next
run_all.py. Each emitting block goes with its asset.

liml_comparison.csv goes too: with K=1 the estimator is 2SLS = LIML by
construction, so the check confirmed a mechanical identity and no document ever
cited it. The removal point is recorded in exploration/README.md so a referee
question can be answered from history.

Every surviving fragment is byte-identical after re-running the five affected
scripts."
```

---

### Task 5: Build `code/utils/audit_pipeline.py`

The classification will drift as scripts are added. Without this, the analysis has to be redone by hand.

**Files:**
- Create: `code/utils/audit_pipeline.py`

**Interfaces:**
- Consumes: the repo state after Tasks 3 and 4
- Produces: a CLI reporting archive candidates, orphan outputs, build breakers, and unreferenced CSVs. Exits 0 always.

- [ ] **Step 1: Write the auditor**

```python
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

WRITE = r"(to_csv|write_csv|fwrite|write\.csv|savefig|ggsave|write_parquet|writeLines)"
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
```

- [ ] **Step 2: Run it**

```bash
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/utils/audit_pipeline.py
```

Expected after Tasks 3 and 4:
- ARCHIVE CANDIDATES: **0** — the three `utils/` helpers must be absorbed by the "sourced by" branch, not listed here. If they appear, that branch is broken.
- ORPHAN OUTPUTS: **0**
- BUILD BREAKERS: **1** — `extended_abstract.tex -> ../figures/forest_voter_behavior.pdf` (a known, flagged issue; not fixed here)
- UNREFERENCED CSVs: **10** — the nine record CSVs from the spec's category B plus `gps_balance_tests.csv`. The six category-A CSVs are gone from `output/` (they moved to `exploration/output/`) and `liml_comparison.csv` is deleted.
- INFRASTRUCTURE: 4

If ARCHIVE CANDIDATES is non-zero, read each one before moving it — the auditor is a report, not an oracle, and a false positive means the detection heuristic needs widening, not that a script should be archived.

If UNREFERENCED CSVs is **larger** than 10, do not delete the extras. Check first whether the producing script emits something the deck shows; if it does, the CSV is a record and the count in the spec was low. That is exactly how the count went 13 → 17 during design.

- [ ] **Step 3: Commit**

```bash
git add code/utils/audit_pipeline.py
git commit -m "utils: add a re-runnable pipeline auditor

Implements the three tests from the reorganization spec so the classification
can be re-checked instead of re-derived by hand. Reports archive candidates,
orphan outputs, build breakers, and unreferenced CSVs; always exits 0.

Unreferenced CSVs are listed separately and never as deletion candidates: under
csv = source of truth, an unreferenced CSV is a question ('is this result shown
anywhere?'), not a defect. Detection uses a context window around each filename
because R splits the path constant from the write call across lines."
```

---

### Task 6: Update `README.md` and `CLAUDE.md`

**Files:**
- Modify: `README.md` (stage tables for 03/04, orphan-tracking tables at ~322–329, known wrinkles at ~398)
- Modify: `CLAUDE.md` (naming rules, "Output tables" quick reference)

**Interfaces:**
- Consumes: the final file layout from Tasks 3–5
- Produces: documentation matching the repo

- [ ] **Step 1: Update `README.md`**

Four edits:

1. **Stage tables for 03 and 04** — remove the rows for `03_family_iv.R`, `08_mean_reversion.R`, `05_validation.R`, `11_lawsuit_topic_selection.py`. Add a line under each stage table: `Exploration scripts for this stage live in `exploration/<stage>/` — see `exploration/README.md`.`
2. **Figure table at ~line 322** — delete the `firststage_binscatter.pdf` and `firststage_splitsample.pdf` rows, and the three `litigation_timing_{count,rate,share}.pdf` rows.
3. **Fragment note at ~lines 328–329** — the sentence naming `pretrend_balance_consolidation.tex`, `pretrend_balance_voterbehavior.tex`, `nonadversarial_placebo_rf.tex`, `open_seat_blank_rate.tex` as "produced but unreferenced" is now false. Delete it.
4. **Known wrinkles** — resolve items 6 and 8; restate item 3. Replace item 8 with:

```markdown
8. **Orphan outputs.** Resolved 2026-08-12. `code/utils/audit_pipeline.py` reports
   orphan outputs on demand; the reorganization deleted the nine that existed and
   stripped the blocks that regenerated them.
```

Replace item 3 with:

```markdown
3. **The share-balance defense shows no numbers.** `gps_balance_tests.csv` holds the
   share-covariate balance test, but the deck asserts that defense in prose
   (`slides_report.tex:989`) without citing a figure from it — and the test is
   computed in Python, which the R-only rule bars for anything reaching a slide.
   Port to R and cite, or drop the claim.
```

Add a new wrinkle:

```markdown
9. **`output/tables/` is the declared source of truth but is entirely untracked.**
   `*.csv` is gitignored repo-wide, so a clean checkout has no saved regression
   records — they exist only on the machine that ran the pipeline. Consistent with
   "data never leaves this repo", but currently a side effect rather than a decision.
```

- [ ] **Step 2: Update `CLAUDE.md`**

Two edits:

1. Under the file-and-output naming rules, after the "Drop dead scripts on sight" sentence, add:

```markdown
- **A script stays in `code/` only if it produces a paper input or result.** Three
  tests, any one sufficient: a document `\input`s/`\includegraphics`es one of its
  outputs; `04_analysis/06_abstract_macros.py` reads one of its CSVs; or it writes a
  `data/` artifact that a passing script reads. Scripts that fail all three but are
  worth keeping go to `exploration/<stage>/` — same depth, so root resolution is
  unchanged — never deleted. Verification gates (`00_verify_*`) are exempt as
  pipeline infrastructure. Run `python code/utils/audit_pipeline.py` to re-check.
```

2. In the "Output tables" quick-reference table, delete the `regressions/liml_comparison.csv` row.

- [ ] **Step 3: Verify no doc still names a moved or deleted file**

```bash
grep -rn "liml_comparison\|firststage_binscatter\|firststage_splitsample\|litigation_timing_count\|litigation_timing_rate\|litigation_timing_share\|open_seat_blank_rate\|nonadversarial_placebo_rf\|pretrend_balance_consolidation\|pretrend_balance_voterbehavior" README.md CLAUDE.md
```

Expected: no output.

```bash
grep -rn "03_family_iv\|08_mean_reversion\|04_analysis/05_validation\|11_lawsuit_topic_selection" README.md CLAUDE.md
```

Expected: hits only in text that points at `exploration/`.

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: record the exploration lane and drop the resolved orphan rows

README's orphan-tracking tables described a state the reorganization removed.
Wrinkles 6 and 8 are resolved; 3 is restated as the real open question (the
share-balance defense cites no numbers and is computed in Python); a new
wrinkle records that output/tables/ is the declared source of truth yet is
entirely untracked.

CLAUDE.md gains the three-test rule so the classification survives as a
convention rather than a one-off cleanup."
```

---

### Task 7: Verify end to end, then merge to `main` and push

**Files:**
- No content edits; this task runs the pipeline, compiles both decks, and merges

**Interfaces:**
- Consumes: everything from Tasks 1–6
- Produces: `main` containing the reorganization, pushed

- [ ] **Step 1: Run the full pipeline**

```bash
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/run_all.py
```

Expected: completes with `Pipeline complete.` and no "file not found" for a moved script. This is long-running — if it fails, the failure point identifies which task's edit broke it.

- [ ] **Step 2: Confirm the pipeline did not resurrect a deleted asset**

```bash
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/utils/audit_pipeline.py
git status --porcelain
```

Expected: ORPHAN OUTPUTS 0, ARCHIVE CANDIDATES 0. `git status` may show modified PDFs (timestamps) but **no new untracked file** under `output/`.

- [ ] **Step 3: Compile both decks twice each**

```bash
cd output/presentation
pdflatex -interaction=nonstopmode slides_report.tex > /dev/null
pdflatex -interaction=nonstopmode slides_report.tex > /dev/null
pdflatex -interaction=nonstopmode slides_advisor.tex > /dev/null
pdflatex -interaction=nonstopmode slides_advisor.tex > /dev/null
cd ../..
```

Twice for references and navigation.

- [ ] **Step 4: Verify the page counts**

```bash
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import re, pathlib
for f in ['slides_report', 'slides_advisor']:
    log = pathlib.Path('output/presentation') / f'{f}.log'
    m = re.findall(r'\((\d+) pages', log.read_text(encoding='utf-8', errors='replace'))
    print(f, m[-1] if m else 'NO PAGE COUNT FOUND')
"
```

Expected: `slides_report 67` and `slides_advisor 11`. **A different count means a fragment went missing** — check the `.log` for "File ... not found" before proceeding. Do not merge on a page-count change.

- [ ] **Step 5: Merge to `main`**

```bash
git checkout main
git merge --no-ff framing-application -m "merge: FRAMING application and repo reorganization

Brings in the framing work closed on 2026-08-11 plus the reorganization: code/
now holds only scripts producing paper inputs or results, exploration/ holds the
four that did not reach the paper, and the orphan outputs are gone along with
the blocks that regenerated them."
```

If the merge reports conflicts, STOP and report them — `main` has 5 unpushed commits and a conflict means they touched the same files.

- [ ] **Step 6: Push**

```bash
git push origin main
git status
```

Expected: `Your branch is up to date with 'origin/main'` and a clean working tree.

- [ ] **Step 7: Report what was left open**

Confirm these remain deliberately unresolved — all six are in the spec's "Flagged for Nara" section — and state them in the final summary:

1. `extended_abstract.tex` references `../figures/forest_voter_behavior.pdf`, which is not on disk — that document cannot compile. Fixing it means restoring a figure or editing a paper file, which is Nara's call.
2. `gps_balance_tests.csv` backs a deck claim (`slides_report.tex:989`) that cites no numbers, and is computed in Python against the R-only rule.
3. `output/tables/` is the declared source of truth but is entirely untracked — `*.csv` is gitignored repo-wide, so a clean checkout has no saved regression records.
4. `FRAMING.md` uses "concentration" for the top-two margin in its D4 header and D5 table column, which the vocabulary lock reserves for *consolidation*.
5. Three R scripts hard-code an absolute `ROOT` (`"c:/Users/naral/..."`) instead of deriving it from `SCRIPT_DIR` — one of them, `08_mean_reversion.R`, is now in `exploration/`. Pre-existing portability defect, untouched.
6. `data/clean/zona_eleitoral_lookup.csv` is written by no script and read by no script, so deleting it is not undoable by re-running the pipeline. Left alone.

---

## Notes for the implementer

- **The strips are the risky part.** Tasks 3, 5, 6 and 7 are mechanical; Task 4 edits the headline estimation script. The `diff -rq` in Task 4 Step 10 is the real gate — if a surviving fragment differs by a single byte, a strip removed something it should not have.
- **PDF checksums are not a regression test.** `ggsave` embeds a creation timestamp, so every run produces different bytes. Figures are verified by deck page count, not by hash.
- **`git mv` fails on untracked files.** `SPECIFICATION.md` and `11_lawsuit_topic_selection.py` are untracked; use plain `mv`.
- **Nothing in `exploration/` is deleted, ever.** If a moved script turns out to back a deck claim, move it back — it is runnable where it sits.
