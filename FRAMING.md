# FRAMING.md — Locked Framing Decisions

**Status:** LOCKED, 2026-08-11.
**Supersedes:** `WRITING_GUIDE.md` §3 ("Reconcile the framing FIRST"), which is now resolved.
**Governs:** `output/presentation/slides_report.tex`, `output/presentation/slides_advisor.tex`,
and — as a reference for Nara's own drafting — `output/paper/paper.tex` and
`output/paper/extended_abstract.tex`.

This file records *what the paper claims and why*, so the decision is retrievable
months from now without re-deriving it. Estimates are not duplicated here: the
architecture lives in this file, the numbers live in
`output/tables/tex/abstract_macros.tex` (auto-generated). A few are quoted below
only where the architecture is unintelligible without them.

---

## The problem this resolves

Three artifacts encoded three different framings:

- **`extended_abstract.tex`** (lines 64–113) — litigation *grew* in volume; three
  causal channels (information / lawfare / direct judicial action); a bare "first
  causal estimates" claim.
- **`slides_report.tex`** — expanded role, flat volume; two faces (Leveling vs
  Barrier); a three-row mechanism collapse buried in `app:theory`.
- **`slides_advisor.tex`** — same two faces, but committing H1 to predicting
  *closer races*, which makes consolidation diagnostic on its own.

The last of these is the substantive disagreement, and `slides_report.tex`
contradicted *itself* on it: frame 2 marks competition `?`/"Open" under both faces
(L72, L85) while the same frame's closing line (L90) commits H1 to "disperses the
vote." The decisions below resolve all of it.

---

## D1 · Object of study: role, not volume

The paper estimates the effect of the **intensity of adversarial litigation a race
faces**, identified from **cross-sectional exposure** — never from a time trend.

Adversarial filings are roughly **flat** across 2020→2024 and **recompose** across
topics rather than rising. The SIG extract under-captures 2024 (coverage falls
78%→70%), so count *levels* are not cleanly measured and no volume trend is
reported anywhere; only coverage-robust shares.

**Diction ban:** no "grew", "surge", "wave", "rising judicialization", "increasing
litigation". The margin of interest is the judiciary's **expanded role** —
rule-making, weaponization, and the anticipation of both — of which observed
lawsuit counts are the visible tip.

*(This ratifies a standing project directive; it was already obeyed by the report
deck and violated by the extended abstract.)*

---

## D2 · Estimand boundary: direct judicial action is out by construction

Treatment is the **adversarial, candidate-vs-candidate core**. The administrative
eligibility and finance machinery — candidacy registration (RRC/DRAP), campaign
finance accounts (*prestação de contas*), tallying and poll-worker administration
— is **dropped by the filter**, and with it the mechanism by which courts
mechanically remove candidates and reallocate their votes.

**Disqualification-as-mechanism is therefore not what this paper estimates.** This
is stated as a **scope boundary**, flatly and once. It is *not* framed as a
hypothesis the paper tests and rejects, and it carries no hedge in prose.

Consequence: the extended abstract's three-channel scheme loses its third channel
here, not on evidence. See *Known exposures* below.

---

## D3 · Two mechanisms, and they do not separate

Past the D2 boundary, two mechanisms remain:

- **Information** — a filing reveals candidate type; courts sanction abuse;
  cleaner competitors advance.
- **Weaponization** — litigation as a campaign weapon, aimed up the ladder,
  judicially weak, media-amplified.

**They are observationally non-separable when the weapon persuades.** A true
accountability signal and a *sticky* strategic attack both move votes toward
someone. The paper does not claim to tell them apart.

What the design **can** separate is whether litigation moves votes *at all*, or
merely **fouls the contest without re-sorting**:

| Mechanism | Observable face |
|---|---|
| Information / accountability signal | **Leveling** — votes re-sort |
| Weaponization that *sticks* (persuades) | **Leveling** — indistinguishable from the above |
| Weaponization that only *fouls* | **Barrier** — blank/null ↑, valid ↓, no re-sorting |

This is the argument currently sitting in `app:theory`. It is **promoted from
appendix to the core of the framing** — it is the reason the paper's dichotomy is
Leveling/Barrier rather than information/weaponization.

**Terminology:** "weaponization", never "lawfare".

