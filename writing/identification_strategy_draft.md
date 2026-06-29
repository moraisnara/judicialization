# Identification Strategy (draft v2 — committed subject-level instrument)

*Framework: Borusyak, Hull & Jaravel (2025), "A Practical Guide to Shift-Share
Instruments," JEP 39(1):181–204. This draft commits to their **exogenous-shares
(GPSS) path** for the **committed subject-level adversarial instrument**, and states
the assumptions, estimator, inference, and diagnostics that choice entails —
including the parts of the evidence base that are NOT clean and how they are
handled.*

> **Revision note (v2).** The instrument that anchors the paper is the **subject-level**
> adversarial shift-share (224 TSE subjects). Its identifying variation is dominated
> by **propaganda-eleitoral** litigation, and its effective number of shocks is
> **K_eff ≈ 26** (importance) / **≈ 10** (Rotemberg) — it is *not* a few-shocks,
> fraude-centered instrument. (That alternative is the parked act-family design.)
> The framing below is therefore built on the **state-FE mechanics + share-tailoring**
> argument, not on a "too few shocks" claim, and it confronts the propaganda
> dominance directly.

## 1. The instrument

Each municipality $m$ has treatment
$x_m = \Delta\log(1+\text{adversarial lawsuits})_{m,\,2024-2020}$, instrumented with
$$
z_m = \sum_{k} s_{m,k}\, g_{k,-s(m)},
\qquad s_{m,k}=\frac{\text{adversarial lawsuits}_{m,k,2020}}{\sum_{k'}\text{adversarial lawsuits}_{m,k',2020}},
$$
where $k$ indexes adversarial litigation **subjects** (after the mandatory- and
administrative-filing exclusion), $s_{m,k}$ is the 2020 exposure share, and
$g_{k,-s(m)}$ is the **leave-own-state-out** national log-growth of subject-$k$
filings, 2020→2024. Two structural facts govern the analysis:

1. **Shares are complete within the adversarial universe** ($\sum_k s_{m,k}=1$) for
   municipalities with any 2020 adversarial caseload, but ~20% of municipalities have
   **zero** adversarial caseload ($\sum_k s_{m,k}=0$). The shares are therefore
   *incomplete sample-wide*; the Rotemberg decomposition uses the **raw component
   basis** (which sums exactly to the committed instrument), not the fn-9 demeaned
   variant, which is appropriate only under full completeness.
2. **The shift carries a state index.** Because $g_{k,-s(m)}$ is leave-own-state-out,
   it is constant within a state for given $k$. With **state fixed effects**, the only
   within-state variation in $z_m$ enters through the shares $s_{m,k}$ — so the
   estimator is a shares design by construction.

## 2. Why the exogenous-shares path (for THIS instrument)

BHJ offer two justifications: exogenous **shifts** (a share-weighted average of
as-good-as-random national shocks; needs many shocks + a LLN; exposure-robust SEs) or
exogenous **shares** (each share an as-good-as-random exposure under per-share
parallel trends; needs tailored shares; conventional cluster-robust SEs).

For the committed instrument the **shares path is the right frame — but not because of
a few-shocks argument.** With K_eff ≈ 26 the shift-LLN is not obviously unavailable;
the decisive points are instead:

- **State FE neutralise the shift variation.** Leave-own-state-out shifts are
  within-state constant; with state FE, identification runs entirely through share
  variation. The exogenous-shifts interpretation has essentially no within-state
  variation to stand on.
- **The shifts are not credibly exogenous.** National litigation-subject growth is a
  product of the same political and institutional dynamics that move elections; it is
  not a quasi-random supply shock. Share exogeneity (parallel trends across exposed vs
  unexposed municipalities) is the more defensible primitive.

I therefore make **share exogeneity** the identifying assumption, with
exposure-robust SEs reported only as a secondary check.

## 3. Identifying assumption (parallel trends), and the tailoring problem

With the outcome in changes, share exogeneity is a **parallel-trends** condition:
conditional on controls $w_m$, municipalities with high vs low 2020 exposure to a
given litigation subject would have followed the same 2020→2024 electoral trajectory
absent the change in litigation, i.e. $\mathbb{E}[s_{m,k}\varepsilon_m\mid w_m]=0$ for
each consequential $k$. GPSS show 2SLS is a Rotemberg-weighted average of $K$
one-share-at-a-time estimates; validity requires the condition to hold for the shares
that carry weight.

