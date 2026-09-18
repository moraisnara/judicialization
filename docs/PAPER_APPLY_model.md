# Apply to the paper — the companion theory model

Built 2026-09-17. Source: `docs/model/theory_model.tex` (compiled PDF beside it).
Spec: `docs/superpowers/specs/2026-09-17-toy-model-design.md`.

Claude owns the deck and this sheet. The paper prose is yours. This lists what
the model changes about the paper's argument and what to copy where.

## 1. The theory section now has a result to state

The paper's theory section currently asserts the Leveling/Barrier dichotomy.
The model derives it, and it derives three other things the paper states as
assumptions:

| Paper currently asserts | Model derives it as |
|---|---|
| H1 and H2 are observationally non-separable (D3) | Both enter the posterior through one parameter, the effective precision of the type signal |
| Concentration does not identify a face (D4) | Prop. 3: concentration indices are monotone functions of the same top-two reallocation parameter |
| The open/contested split is the identifying test (D5) | Prop. 5: the prior's precision and the selection of an incumbent's opponents determine whether the runner-up's support joins the leader or leaves the ballot |
| The candidate-supply and turnout nulls | Structural: registration closes before filings land; voting is compulsory |

*Correction from the brief: the D4 row cites Proposition 3 ("Concentration
indices are redundant," `docs/model/theory_model.tex:523`), not Proposition 2.
The D5 row cites Proposition 5 ("The seat split," `docs/model/theory_model.tex:714`),
not Proposition 4 (Proposition 4 is "Exit," `docs/model/theory_model.tex:576` —
the blank-vote result, a different proposition). The memo's proposition order is
1 Transfer foil (L143), 2 Consolidation (L469), 3 Concentration (L523), 4 Exit
(L576), 5 Seat split (L714); see this sheet's verification note below.*

## 2. The one new claim

The paper can now open its theory section by ruling out the obvious
alternative rather than ignoring it. Proposition 1: in the transfer class of
campaign-attack models, under the equilibrium attack direction those models
derive and document, the map contracts the top-two margin. The consolidation
result cannot come from candidate-to-candidate transfer.

This is a positive contribution and it costs nothing, because Nakaguma and
Souza measure attacks on Brazilian electoral lawsuits — the same institutional
data family.

## 3. The reconciliation with Chin et al.

They find no large candidate-level effect of individual lawsuits. That is
awkward under a transfer model and natural here: the channel is race-level
intensity changing how every voter weights every signal, not a per-lawsuit
penalty on the defendant. Worth one sentence in the literature discussion.

## 4. Bibliography

Six entries were added to `output/presentation/biblio.bib` and are not yet in
`output/paper/references.bib`, which is still a stub. Copy them across when the
paper's bibliography starts:

`myerson1993`, `fey1997`, `cox1997`, `anagol2016`, `ghirardato2006`,
`feddersen1996`.

## 5. Proposed amendment to FRAMING.md

`FRAMING.md` is locked, so this is a proposal, not an edit.

D4 currently states that concentration does not identify a face. Proposition 3
gives that a reason: when the shift is a one-parameter reallocation between the
top two, every concentration index is a monotone function of that parameter, so
even a precise concentration estimate would be the margin restated. If D4 is
ever reopened, that sentence belongs in it. This is the only place this sheet
proposes touching D4's statement; D4 is not restated anywhere else in this
document, and this sheet does not instruct the paper to state D4 a second time.
`FRAMING.md:117-119` already requires D4 to appear "once, early," with every
later face-assignment referring back to it, and `FRAMING.md:274-283` fixes
where that sits in the introduction — this sheet defers to both and adds
nothing to either.

Unrelated to the model, and noted while reading: `FRAMING.md` uses the word
"concentration" loosely at the D4 header (`FRAMING.md:104`) and in the D5 table
(`FRAMING.md:130-133`), where the vocabulary lock requires "consolidation".
Left unedited because the memo is locked. (The brief this sheet was built from
cited these as L103 and L129--132; the file's actual current line numbers are
104 and 130--133, one line later throughout — corrected here.)

## 6. What the model does not license

- No calibration and no structural estimation. The model gives signs and
  orderings.
- **The open-seat branch is the weaker half of the seat contrast**, which is
  the opposite of how it reads. In open seats nothing on the ballot moves
  (blank p=.571, null p=.232, valid p=.645, turnout p=.076), the top-two moves
  are marginal (winner p=.061, runner-up p=.062), every coefficient fails tF,
  and the margin fails its pre-trend (p=.047, against p=.905 for contested).
  The contested branch is the one that carries weight: winner p=.018,
  runner-up p=.019 and blank p=.035 all clear weak-IV inference.
- **Do not write the open-seat turnout rise as a finding.** It is +0.9pp with
  p=.076, it fails tF, and the pooled turnout reduced form fails its pre-trend
  (p=.007). The model does not need it: the open-seat prediction is that
  nothing leaves the ballot, and a null ballot response is what confirms that.
- The ballot decomposition in `app_ballotdecomp` is arithmetic on separate
  point estimates with no propagated standard errors. The three valid-vote
  shares should sum to zero and miss by −0.42pp (open) and +0.27pp
  (contested), because each outcome is fit on its own non-missing sample —
  which is the same order as the "others" entry, so that column is not
  interpretable. If the decomposition goes in the paper as a table it needs a
  joint estimate: delta method, or a bootstrap over the seat fits. Out of
  scope here deliberately.
- The first-difference specification still gives a margin null (−0.007,
  p=.822) against the ANCOVA headline. The model explains the ANCOVA-identified
  pattern and does not make the result specification-invariant.
- **The exit column of that same table is a selected p-value, not a joint
  test.** `app_ballotdecomp.tex` prints `\DecompOpenExitP` (0.232) and
  `\DecompContExitP` (0.035) as the "Blank/null" column's significance, and
  each is `min(blank_p, null_p)` (`code/04_analysis/06_abstract_macros.py:463`)
  — the more significant of two dependent one-sided tests, not a p-value for
  a joint blank-or-null hypothesis. If the paper reports 0.232 or 0.035, it
  must describe them the same way: a selection over two tests, never as
  though a single joint test were run.

## 7. Three out-of-sample tests the model already passes

None of these is a new estimate. They are existing coefficients that the model
predicted before it was written, and they belong in the theory section as
discipline rather than in the results.

1. **The council race.** The mechanism needs a focal rank for the status signal
   to reveal, which an open-list proportional race does not offer. On the
   council ballot nothing moves: blank +0.0005 (0.001) p=.455, null +0.0002
   (0.001) p=.812, valid −0.0030 (0.005) p=.535. Mayoral and council ballots
   are counted in the same polling place on the same day, so a general
   discouragement story would have to move both.
2. **Candidate supply.** The status signal arrives after registration closes on
   15 August while filings run through October, so the candidate set cannot
   respond. Council candidate supply is +0.0211 (0.032) p=.515.
3. **Turnout.** Compulsory voting turns the exit option into a blank or null
   vote rather than an abstention, so the model predicts exit on the ballot
   with turnout unmoved. Do not lean on this one as confirmation: the pooled
   turnout reduced form fails its pre-trend (p=.007), so the null is not
   cleanly interpretable. The prediction is stated; the test is weak.

Two council results do move — mean candidate age −0.317 (0.130) p=.022 and the
elected female share +0.0225 (0.010) p=.036 — and the model says nothing about
either. They are not evidence for it and should not be recruited as such.

## 8. One bug fixed in passing

`code/04_analysis/06_abstract_macros.py` was missing
`delta_others_vote_share_2024_2020` from its `ANCOVA_LEVEL` dict, although
`code/03_estimation/02_iv_main.R` estimates that outcome as ANCOVA on
`others_vote_share_2016`. Any macro reporting that outcome's dependent-variable
mean would have shown a delta mean (near zero) instead of the 2024 level
(about 0.06). No macro read it, so nothing published was wrong; the entry was
added because the decomposition needs the level. Worth knowing if an "others
share" row is ever added to a table.

## 9. A data defect found while checking the model, harmless to what is published

Nine municipalities in `data/estimation/executive_margin_design.csv` carry
`winner_vote_share_2024 = 0` and `effective_n_candidates_vote_2024 = 0`, which
cannot happen -- every municipality holds a mayoral race. Their
`delta_effective_n_candidates_vote_2024_2020` runs from -1.00 to -4.28, against
an estimated coefficient of -0.044.

They are inside the baseline estimation sample. They do not corrupt the
published coefficients, because the headline spec is ANCOVA on the 2016
baseline: the left-hand side is the bounded 2024 level (0 for these rows), and
the exploding delta column is only one of the columns `build_sample()` gates on
with `complete.cases`, never the modeled outcome. Dropping the nine moves the
effective-N estimate from -0.044 (0.039) to -0.050 (0.041) and the HHI estimate
from +0.0229 (0.0129) to +0.0214 (0.0123): same signs, no significance flip,
the concentration null stands either way.

Two things follow. The zeros should be fixed at the source in
`code/02_build/03_vote_outcomes.py` rather than filtered downstream, since any
future spec that models the delta directly would be badly contaminated. And the
11 rows the baseline sample does drop are dropped for an unrelated reason -- all
four 2010 Census controls are missing, mostly post-2010 emancipations plus
Brasilia and Fernando de Noronha -- so the 5,560 count matching the model
check's 5,560 is a coincidence of arithmetic, not the same set of
municipalities.

## 10. Three binding limits on Proposition 5 (the seat split)

Proposition 5 is the theoretical support for D5 and for the "withdrawal in
contested seats" claim. It is narrower than a first read suggests, in three
ways the paper needs to carry every time it cites the seat split.

1. **It compares two races, not one race over time.** The proof holds the
   leader's realized posterior mean `θ̂₁` at a common value across seat types
   and compares "two races that share a realized leader standing and differ
   only in whether an incumbent is running" (`docs/model/theory_model.tex:760-761`).
   It is a between-race statement conditional on that shared realization, not
   a claim about what happens inside one municipality as judicialization
   rises, and not an unconditional claim across realizations — the memo says
   this explicitly: "Neither averages over the prior on valences"
   (`docs/model/theory_model.tex:848-850`).
2. **It holds outright only at a common blank-vote threshold, ρ = 0.** Above
   that, the ambiguity term raises the blank rate in both kinds of seat and,
   because the posterior variance of the leader's valence is largest exactly
   where the prior precision `h₁` is smallest, the penalty is heaviest in the
   open seat — the opposite of where the model predicts less blanking. "The
   prediction therefore holds outright at ρ = 0 and, for ρ > 0, requires the
   selection effect of Lemma [Selection] to dominate that differential
   penalty" (`docs/model/theory_model.tex:782-785`).
3. **It rests on the second half of Assumption 1** (Impressions,
   `docs/model/theory_model.tex:84`) — that pre-campaign impressions sort
   voters into camps but are washed out of the ballot-stage payoff. Without
   it, "the selected object in Lemma [Selection] would be the composite
   `ε_i1 + ζ_i1` rather than `ε_i1`, and the selection would reverse"
   (`docs/model/theory_model.tex:817-824`): the prediction flips, it does not
   just weaken.

None of this changes the tiers. Consolidation (Proposition 2) stays **Robust**;
withdrawal in contested seats (Proposition 5, contested branch) stays
**Tentative**; the open-seat branch stays **Exploratory** because its margin
fails its pre-trend (p=.047 vs p=.905 for contested — §6 above). `FRAMING.md`
already states that the finding is robust and the face assignment is
tentative (`FRAMING.md:163-165`); the model does not upgrade that — if
anything, limit 1 and limit 2 above are further reasons the interpretation
stays tentative.

## 11. What the memo itself flags as assumed, not derived

`docs/model/theory_model.tex`, Section 6 ("What the model does not do",
`docs/model/theory_model.tex:797-798`) names six steps the model asserts
rather than proves. The paper should not claim more certainty for these than
the memo does:

1. **The attack direction.** Taken from Nakaguma (2025) as a maintained
   assumption; both the status channel (Section 3) and Proposition 1's foil
   rest on it (`docs/model/theory_model.tex:811-813`).
2. **Assumption 2 (the noisy arena),** `docs/model/theory_model.tex:288-292`,
   is the entire modeling content of the consolidation section: nothing in
   the memo shows that `λ` must push the type-signal precision down and the
   status-signal precision up — only that everything else follows if it does
   (`docs/model/theory_model.tex:814-817`).
3. **The second half of Assumption 1** (Impressions), that pre-campaign
   impressions wash out by the ballot stage — the same assumption limit 10.3
   above states for Proposition 5 specifically
   (`docs/model/theory_model.tex:817-824`).
4. **The identity of the departing set** in Proposition 5's proof: taking the
   movers to be candidate 2's camp (or a uniform subsample of it) is an
   assumption, not a consequence of Proposition 2, which moves mass between
   the top two without naming who moves (`docs/model/theory_model.tex:824-828`).
5. **The size of the departing mass.** Proposition 2 is derived at
   `h₁ = h₂ = h`; Proposition 5 turns on `h₁` differing by seat. Treating the
   departing mass as comparable across seat types is a further assumption,
   not something Proposition 2 delivers (`docs/model/theory_model.tex:828-833`).
6. **The coordination leg of Proposition 2** (mass flowing from the
   runner-up to the leader as rank becomes common knowledge) is imported from
   Myerson & Weber, Fey, and Cox rather than derived
   (`docs/model/theory_model.tex:833-835`).

## 12. Verification run for this sheet

`FRAMING.md` concentration usage, `output/paper/references.bib` entry count,
and the four macros this sheet cites all checked against the repository on
2026-09-17 and matched expectation (see the task's verification log). The
seven out-of-sample coefficients in §7 were re-read from
`output/tables/regressions/executive_margin_iv_fixest.csv` and
`legislative_iv_fixest.csv` and matched to four decimal places. The two
consistency-check numbers in §5 and in the spec's §6 were reproduced by
`docs/model/check_proposition3.py` (implied ΔHHI +0.0179 vs. estimated +0.0229;
implied ΔENP −0.0548 vs. estimated −0.0443; both inside the CI; 5,560
municipalities). `docs/model/check_proposition1.py` reproduced 18,050 profiles,
0 closed-form mismatches, 0 widenings.
