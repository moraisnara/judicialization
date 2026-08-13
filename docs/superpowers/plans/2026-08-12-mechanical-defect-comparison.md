# Mechanical defect fixes — before/after

Fixed and re-run 2026-08-12. "Before" was read from the committed tree before any
change; "After" from the tree after the full build → estimation → analysis re-run.

Commits: `c07d9c9` (defect 1), `a08416a` (defect 2), `0ccf876` (defect 3).

---

## Did the headline move? No.

| Quantity | Before | After | Moved? |
|---|---|---|---|
| Margin, baseline spec | 0.0615 (0.0230) p=.0131 N=5560 | 0.0615 (0.0230) p=.0131 N=5560 | no |
| First-stage F, full sample | 102.288 | 102.288 | no |
| AR-WCR p, margin | — | 0.015, 95% CI [0.017, 0.117] | still rejects |
| `extended_controls` | — | 0.0663 (0.0242) p=.0111 N=5560 | — |
| Multiplicity (18-outcome family) | Holm .2365 / BH .1435 | Holm .2365 / BH .1435 | no |

The strongest evidence that the headline is untouched is the `abstract_macros.tex`
diff: 30 macro lines changed and **every one of them is a Rotemberg macro**. No
result macro, no coefficient macro, no p-value macro moved.

---

## Defect 1 — GPS pre-trend balance test

### The test now exists

| Quantity | Before | After |
|---|---|---|
| max\|beta_margin\| | 7.15e-16 (machine zero) | 0.9313 |
| median\|beta_margin\| | 5.22e-17 | 0.0532 |
| topics rejecting at 5% | 0 (arithmetically impossible) | **5 / 15** |
| topics rejecting at 10% | 0 | **6 / 15** |

### Topic-by-topic, ordered by Rotemberg weight

| Topic | alpha | beta_margin | p |
|---|---|---|---|
| Propaganda — Internet | +0.1454 | +0.0019 | .949 |
| Propaganda — Extemporânea/Antecipada | +0.1162 | +0.0048 | .856 |
| Propaganda — Lei de Postura Municipal | +0.1155 | −0.0096 | .888 |
| Propaganda — Comício/Showmício | +0.1028 | −0.0233 | .466 |
| **Eleições — 1º Turno** | **+0.0750** | **−0.0961** | **.048** |
| Propaganda — Adesivo | +0.0742 | +0.0138 | .758 |
| Propaganda — Alto-falante | +0.0691 | −0.0576 | .063 |
| Propaganda — Inobservância do Limite Legal | +0.0686 | −0.0959 | .117 |
| **Pesquisa Eleitoral — Divulgação Fraudulenta** | **−0.0605** | **−0.0986** | **.0001** |
| Propaganda — Redes Sociais | +0.0515 | −0.0067 | .814 |
| **Propaganda — Aplicativo de Mensagem** | **+0.0406** | **−0.0961** | **.035** |
| **Propaganda — Notícia Sabidamente Falsa** | **−0.0315** | **−0.0532** | **.043** |
| Calúnia na Propaganda Eleitoral | +0.0118 | −0.0557 | .454 |
| Propaganda — Impulsionamento | +0.0016 | −0.0479 | .677 |
| **Registro de Candidatura — DRAP** | **+0.0011** | **+0.9313** | **.002** |

The four highest-weighted topics — 48% of net alpha between them — pass
comfortably. The failures cluster in two places: the three disinformation-adjacent
topics (fraudulent polling, knowingly false news, messaging apps), and
`Eleições — 1º Turno` at 7.5% weight. DRAP fails hardest but carries 0.1% weight.

Every failing beta is **negative**: municipalities more exposed to those topics
were on a *downward* margin path 2016→2020, the opposite sign to the effect the
instrument produces 2020→2024. That direction does not manufacture the headline.

### Rotemberg drift from running on-spec

The script had been running the rejected V1 control set, so these move too.

| Quantity | Before | After |
|---|---|---|
| `\KeffRotemberg` | 10.4 | 10.3 |
| `\RotPropagandaPct` | 90.2 | 89.9 |
| `\RotNPositive` | 101 | 99 |
| `\RotTopFiveCumPct` | 56.1 | 55.5 |
| 5th-ranked topic | Adesivo (7.7%, F 30.2) | **1º Turno (7.5%, F 13.4)** |
| negative-alpha topics | 78, sum −0.252 | 80, sum −0.258 |
| total topics / sum alpha | 223 / 1.000 | 223 / 1.000 |