---

## D4 · The discriminator is the ballot, not concentration

**Concentration does not identify a face.**

- **Barrier** predicts it: costs concentrate power toward the entrenched.
- **Leveling** is *ambiguous* on it: more credible entrants could sharpen a race,
  or could merely weed out weak names. Felled front-runners could equally scramble
  the field.

The report deck already conceded this with the `?` bullets in frame 2 — the
concession was simply buried, and contradicted by the frame's own closing line and
by the advisor deck's Layer-3 claim.

**What discriminates is the ballot**: withdrawal (blank ↑, null ↑, valid ↓) versus
sustained engagement. This is stated **once, early**, and every downstream
face-assignment refers back to it.

---

## D5 · The seat split is the identifying test

Splitting mayoral races by whether the seat is **open** (incumbent term-limited,
no front-runner defending, N=2,026) or **contested** (sitting mayor may seek
re-election, N=3,534) is **not heterogeneity garnish — it is how the face gets
assigned.**

| Seat type | Concentration | Ballot | Face |
|---|---|---|---|
| **Contested** | margin +0.068, p=.01 | blank +0.005 (p=.04); valid −0.013 (p=.08) | **Barrier** |
| **Open** | margin +0.076, p=.05; majority +0.160 (p=.06) | no demobilization | **Not barrier** — decisiveness |

Read together: **consolidation is general** across seat types; the **face is
seat-conditional**.

**"Decisiveness" is not a leveling claim.** Absence of a barrier signature is not
evidence of leveling: valid votes do not *rise* in open seats, they merely fail to
fall, and the winner's identity does not change. The honest label is coordination
on a leader with no evidence of fouling.

---

## Confidence architecture

The tiers are unchanged, but D4 makes them load-bearing rather than decorative.

| Tier | Finding | Basis |
|---|---|---|
| **Robust** | The mayoral race consolidates | clears AR wild-cluster bootstrap **and** BHJ/AKM exposure-robust SE; multiplicity-corrected at 5% by Holm (p=.015) and BH (p=.011), and at 10% by Romano–Wolf (p=.059) |
| **Tentative** | Voters withdraw (contested seats) | conventional + exposure-robust inference, **not** the AR bootstrap |
| **Precise null** | Candidate supply, representation, renewal, who wins, elastic/education turnout, campaign finance, entire legislative side | tightly bounded around zero |
| **Exploratory** | The winner's gain lands on male front-runners | differential test does not clear (p=.129); outside the declared family |

**The consequence, stated deliberately rather than blurred:**

> The paper's headline **finding** (consolidation) is **robust**.
> Its **interpretation** (which face) rests on the ballot, and is therefore
> **tentative**.

This is the honest structure the evidence has. It is currently papered over by
the formulation "the consolidation is the barrier signature", which borrows the
robust tier for a tentative claim. That formulation is retired.

---

## Vocabulary lock

One word per concept. Deviations are drift, not style.

| Concept | Locked term | Guard |
|---|---|---|
| The phenomenon | **judicialization** = the judiciary's expanded role | never "rising/growing judicialization" |
| Treatment | **adversarial litigation intensity** | never bare "lawsuits" or "volume" |
| The dichotomy | **Leveling / Barrier** | reserved exclusively for H1/H2; never reused for another split |
| The seat split | **open** vs **contested** seats | never "two faces by seat type" |
| Open-seat outcome | **decisiveness** | not a leveling claim |
| Contested-seat outcome | **withdrawal** | "disengagement" only where prose needs variety |
| Headline result | **consolidation** = top-two margin widening | never call this "concentration" |
| Whole-field measures | **concentration** = effective N, HHI | never use for the top-two margin |
| Mechanisms | **information** · **weaponization** | never "lawfare" |
| Excluded channel | **direct judicial action** | named once in the D2 boundary, never again |

**Spelling: American**, throughout both decks and the paper — *Leveling, favors,
behavior, demobilization, characterize, organize*. (The decks previously mixed
British `-our/-ise` forms with American "Leveling"; decided 2026-08-11.)

---

## Novelty claim

Locked form:

> **the first *aggregate* causal estimate of what adversarial litigation does to
> the contest itself**

