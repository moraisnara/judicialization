# DECK_WORKPLAN.md — design punch-list from the frame-by-frame review

Companion to `DECK_GUIDE.md` (how the deck is built) and `FRAMING.md` (the locked
argument). This file collects **design** decisions raised during the frame-by-frame
pass and deliberately *not* acted on at the time. Writing fixes are applied in place
when found; only design questions land here.

A design item is anything that changes **what is on the slide** rather than how it is
worded: which figure or table appears, what the figure plots, whether a frame exists
at all, where it sits in the spine, promotion between main and appendix, and any
change that requires re-running an R/Python script.

Status vocabulary: `open` · `decided` · `done` · `dropped`.

## Review progress

`slides_report.tex`, driver order. Frames reviewed: title page, `src_motivation` (rewritten
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
`src_thispaper` (p. 4). Decide which frame owns it. Keeping both is defensible in a
report, which is a reference document.

### D3 · Three nav buttons on a setup frame — `dropped` (2026-09-16)
`Theory`, `Recomposition`, `Timeline` all sit on the motivation frame. The question was
whether the talk-deck one-button cap extends to setup frames in the short decks. The
short decks were dropped 2026-09-16 and the report is exempt from the cap.

### D4 · Title page uses `\date{\today}` — `open`
Every recompile re-stamps the date, so two printouts of the same content disagree.
For a circulated working document, consider a manual `\date{}` bumped deliberately.

### D5 · Motivation now carries the empirical literature — `done` (2026-08-12)
The rewritten frame states what Chin--Lambais--Sigstad, Nakaguma--Souza and Assump\c{c}\~ao
actually find (a third of mayoral candidates litigate, a ninth of campaign money to
lawyers, suits aimed up the ladder and seldom won, a disclosed conviction worth some
13 points of vote share), because that evidence is what makes the mechanism concrete.
`src_literature` (p. 5) then covers the same three papers as a literature block.
**Resolved: motivation keeps the numbers, `src_literature` keeps the positioning.** The
literature bullet was also factually wrong — it called this evidence "case-level and
observational" when Chin et al. is 27,260 lawsuits matched to 19,358 candidates,
Nakaguma--Souza is a regression discontinuity, and Assump\c{c}\~ao is an IV. It now states
the true gap (all three are candidate-level) and discloses that Chin et al.'s poll test
rules out drops larger than two to five points, which is the closest paper to our voter
result. *2026-09-16 citation audit:* the motivation frame no longer says suits are
"seldom won" or that publicity is what they produce. It now states that
disqualification suits almost never succeed and that candidates feature suits in their
media campaigns (Chin et al.), and that attacks target candidates with an electoral
advantage (Nakaguma--Souza).

### D6 · The council race is no longer set up on the motivation frame — `decided` (2026-08-12)
Checked: `src_thispaper` (p. 4) carries it in the closing rule-line, "These effects are
confined to the mayoral race... The council race exhibits neither face." The reader meets
the two-office design before the first council null. No change.

### D7 · Motivation and `src_ejustice` now state the same dual role — `open`
`src_ejustice` (p. 6, "One Branch, Two Roles") is built on the Normative/Adjudicative
split and lists examples that overlap the motivation frame's (council seats, party
loyalty). Four frames apart, this reads as repetition. The motivation frame dropped the
gender- and race-fund shares on 2026-09-16 because its citations do not cover them;
`src_ejustice` still lists them with no citation.
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

### D9 · The short decks were never overflow-checked — `dropped` (2026-09-16)
The 30- and 15-minute decks carried 7 and 5 overfull boxes. Both decks were dropped
2026-09-16; `slides_report` is the only deck.

## Open result questions for Nara

Raised during the 2026-09-16 consistency pass. The deck now states each fact below
correctly and from macros; what it should *conclude* from them is Nara's call. Each
item says where the fact is on the deck.

### Q1 · Which multiplicity basis leads — `open`
Over the 18 reduced-form p-values the margin survives Holm (.015) and BH (.011), and
Romano–Wolf only at 10% (.059). Over the 18 2SLS p-values nothing survives (margin Holm
.237, BH .143). The deck states both (`src_findings`, `src_robustness`,
`app_multiplicity`). Decide which one the Robust tier cites first, or whether the
multiplicity sentence belongs in the tier basis at all.

### Q2 · The open-seat margin has a pre-trend — `open`
The open-seat margin already widened before 2020 (+0.120, p=.047); the contested-seat
margin did not (p=.905). FRAMING D5 says "consolidation is general" across seat types,
and `app_ptrobust` reads the margin as a response to the shock. The deck now reports
the open-seat pre-trend on `src_story`, `src_seathet`, `app_seathet`, `src_pretrend`
and `app_pretrend`, and no longer says "the consolidation is general".

### Q3 · The ballot signature has pre-trend failures — `open`
The reduced-form placebo fails the mayoral valid-vote rate (p=.012), the council
valid-vote rate (p=.008) and turnout (p=.007); the margin passes (p=.137). A falling
valid-vote rate is half of the withdrawal signature that assigns the face (FRAMING D4).
Stated on `src_pretrend` and `src_voterballot`.

