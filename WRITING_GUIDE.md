# Writing Guide — *When It Gets to Court: The Electoral Costs of Judicialization*

A working guide for turning the skeleton `paper.tex` into a finished manuscript.
Synthesised from two sources and adapted to where **this** paper actually stands:

- **Evans (CGD), "How to write the introduction of your development economics paper"** — the 7-element introduction.
- **Oliveira (UNU-WIDER), "How to write a successful proposal"** — which explicitly says a proposal *is* a paper introduction, and extends Evans with a setting/methodology/contribution scaffold.

The one-line thesis of both: **the introduction is the paper in miniature. Write it first, get it right, and it disciplines every other section.** A reader should be able to cite this paper confidently having read only the introduction.

---

## 0. Where this paper stands right now (read before writing)

- `paper.tex` is a **skeleton**: seven empty `\section` headers and an `ABSTRACT GOES HERE` placeholder.
- The **content already exists**, in two places, and the writing job is largely *transcription + reconciliation*, not invention:
  1. **`output/presentation/slides_report.tex`** — the Beamer deck, deliberately built as a *full report* (per the standing "presentation is a report" rule). Every section of the paper has a corresponding block of frames. **This is your outline and your evidence inventory.** Mine it section by section.
  2. **`extended_abstract.tex` (lines 64–113)** — a genuinely good ~900-word intro draft that already follows the Evans arc (motivation → setting → question → mechanisms → approach → contribution).
- **The catch:** the extended-abstract draft encodes an *older framing* than the current deck. Reconciling the two (see §3) is the single highest-value writing task and must happen **before** drafting the introduction, because the framing decision propagates into every section.

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
| 1 | **Motivation** | 1–2 ¶ | Open on the big fact: in Brazil *one branch both writes and adjudicates the rules of electoral competition*. Litigation cuts two ways — a **leveller** (screens unfit candidates, deters abuse) or a **barrier** (a strategic weapon that raises the cost of competing). Net effect theoretically ambiguous. This is the deck's opening frame + the extended-abstract ¶1. |
| 2 | **Research question** | 1 ¶ | State it flatly, one sentence: *as a race faces more adversarial litigation, does the contest level or does a barrier emerge — and does who runs and who wins change?* Note you ask **separately for the mayoral and council races, and the answer differs by office.** Be direct; the question must be unmistakable. |
| 3 | **Empirical approach** | 1 ¶ | Shift-share (Bartik) instrument built from national, subject-level adversarial-litigation diffusion × municipal baseline shares (following Ash-Morelli-Vannoni); outcome read on the clean **2016** baseline (ANCOVA), 2SLS, state FE, state-clustered SE, N = 5,560. You do **not** need to explain what 2SLS is — name it, name the identifying variation, name the fallback (reduced form survives, which is why you can lean on it). |
| 4 | **Detailed results** | **3–4 ¶, 25–30% of the intro** | This is the part most drafts under-write. State the **four findings with magnitudes** so a reader can cite you: (1) the mayoral race **consolidates** (top-two margin widens, winner share up, runner-up down, fewer effective candidates); (2) **voters disengage** on the same ballot (blank + null up, valid down, in contested seats; compulsory turnout pinned); (3) a **wide band of precise nulls** (representation, renewal/entrant typology, elastic + education-stratified turnout, the entire legislative side); (4) **the channel is disengagement, not attrition** (direct 2SLS on campaign spending finds no out-financing). **Report each at the confidence it actually holds** (see §4). |
| 5 | **Value-added vs literature** | 1–3 ¶, **placed late** | Do *not* front-load a literature review. Position against: (a) courts-and-elections in Latin America, largely qualitative/institutional → you give the first *aggregate causal* estimate on the contest itself; (b) recent Brazilian lawsuit studies at the *candidate* level (Chin, Nakaguma) → you shift the unit to the *local election*; (c) shift-share methodology → you adapt a many-diffuse-shocks design to *few, concentrated* litigation shocks. Review each *only as it relates to your contribution*. |
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

