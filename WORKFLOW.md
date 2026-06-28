# WORKFLOW.md — Section-completion protocol

This is the **repeatable checklist run every time an outcome group (or section) is
finished**. The project is rebuilt one decided outcome group at a time (voters →
candidates → electorate / who-wins); each group goes through the same closing steps so
the repo, the report, the README, and memory never drift out of sync.

Invoke it as the `/finish-section` slash command (`.claude/commands/finish-section.md`)
or just follow the steps below. `.claude/` is gitignored, so **this file is the
authoritative copy** — the slash command only points back here.

## The steps

Run in order. Don't skip; if a step genuinely doesn't apply, say so explicitly.

1. **Script is current-language.** The results come from a script that reads
   `code/spec_config.json` (via `code/utils/spec_config.{R,py}`) — never hardcoded
   control lists or the old 7-spec grid. No inline one-off computations feed the
   report (reproducibility rule).

2. **Run & verify.** Execute the script end-to-end. Confirm the headline numbers by
   eye: first-stage F is cluster-robust (`fitstat(m, "ivwald1")`, ≈16, *not* the
   non-robust `ivf` ≈95), tF correction applied, N matches the expected sample, signs
   and significance are sane. Note anything surprising.

3. **Report frames.** Update `output/presentation/slides_report.tex`: insert/replace
   the frames for this group, drop any stale frames from the old design, wire in the
   freshly generated `output/tables/tex/*.tex` fragments. Numbers in prose must be
   literal and match the tables.

4. **Compile & eyeball.** `pdflatex` twice from `output/presentation/`, open the PDF,
   visually confirm the new frames render (no broken siunitx — hand-built tabulars
   only) and stale frames are gone.

5. **Archive superseded code.** Any script that no longer speaks the current spec
   language moves to `code/_archive/` via `git mv`, with a one-line reason added to
   `code/_archive/README.md`. (Per the cleanup rule, archiving is only for the
   superseded-design engines we're keeping "for now"; truly orphan one-offs get
   deleted.)

6. **README.** Update `README.md`: script tables, spec/instrument tables, and the
   **Results status (by outcome group)** block (flip this group to ✅, set the next to
   ⏳). README is updated after *every* section.

7. **SPECIFICATION.md.** Record any decision made this round and update the
   per-group status / open-items there. `SPECIFICATION.md` + `code/spec_config.json`
   remain the single source of truth for the design.

8. **Memory handout.** Update the project-state memory file so the next session
   resumes cleanly (current group done, next group, any new open items).

9. **Open items.** List what's still outstanding for this group (e.g. the GPS
   pre-trend placebo) so nothing is silently dropped.

10. **Commit.** Stage and commit with a clear message. **Never** add a
    `Co-Authored-By: Claude` trailer.

## Current status

See the **Results status (by outcome group)** table in `README.md`.
As of 2026-06-22: voter behaviour ✅ done; candidate composition ⏳ next.