Note the collision: `1º Turno` enters the top-five alpha table **and** is one of the
topics that now fails the balance test.

Deck claims touching these numbers: `app:rotemberg`, `app:exposure`, `src:pretrend`.

---

## Defect 2 — `broader_treatment`

| Spec | Before | After |
|---|---|---|
| baseline | 0.0615 (0.0230) p=.0131, F=102.29 | unchanged |
| broader_treatment | 0.0615 (0.0230) p=.0131, F=102.29 — *identical to baseline* | **6.5421 (47.0162) p=.891, F=0.018** |
| base_conditioned | did not exist | **6.4850 (46.2177) p=.890, F=0.018** |

Repairing the no-op did not produce a robustness check. It produced a **first-stage
collapse**: F falls from 102.3 to 0.018 and the coefficient explodes to 6.5 with a
standard error of 47.

Why: Z = (2020 topic shares) × (national shock), so Z is a deterministic function of
the 2020 litigation base. Conditioning on the log 2020 level removes essentially all
of Z's variation. The endogenous variable is itself a difference,
`log1p(L_2024) − log1p(L_2020)`, so the control is an **endpoint of the treatment** —
the treatment-side mirror of defect 1, where the problem was an endpoint of the
*outcome* sitting in the control matrix.

That symmetry is the reason to read this as diagnostic rather than falsification: a
shift-share design cannot survive conditioning on its own exposure, and no shift-share
paper reports such a spec as a robustness check. What it does establish, cleanly, is
that **the instrument has no power orthogonal to the 2020 litigation base**. That is
the same fact the zero-exposure table already shows from the other direction:

| Sample | N | First-stage F | Margin coef | p |
|---|---|---|---|---|
| Full | 5,560 | 102.29 | 0.0615 | .013 |
| Positive 2020 litigation | 4,414 | 1.118 | 0.523 | .413 |
| Nonzero instrument | 4,412 | 1.111 | 0.514 | .419 |

Identification is entirely the extensive margin — zero-versus-any 2020 adversarial
filing. `base_conditioned` is the parametric statement of the same thing.

---

## Defect 3 — candidate-history deltas

### The variables are now differences

| Column | Before (nonzero / mean) | After (nonzero / mean) |
|---|---|---|
| `new_candidate_share_2020` (exec) | 0 / 0.0000 | 5,211 / 0.6546 |
| `new_candidate_share_2024` (exec) | 5,035 / 0.6341 | 5,035 / 0.6341 (unchanged) |
| `incumbent_candidate_share_2020` (exec) | 0 / 0.0000 | 3,223 / 0.2076 |
| `incumbent_candidate_share_2024` (exec) | 2,833 / 0.2197 | 2,833 / 0.2197 (unchanged) |
| `new_candidate_share_2020` (leg) | 0 / 0.0000 | 5,560 / 0.6698 |
| `incumbent_candidate_share_2020` (leg) | 0 / 0.0000 | 5,554 / 0.1323 |

The 2024 terms are byte-identical, which is the required check: the fix dates 2020
against 2016 and leaves 2024-against-2020 exactly as it was.

### Estimates

| Outcome | Before | After |
|---|---|---|
| Exec Δ new-cand. share | 0.0142 (0.0293) p=.632 | 0.0298 (0.0506) p=.561 |
| Exec Δ incumbent-cand. share | −0.0064 (0.0234) p=.788 | −0.0081 (0.0351) p=.819 |
| **Leg. Δ new-cand. share** | **−0.0017 (0.0078) p=.828** | **+0.0217 (0.0118) p=.078** |
| Leg. Δ incumbent-cand. share | 0.0009 (0.0056) p=.869 | −0.0089 (0.0064) p=.176 |
| Estimation N | 5,560 | 5,560 |

The executive arms stay null with wider standard errors — expected, since a
difference carries more variance than a level.

**The legislative new-candidate share flips sign and becomes marginal.** It was a
tight zero (−0.002, p=.83); it is now +0.022 with p=.078. Direction: more
adversarial litigation, more first-time candidates in the council race. Both
legislative coefficients flip sign, and the incumbent arm moves from a precise zero
to −0.009 (p=.176).

This is a Leveling-direction result on the side FRAMING currently tiers as
*"Precise null … the entire legislative side."* At p=.078 it is not a finding, but
"precise null" is no longer an accurate description of that cell.

