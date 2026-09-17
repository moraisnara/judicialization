# Toy model — design

Date: 2026-09-17
Status: design approved, not yet implemented
Scope: a companion theory model for the judicialization shift-share IV paper
("When It Gets to Court: The Electoral Costs of Judicialization")

## 1. Purpose

`app:theory` currently *asserts* the Leveling/Barrier dichotomy and the
seat-conditional prediction. The model's job is to **derive** them from
primitives, so that D3 (H1/H2 non-separability), D4 (the ballot, not
concentration, is the discriminator) and D5 (the open/contested split is the
identifying test) become results rather than framing choices.

The model is an organizing device. It produces signs and orderings. It is not
calibrated, not structurally estimated, and implies no new estimation to
support the existing results.

It is built as **A' — noise model vs. transfer foil**: open by proving that the
transfer class (Nakaguma–Souza 2023) cannot generate the headline under the
attack direction that paper itself documents, then build the noisy-arena model
that can. Two levels of discrimination: the **margin** separates transfer from
noise; the **ballot** separates Leveling from Barrier.

## 2. Target facts

Every number below is an existing estimate from
`output/tables/tex/abstract_macros.tex` and
`output/tables/tex/executive_iv_heterogeneity_seat.tex`. The model must
reproduce the signs and the orderings; it must not require any of the nulls to
become non-null.

### Pooled (N = 5,560; first stage F = 102.3)

| Outcome | Coef | p | 2024 mean |
|---|---|---|---|
| Top-two margin | +0.062 (0.023) | .013 | 0.270 |
| Winner vote share | +0.031 (0.013) | .027 | 0.607 |
| Runner-up vote share | −0.032 (0.012) | .016 | 0.337 |
| Winner majority (>50%) | +0.057 (0.036) | .124 | 0.832 |
| Blank-vote rate | +0.003 (0.002) | .095 | 0.016 |
| Null-vote rate | +0.003 (0.002) | .120 | 0.027 |
| Valid-vote rate | −0.007 (0.006) | .277 | 0.792 |
| Effective N candidates | −0.044 (0.039) | .269 | 2.021 |
| HHI | +0.023 (0.013) | .088 | 0.527 |
| Executive candidate supply | −0.007 (0.016) | .677 | — |
| Turnout | −0.002 (0.004) | .568 | 0.835 |
| Winner gender gap | −0.048 (0.031) | .129 | — |

### Seat split

| Outcome | Open (N=2,026, F=18.6) | Contested (N=3,534, F=65.1) |
|---|---|---|
| Top-two margin | +0.076 (0.037), p=.047 | +0.068 (0.024), p=.010 |
| Winner vote share | +0.039 (0.020), p<.10 | +0.033 (0.013), p<.05 |
| Winner majority | +0.160 (0.081), p=.059 | +0.011 (0.033), p=.737 |
| Blank-vote rate | +0.001 (0.002), p=.571 | +0.005 (0.002), p=.035 |
| Null-vote rate | +0.004 (0.003) | +0.003 (0.002) |
| Valid-vote rate | +0.004 (0.009), p=.645 | −0.013 (0.007), p=.084 |
| Margin pre-trend | +0.120, p=.047 (**fails**) | +0.004, p=.905 (passes) |

### Council (open-list PR), same municipalities

Blank 0.000 (0.001) · Null 0.000 (0.001) · Valid −0.003 (0.005) ·
Council candidate supply +0.021 (0.032), p=.515.

## 3. Primitives

One mayoral race. Candidates `j = 1, …, J` indexed by pre-shock support
`s°_1 ≥ s°_2 ≥ … ≥ s°_J`. A continuum of voters of mass 1.

Voter `i`'s payoff from candidate `j`:

    u_ij = θ̂_j − (ρ/2)·V̂_i(θ_j) + ε_ij

- `θ_j` — common-value valence, unobserved.
- `ε_ij` — fixed idiosyncratic taste, known to the voter.
- Prior `θ_j ~ N(m_j, 1/h_j)`: `m_j` is reputation, `h_j` is how settled the
  record is. Incumbents have high `h`; fresh candidates low `h`.
- `b̄` — the reservation payoff from a blank or null vote: what refusing to
  endorse anyone is worth once the instrumental value of the ballot is gone.

Treatment `λ` — adversarial filing intensity in the race. This is the object the
Bartik instrument shifts. Candidate registration closes before filings land
(registration 15 August; adversarial filings run through October), so entry is
**predetermined by construction**, not by assumption.

