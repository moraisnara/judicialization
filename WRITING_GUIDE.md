# Writing Guide — *When It Gets to Court: The Electoral Costs of Judicialization*

A working guide for turning the skeleton `paper.tex` into a finished manuscript.
Synthesized from two sources and adapted to where **this** paper actually stands:

- **Evans (CGD), "How to write the introduction of your development economics paper"** — the 7-element introduction.
- **Oliveira (UNU-WIDER), "How to write a successful proposal"** — which explicitly says a proposal *is* a paper introduction, and extends Evans with a setting/methodology/contribution scaffold.

The one-line thesis of both: **the introduction is the paper in miniature. Write it first, get it right, and it disciplines every other section.** A reader should be able to cite this paper confidently having read only the introduction.

---

## 0. Where this paper stands right now (read before writing)

- `paper.tex` is a **skeleton**: seven empty `\section` headers and an `ABSTRACT GOES HERE` placeholder.
- The **content already exists**, in two places, and the writing job is largely *transcription + reconciliation*, not invention:
  1. **`output/presentation/slides_report.tex`** — the Beamer deck, deliberately built as a *full report* (per the standing "presentation is a report" rule). Every section of the paper has a corresponding block of frames. **This is your outline and your evidence inventory.** Mine it section by section.
  2. **`extended_abstract.tex` (lines 64–113)** — a genuinely good ~900-word intro draft that already follows the Evans arc (motivation → setting → question → mechanisms → approach → contribution).
- **The catch:** the extended-abstract draft encodes an *older framing* than the current deck. The framing is now locked in `FRAMING.md` (§3), whose apply-to-the-paper sheet lists what is stale in `extended_abstract.tex`. Bring the draft in line with it **before** drafting the introduction, because the framing propagates into every section.

---

## 1. The core method: introduction-first

Both guides converge on this. Do not write the paper front-to-back. Write the **introduction first**, because:

- It forces you to commit to *one* research question, *one* framing, and an honest statement of *what you actually found*.
- Every downstream section then becomes "expand the corresponding intro paragraph with the full evidence."
- WIDER's framing: your proposal/intro must be crystal-clear on (1) what you do, (2) the research question, (3) methodology + data + a fallback if the preferred method fails, (4) the contribution.

**Then** fill Background → Data → Strategy → Results → Robustness → Conclusion, each an expansion of a promise the introduction already made.

---

## 2. The introduction, element by element (Evans's 7, applied to this paper)

Target length **~1,500–2,000 words**. Budget shares below are Evans's.

| # | Element | Length | For *this* paper |
|---|---------|--------|------------------|
| 1 | **Motivation** | 1–2 ¶ | Open on the big fact: in Brazil *one branch both writes and adjudicates the rules of electoral competition*. Litigation cuts two ways — a **leveler** (screens unfit candidates, deters abuse) or a **barrier** (a strategic weapon that raises the cost of competing). Net effect theoretically ambiguous. This is the deck's opening frame + the extended-abstract ¶1. |
| 2 | **Research question** | 1 ¶ | State it flatly, one sentence: *as a race faces more adversarial litigation, does the contest level or does a barrier emerge — and does who runs and who wins change?* Note you ask **separately for the mayoral and council races, and the answer differs by office.** Be direct; the question must be unmistakable. |
| 3 | **Empirical approach** | 1 ¶ | Shift-share (Bartik) instrument built from national, subject-level adversarial-litigation diffusion × municipal baseline shares (following Ash-Morelli-Vannoni); outcome read on the clean **2016** baseline (ANCOVA), 2SLS, state FE, state-clustered SE, N = 5,560. You do **not** need to explain what 2SLS is — name it, name the identifying variation, name the fallback (reduced form survives, which is why you can lean on it). |
| 4 | **Detailed results** | **3–4 ¶, 25–30% of the intro** | This is the part most drafts under-write. State the **findings with magnitudes** so a reader can cite you, each at its tier in `FRAMING.md` (Confidence architecture), which is the list to write from. Points earlier drafts overstated (2SLS cluster-robust p-values): consolidation is the top-two margin, winner share and runner-up share, and the effective number of candidates does not move significantly (p=.27); in contested seats only the blank rate clears 5% (p=.035), the valid-vote fall clears 10% (p=.084) and the null rate does not (p=.165); the council side is not a uniform null (elected female share p=.036, candidate mean age p=.022); the campaign-spending 2SLS finds no out-financing, which does not by itself establish a channel, and the interpretation follows `FRAMING.md` D4. Pull magnitudes from `abstract_macros.tex` and **report each at the confidence it actually holds** (see §4). |
| 5 | **Value-added vs literature** | 1–3 ¶, **placed late** | Do *not* front-load a literature review. Position against the three contrasts and use the locked novelty sentence in `FRAMING.md` (Novelty claim). Review each strand *only as it relates to your contribution*. |
| 6 | **Optional paragraphs** | as needed | Mechanism, policy relevance, scope. Keep only what strengthens the argument. |
| 7 | **Roadmap** | ≤1 ¶ or cut | Evans's warning: a roadmap "kills the momentum of most papers on the second page." Keep it to one sentence or drop it. |

---

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

---

## 4. Report results at their true confidence (non-negotiable)

Evans: readers will **cite your paper from the introduction alone.** So the intro cannot overclaim. The tiers, the basis for each, and the robust-finding/tentative-interpretation structure are in `FRAMING.md` (Confidence architecture, Known exposures). Write each claim at its tier and state the tier in a clause where the claim first appears. Two points the prose must carry exactly:

