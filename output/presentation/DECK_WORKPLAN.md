# DECK_WORKPLAN.md — design punch-list from the frame-by-frame review

Companion to `DECK_GUIDE.md` (how the decks are built) and `FRAMING.md` (the locked
argument). This file collects **design** decisions raised during the frame-by-frame
pass and deliberately *not* acted on at the time. Writing fixes are applied in place
when found; only design questions land here.

A design item is anything that changes **what is on the slide** rather than how it is
worded: which figure or table appears, what the figure plots, whether a frame exists
at all, where it sits in the spine, promotion between main and appendix, and any
change that requires re-running an R/Python script.

Status vocabulary: `open` · `decided` · `done` · `dropped`.

## Review progress

Report deck, driver order. Frames reviewed: title page, `src_motivation` (rewritten
2026-08-12 to Nara's reframe: the branch's rulemaking + adjudication role, the arena
as a campaign instrument, the voter-side evidence, and the question stated as "what
happens to the local election"). Next: `src_twofaces`.

## Items

### W1 · Title keeps "The Electoral Costs of Judicialization" — `decided` (Nara, 2026-08-12)
Raised as a tier concern: "costs" reads as the Barrier face, which FRAMING tiers as
Tentative. **Resolved: the title states the hypothesis under exploration, not the
finding.** The paper asks whether judicialization is a cost to competition, and
answers it by testing Leveling against Barrier. "Costs" is therefore the object of
study; the Leveling result would be a negative answer to the title's question, not a
contradiction of it. No change. Do not re-open.

### D1 · Recomposition is asserted, not shown, on the motivation frame — `open`
Bullet 3 claims adversarial litigation "stays roughly flat and recomposes across
topics" and sends the reader to `app:recomp` for the evidence. This is the oldest
item on the standing critique list. Options: (a) leave as is, (b) inline a small
recomposition sparkline/stacked-share strip, (c) split motivation into two frames.
Cost of (b): a new figure from the recomposition script.

### D2 · The research-question block duplicates `src_thispaper` — `open`
The question is stated in the block here and again as Evans element 2 on
`src_thispaper` (p. 4). Decide which frame owns it. Keeping both is defensible in the
*report* (it is a reference document) but the 30/15-min decks should state it once.

### D3 · Three nav buttons on a setup frame — `open`
`Theory`, `Recomposition`, `Timeline` all sit on the motivation frame. The talk-deck
minimalism rule caps results frames at one button; setup frames have no stated cap.
Decide whether the cap extends to setup frames in the short decks.

### D5 · Motivation now carries the empirical literature — `done` (2026-08-12)
The rewritten frame states what Chin--Lambais--Sigstad, Nakaguma--Souza and Assump\c{c}\~ao
actually find (a third of mayoral candidates litigate, a ninth of campaign money to
lawyers, suits aimed up the ladder and seldom won, a disclosed conviction worth some
13 points of vote share), because that evidence is what makes the mechanism concrete.
`src_literature` (p. 5) then covers the same three papers as a literature block. Decide
**Resolved: motivation keeps the numbers, `src_literature` keeps the positioning.** The
literature bullet was also factually wrong — it called this evidence "case-level and
observational" when Chin et al. is 27,260 lawsuits matched to 19,358 candidates,
Nakaguma--Souza is a regression discontinuity, and Assump\c{c}\~ao is an IV. It now states
the true gap (all three are candidate-level, the outcome being the candidate's own vote
share) and discloses that Chin et al. bound the polling effect near zero, which is the
closest paper to our voter result.

### D6 · The council race is no longer set up on the motivation frame — `decided` (2026-08-12)
Checked: `src_thispaper` (p. 4) carries it in the closing rule-line, "These effects are
confined to the mayoral race... The council race exhibits neither face." The reader meets
the two-office design before the first council null. No change.

### D7 · Motivation and `src_ejustice` now state the same dual role — `open`
`src_ejustice` (p. 6, "One Branch, Two Roles") is built on the Normative/Adjudicative
split and lists the same examples the motivation frame now uses (council seats, party
loyalty, gender- and race-fund shares). Four frames apart, this reads as repetition.
Options: (a) motivation drops the examples and keeps only the three-levels claim;
(b) `src_ejustice` drops the example list and its Normative block covers the *instruments*
instead (\emph{resolu\c{c}\~oes}, binding \emph{s\'umulas}, STF review), which is what §2 is
actually for. Preference is (b). Either way, align the vocabulary: `src_ejustice` says
"two roles" where motivation says three levels of electoral governance, two of which are
the object.

### D8 · Suits target the front-runner, yet the front-runner gains — `open`
The motivation frame now states the Chin/Nakaguma finding that suits are aimed up the
ladder at the leader. Our headline is that the top-two margin widens: the attacked leader
ends up further ahead. That tension is currently unstated anywhere in the deck, and it is
the most interesting thing the new evidence buys. It can be written as a prediction rather
than a puzzle: litigation aimed at the leader fails to dislodge them, and its cost lands on
the electorate instead. Decide whether that line goes on `src_twofaces` (as a sharpened
Barrier prediction) or on `src_story` / `src_spine1` (as the interpretation of the result).
Touches the argument, so it needs Nara's call, not just a wording choice.

### D9 · The short decks were never overflow-checked — `open`
The overflow audit was run on `slides_report` only. The 30-minute deck carries 7 overfull
boxes and the 15-minute deck 5, the largest being `src_candidates_talk` (17.3pt) and
`src_seathet_talk` (15.8pt) in both. The talk variants are generated files, so the fix has
to go into the source frame or into `build_talks.py`, not the `_talk` file. Rasterize those
two pages in both decks before either is presented.

### D4 · Title page uses `\date{\today}` — `open`
Every recompile re-stamps the date, so two printouts of the same content disagree.
For a circulated working document, consider a manual `\date{}` bumped deliberately.