Voting is compulsory (CF/88 art. 14 §1). The margin of adjustment is therefore
the *mark* (valid / blank / null), not attendance.

## 4. Proposition 1 — the transfer foil

### 4.1 The transfer map

Nakaguma–Souza's model, including the Appendix G.2 demobilization extension. An
attack from `k` to `j` moves a fraction `φ` of `j`'s support away; a fraction
`α` of that mass exits to the outside option rather than reaching `k`; and the
attacker loses a fraction `γ` of its own support to backlash.

### 4.2 Their equilibrium and their evidence

Theory: every candidate targets their **highest-ranked opponent**. So in a
three-candidate race the equilibrium profile is `1→2`, `2→1`, `3→1` — mutual
between the top two, plus the third attacking the leader.

Evidence (their Figure 1 / B.2, Brazilian electoral lawsuits — the same
institutional data family we use): in three-candidate races the observed
frequencies are `2→1` 3.0pp, `1→2` 1.9pp, `3→1` 0.8pp. The second-place
candidate is the most aggressive; the front-runner is the most attacked.

### 4.3 The result

> **Proposition 1.** Under mutual `1↔2` attacks, the transfer map scales the
> top-two margin by a factor strictly less than one:
>
>     s_1 − s_2 = (s°_1 − s°_2) · [1 − γ − φ(2 − α)]
>
> for all `φ ∈ (0,1)`, `α ∈ [0,1]`, `γ ∈ [0,1)`. Adding `3→1` subtracts a
> further `φ·s°_1`. The margin therefore **weakly narrows**, and can only widen
> in absolute value by overshooting — which reverses the winner.

The proof is two lines of algebra; no grid search is needed and the earlier grid
check is superseded.

Widening with the winner preserved requires a **one-sided downward** attack
(`1→2` with no reciprocation), which their equilibrium excludes and their data
does not show. Their per-pair attack frequencies are 1–3pp, so the transfer
channel is in any case too small to move municipality-level shares by 3pp.

**Conclusion.** The consolidation result cannot come from candidate-to-candidate
transfer. Something race-level is doing the work.

### 4.4 Scope condition, stated up front

The top-two margin is an **order statistic**: any mean-preserving increase in
the dispersion of vote shares widens it mechanically. Proposition 1 rules out
the transfer channel under the documented attack direction. It does **not** by
itself rule out generic dispersion. What rules out generic dispersion is the
ballot response and the seat asymmetry — a dispersion shock predicts neither,
and predicts no directional flow from #2 to #1.

## 5. What a filing emits

A filing carries two signals with very different precisions.

**Type signal** about `θ_j`. The filing is an allegation: informative with
probability `π` (H1, genuine information about the candidate), pure noise with
probability `1 − π` (H2, weaponization). The voter cannot tell which, so the
effective precision is `τ̄ = π·τ_I`, which is low. The posterior mean is

    θ̂_j = (h_j·m_j + τ̄·s_j) / (h_j + τ̄)

This is **D3 formalized**: H1 and a sticky H2 enter the voter's posterior
through the same reduced-form parameter `τ̄`, so they are not separable for the
voter, and therefore not separable for the econometrician. The non-separability
is a derived property of the environment, not a limitation of the design.