- **The blank-rate rise** reaches 10% only under conventional inference in the full sample (2SLS p=.095) and does not clear the AR bootstrap (p=.108). It clears 5% under the BHJ exposure-robust SE (p=.028) and in contested seats (p=.035).
- **Multiplicity** has two bases; state both and do not pick one. On reduced-form normal-approximation p-values, Holm and BH clear at 5% (margin Holm .015, BH .011) and Romano–Wolf gives p=.059. On the 2SLS cluster-robust p-values, no outcome of the 18 survives (margin Holm .237, BH .143). The overall summary index (p=.039) and the closeness index (p=.009) clear.

---

## 5. Body sections — each expands an intro promise (mine the deck)

Write these *after* the intro. For each, the deck already holds the argument and the exhibits.

- **Institutional Background** (`sec:background`). From deck's Institutional Background frames: where electoral justice decides (first-instance locus, `sample_map`); who has standing (candidate-vs-candidate, MPE the only institutional actor, voter excluded from *polo ativo*); two decades of new regulatory fronts (the timeline); valid/blank/null ballot institutions. Purpose (WIDER): explain the setting so the reader **never has to Google**. Brazil is not common knowledge — spell out the *Justiça Eleitoral*, the four-year municipal cycle, compulsory voting, the RRC/DRAP vs adversarial distinction.
- **Data** (`sec:data`). From deck's Data frames: sources table; **the adversarial filter** (why dropping mandatory RRC/DRAP/*prestação de contas* is "the whole game": 3.8% of filings kept, `\KeptAdversarialPct`); recomposition rather than a rise in volume; the analysis sample (Table 1 summary stats). State clearly: TSE SIG microdata, publicly available, município × subject × year, the coverage caveat for 2024.
- **Empirical Strategy** (`sec:strategy`). From deck's Empirical Strategy frames: the intuition (same national shift, unequal local exposure); construction (shares × shifts); the endogenous variable $\Delta\log(1+\ell_m)$; the ANCOVA-on-2016 estimator and why (not FD, which over-differences); the identifying-assumption route (share/GPS exogeneity, since shocks are few). Give the specification equation explicitly (WIDER: "provide a basic specification").
- **Results** (`sec:results`). Follow the deck's Results order: the first stage; what the contest produces (the consolidation, then its gender incidence); candidates and voters (who is favored, representation, candidate supply, the ballot); heterogeneity by seat type, presented as the identifying test (`FRAMING.md` D5). The council results sit in the deck appendix. Lead each with the human-readable claim; the house-style tables are already generated.
- **Robustness** (`sec:robustness`). The deck's four families: (1) is the identifying variation what we claim (extensive-margin + reclassification); (2) does the treatment definition drive it; (3) is the inference honest (AR-WCR, BHJ/AKM, FD bracket); (4) is it multiple testing (Romano–Wolf, summary index, pre-trend placebos), stating both p-value bases (§4). One paragraph per family; full tables to appendix.
- **Conclusion** (`sec:conclusion`). From the deck's "Findings by Confidence Tier" and Limitations frames: the findings restated at their tiers, contribution, and an explicit **limitations** paragraph (few effective shocks + few clusters → no LLN, defended on share-exogeneity; extensive-margin first stage → magnitude not identified; municipal-level treatment ≠ single suit).

---

## 6. Abstract (write last, or right after the intro)

One paragraph, in this order (per the placeholder and both guides): **question · design · data + sample size · headline result · contribution.** ~150 words. Pull the numbers from the auto-generated `abstract_macros.tex` so they never drift from the estimates. Fill JEL codes (candidates: D72 elections, K41 litigation, P48 institutions) and keep the keyword line.

---

## 7. Standing writing rules for this project (apply throughout)

- **Future → past tense.** The extended abstract uses "we argue / we measure"; in the paper these become "we find / we estimate." (WIDER allows future tense only because a *proposal* has no results yet — you do.)
- **One research question**, stated once, unmistakably.
- **Literature late and instrumental** — never a standalone lit-review dump early; review each strand only as it bears on your contribution.
- **Tables**: readable outcome labels, "Mean of dep. var." row, no misleading homoskedastic F, stars from the 2SLS cluster-robust p-value, no stars legend, no "+" on positive coefficients (house conventions already encoded in the generators).
- **Figures carry no baked-in titles/captions** — captions live in the LaTeX `\caption`, mirroring the Beamer-frame rule.
- **Reproducibility**: every number in the paper traces to a saved script's output (mostly `abstract_macros.tex` and the `tables/tex/*.tex` fragments); no inline hand-computed figures.
- **References**: check the local Zotero library (`C:\Users\naral\Zotero`) before hunting the web; add to `references.bib`.
- Build: `pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper`.

---

## 8. Recommended order of operations

1. **Read `FRAMING.md`** (§3). The framing is already locked (volume-vs-role, the two faces, novelty phrasing); do not re-decide it.
2. **Draft the Introduction** (§2) from the extended-abstract prose + deck opening frames, updated to the locked framing and honest confidence tiers (§4).
3. **Write the Abstract** (§6) from the finished intro.
4. **Fill the body** (§5), each section expanding its intro promise, transcribing argument + exhibits from the matching deck frames.
5. **Conclusion + limitations**, then a **pass for tense, overclaiming, and roadmap bloat.**
6. Compile, check no undefined refs/citations, and read the intro *alone* to confirm it stands as a citable summary.