### Q4 · The council side is not a clean null — `open`
2 of 16 council outcomes clear 5%: elected female share (p=.036) and mean candidate age
(p=.022). No council multiplicity correction has been computed. The tier formerly
called "Precise null" includes the "entire legislative side". Stated on
`app_councilplacebo`, `src_candidates`, `src_findings`, `src_thispaper`.

### Q5 · Compulsory turnout rises — `open`
Compulsory turnout moves (p=.054; the tF interval excludes zero), while
`app_turnoutplacebo` treats turnout as institutionally floored. Stated on
`src_turnoutprofile` and `app_turnoutplacebo`.

### Q6 · Share balance fails on unclustered tests — `open`
14 of 14 tested topic shares correlate with the baseline controls and 4 of 14 predict
the 2016→2020 margin change (`gps_balance_tests.csv`, DRAP benchmark excluded). The
tests use homoskedastic, unclustered SEs, and the control set includes variables that
are not predetermined. Options: re-estimate with state-clustered SEs on predetermined
covariates only, or report as is. Stated on `src_limitations`.

### Q7 · The Rotemberg top five — `open`
4 of the top five subjects are propaganda subjects; their own first-stage F ranges from
8.6 to 44.2, so one high-weight subject is weak. "Eleições - 1° Turno" is in the top
five, and it is a generic subject label rather than a litigation topic. Stated on
`app_rotemberg` and `src_identbrief`. The frame's former claim that a finer partition
changes the picture was removed because it could not be verified for this design.

### Q8 · Tier labels and marks — `open`
- "Precise null" was renamed "Null" on the deck and in FRAMING.md; precision of the
  bounds was never checked.
- The pooled blank rate (conventional p=.095) sits in the Tentative tier on the
  strength of the exposure-robust SE (p=.028) and the contested-seat split.
- `src_robustness` keeps its check/cross marks; some rows pass on one basis and fail on
  another (see its footer).

### Q9 · How to present first differences — `open`
Pure FD returns -0.007 (p=.822). Older text called FD a "conservative bracket"; the
deck now reports it as a result that the margin does not survive. `WRITING_GUIDE.md`
§5 still lists an "FD bracket" among the inference checks.

### Q10 · Two robustness specs are broken — `open`
`broader_treatment` and `base_conditioned` (in `executive_margin_iv_fixest.csv`) add a
2020 litigation level as a control and return a first-stage F of about 0.02. Neither
reaches the deck. Fix, drop from `02_iv_main.R`, or document.

### Q11 · Smaller items — `open`
- The first-stage binscatter uses a different control set from the estimating spec.
- The seat-heterogeneity figure (`03_result_figures.R`) and `summary_indices.tex`
  (`11_summary_indices.R`) still label the ballot family "Voter disengagement"; the
  lock says "withdrawal". Relabeling needs an R re-run.
- The header of `11_summary_indices.R` says the headline survives "on a tight
  closeness-4 family"; that family is not computed anywhere in the current outputs.
- The 99.8% campaign-finance match rate is printed to the console only; it was removed
  from `app_spending` for that reason.
- The summary-statistics table (`app_sample`) describes 2020→2024 changes, while the
  estimator conditions on 2016 levels.
- `src_entrant` and `src_turnoutprofile` sit in the appendix run (the UNRESOLVED
  comment in `slides_report.tex`) although their titles no longer say "Appendix".
- Paper files are untouched by request: `estimating_equations.tex` is stale, and
  `extended_abstract.tex` includes the deleted `forest_voter_behavior.pdf`.

## Citation gaps

From the 2026-09-16 citation audit. The bib entries were corrected and the missing
method citations added; these need a source Nara chooses.

- `src_ejustice`, Normative block: *resoluções*, binding *súmulas*, STF review, and the
  examples (council seats, party loyalty, gender- and race-fund shares, disinformation
  removal) carry no citation. For the funds, a TSE ruling or ADPF 738.
- `app_reclass`: the "documented" propaganda recoding and the substitution of suits by
  takedown orders have no source in the bib.
- `app_timeline`: the legal acts are sourced only in LaTeX comments.
- `src_adjudication`: TSE *Temas Selecionados* is a web resource with no bib entry.
- `nakaguma2025` is forthcoming in AEJ: Microeconomics; its DOI is not registered, so
  volume and pages are unverified.
- `chin2025`: a 2026 revision is retitled "Electoral Litigation in Political Campaigns"
  (Zotero, 17 Apr 2026). The entry cites the 2025 SSRN version.
- `src_twofaces`: `ramos2020` supports "inclusion" with a caveat, since the TSE is
  restrained in difficult, high-impact quota cases.
- `11_summary_indices.R` cites Clarke–Romano–Wolf (2020), which is not in the bib.
- `dixcarneiro2017` is in the bib but cited by no frame.
