> **⚠️ ARCHIVED / STALE — superseded by `docs/STATE_OF_THE_ART.md` (2026-06-26).**
> This document describes the RETIRED substance-family / connected-component design (with the
> old female-candidate headline). It is kept only as version history. For the current act-based
> 10-family design, the authoritative source is `docs/STATE_OF_THE_ART.md` and `code/spec_config.json`.
> _Reason this file is stale:_ it proposes the old substance-defined 7-family taxonomy; the live design uses a flat 10-family **act-based** scheme (act alleged, merging civil+criminal vehicles) built by `01d_act_family_crosswalk.py`.

# Proposed lawsuit-subject family taxonomy

Companion to [`subject_reference_TPU.md`](subject_reference_TPU.md), which lists
all 474 subjects with their official CNJ name, glossary, and TPU branch. This
document proposes (a) **which subjects to drop** and (b) **how to aggregate the
kept ones into families**, grounded in the official TPU tree and in what the
shift-share instrument actually needs.

---

## Method: define families on substance, select instruments downstream

**Families are substantive topics** — "what is this lawsuit *about*?" — defined
**independently of how a topic behaves as an instrument**. Defining families by
shock-behavior would be circular (the outcome data shaping the regressor). Order:

1. **Define families on topic coherence** (exogenous to any result).
2. **Drop on substance / validity only** (filters below) — never on instrument
   strength.
3. **Instrument selection is a separate downstream step** applied to the valid
   topical families, and *reported*, not baked into the definitions.

### Two drop filters (validity, not power)

- **(F-i) Not a dispute-topic.** Administrative routing tags the court attaches to
  every candidacy/office (e.g. `Cargo - Vereador`), procedural/enforcement nodes,
  and non-electoral codes are not substantive electoral disputes → drop.
- **(F-ii) Mandatory-filing exclusion rule.** **Drop any subject that is a
  mandatory filing every candidate/party must make** — its count tracks the
  candidate pool one-for-one, so it mechanically encodes the very outcome we study
  (exclusion violation). **Keep only the adversarial *challenge* to it.** This is
  the request-vs-challenge cut the official TPU tree already makes:
  `11618` RRC (request) → drop, `11616` Impugnação (challenge) → keep;
  `12046` Prestação de Contas – De Candidato (mandatory accounts) → drop, disputes
  over campaign money → keep. `11698` Não Apresentação das Contas is the
  **complement** of presenting (same mandatory universe, just which side of the
  event a candidacy falls on) → drop too.

### The math to report

> Of all **6,232,383** lawsuits (474 subjects, TSE 2020+2024), **48.5% are
> mandatory one-per-candidate/party filings** carrying no usable identifying
> variation — RRC `11618` alone is **42.2%** (2,627,122), DRAP `12044` 5.5%,
> RRCI `11619` 0.2%, mandatory prestação de contas ≈ 0.6%. Registration filings
> alone are **47.9%**. Only the remaining **~51.5%** is potentially adversarial
> litigation where genuine disputes — and identifying variation — can live.
>
> _(Table to be added to the paper/report once the keep-set is locked; computed
> reproducibly from `data/raw/tpu_assunto_reference.csv`.)_

### (F-iii) Minimum-mass rule for a family's shift

A shift-share family's shock is its **leave-one-state-out national log-growth**.
For that shift to be *signal*, the family needs enough national mass; a family
built from a **single leaf with too few cases** yields a shift dominated by
sampling noise, which both inflates its spurious variance share and *attenuates*
the first stage (classical measurement error in Z). This is a statement about
**shift-measurement quality, not outcome behavior** — so it is not circular.

Concretely: `11593 Direito de Resposta` is a single leaf with only **3,085**
national cases. As its own family it carried **~75% of Var(Z)** yet dragged the
first-stage F down to ~7. The fix is **not to drop it** (it is a real electoral
dispute) but to **aggregate it into the substantively correct larger family** so
its shift is computed off that family's mass. Right of reply (Lei 9.504/97 art.
58) is the remedy granted against calumnious/defamatory/false propaganda, so it
belongs with **honor/disinformation**. Tested both homes: folding into honor
gives F = **18.2** (HHI 0.26); into propaganda F = 15.9; dropping it F = 17.2.
Honor wins on strength *and* substance.

### Method validation — the chosen instrument (decided)

The substance-first families were partitioned at several granularities and the
matched first stage estimated in R (`03d_version_first_stage.R`):

| version | families | F | HHI | note |
|---|---|---|---|---|
| G3 | 3 | 4.1 | .51 | coarse |
| G6 | 6 | 6.6 | .61 | misconduct merge; reply still its own shift |
| G8 | 8 | 7.4 | .60 | topical; reply its own shift |
| G11 | 11 | 7.8 | .58 | propaganda by medium; reply its own shift |
| B10 | 10 | 3.5 | .40 | + voterroll + crimes → off-topic dilutes |
| **G8rh** | **7** | **18.2** | **.26** | **HEADLINE: reply→honor** |
| G8rp | 7 | 15.9 | .25 | reply→propaganda (robustness) |
| G10n | 10 | 13.7 | .22 | G11 with reply→honor split-propaganda (robustness) |