**Status signal** about rank. The filer is optimizing and targets their
highest-ranked opponent (Proposition 1's premise, now used constructively).
So *who gets sued* is informative about *who is ahead*. Precision is high — the
filer knows the race — and it is reinforced by the local attention a court case
attracts.

> **The one-line result.** Judicialization is precise about position and
> imprecise about quality. It reveals the horse race, not the horse.

## 6. Propositions 2 and 2b — consolidation

> **Proposition 2.** As `λ` rises, rank moves toward common knowledge while
> valence beliefs barely update. In a top-two coordination equilibrium
> (Myerson–Weber pivot logic), mass flows from #2 to #1. The winner's identity
> is unchanged and the field does not shrink.

Matches: margin +0.062, winner share +0.031, runner-up −0.032, candidate supply
null (−0.007, p=.677), winner gender gap null (−0.048, p=.129).

The entry null is *structural* here, not a coincidence: the status signal
arrives after the registration deadline, so it cannot act on the candidate set.

> **Proposition 2b.** When the shift is a one-parameter top-two reallocation,
> every summary concentration index is a monotone function of that same
> parameter and carries no restriction independent of the margin.

Consistency check. The margin estimate implies ΔENP = −0.073 and ΔHHI = +0.018;
the estimates are −0.044 (0.039) and +0.023 (0.013). Both within one standard
error of the implied value, and both informationally redundant.

This gives **D4 a derivation instead of an assertion**: concentration cannot
identify a face because it is the margin restated.

## 7. Propositions 3 and 4 — exit and the seat split

> **Proposition 3.** A #2 supporter who learns the race is not close faces a
> collapsed pivot probability, so the choice becomes expressive: mark #1 if
> `θ̂_1 + ε_i1 ≥ b̄`, otherwise mark blank. Under compulsory voting the exit
> option is a blank or null vote, not abstention — which is why turnout is
> unmoved (−0.002, p=.568).

> **Proposition 4 (the seat split).** #2 loses a similar mass in both seat types
> (2.8pp open, 3.2pp contested). What differs is where it goes: to #1 where the
> revealed leader is a fresh face, off the valid ballot where the revealed
> leader is an incumbent with committed opponents.

Two primitives differ across seat types, and both push the same way.

1. **Prior precision `h_1`.** In a contested seat #1 is the incumbent: `h_1` is
   high, so `θ̂_1 ≈ m_1` and the type signal moves nothing. In an open seat #1
   is a fresh candidate with diffuse reputation and genuinely unresolved rank,
   so the status signal has more to resolve and coordination is stronger.
2. **Selection on `ε_i1`.** Supporting the challenger *against a sitting mayor*
   is itself evidence of a settled negative view of that mayor. The distribution
   of `ε_i1` among #2 supporters is first-order dominated in contested seats, so
   a larger mass sits below `b̄` and exits. An open-seat front-runner has not
   been in office long enough to accumulate committed opponents.

Hence: margin roughly flat across seat types (+0.076 vs +0.068) while the
ballot is not (blank +0.001, p=.571 vs +0.005, p=.035), and majority crossing is
open-only (+0.160, p=.059 vs +0.011, p=.737).

### 7.1 The implied decomposition

Converting the seat table from shares-of-valid into shares of registered voters
(so that the columns must sum to zero) gives:

| | #1 | #2 | blank/null | others | turnout |
|---|---|---|---|---|---|
| Open | **+3.3pp** | −2.8pp | +0.5pp | −0.1pp | **+0.9pp** |
| Contested | **+1.8pp** | −3.2pp | +0.8pp | +0.1pp | **−0.5pp** |

The two rows describe different events, and this is the sharpest statement of
the Leveling/Barrier contrast the data supports.

- **Open seats: mobilization toward the leader.** #1 gains 3.3pp, *more* than #2
  loses (2.8pp); the balance comes from a 0.9pp rise in turnout. Nothing leaves
  the ballot. Hence the majority crossing.
- **Contested seats: withdrawal.** Of the 3.2pp leaving #2, 1.8pp reaches #1,
  0.8pp becomes a blank or null vote and 0.5pp abstains — so 1.3pp, about 41%,
  exits the valid ballot entirely. Hence no majority crossing.

Three caveats, all of which the memo must carry:

1. This is arithmetic on separate point estimates with **no propagated standard
   errors**. It is an implication, not a result. Estimating it jointly (delta
   method or bootstrap over the seat fits) is an optional follow-up, explicitly
   outside this design's scope.
2. The seat table reports only **pooled** 2024 means (winner 0.607, runner-up
   0.337, valid 0.792), so those are used for both subsamples. Subsample means
   would shift the levels somewhat.
3. The open-seat row rests on the estimate that **fails its pre-trend** (§9).
   The contested row is the pre-trend-clean one. The visually stronger half of
   the contrast is the empirically weaker half, and the memo must say so where
   the table appears, not only in a caveats section.

## 8. Out-of-sample predictions

1. **Council (open-list PR).** A large field with no focal two-horse rank gives
   the status signal nothing to coordinate on, and a single candidate's filing
   carries no information about the seat-allocation margin. Prediction: no
   consolidation, no ballot response. Observed: council blank 0.000, null 0.000,
   valid −0.003 (0.005), candidate supply +0.021 (p=.515).
2. **Turnout.** Compulsory voting means adjustment happens on the mark, not on
   attendance. Observed: −0.002 (p=.568).
3. **Candidate entry.** Filings post-date registration, so there is no supply
   response. Observed: −0.007 (p=.677).

## 9. Confidence discipline

The model must not upgrade any result past its FRAMING tier.

- **Consolidation (Robust).** Margin pre-trend passes (p=.137); AR p=.015;
  RF Holm p=.015, BH p=.011.
- **Withdrawal in contested seats (Tentative).** Blank pre-trend passes
  (p=.148), BHJ p=.028, AR p=.108. The **valid-vote pre-trend fails**
  (p=.012), so the model leans on blank and treats valid as corroborating, not
  load-bearing.
- **Open-seat branch (Exploratory).** The open-seat margin **fails its
  pre-trend** (p=.047) while contested passes (p=.905). The majority-crossing
  and "all losses land on the winner" branch is therefore the *weaker* one, not
  the stronger one, and the memo must say so plainly.
- **Male front-runner incidence (Exploratory).** Male winner share +0.039
  (p=.042) but the gender gap itself is null (p=.129). The model makes no
  gendered prediction and must not be read as supporting one.

## 10. Out of scope

- No calibration, no structural estimation, no new estimation to support
  existing results.
- No separation of H1 from H2 — the non-separability is a derived feature.
- The filer's decision is **not** endogenized. Attack direction is taken from
  Nakaguma–Souza as a cited maintained assumption, because endogenizing it
  requires exactly the selection the instrument exists to sidestep.
- No judges. Judicial behavior belongs to the `judicial_bias` paper.
- No welfare claim. The model says nothing about whether consolidation is good.
- Runoff municipalities (over 200k registered voters, two rounds) are a stated
  scope condition, not modeled.
- `FRAMING.md` stays locked. Where the model bears on D1–D5 it goes in the
  apply-to-the-paper sheet as a proposed amendment, never as an edit to the
  locked memo.

## 11. Artifacts

| Artifact | Path | Contents |
|---|---|---|
| Model memo | `docs/model/theory_model.tex` (+ PDF) | Full statements and proofs, including the closed-form proof of Prop. 1 |
| Theory appendix frames | `output/presentation/frames/app_theory.tex` (rewritten) plus two new frames | The two signals; the transfer foil; the ballot decomposition |
| Main-deck frame | beside `output/presentation/frames/src_twofaces.tex` | One frame: "position, not quality" |
| Apply sheet | `docs/PAPER_APPLY_model.md` | What changes in the paper's theory section, for Nara to write |
| Citations | `output/presentation/biblio.bib`, `references.bib` | New theory entries (§12) |

Nara writes the paper. No prose goes into `output/paper/paper.tex` or
`output/paper/extended_abstract.tex`.

## 12. Citations to add

To be verified in `C:\Users\naral\Zotero` before any web search.

- Myerson & Weber — voting equilibria, coordination on focal contenders.
- Fey — informational cascades and strategic coordination in plurality races.
- Cox, *Making Votes Count* — Duverger's law as a coordination result.
- Anagol & Fujiwara — the runner-up; salience of rank information.
- Ghirardato & Katz — ambiguity and the decision to abstain (blank as a hedge).
- Feddersen & Pesendorfer — the swing voter's curse (voting on low-precision
  signals).

Already in `biblio.bib`: `nakaguma2025`, `chin2025`.

## 13. Risks and open items

1. **Chin et al. reconciliation.** They find no large *candidate-level* effect
   of individual lawsuits. That is awkward for a transfer model and natural
   here: the model's channel is race-level intensity changing how every voter
   weights every signal, not a per-lawsuit penalty on the defendant. State this
   explicitly; it is a feature, and it is free.
2. **Win probability vs. vote-share margin.** Nakaguma–Souza's object is a win
   probability through a logit contest function; ours is a vote-share margin.
   Both are monotone in `s_1 − s_2`, but Proposition 1 must say so rather than
   assume the mapping.
3. **The FD null.** The first-difference specification gives a margin null
   (−0.007, p=.822) against the ANCOVA headline (+0.062). This is the documented
   ANCOVA-vs-FD decision, not a new problem, but the memo must not write as
   though the result is specification-invariant.
4. **Open-seat pre-trend.** See §9. The branch of the model with the most
   visually striking prediction rests on the weaker estimate.
5. **Coordination needs a two-horse race to be focal.** Municipalities with a
   genuinely three-way race weaken the mechanism. The model states this as a
   condition; testing it would need a new subsample split and is out of scope.
