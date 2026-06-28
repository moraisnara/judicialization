> **⚠️ ARCHIVED / STALE — superseded by `docs/STATE_OF_THE_ART.md` (2026-06-26).**
> This document describes the RETIRED substance-family / connected-component design (with the
> old female-candidate headline). It is kept only as version history. For the current act-based
> 10-family design, the authoritative source is `docs/STATE_OF_THE_ART.md` and `code/spec_config.json`.
> _Reason this file is stale:_ its power/MDE/bounds null defense is built on the retired `bartik_iv_2020_2024` design and its companion `INSTRUMENT_ROBUSTNESS.md` (K_eff ≈ 3); the null must be re-defended on the act instrument and under the broadened voters-and-candidates framing.

# Defending the null: power, bounds, and the mechanical footprint

The paper's central empirical claim is a **null**: adversarial electoral
litigation does not measurably move candidate composition (groups A–D) or voter
behaviour. A null is only persuasive if (1) the design could have detected a
policy-relevant effect, and (2) the design demonstrably has teeth — it moves the
mechanically-proximate quantities where one must exist. This memo assembles both.

Companion: [INSTRUMENT_ROBUSTNESS.md](INSTRUMENT_ROBUSTNESS.md) (the instrument is
relevant but concentrated; K_eff≈3; the one marginal result fails weak-IV /
exposure-robust inference).

## 1. Minimum detectable effects (`23_mde_power.R`)

Per outcome we report the weak-IV-robust 95% CI (coef ± tF·SE), the 80%-power MDE
((tF+z₀.₈)·SE, using the per-row tF critical value so the bound is honest about
the weak instrument), and the MDE as a fraction of the 2020 baseline level.

Representative outcomes:

| Outcome | β̂ | 95% CI (tF) | MDE | base | MDE/base |
|---|---|---|---|---|---|
| **Candidates, executive** | | | | | |
| Female | −0.005 | [−0.076, 0.066] | 0.099 | 0.131 | **0.76** |
| Non-white | −0.076 | [−0.176, 0.024] | 0.140 | 0.331 | 0.42 |
| Higher-ed | 0.040 | [−0.065, 0.144] | 0.146 | 0.599 | 0.24 |
| **Candidates, legislative** | | | | | |
| Female | 0.015 | [−0.005, 0.036] | 0.028 | 0.216 | **0.13** |
| Non-white | −0.002 | [−0.050, 0.046] | 0.067 | 0.464 | 0.14 |
| Higher-ed | −0.002 | [−0.031, 0.027] | 0.040 | 0.293 | 0.14 |
| **Voter behaviour** | | | | | |
| Null votes | −0.011 | [−0.022, −0.000] | 0.015 | 0.042 | 0.36 |
| Non-valid votes | −0.016 | [−0.034, 0.002] | 0.025 | 0.061 | 0.41 |
| Blank votes | −0.005 | [−0.014, 0.005] | 0.013 | 0.019 | **0.69** |

**Overall: 20 of 28 estimated outcomes are well-powered** (MDE < 50% of baseline).
The verdict is heterogeneous and must be stated honestly:

- **Tightly-bounded nulls (claim "no effect"):** legislative candidate composition
  (MDE 13–14% of baseline), legislative fragmentation, turnout. The design would
  detect modest effects here and finds nothing.
- **Wide CIs (claim "cannot rule out moderate effects," NOT "no effect"):**
  **executive female share** (MDE 76% of baseline) and **blank votes** (69%).
  These are underpowered; calling them precise nulls would overclaim.
- **Delta-defined outcomes** (e.g. winner-is-new-vs-2020) have no meaningful 2020
  baseline; read them off the raw CI, not the ratio.

Implication for the write-up: replace blanket "precisely-estimated null" language
with outcome-specific bounding. The legislative and turnout results carry the null
claim; the executive single-winner outcomes are honestly inconclusive (small N of
effective events per municipality + a single contest = inherently noisier).

## 2. Does the design have teeth? Mechanical footprint

The ideal manipulation check — does litigation **bar candidates** (the
mechanically first-order effect of an eligibility challenge)? — **cannot be built
from current data.** TSE's candidacy-aptitude field `DS_SITUACAO_CANDIDATURA`
(APTO/INAPTO) is populated for 2020 but is entirely `#NE` (blank) in the 2024
registry release; `DS_SIT_TOT_TURNO` carries the electoral *result*, not the
registration status. A first-differenced barred-rate outcome is therefore
infeasible and is not constructed. (Revisit if TSE republishes 2024 aptitude.)

The available proxy is the **effective number of candidates / parties** (group C):
a successful challenge mechanically removes candidates, so litigation should push
these down. Results:

| Outcome | office | coef | p | MDE/base | well-powered |
|---|---|---|---|---|---|
| eff. N candidates | executive | −0.100 | 0.19 | 0.10 | yes |
| eff. N candidates | legislative | −0.643 | 0.56 | 0.09 | yes |
| eff. N parties | legislative | −0.340 | 0.16 | — | yes |

The sign is **negative in every case — the direction candidate-barring predicts** —
but the magnitude is small and insignificant, and the (well-powered) legislative
estimate is a tight null. Combined with a strong first stage (F=18.2), this says:
the instrument robustly moves the *volume* of litigation, that litigation points
the predicted direction on candidate counts, but its footprint on realized
composition is at most faint. This is evidence of a true small/zero effect, not of
a design that cannot see anything.

## 3. The argument, assembled

1. **Relevance:** first stage F=18.2; the instrument demonstrably moves litigation.
2. **The design can detect effects** of 13–42% of baseline for most outcomes; it
   finds none. For the few underpowered cells (executive female, blank votes) we
   say so and decline to claim a null.
3. **The mechanism points the right way but faintly:** litigation → fewer effective
   candidates (correct sign), too small to register.
4. **The lone marginal signal (null votes)** is exactly where weak-IV and
   exposure-robust inference tell us to withhold confidence — so it does not
   undercut the null; it illustrates the discipline.

Net: across the outcomes the design is powered to speak to, adversarial electoral
litigation has no economically meaningful effect on who runs, who wins, or how
voters behave. The result is a bounded, design-robust null — with the executive
single-winner margins flagged as inconclusive rather than null.