### Table footer repaired

`legislative_iv_candidate_pool.tex`, `Mean of dep. var.` row:

| Column | Before | After |
|---|---|---|
| Δ New candidate share | 0.613 (a 2024 level) | −0.057 (= 0.6129 − 0.6698) |
| Δ Incumbent share | 0.157 (a 2024 level) | 0.025 (= 0.1571 − 0.1323) |

---

## Two plan predictions that were wrong

- The plan expected N to rise by 6 once `share_career_politicians_2020` left
  `ROBUSTNESS_CONTROLS`. It did not — N is 5,560 before and after. `complete.cases`
  was already binding on other controls.
- The plan expected the 2024 candidate-share means near 0.79 and 0.14. The real
  values are 0.6341 and 0.2197. The check that mattered — 2024 unchanged — passed.

---

## What still needs Nara's call

1. **`src_findings.tex:9` and the `FRAMING.md` tier table** claim the margin clears
   Holm and BH at 5%. `multiplicity_adjusted.csv` gives Holm .2365 / BH .1435 and
   `\MultHolmSig 0` over the committed 18-outcome family. Re-running changed nothing
   here; the contradiction is unaffected by these fixes and `app_multiplicity`
   already tells the honest version.
2. **The legislative "precise null" tier**, given +0.0217 (p=.078) on new candidates.
3. **How `broader_treatment` / `base_conditioned` are reported.** They are now real
   specs that collapse the first stage. My reading is diagnostic-not-falsification
   (conditioning on an endpoint of the treatment), but that argument has to be made
   explicitly wherever the spec appears, or the row reads as a failed robustness check.
4. **Whether the four failing balance topics get disclosed on `src:pretrend`.** The
   frame currently says the consolidation measures are pre-trend clean, which the
   outcome-level test still supports; this is a *share*-level failure, a different
   test, and one that until today could not fail.
5. **The open-seat pre-trend placebo** (0.120, p=.047) exceeding the open-seat effect
   (0.0765, p=.047), which bears on FRAMING D5. Unaffected by these fixes.

---

## A fourth defect, found by the verification step

Re-running `code/utils/audit_pipeline.py` reported 6 archive candidates, 33 orphan
figures/tables and 105 build breakers — including files the deck visibly uses. All
false. `documents()` globbed `output/presentation/*.tex` non-recursively, and the
decks were refactored this session into a frame library
(`output/presentation/frames/*.tex`, one file per frame) with the drivers reduced to
`\input` lists. The audit was reading the drivers, seeing no `\includegraphics`
anywhere, and declaring the entire output tree orphaned. The build-breaker check had
the mirror bug: it resolved `\input{frames/src_x}` by *stem* against
`output/presentation/`, so every frame read as missing.

Fixed both: recurse into subdirectories, and resolve an `\input` target relative to
the directory of the file that includes it. The audit now reports:

| Section | Before the tool fix | After |
|---|---|---|
| Archive candidates | 6 | **0** |
| Orphan outputs | 33 | **0** |
| Build breakers | 105 | **1** |
| Unreferenced CSVs | 14 | 10 |

The one surviving breaker is real and pre-existing:
`output/paper/extended_abstract.tex` calls `../figures/forest_voter_behavior.pdf`,
a figure that no longer exists under any name (the closest, `voterbehavior_forest.pdf`,
is itself deleted in the working tree). That file is Nara's to edit — flagged, not
touched.

---

## Scripts re-run

Build: `02_shift_share_design.py`, `04_candidate_history.py`, `03_vote_outcomes.py`.
Estimation: `01_assemble_design.py`, `01b_assemble_legislative_design.py`,
`02_iv_main.R`, `02b_iv_legislative.R`, `04`, `05`, `06`, `07`, `09`, `10`, `11`,
`12`, `13`.
Analysis: `01_descriptives.py`, `03_result_figures.R`, `04_iv_diagnostics.py`,
`07_exposure_robust_se.R`, `09_summary_statistics.R`, `10_candidate_rank_profile.py`,
`06_abstract_macros.py`.

`03_vote_outcomes.py` was not in the plan's re-run list and had to be added:
`01_assemble_design.py` reads `executive_vote_shift_share_design.csv`, which that
script owns, so the first reassembly silently carried the old zero-valued 2020
columns through.