"First" attaches to **aggregate + contest-level**. It never stands bare as "the
first causal estimates."

Defended by the three contrasts already in the Four Literatures frame:

1. Courts-and-elections in Latin America is largely qualitative and institutional
   → we estimate the effect on the contest.
2. Brazilian lawsuit studies (Chin, Nakaguma) are candidate-level and
   observational → we shift the unit to the local election.
3. Shift-share methodology is built for many diffuse shocks → we adapt it to few,
   concentrated litigation shocks via the share-exogeneity (GPS) route.

---

## Known exposures

Recorded so the decision is retrievable. **These do not appear in prose.**

- **D2 vs. the filter table.** The adversarial filter *keeps* registration and
  eligibility **challenges** (*impugnação*, inelegibilidade / AIRC), abuse-of-power
  actions (AIJE), and mandate challenges (AIME/RCED) — deliberately, per the
  "routed by subject, gated by class" rule. Those classes *can* legally remove a
  candidate or unseat a winner. D2's construction argument is therefore exact for
  the **administrative eligibility screen** and stronger than the class list alone
  supports for adversarial removal actions. Decided 2026-08-11 to state D2 flatly
  and without hedge. If a referee presses, the available fallback is the
  candidate-supply null (no candidates disappear in the aggregate) plus the
  literature's finding that pre-election attack filings rarely produce
  disqualification.
- **Romano–Wolf is a 10% pass, not a 5% one.** `romano_wolf_stepdown.csv` gives
  the margin p_rw = .059 (runner-up .071). Holm (.015) and BH (.011) clear at 5%;
  Romano–Wolf does not. `slides_report.tex` L749 currently lists Romano–Wolf
  among the Robust tier's clean passes without the qualifier. Corrected here;
  the deck edit carries the same correction. The Robust tier still stands on
  AR-WCR and BHJ/AKM, which are the binding tests.
- **Extensive-margin identification.** The first stage moves treatment on the
  extensive margin (onset of adversarial contestation). Existence and sign are
  identified; per-unit-of-volume magnitude is not. The estimate is a local effect
  for **onset compliers**. Already carried in the Limitations frame; must survive
  into the paper as a clause, not be quietly dropped.

---

## Apply-to-the-paper sheet

Nara drafts the paper. This is what the locked framing requires of it.

**Stale in `extended_abstract.tex` (lines 64–113):**

1. *"Adversarial filings reached X M in 2020 and **grew** to Y M in 2024"* —
   violates D1. Replace with the expanded-role framing; report no volume trend.
2. The **three-channel paragraph** (information / lawfare / direct judicial
   action, "the evidence below favors degradation") — violates D2 and D3. Replace
   with: the D2 boundary sentence, then the two surviving mechanisms, then the
   collapse onto Leveling/Barrier.
3. *"we provide the **first causal estimates**"* — violates the novelty lock.
   Use the locked form.
4. Tense — "we argue / we measure" → "we find / we estimate."

**Required of the introduction:**

- The research question names both faces and asks them **by office**.
- D4 appears **once, early**: concentration does not identify a face; the ballot
  does.
- The four findings are stated with magnitudes **at their true tier** — and the
  robust-finding/tentative-interpretation structure is stated, not smoothed.
- The D2 boundary appears as one flat sentence.
- The extensive-margin caveat appears as one clause.

**Required of the Results section:** the seat split is presented as the
**identifying test** (D5), not as a heterogeneity appendix.

---

## Application record

**Status: pending — this section is updated once the edits land.**

Scope agreed 2026-08-11: 11 edits to `slides_report.tex`
(RQ block; Two Faces frame incl. its internal contradiction at L90; the
What-We're-Measuring row 3; This Paper's closing line; Story-in-One-Frame;
the seat-heterogeneity retitle and promotion; Findings-by-Confidence;
Contribution; `app:theory` boundary sentence; the Romano–Wolf qualifier at
L749) and 4 to `slides_advisor.tex`
(hypothesis-grid row 3; the Layer-3 claim at L128; the Layer-3 verdict tier;
the structural header comment), plus the American-spelling sweep.

`slides_advisor.tex`'s **Layer-2 verdict was already correct** under D5 ("the
response is to a *defended* seat, not to litigation as such") and was left alone.
