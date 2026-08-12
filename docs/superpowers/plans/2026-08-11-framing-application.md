# Framing Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the locked framing in `FRAMING.md` to both Beamer decks, retire the formulation "the consolidation is the barrier signature", and mark `WRITING_GUIDE.md` §3 resolved.

**Architecture:** Fifteen targeted prose edits across two `.tex` decks, plus an American-spelling sweep and one guide update. There is no code and no test suite — the verification cycle for each task is **compile → rasterize the affected page → look at it → assert page count unchanged → commit**. Deck overflow in Beamer is *silent* (content runs off the frame without a LaTeX error), so visual inspection is mandatory, not optional.

**Tech Stack:** LaTeX/Beamer (TinyTeX pdflatex), PyMuPDF for rasterization, git.

## Global Constraints

- **Never edit `output/paper/paper.tex` or `output/paper/extended_abstract.tex`.** Nara writes all paper prose. This plan touches decks and internal documents only.
- **Source of truth for every decision is `FRAMING.md`** (repo root, commit `a6b42a1`). Decisions are referenced as D1–D5 below.
- **Numbers are never hardcoded.** Every estimate in the decks comes from a `\Macro` defined in `output/tables/tex/abstract_macros.tex`. If new prose needs a number, use the existing macro. The one exception authorized by this plan is the literal `$p=.059$` in Task 5, which has no macro.
- **New text must be pure ASCII.** Write `---` for em-dashes and LaTeX escapes for accents (`\c{c}`, `\~a`). Never paste a literal `—` or `ç`.
- **Encoding baselines (measured 2026-08-11):** `slides_report.tex` = 79 non-ASCII bytes + a UTF-8 BOM; `slides_advisor.tex` = 79 non-ASCII bytes. Both counts must be **unchanged** at the end of every task that edits a deck. Both files mix genuine UTF-8 (accents, em-dashes) with true mojibake (`â€”` at advisor L22), so a decode/re-encode round trip must be lossless.
- **Never put a non-ASCII byte inside an Edit `old_string`.** Of the 15 prose anchors, exactly one line carries a non-ASCII character (advisor L17); that edit matches on a pure-ASCII substring of the line. All 14 others were verified pure ASCII.
- **Never match on a line containing mojibake.** Choose `old_string` anchors from pure-ASCII substrings only. Task 7 Step 9 depends on this.
- **Spelling is American** (FRAMING.md vocabulary lock): Leveling, favors, behavior, demobilization, characterize.
- **Do not run `convert`.** On this machine `/c/Windows/system32/convert` is the Windows FAT→NTFS filesystem utility, not ImageMagick. Rasterize with PyMuPDF only.
- **Build command** (must run *from* `output/presentation/`, twice, for navigation):
  ```bash
  cd output/presentation && pdflatex -interaction=nonstopmode slides_report.tex && pdflatex -interaction=nonstopmode slides_report.tex
  ```
- **Baseline page counts:** `slides_report.pdf` = **67**, `slides_advisor.pdf` = **11**. A changed count after a prose-only edit means a frame overflowed into a new page — investigate, do not accept.
- **Binaries:**
  - pdflatex: `/c/Users/naral/AppData/Roaming/TinyTeX/bin/windows/pdflatex` (on PATH)
  - python: `/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe`