**Headline = G8rh**: 7 topical families — `elig`, `abuso`, `conduct`,
`propaganda`, `finance`, `polls`, `honor`(+reply) — 108 codes, 295,073 lawsuits.
Strong (F = 18.2) and many-shock (HHI = 0.26, identification spread across
eligibility .39 / polls .27 / honor .14 / propaganda .11 / conduct .08). Beats
the old narrow gatekeeping core (F≈16, ~1 effective topic) on both strength and
spread with **zero topics dropped**. Off-topic domains (voterroll T9, crimes T11)
excluded — they cut F to 3.5 (B10) and are not about candidate litigation.

_The family list below (Section B) is being revised to match the decided G8rh
partition; the DROP logic (Section A) already follows the filters above._

---

## A. DROP — and why

### A1. Registration mechanics (fails test #2 — exclusion)
Official branch *Candidatos > Registro de Candidatura*. These are the request-to-
register filings and their bookkeeping; their count tracks the candidate pool
one-for-one, so they are mechanically tied to every candidate-composition outcome.

| code | name | vol |
|---|---|---|
| 11618 | RRC – Candidato | 2,627,122 |
| 12044 | DRAP – Partido/Coligação | 344,425 |
| 11617 | Preenchimento de Vaga Remanescente | 29,347 |
| 11621 | Substituição – Por Cassação | 21,116 |
| 11619 | RRCI – Candidato Individual | 13,226 |
| 12363 | Cancelamento de Registro | 1,237 |
| 11627, 11625, 11620, 11622, 11624, 11626, 11623, 11615 | substitution/registration bookkeeping | <1,300 each |
| 14941 | Percentual de Gênero | 40 |
| 15018 | Candidatura Avulsa | 8 |

**Keep the one true contest in this branch:** `11616 Impugnação ao Registro de
Candidatura` (the *challenge* to a registration, Art. 3 LC 64/90) — see family **F1**.
The official tree itself separates the request (11618) from the challenge (11616);
dropping the request while keeping the challenge is faithful to the leaf-level
distinction.

### A2. Office / mandate labels (fails test #1 — not litigation)
Official branch *Cargos*. `Cargo - Vereador` (2.3M), `Cargo - Prefeito` (110k),
etc. are **classification tags** for which office a case concerns, not a distinct
adversarial subject. Codes: 11638, 11633, 11640, 11637, 11628, 11629, 11630, 11641.

### A3. Internal party administration (fails test #1)
*Órgão de Direção Partidária* (213k via 11767 alone), party creation/merger,
provisional commissions, statutory changes, coligação registration: 10741, 11763,
11769, 11748, 11764, 11765, 11766, 11768, 15089, 11750, 11751, 11752, 11753,
11772–11776, 11770, 11771. Party plumbing, not electoral disputes over candidates.

### A4. Filiação / desfiliação bookkeeping (fails test #1)
12586, 11757, 11756, 11758, 12585, 11760, 11761. Membership record-keeping.

### A5. Voter roll administration (fails test #1)
*Alistamento Eleitoral* (domicílio, cancelamento, inscrição, exclusão, fraude,
duplicidade, estrangeiro): 11576, 11575, 11579, 11578, 11577, 12564, 12563, 15308,
12605, 12566, 11580–11582. Administrative roll maintenance.

### A6. Results / vote-count / election-event labels (fails test #1)
*Resultados*, *Eleições - N Turno*, apuração, quociente: 11714, 11638-adjacent
event codes 11642–11647, 11715, 12642. Procedural/event tags.

### A7. Procedure, enforcement, writs, requests (fails test #1)
Execução, cautelar inominada, liminar, tutela, exceção, citação/intimação/oitiva,
requerimento, providência, diligências, habeas corpus, suspensão condicional,
COVID-19, auxílio emergencial, etc.: 12366, 11731, 11730, 11732, 11734–11738,
9196, 12416, 12417, 11782–11786, 11778, 12598, 12599, 12463, 11704, 11705, 10602,
12731, 12732, 11740, 11742, 11746, 12612, 12754, and the rest of the unrooted
*Requerimento/Cautelar/Execução* nodes.

### A8. Non-electoral criminal & common-law codes (outside the electoral root)
The 161 codes the official tree resolves **outside** `DIREITO ELEITORAL` — generic
calúnia/difamação/injúria (3395–3402…), furto/roubo/estelionato, drogas, armas,
homicídio, peculato, lavagem, etc. They appear only as incidental classifications
and have no electoral shift meaning. **Exception:** the *honra-on-propaganda* leaves
that DO live under the electoral root are kept as family **F7** below.

---

## B. KEEP — family aggregations