**The tailoring problem is the central vulnerability, and it is acute here.** The
shares that drive this instrument are **propaganda-eleitoral** subjects (the top
Rotemberg and importance weights are almost all "Propaganda Política – Propaganda
Eleitoral" codes, plus electoral-polling disputes). Propaganda litigation is *not*
obviously tailored to a litigation-burden mechanism: a municipality's 2020 propaganda-
dispute exposure may proxy **campaign intensity, media environment, and partisan
competitiveness**, all of which can move 2024 elections through channels other than
subsequent litigation growth. This is exactly BHJ's "generic shares" failure mode.

Two design features partially defend tailoring, and a third is added in response:

1. The mandatory-/administrative-filing **exclusion** keeps only adversarial
   *challenges*, not "having courts."
2. Normalising **within the adversarial caseload** strips overall litigation
   *intensity* from the instrument, leaving only adversarial *composition*.
3. **(New) Non-adversarial conditioning + placebo instrument.** To address the
   generic-shares concern directly, I (a) control for **non-adversarial litigation
   intensity** (the volume of excluded mandatory/administrative filings) so the
   instrument leverages composition conditional on overall litigiousness, and (b)
   construct a **placebo shift-share** from the *excluded* filings and show it has no
   electoral effect and that the main estimates survive conditioning on it. A
   significant placebo would indicate the shares proxy something generic.

## 4. Controls (V3) follow from the parallel-trends logic

- **Census fundamentals (2010):** log population, urban share, log income p.c.,
  higher-education share.
- **Pre-period electoral baseline:** 2016 margin, 2020 valid-vote scale.
- **Per-outcome 2016 lagged level (V3):** each Δ outcome on its own pre-window 2016
  level — the textbook lagged-DV device for parallel trends.
- **Excludes the two 2020 same-outcome levels** ($\text{margin}_{2020}$,
  $\log(1+\text{candidates})_{2020}$): conditioning on the 2020 level of an outcome
  whose LHS is the 2024−2020 change is **Lord's paradox**. `13_lagged_dv_diagnostic.R`
  shows the old mayoral-consolidation "headline" survived only with those levels
  ($F\approx28$ throughout — a spec artifact, not weak-IV) and vanishes under V3.
- **(New) Non-adversarial litigation intensity** enters the robustness column per §3.

## 5. Inference

Primary: **conventional cluster-robust** SEs clustered at the **state** level. Because
$G=26$, I report **wild cluster bootstrap** p-values — specifically the **Anderson–
Rubin wild cluster restricted bootstrap**, which is both few-cluster- and weak-IV-
robust — for the headline coefficients. Exposure-robust (AKM/BHJ) SEs are an appendix.

## 6. Diagnostic evidence base — and what it shows

Per the BHJ shares-path checklist (`03_shares_path_diagnostics.R`):

1. **Rotemberg weights** (raw-component basis; identity $\sum_k\alpha_k\tau_k=\tau_{IV}$
   holds exactly): HHI(α)=0.10, top-1 weight 14.6%, weights concentrated on propaganda
   subjects; 99/164 subjects carry positive weight.
2. **Balance on high-Rotemberg shares — fails where it matters.** 21 of 48
   share×pre-trend coefficients are significant at 5%: the dominant propaganda shares
   *predict* 2016→2020 electoral trends. Reported honestly as the principal threat to
   the design; the non-adversarial placebo (§3) is the targeted response.
3. **Over-identification — rejected for the competition outcomes.** Hansen J p=0.001
   (margin), 0.0002 (winner), 0.043 (runner-up); winner-majority passes (0.14). Under
   homogeneous effects this signals a share-exogeneity violation; under heterogeneous
   effects the 2SLS estimand is a hard-to-interpret complier-weighted object. Either
   reading is consistent with the paper's **null** headline.
4. **Drop-the-dominant-share — the null is robust.** Removing the top one/two
   propaganda shares barely moves the (insignificant) estimates and keeps $F\approx50$.
   So whatever the validity concerns, they do **not** manufacture a spurious effect —
   the estimates are null with or without the dominant shares.
5. **Visual IV / GPSS scatter** ($\delta_k$ vs $\pi_k$; $\beta_k$ vs $F_k$) accompany
   the over-id test.

The honest summary: the committed instrument's **point estimates are null and robust**,
but its **share-exogeneity diagnostics are not clean** (propaganda dominance, pre-trend
imbalance, over-id rejection). The paper's claims are therefore framed as a **robust
null** — "we find no evidence that adversarial-litigation growth shifts electoral
competition" — rather than a precisely-identified causal zero, with the validity
caveats stated plainly and the non-adversarial placebo as the key reassurance that the
nulls are not a generic-shares artifact.

## 7. What the first-stage sign means

The first-stage passthrough governs *complier interpretation*, not validity: on the
shares path the sign of $\hat\psi$ divides out of the IV ratio. The amplification-vs-
convergence reading is a narrative question about which municipalities comply, kept
separate from identification.

---

### One-line summary
For the committed **propaganda-dominated subject-level** instrument, identification is
**shares-based / parallel-trends** (forced by state-FE mechanics, not by few shocks);
V3 lagged-DV controls operationalise it; state-clustered AR wild-bootstrap SEs are the
inference; and the diagnostic suite shows a **robust null** whose chief vulnerability —
the generic-shares concern around propaganda — is addressed by a non-adversarial
intensity control and an excluded-filing **placebo shift-share**.