Evans: readers will **cite your paper from the introduction alone.** So the intro cannot overclaim. This paper has a genuine two-tier result and the writing must preserve it:

- **Consolidation** is the finding that carries statistical weight — survives AR wild-cluster bootstrap **and** BHJ/AKM exposure-robust SE. State it firmly.
- **Disengagement (blank/null)** is **more tentative** — significant under conventional and exposure-robust inference but **not** under the AR bootstrap. Say so, in the intro, in a clause. This honesty is a feature: it is exactly what distinguishes a careful paper.
- The nulls are **precise nulls**, not "no data" — frame them as informative.
- Magnitude language: effect **exists, sign identified**; per-unit-of-volume magnitude is not — it is a local effect for **onset compliers**.

---

## 5. Body sections — each expands an intro promise (mine the deck)

Write these *after* the intro. For each, the deck already holds the argument and the exhibits.

- **Institutional Background** (`sec:background`). From deck's Institutional Background frames: where electoral justice decides (first-instance locus, `sample_map`); who has standing (candidate-vs-candidate, MPE the only institutional actor, voter excluded from *polo ativo*); two decades of new regulatory fronts (the timeline); valid/blank/null ballot institutions. Purpose (WIDER): explain the setting so the reader **never has to Google**. Brazil is not common knowledge — spell out the *Justiça Eleitoral*, the four-year municipal cycle, compulsory voting, the RRC/DRAP vs adversarial distinction.
- **Data** (`sec:data`). From deck's Data frames: sources table; **the adversarial filter** (why dropping mandatory RRC/DRAP/*prestação de contas* is "the whole game" — 6.8% kept); recomposition-not-a-wave; the analysis sample (Table 1 summary stats). State clearly: TSE SIG microdata, publicly available, município × subject × year, the coverage caveat for 2024.
- **Empirical Strategy** (`sec:strategy`). From deck's Empirical Strategy frames: the intuition (same national shift, unequal local exposure); construction (shares × shifts); the endogenous variable $\Delta\log(1+\ell_m)$; the ANCOVA-on-2016 estimator and why (not FD, which over-differences); the identifying-assumption route (share/GPS exogeneity, since shocks are few). Give the specification equation explicitly (WIDER: "provide a basic specification").
- **Results** (`sec:results`). The three layers, in order: candidate supply (null) → voter behaviour/ballot (disengagement) → electoral equilibrium (consolidation), plus the council **placebo** office. Lead each with the human-readable claim; the house-style tables are already generated.
- **Robustness** (`sec:robustness`). The deck's four families: (1) is the identifying variation what we claim (extensive-margin + reclassification); (2) does the treatment definition drive it; (3) is the inference honest (AR-WCR, BHJ/AKM, FD bracket); (4) is it multiple testing (Romano-Wolf, summary index, pre-trend placebos). One paragraph per family; full tables to appendix.
- **Conclusion** (`sec:conclusion`). From deck's "What the Design Shows": four findings restated, contribution, and an explicit **limitations** paragraph (few effective shocks + few clusters → no LLN, defended on share-exogeneity; extensive-margin first stage → magnitude not identified; municipal-level treatment ≠ single suit).

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

1. **Lock the framing** (§3) — a short decision memo to yourself: volume-vs-role, three-channel-vs-two-faces, novelty phrasing.
2. **Draft the Introduction** (§2) from the extended-abstract prose + deck opening frames, updated to the locked framing and honest confidence tiers (§4).
3. **Write the Abstract** (§6) from the finished intro.
4. **Fill the body** (§5), each section expanding its intro promise, transcribing argument + exhibits from the matching deck frames.
5. **Conclusion + limitations**, then a **pass for tense, overclaiming, and roadmap bloat.**
6. Compile, check no undefined refs/citations, and read the intro *alone* to confirm it stands as a citable summary.