- **Commits:** no `Co-Authored-By: Claude` line, ever.
- **When mandated prose overflows a frame — the layout ladder.** Discovered in execution: this plan's replacement prose is systematically *longer* than the text it replaces, and several frames were already at capacity. Never reword mandated text to fit. Instead climb this ladder and **stop at the first rung that clears the overflow**, so fixes stay consistent across frames:
  1. Delete a redundant manual `\vspace`/`\smallskip` and let the natural spacing apply
  2. `\itemsep` down to `1pt` (the deck's established floor)
  3. `\\[2pt]` → `\\[1pt]`
  4. `\vspace{0pt}`, then `-2pt`, then `-4pt`
  **`-4pt` is the floor** — it is the most negative value used anywhere else in the deck. Going past it requires reporting the overflow as a BLOCKED finding instead, because at that point the frame is genuinely over capacity and the author must decide what to cut. Whichever rung you use, **verify both edges**: the bottom margin against the footline *and* the top junction against whatever sits above. Report both measured gaps in points.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `output/presentation/slides_report.tex` | Canonical 67pp research report deck | Modify — 11 framing edits + spelling |
| `output/presentation/slides_advisor.tex` | 11pp advisor talk deck, minimalist register | Modify — 4 framing edits + spelling |
| `WRITING_GUIDE.md` | Paper-drafting guide; §3 currently issues a now-completed instruction | Modify — §3 → RESOLVED pointer |
| `FRAMING.md` | The locked memo | Modify — flip Application record from pending to done |
| `output/paper/*.tex` | Paper prose | **DO NOT TOUCH** |

Task order matters: **Task 1 first** (frame 2 is the linchpin every later frame refers back to), **Task 8 (spelling) after all prose edits** so the sweep also normalizes any text the earlier tasks introduced, **Task 9 last** so the guide and memo describe finished work.

---

## Shared Helper: verify-and-look

Every task uses this cycle. Run it verbatim, substituting the deck name and a distinctive search string.

**Compile (report):**
```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation && \
pdflatex -interaction=nonstopmode slides_report.tex > /dev/null && \
pdflatex -interaction=nonstopmode slides_report.tex > /dev/null; echo "exit=$?"
```

**Check for real errors** (Beamer emits many benign warnings; only `!` lines are fatal):
```bash
grep -E "^! " /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation/slides_report.log || echo "NO FATAL ERRORS"
```

**Assert page count and find + rasterize the edited frame** — replace `SEARCH_STRING` with a distinctive phrase from the frame you just edited:
```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe -c "
import fitz
d = fitz.open(r'C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation\slides_report.pdf')
print('PAGE COUNT:', d.page_count, '(baseline 67)')
hits = [i for i in range(d.page_count) if 'SEARCH_STRING' in d[i].get_text()]
print('found on pages:', [h+1 for h in hits])
for i in hits[:3]:
    d[i].get_pixmap(dpi=110).save(rf'C:\Users\naral\AppData\Local\Temp\claude\C--Users-naral-Desktop-Nara-Doutorado-Tese-judicialization\324cc02a-4413-4040-8299-d7f70dfbdf42\scratchpad\check_p{i+1}.png')
    print('wrote check_p%d.png' % (i+1))
"
```

**Then use the Read tool on each generated PNG.** You are looking for: text running past the frame's bottom edge, a block colliding with the footline, or a line overflowing the right margin. If the frame is full, tighten wording — do not accept a visibly overfull frame.

---

### Task 1: Frame 2 — establish the ballot as the discriminator (R2, R3)

This is the linchpin. Every later edit refers back to this frame, and its current self-contradiction (L90 commits H1 to "disperses the vote" while L72/L85 mark competition ambiguous) is what propagated into the advisor deck.

**Files:**
- Modify: `output/presentation/slides_report.tex:72`, `:85`, `:90`

**Interfaces:**
- Produces: the claim "concentration is not diagnostic; the ballot discriminates", which Tasks 2, 3, 4, 5 and 7 all cite. The phrase **"Not diagnostic."** is introduced here in frame 2's two Competition bullets. Note it is *not* reused verbatim downstream: Task 2's measurement-table cell deliberately says `\emph{ambiguous}` instead, because a table cell reads better with a single adjective than with a sentence fragment. Both express the same claim; follow each task's literal mandate.

- [ ] **Step 1: Look at the frame before changing it**

Rasterize the current state so you can compare after. Search string: `Two Faces of the Same Power`. Use the helper above, then Read the PNG.

- [ ] **Step 2: Promote the two ambiguity bullets (L72, L85)**

Edit `output/presentation/slides_report.tex`. Replace:
```latex
  \item[\ns{?}] \textbf{Competition:} more entrants could \emph{sharpen} it --- or just weed out weak names. \ns{Open.}
```
with:
```latex
  \item[\ns{?}] \textbf{Competition:} more entrants could \emph{sharpen} it --- or just weed out weak names. \ns{\textbf{Not diagnostic.}}
```

Then replace:
```latex
  \item[\ns{?}] \textbf{Competition:} costs could \emph{concentrate} power --- or felled front-runners could scramble it. \ns{Open.}
```
with:
```latex
  \item[\ns{?}] \textbf{Competition:} costs could \emph{concentrate} power --- or felled front-runners could scramble it. \ns{\textbf{Not diagnostic.}}
```

- [ ] **Step 3: Rewrite the closing line (L90) to remove the contradiction**

Replace:
```latex
{\footnotesize Two competing hypotheses, tested below --- \pos{\textbf{H1 (Leveling)}}: exposure raises valid voting and disperses the vote; \negt{\textbf{H2 (Barrier)}}: exposure raises blank and null voting and concentrates it. Both move engagement, with opposite sign.}
```
with:
```latex
{\footnotesize Two competing hypotheses, tested below --- \pos{\textbf{H1 (Leveling)}}: exposure raises \textbf{valid} voting; \negt{\textbf{H2 (Barrier)}}: exposure raises \textbf{blank} and \textbf{null} voting and lowers valid. They disagree on the \textbf{ballot}, and the ballot is what identifies them --- \emph{not} concentration, which either face can produce.}
```

- [ ] **Step 4: Compile twice**

Run the compile block from Shared Helper. Expected: `exit=0`.

- [ ] **Step 5: Check for fatal errors**

Run the grep block. Expected: `NO FATAL ERRORS`.

- [ ] **Step 6: Rasterize and look**

Search string: `Two Faces of the Same Power`. Expected: `PAGE COUNT: 67`. Read the PNG and confirm both `Not diagnostic.` markers render and the closing footnote fits on one or two lines without touching the frame edge.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: the ballot discriminates, not concentration (FRAMING D4)

Frame 2 contradicted itself: L90 committed H1 to dispersing the vote while
the same frame's competition bullets marked it ambiguous. The bullets are
now the frame's point, and the closing line names the ballot as the
identifying margin."
```

---

### Task 2: The research question and the measurement table (R1, R4)

**Files:**
- Modify: `output/presentation/slides_report.tex:52`, `:405`, `:410`

**Interfaces:**
- Consumes: Task 1's "not diagnostic" claim.

- [ ] **Step 1: Unbundle concentration from the barrier definition (L52)**

The RQ block currently *defines* barrier as including concentration, which is precisely the conflation D4 removes. Replace:
```latex
As a race faces more adversarial litigation, does the contest \textcolor{mygreen}{\emph{level}} (voters re-sort) or does a \textcolor{myred}{\emph{barrier}} emerge (voters withdraw, the vote concentrates) --- and does who runs and who wins change? We ask separately by office; \textbf{the answer differs}.
```
with:
```latex
As a race faces more adversarial litigation, does the contest \textcolor{mygreen}{\emph{level}} (voters re-sort) or does a \textcolor{myred}{\emph{barrier}} emerge (voters withdraw from the ballot) --- and does who runs and who wins change? The vote may concentrate under \emph{either}, so it is the \textbf{ballot} that tells them apart. We ask separately by office; \textbf{the answer differs}.
```

- [ ] **Step 2: Mark layer 3 ambiguous under Leveling (L405)**

The table's columns are: layer | what we measure | Leveller widens | Barrier narrows. Replace:
```latex
\textbf{3\ \ How open it stays} & Victory margin, effective \# of candidates, incumbency advantage & closer races & consolidation \\
```
with:
```latex
\textbf{3\ \ How open it stays} & Victory margin, effective \# of candidates, incumbency advantage & \emph{ambiguous} & consolidation \\
```

- [ ] **Step 3: Name the discriminating layer in the closing line (L410)**

Replace:
```latex
{\centering\footnotesize Together these are the two behavioural engines --- \textbf{candidates} and \textbf{voters} --- and the \textbf{result} they produce, the spine of the Results section; next, the equation, then the instrument behind it.\par}
```
with:
```latex
{\centering\footnotesize Together these are the two behavioral engines --- \textbf{candidates} and \textbf{voters} --- and the \textbf{result} they produce, the spine of the Results section. Layer 2 is the \textbf{discriminating} layer: layer 3 concentrates under either face, so the ballot assigns one. Next, the equation, then the instrument behind it.\par}
```

- [ ] **Step 4: Compile twice**

Run the compile block. Expected: `exit=0`.

- [ ] **Step 5: Check for fatal errors**

Expected: `NO FATAL ERRORS`.

- [ ] **Step 6: Rasterize and look — two frames**

Run the rasterize block twice, with search strings `Level the Field, or Raise the Bar` and `Research question`. Expected: `PAGE COUNT: 67`. Read both PNGs. The measurement table is inside a `\resizebox` — confirm the `\emph{ambiguous}` cell has not made the table wider than the frame, and that the longer closing line has not pushed content off the bottom.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: unbundle concentration from the barrier definition (FRAMING D4)

The research question defined barrier as 'voters withdraw, the vote
concentrates'. Concentration is now stated separately as the outcome whose
face the ballot decides, and layer 3 of the measurement table is marked
ambiguous under Leveling."
```

---

### Task 3: This Paper and Story-in-One-Frame (R5, R6)

**Files:**
- Modify: `output/presentation/slides_report.tex:118`, `:572`

- [ ] **Step 1: Replace the "barrier configuration" claim (L118)**

Replace:
```latex
{\footnotesize These effects are confined to the \emph{mayoral} race --- the barrier configuration --- and are sharpest in contested seats. The council race exhibits neither face: both the ballot and the composition of the field are flat.}
```
with:
```latex
{\footnotesize These effects are confined to the \emph{mayoral} race. The consolidation is \textbf{general} across seat types; the \textbf{barrier} reading holds where an incumbent is defended --- there, and only there, do voters leave the ballot. The council race exhibits neither face: both the ballot and the composition of the field are flat.}
```

- [ ] **Step 2: Retire "the barrier signature" (L572)**

Replace:
```latex
\footnotesize The candidate engine is quiet while voters withdraw \emph{where an incumbent is defended}; the consolidation --- general across seats --- is the electorate re-allocating toward the leader, not candidates removed, the barrier signature. The council race is null throughout.
```
with:
```latex
\footnotesize The candidate engine is quiet while voters withdraw \emph{where an incumbent is defended}; the consolidation --- general across seats --- is the electorate re-allocating toward the leader, not candidates removed. Concentration alone does not name a face: the \textbf{barrier} reading rests on the ballot, and so holds for \textbf{contested} seats. The council race is null throughout.
```

- [ ] **Step 3: Compile twice**

Expected: `exit=0`.

- [ ] **Step 4: Check for fatal errors**

Expected: `NO FATAL ERRORS`.

- [ ] **Step 5: Rasterize and look — two frames**

Search strings: `Question, Design, Answer` and `Two Engines, One Result`. Expected: `PAGE COUNT: 67`. Both replacement strings are longer than what they replace and both frames are dense — the Story frame carries a TikZ diagram above its footnote. Read both PNGs carefully for bottom-edge overflow. If the Story frame is tight, drop "The council race is null throughout." to a new line rather than shortening the D4 clause.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: consolidation general, barrier reading seat-conditional (FRAMING D5)

Retires 'the consolidation is the barrier signature', which borrowed the
robust tier for a claim resting on the tentative ballot result."
```

---

### Task 4: Promote the seat split to the identifying test (R7)

**Files:**
- Modify: `output/presentation/slides_report.tex:673`, `:676`

Under D5 this frame is not heterogeneity garnish — it is how the face gets assigned. Its title also currently collides with frame 2's "Two Faces", which the vocabulary lock forbids.

- [ ] **Step 1: Retitle the frame (L673)**

Replace:
```latex
\begin{frame}{Heterogeneity --- One Shock, Two Faces by Seat Type}
```
with:
```latex
\begin{frame}{The Identifying Test --- Which Face, by Seat Type}
```

- [ ] **Step 2: Rewrite the setup sentence (L676)**

Replace:
```latex
Split the mayoral races by whether the seat is \textbf{open} --- the incumbent is term-limited, so no front-runner defends it ($N=2{,}026$) --- or \textbf{contested}, where the sitting mayor may still seek re-election ($N=3{,}534$). The consolidation and the disengagement findings then reveal themselves as two faces of one shock, sorting cleanly by seat type.
```
with:
```latex
Split the mayoral races by whether the seat is \textbf{open} --- the incumbent is term-limited, so no front-runner defends it ($N=2{,}026$) --- or \textbf{contested}, where the sitting mayor may still seek re-election ($N=3{,}534$). This split is what \emph{assigns} the face: the vote concentrates in both, so only the ballot separates them.
```

- [ ] **Step 3: Verify no cross-reference broke**

The frame carries `\hypertarget{src:seathet}{}` and other frames link to it with `\hyperlink{src:seathet}`. You changed only the *title* and body prose, never the target. Confirm:
```bash
grep -n "src:seathet" /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation/slides_report.tex
```
Expected: the `\hypertarget{src:seathet}{}` definition still present, plus any `\hyperlink` references — all unchanged.

- [ ] **Step 4: Compile twice**

Expected: `exit=0`.

- [ ] **Step 5: Check for fatal errors**

Expected: `NO FATAL ERRORS`.

- [ ] **Step 6: Rasterize and look**

Search string: `Which Face, by Seat Type`. Expected: `PAGE COUNT: 67`, and the string found (confirming the retitle landed). Read the PNG — this frame holds a figure plus a long `\takeaway{}`, so it is one of the tightest in the deck.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: seat split is the identifying test, not heterogeneity (FRAMING D5)

Also retitles away from 'Two Faces by Seat Type', which collided with the
Leveling/Barrier dichotomy reserved by the vocabulary lock."
```

---

### Task 5: Findings by confidence — Romano–Wolf qualifier and the claim structure (R8, R11, R9)

**Files:**
- Modify: `output/presentation/slides_report.tex:749`, `:755`, `:760`

The Romano–Wolf correction is listed among the Robust tier's clean passes. `output/tables/regressions/romano_wolf_stepdown.csv` gives margin `p_rw = 0.0589` and runner-up `p_rw = 0.0712` — a 10% pass, not 5%. Holm (0.0148) and BH (0.0114) do clear at 5%.

- [ ] **Step 1: Confirm the numbers before editing**

```bash
head -3 /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/tables/regressions/romano_wolf_stepdown.csv
```
Expected: the margin row shows `p_rw` = `0.0589`, `p_holm` = `0.0147...`, `p_bh` = `0.0113...`. If these differ, stop and report — the estimates have been re-run since this plan was written.

- [ ] **Step 2: Qualify the multiplicity claim (L749)**

Replace:
```latex
the BHJ/AKM exposure-robust SE (CI $\ERMarginCI$ excludes zero), and a Romano--Wolf multiplicity correction --- the finding that carries statistical weight.
```
with:
```latex
the BHJ/AKM exposure-robust SE (CI $\ERMarginCI$ excludes zero), and multiplicity correction at 5\% by Holm and Benjamini--Hochberg (Romano--Wolf, the most conservative of the three, clears at 10\%: $p=.059$) --- the finding that carries statistical weight.
```

- [ ] **Step 3: State the claim structure explicitly (L755)**

Replace:
```latex
\footnotesize The candidate engine is quiet while some voters withdraw, so the consolidation is the electorate re-allocating votes toward the leader --- the barrier signature, not candidates removed.
```
with:
```latex
\footnotesize The candidate engine is quiet while some voters withdraw, so the consolidation is the electorate re-allocating votes toward the leader, not candidates removed. Note the structure of the claim: the \textbf{consolidation is robust}, while the \textbf{barrier reading is tentative} --- it rests on the ballot, one tier down.
```

- [ ] **Step 4: Qualify the Contribution frame (L760)**

Replace:
```latex
an expanded judicial arena operates as a \negt{barrier} --- re-concentrating the vote toward the front-runner and pushing marginal voters off the ballot, without reshaping who runs or who wins.
```
with:
```latex
an expanded judicial arena \textbf{re-concentrates} the vote toward the front-runner without reshaping who runs or who wins --- and, where an incumbent is defended, pushes marginal voters off the ballot, the \negt{barrier} signature.
```

- [ ] **Step 5: Compile twice**

Expected: `exit=0`.

- [ ] **Step 6: Check for fatal errors**

Expected: `NO FATAL ERRORS`.

- [ ] **Step 7: Rasterize and look — two frames**

Search strings: `Findings by Confidence` and `Contribution`. Expected: `PAGE COUNT: 67`. The Findings frame is a four-item list that already fills its frame and Step 2 makes the first item materially longer — read that PNG with particular care. If it overflows, shorten the parenthetical to `(Romano--Wolf clears at 10\%: $p=.059$)`.

- [ ] **Step 8: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: qualify Romano-Wolf as a 10% pass; state the claim structure

romano_wolf_stepdown.csv gives margin p_rw=.059, so listing it among the
Robust tier's clean 5% passes overstated it. Holm (.015) and BH (.011) do
clear. The Robust tier still stands on AR-WCR and BHJ/AKM.

Also states outright that the consolidation is robust while the barrier
reading of it is tentative (FRAMING D4)."
```

---

### Task 6: State the estimand boundary in app:theory (R10)

**Files:**
- Modify: `output/presentation/slides_report.tex:848`

D2 holds that direct judicial action is outside the estimand by construction. The theory frame currently never mentions it, which leaves the deleted third channel unexplained to anyone who read the extended abstract.

- [ ] **Step 1: Insert the boundary sentence after the frame's opening line (L848)**

Replace:
```latex
The \textbf{Leveling} and \textbf{Barrier} faces of the main text rest on two hypotheses about \emph{why} litigation moves an election:
```
with:
```latex
The \textbf{Leveling} and \textbf{Barrier} faces of the main text rest on two hypotheses about \emph{why} litigation moves an election. A third channel --- \emph{direct judicial action}, where a ruling removes a candidate and mechanically reallocates the vote --- lies \textbf{outside the estimand}: the adversarial filter drops the candidacy-registration and campaign-finance machinery (RRC/DRAP, \emph{presta\c{c}\~ao de contas}), so it is not what these estimates measure.
```

- [ ] **Step 2: Compile twice**

Expected: `exit=0`.

- [ ] **Step 3: Check for fatal errors**

Expected: `NO FATAL ERRORS`. The `\c{c}` and `\~a` escapes are the risk here — a mistyped escape produces a `!` line.

- [ ] **Step 4: Rasterize and look**

Search string: `Signal vs Weapon`. Expected: `PAGE COUNT: 67`. Read the PNG and confirm "prestação de contas" renders with correct accents, and that the added sentence has not pushed the two-column block or the mechanism table off the frame. This frame is already dense — if it overflows, move the new sentence to the frame's closing line instead, above the `\beamerreturnbutton`.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex && \
git commit -m "deck: state the estimand boundary in app:theory (FRAMING D2)

Direct judicial action is out by construction, not rejected on evidence.
Says so once, where the mechanism scheme is laid out."
```

---

### Task 7: Advisor deck — four edits (A1–A4)

**Files:**
- Modify: `output/presentation/slides_advisor.tex:17`, `:85`, `:128`, `:135`

This deck is Nara's hand-trimmed artifact. Preserve its minimalist register: single sentences, no qualifier chains, no methods footlines on results frames. Its **Layer-2 verdict (L120) is already correct** under D5 — "the response is to a *defended* seat, not to litigation as such" — and must be left untouched.

**Note the different build command** (different filename):
```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation && \
pdflatex -interaction=nonstopmode slides_advisor.tex > /dev/null && \
pdflatex -interaction=nonstopmode slides_advisor.tex > /dev/null; echo "exit=$?"
```
And the different PDF path and baseline in the rasterize block: `slides_advisor.pdf`, baseline **11** pages.

- [ ] **Step 1: Mark the hypothesis grid's layer-3 row ambiguous (L85)**

The grid columns are: Layer | What I measure | H1 — Leveller | H2 — Barrier. Replace:
```latex
\pos{closer races} &
\negt{consolidation} \\
```
with:
```latex
\ns{\emph{ambiguous}} &
\negt{consolidation} \\
```

- [ ] **Step 2: Remove the overclaim at L128**

This is the line that commits H1 to predicting closer races and so makes consolidation self-identifying. Replace:
```latex
The winner's vote share rises, the runner-up's falls, and the top-two margin between them widens --- all three point one way: \negt{H2's consolidation}, not \pos{H1's closer races}. The proportional council race shows none of it.
```
with:
```latex
The winner's vote share rises, the runner-up's falls, and the top-two margin between them widens --- the race \negt{consolidates}. Either face can concentrate a vote, so the reading comes from Layer 2's ballot. The proportional council race shows none of it.
```

- [ ] **Step 3: Re-tier the Layer-3 verdict (L135)**

Replace:
```latex
\takeaway{\textbf{Layer-3 verdict: \negt{H2}, at full confidence.} A one-SD rise widens the winner's margin by $+\MarginPerSD$~pp ($p=\MarginP$), clearing the AR bootstrap ($p=\ARMarginP$) and the exposure-robust CI ($\ERMarginCI$) --- and it is general across seat types. The front-runner it reinforces is the \textbf{sitting incumbent} (${\approx}5\times$ the runner-up), a demographic near-twin --- which is why representation cannot move. Candidates silent, voters withdrawing, the vote re-allocating toward the leader: \negt{a barrier}, not \pos{a leveller}.}
```
with:
```latex
\takeaway{\textbf{Layer-3 verdict: the consolidation, at full confidence.} A one-SD rise widens the winner's margin by $+\MarginPerSD$~pp ($p=\MarginP$), clearing the AR bootstrap ($p=\ARMarginP$) and the exposure-robust CI ($\ERMarginCI$) --- and it is general across seat types. The front-runner it reinforces is the \textbf{sitting incumbent} (${\approx}5\times$ the runner-up), a demographic near-twin --- which is why representation cannot move. The \negt{barrier} reading of it inherits Layer 2's tentative tier.}
```

- [ ] **Step 4: Update the structural header comment (L17)**

**This line contains a non-ASCII em-dash** (a genuine `—`, unlike the true mojibake on L22). Either way the rule is the same: match on the pure-ASCII substring only, so the non-ASCII byte is never part of `old_string` or `new_string`. Replace:
```
consolidation, H2 at full confidence, the
```
with:
```
consolidation at full confidence (the H2 reading of it is tentative), the
```

- [ ] **Step 5: Compile twice**

Use the advisor build command above. Expected: `exit=0`.

- [ ] **Step 6: Check for fatal errors**

```bash
grep -E "^! " /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation/slides_advisor.log || echo "NO FATAL ERRORS"
```

- [ ] **Step 7: Rasterize and look — two frames**

Adapt the rasterize block for `slides_advisor.pdf`. Search strings: `Hypotheses` and `How Open It Stays`. Expected: `PAGE COUNT: 11`. Read both PNGs. The `\takeaway{}` box on the Layer-3 frame is the tightest element in this deck; the replacement is slightly shorter than the original, so it should fit, but confirm visually.

- [ ] **Step 8: Confirm the Layer-2 verdict was not touched**

```bash
grep -c "not to litigation as such" /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/output/presentation/slides_advisor.tex
```
Expected: `1`.

- [ ] **Step 9: Confirm no encoding damage**

Compare the count of non-ASCII bytes before and after. It must be unchanged — the edits were all ASCII-to-ASCII:
```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe -c "
d = open(r'C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation\slides_advisor.tex','rb').read()
print('non-ascii bytes:', sum(1 for b in d if b > 127))
"
```
Expected: `79` (measured baseline). A different number means an edit mangled the encoding — revert and redo matching on ASCII-only anchors.

- [ ] **Step 10: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_advisor.tex && \
git commit -m "advisor deck: consolidation is the finding, the face comes from the ballot

L128 committed H1 to predicting closer races, which made consolidation
self-identifying and was the deck's most exposed claim. The Layer-3 verdict
now carries full confidence for the consolidation and inherits Layer 2's
tentative tier for the barrier reading (FRAMING D4). Layer-2 verdict was
already correct and is untouched."
```

---

### Task 8: American spelling sweep, both decks

**Files:**
- Modify: `output/presentation/slides_report.tex`, `output/presentation/slides_advisor.tex`

Runs after all prose edits so it also normalizes text the earlier tasks introduced.

**Verified inventory (measured, do not re-estimate).** Using the precise word-boundary
pattern in Step 1: `slides_report.tex` has **29** occurrences on 29 lines,
`slides_advisor.tex` has **2**. Of the report's 29, three are inside `%` comments
(L203 `colour`, L887 `normalised`, L1127 `BEHAVIOURAL`) and one sits on a line
containing non-ASCII bytes (L830 `analyse`). Of the advisor's 2, one is rendered
prose (L156 `Favours`) and one is a `%` comment on a mojibake line (L22 `defences`).
All are swept — comments included, for consistency.

**Do NOT use `sed -i` here.** Two of the target lines carry non-ASCII bytes, and
`sed -i` on Git Bash rewrites the whole file: it can strip the UTF-8 BOM
(`slides_report.tex` has one), normalize CRLF, or re-encode the mojibake. The
Python sweep below round-trips bytes losslessly and is checked by a byte-level
assertion in Step 3.

**Two traps this pattern avoids:**
- `characteristic` / `characteristics` / `CHARACTERISTICS` are **already American**.
  A `characteris` stem replacement corrupts them to `characteriztic`. Only the verb
  forms (`characterise`/`characterised`/`characterises`/`characterising`) change.
- `analysis` is already American, and LaTeX's `\textcolor`/`\rowcolor`/`\definecolor`
  and the `xcolor` package are already spelled `color`. Only `analyse`-stem verbs and
  standalone `colour` change.

- [ ] **Step 1: Record the pre-sweep state**

```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe << 'PYEOF'
import re, io
base = r"C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation"
PAT = re.compile(r"\b(favour\w*|behaviour\w*|colour\w*|normalis\w*|demobilis\w*"
                 r"|urbanis\w*|organis\w*|modelling|analys(?:e|ed|es|ing)"
                 r"|characteris(?:e|ed|es|ing)\b|defence\w*)\b", re.I)
for f in ("slides_report.tex","slides_advisor.tex"):
    txt = io.open(base+"\\"+f, encoding="utf-8-sig").read()
    print(f, len(PAT.findall(txt)))
PYEOF
```
Expected exactly: `slides_report.tex 29`, `slides_advisor.tex 2`. A different count
means the file drifted since the plan was written — re-inventory before sweeping.

- [ ] **Step 2: Run the byte-safe sweep**

Case is preserved per-match, so `Favours`→`Favors` and `BEHAVIOURAL`→`BEHAVIORAL`
need no separate rules:
```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe << 'PYEOF'
import re
base = r"C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation"
SUBS = [(r"favour", "favor"), (r"behaviour", "behavior"), (r"colour", "color"),
        (r"normalis", "normaliz"), (r"demobilis", "demobiliz"),
        (r"urbanis", "urbaniz"), (r"organis", "organiz"),
        (r"modelling", "modeling"), (r"defence", "defense"),
        (r"analyse\b", "analyze"),
        (r"characteris(?=e\b|ed\b|es\b|ing\b)", "characteriz")]

def keep_case(src, repl):
    if src.isupper():  return repl.upper()
    if src[0].isupper(): return repl.capitalize()
    return repl

for f in ("slides_report.tex","slides_advisor.tex"):
    p = base + "\\" + f
    raw = open(p, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    txt = raw.decode("utf-8-sig")          # strict: raises if not valid UTF-8
    n = 0
    for pat, repl in SUBS:
        rx = re.compile(pat, re.I)
        def _f(m, r=repl):
            global n
            n += 1
            return keep_case(m.group(0), r)
        txt = rx.sub(_f, txt)
    out = txt.encode("utf-8")
    if bom: out = b"\xef\xbb\xbf" + out
    open(p, "wb").write(out)
    print(f, "replacements:", n, "| BOM preserved:", bom)
PYEOF
```
Expected: `slides_report.tex replacements: 29 | BOM preserved: True` and
`slides_advisor.tex replacements: 2`.

- [ ] **Step 3: Verify completeness, encoding integrity, and no collateral damage**

```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe << 'PYEOF'
import re, io
base = r"C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation"
PAT = re.compile(r"\b(favour\w*|behaviour\w*|colour\w*|normalis\w*|demobilis\w*"
                 r"|urbanis\w*|organis\w*|modelling|analys(?:e|ed|es|ing)"
                 r"|characteris(?:e|ed|es|ing)\b|defence\w*)\b", re.I)
BAD = re.compile(r"characteriztic|analyzis|textcolour|rowcolour|definecolour|xcolour", re.I)
for f, nab in (("slides_report.tex", 79), ("slides_advisor.tex", 79)):
    p = base + "\\" + f
    raw = open(p, "rb").read()
    txt = io.open(p, encoding="utf-8-sig").read()
    got = sum(1 for b in raw if b > 127)
    print(f)
    print("   remaining British (expect 0):", len(PAT.findall(txt)))
    print("   corruption (expect []):", BAD.findall(txt))
    print(f"   non-ascii bytes: {got} (baseline {nab})", "OK" if got == nab else "MISMATCH")
    print("   sanity, must be >0 -- characteristic:", len(re.findall(r"characteristic", txt, re.I)),
          "analysis:", len(re.findall(r"analysis", txt, re.I)),
          "textcolor:", len(re.findall(r"textcolor", txt)))
PYEOF
```
Expected: remaining `0`, corruption `[]`, non-ascii `79 ... OK` for both, and nonzero
sanity counts in the report. **A non-ascii MISMATCH means the encoding was damaged** —
revert with `git checkout -- output/presentation/slides_report.tex output/presentation/slides_advisor.tex`
and rerun Step 2. `characteriztic` appearing means the lookahead was dropped from the
`characteris` rule.

- [ ] **Step 4: Compile both decks twice each**

Run both build commands. Expected: `exit=0` for each.

- [ ] **Step 5: Check for fatal errors in both logs**

Expected: `NO FATAL ERRORS` for both.

- [ ] **Step 6: Assert both page counts**

```bash
/c/Users/naral/AppData/Local/Programs/Python/Python313/python.exe -c "
import fitz
for f,base in [('slides_report.pdf',67),('slides_advisor.pdf',11)]:
    p = rf'C:\Users\naral\Desktop\Nara\Doutorado\Tese\judicialization\output\presentation\{f}'
    d = fitz.open(p); print(f, d.page_count, 'baseline', base, 'OK' if d.page_count==base else 'MISMATCH')
"
```
Expected: both `OK`. Spelling changes are length-neutral or one character shorter, so a page-count change would be surprising and warrants investigation.

- [ ] **Step 7: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add output/presentation/slides_report.tex output/presentation/slides_advisor.tex && \
git commit -m "deck: American spelling throughout both decks

Per the FRAMING.md vocabulary lock. The decks previously mixed British
-our/-ise forms with American 'Leveling'."
```

---

### Task 9: Mark WRITING_GUIDE §3 resolved and close out FRAMING.md

**Files:**
- Modify: `WRITING_GUIDE.md:51-61`
- Modify: `FRAMING.md` (Application record section)

`WRITING_GUIDE.md` §3 currently instructs the reader to reconcile the framing "before drafting" — an instruction that has now been carried out. Leaving it in place would send Nara to re-decide settled questions.

- [ ] **Step 1: Replace §3's table with a resolved pointer**

Replace the whole block from the `## 3.` heading through the end of its table (lines 51–61, ending with the `| **Identification honesty** | ... |` row) with:
```markdown
## 3. Framing — RESOLVED

**Locked 2026-08-11 in [`FRAMING.md`](FRAMING.md).** Do not re-decide these while
drafting; read that file first and write from it.

In brief: the object is the judiciary's **expanded role**, never litigation volume
(D1); **direct judicial action is outside the estimand by construction** (D2);
information and weaponization are observationally non-separable and collapse onto
**Leveling vs Barrier** (D3); **concentration does not identify a face — the ballot
does** (D4); and the **open/contested seat split is the identifying test**, not
heterogeneity (D5).

The consequence that governs every claim in the paper: the **consolidation is
robust**, its **face-assignment is tentative**. `FRAMING.md` also carries the
vocabulary lock, the American-spelling rule, the novelty phrasing, and an
apply-to-the-paper sheet listing exactly what is stale in `extended_abstract.tex`.
```

- [ ] **Step 2: Verify §4 still follows and nothing else broke**

```bash
grep -n "^## " /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization/WRITING_GUIDE.md
```
Expected: sections 0 through 8 all present, in order, with `## 3. Framing — RESOLVED` in place of the old heading.

- [ ] **Step 3: Flip the FRAMING.md application record to done**

Replace:
```markdown
**Status: pending — this section is updated once the edits land.**

Scope agreed 2026-08-11: 11 edits to `slides_report.tex`
```
with:
```markdown
**Status: applied 2026-08-11.**

11 edits to `slides_report.tex`
```

- [ ] **Step 4: Confirm the paper files were never touched**

This is the plan's hard constraint. Verify across every commit made by this plan:
```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git diff --name-only a6b42a1..HEAD | sort
```
Expected: only `FRAMING.md`, `WRITING_GUIDE.md`, `docs/superpowers/plans/...`, and the four `output/presentation/slides_*.tex|pdf` files. **`output/paper/paper.tex` and `output/paper/extended_abstract.tex` must NOT appear.** If either does, stop and report before committing.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization && \
git add WRITING_GUIDE.md FRAMING.md && \
git commit -m "Mark WRITING_GUIDE section 3 resolved; close out FRAMING application record

Section 3 instructed the reader to reconcile the framing before drafting.
That is done and locked in FRAMING.md, so the section now points there
instead of re-opening settled questions."
```

---

## Done When

- [ ] Both decks compile with no `!` errors and hold their baseline page counts (67 / 11).
- [ ] Every edited frame has been rasterized and visually confirmed free of overflow.
- [ ] `grep -ri "barrier signature" output/presentation/` returns nothing.
- [ ] The Task 8 Step 3 verifier reports `remaining British: 0` and `non-ascii bytes: 79 ... OK` for **both** decks.
- [ ] `git diff --name-only a6b42a1..HEAD` contains no file under `output/paper/`.
- [ ] `WRITING_GUIDE.md` §3 points at `FRAMING.md` rather than issuing a reconciliation instruction.

Use the Task 8 Step 3 script for the spelling check, **not** a loose `grep -E`. A bare
`analyse` alternation matches `analyses` — the correct American plural of *analysis* —
and a bare `characteris` matches `characteristic`. Both are false positives that would
fail a clean deck.

---

## Spec coverage notes

Checked against FRAMING.md D1–D5 after the plan was drafted:

- **D1 (intensity, not a time trend)** — no deck task. The report deck's framing lines
  are already clean of "grew/surge/wave/rising" diction; the violations live in
  `extended_abstract.tex` lines 64–113, which is Nara's to fix. FRAMING.md's
  apply-to-the-paper sheet already records it.
- **Novelty claim ("the first *aggregate* causal estimate...", "first" never bare)** —
  **no deck task, verified.** Every occurrence of "first" in both decks is
  `first stage`, `first difference`, `first-time candidates`, or the 1932 *Código
  Eleitoral*. Neither deck states a novelty claim, so there is nothing to correct.
  This is a deliberate no-op, not a gap — do not add a task for it.
- **Known exposures** (kept-class removals, Romano–Wolf as a 10% pass, extensive-margin
  identification) — only the Romano–Wolf item reaches a deck, handled in Task 5. The
  other two are memo-only by decision and must not enter deck prose.