Families are defined as unions of official TPU leaves. The first three are the
**identifying core** (the recommended instrument); the rest extend coverage for
the "all electoral topics" robustness instrument.

### Core (recommended headline instrument = F1 ∪ F2 ∪ F3)

**F1 — `impugnacao_registro` (candidacy challenge).** The single atomic challenge
to a registration. `11616` (22,327). The lone instrument-grade contest in the
registration branch; carries the bulk of national shift power.

**F2 — `inelegibilidade` (ineligibility).** Official *Candidatos > Inelegibilidade*,
all 18 leaves: 11596, 11605, 11600, 11604, 11598, 11595, 11597, 11602, 11607,
11603, 14939, 14938, 12392, 11601, 11606, 11610, 14936, 11599 (5,866). Disputes
over whether a candidate is legally barred — the substantive gatekeeping contest.

**F3 — `abuso_poder` (abuse of power).** Official *Transgressões Eleitorais > Abuso*:
11718 (econômico), 11719 (político/autoridade), 11720 (meio de comunicação), 11717
(16,609). Post-registration challenges to a candidacy's legitimacy.

> These three are the **contested-eligibility** instrument already validated:
> strong, clean first stage (F ≈ 158), and the only set with genuine national
> leave-one-out shift variation. **Recommended as the headline instrument.**

### Extended electoral families (for the "all topics" robustness instrument)

**F4 — `conduta_campanha` (campaign conduct/transgressions).** Remaining
*Transgressões Eleitorais*: 12063 (conduta vedada ao agente público), 11721
(captação ilícita de sufrágio), 12062 (captação/gasto ilícito de recursos), 12597
(candidatura fictícia), 11722 (corrupção/fraude), 11723 (propaganda institucional),
11716 (8,841 total). Genuine contests but thin, low national shift power.

**F5 — `propaganda` (campaign advertising), split by medium.** Official
*Propaganda Política - Propaganda Eleitoral* (67 codes, 206,955). High volume but
weak shift identification. Keep the existing medium split:
- `propaganda_digital`: 11679, 12637, 12639, 12638, 12636 (internet, redes sociais, apps, impulsionamento, telemarketing)
- `propaganda_broadcast`: 11670–11676, 11663, 11669, 11677 (rádio/TV/horário gratuito/imprensa)
- `propaganda_rua`: 11654–11662, 11664, 11665, 11668, 11681, 11682, 15016, 11683 (físical: alto-falante, banner, adesivo, outdoor, comício, carreata…)
- `propaganda_outras`: residual propaganda leaves + 11667 (extemporânea), 11678, 11680, 11652, 11666.
- Disinformation leaves 12635 (notícia sabidamente falsa) and 15405 (desinformação sobre integridade) → fold into **F7**.

**F6 — `financas_campanha` (campaign finance).** Official *Recursos Financeiros* +
*Prestação de Contas*: 12046, 12069, 12602, 11698, 11695, 11692, 11697, 12725,
11696, 14220, 11699–11701, 15304, 11690, 11691, 11684, 12047, 12048, 14225, 12045
(≈42,000). Contests over money in campaigns.

**F7 — `honra_desinformacao` (electoral honor/disinformation).** The electoral-root
honor + disinformation leaves: 11484 (calúnia na propaganda), 11486 (difamação),
11487 (injúria), 11485 (falsa imputação), 11483 (fatos inverídicos), 12635 (notícia
sabidamente falsa), 15405 (desinformação), 15143/15142 (violência política de
gênero). Information-environment litigation around candidates.

**F8 — `pesquisa` (electoral polls).** Official *Pesquisa Eleitoral*: 11649, 11651,
11650, 11648, 11524, 11495, 11523 (≈33,000). Polling-conduct disputes.

**F9 — `direito_resposta` (right of reply).** 11593 (3,085). Candidate-protection
remedy; optional, low shift.

---

## C. Summary of the recommendation

| | Families | Codes | Use |
|---|---|---|---|
| **Headline instrument** | F1, F2, F3 | impugnação 11616 + 18 ineleg. + 4 abuso = 23 | **contested-eligibility**, F≈158, clean |
| **"All topics" robustness** | F1–F9 | ~all electoral-root adversarial leaves | shows the headline is not cherry-picked |
| **Dropped** | A1–A8 | registration mechanics, office/party/roll labels, procedure, non-electoral crimes | fail one of the three tests |

**Bottom line.** The official tree confirms the design intuition: only the
*contested-eligibility* leaves (challenge-to-registration + ineligibility + abuse-
of-power) are simultaneously adversarial, exclusion-safe, and nationally shifting.
Propaganda/finance/polls add coverage but little identification and belong only in
the "all topics" robustness instrument — not the headline.

_Sources: [`subject_reference_TPU.md`](subject_reference_TPU.md); official TPU via
`code/01_download/03_download_tpu_assuntos.py`. Family code lists to be encoded in
`data/clean/subject_taxonomy_PROPOSED.csv` on approval._
