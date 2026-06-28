# SIG municipality lawsuit redesign — design log

**Period:** 2026-06-24. **Status:** exploration complete; family taxonomy proposed,
not yet committed to code. **Standing directive:** the identification design is
*unsettled*; every generation is preserved as a revisitable version, never deleted;
research-question fit is checked before mechanics (see memory
`design_not_settled_preserve_versions`).

This log records, end to end, the work that moved the lawsuit data from the old
zona-level reconstruction to the new SIG municipality microdata, the descriptive
evidence gathered, and every keep/drop/family decision with its motivation.

---

## 0. Research question this serves

Does the **judicialization of electoral competition** affect elections?
"Judicialization" = the expanded role of the judicial arena in the election, via
two channels: (1) **institutional/supply** — TSE rule growth gives the court more
to police; (2) **strategic/demand** — candidates weaponize lawsuits offensively
(attack rivals) and defensively. The object of interest is the *climate / noise*
of litigation, at the **macro (place) level**, not the effect of being sued on a
single candidate. Identification = a topic shift-share (Bartik) instrument à la
Ash, Morelli & Vannoni (2025): pre-period topic shares × leave-out topic growth.

Two problems were open going in:
- **(i)** Lawsuit geography was only the electoral **zona**, nested inside
  municipalities — forcing a coarse connected-component unit (only ~9% of
  municipalities kept their identity; 91% merged into clusters).
- **(ii)** Topic choice: which lawsuit types count, and how to build the shock
  families.

---

## 1. New data source — SIG TSE "Processos eleitorais" (solves problem i)

The SIG Eleição export (sig.tse.jus.br) resolves each lawsuit to its **Município
de origem**, not just the zona. We verified this is a *genuine within-zona split*,
not a zona-seat label:
- 62–64% of zonas map to >1 município; in a multi-município zona the dominant
  município holds only ~52% of cases at the median — the rest spreads.

**Decision:** adopt SIG as the **main lawsuit source**; demote the old raw-TSE
build (`01_lawsuit_panel.py` → `zona_lawsuit_panel.csv` + component
reconstruction) to a stale version (archived to `code/_archive/02_build/`, data
CSVs preserved). The component-instrument web (`02_build/instrument/`, `05d/05e`)
stays in place until the new instrument design is chosen, then is ported/archived.

**Why:** the SIG data lets the instrument be built at the **true municipality
unit**, eliminating the zona→component coarsening and the many-to-many duplication
that historically inflated the first stage (memory
`many_to_many_inflates_first_stage`).

### Files and schema
Two SIG exports in `data/raw/` (sep=';', latin-1, **both are zips**; the 2024 one
is named `.csv` but is a zip):
- `processos_eleitorais.csv.zip` — 2020 (1,409,024 processos)
- `processos_eleitorais_2024.csv` — 2024 (1,173,683 processos)

12 columns: Ano de eleição; Assunto principal; Classe; **Data de distribuição**;
Município de origem; **Tipo de origem** (Originário/Recursal); UF de origem; Zona;
Quantidade de decisões; Quantidade de processos; Tempo médio de tramitação; Data
de carga. (An earlier 2020 export had `Candidato parte`—uniformly 0, useless—and
`Instância` instead of the filing date + origin type; the richer one replaced it.)

**Reconciliation vs the old zona panel (2020):** SIG total 1.41M vs old 1.27M
(ratio 1.11); class-by-class the big buckets match ~exactly (Registro de
Candidatura 623,922 vs 622,608 = 99.8%). The gap is the old build's pre-election
date cutoff; same universe, SIG richer.

**Known gap:** SIG has **no 2016** — a bottleneck only for a pre-period
placebo/pre-trend arm or a pre-2020 share base. The core 2020→2024 instrument does
not need it; source 2016 elsewhere (raw `processo_eleitoral_2016`) if/when needed.

---

## 2. Name→IBGE crosswalk

SIG gives município **name + UF**, not a code. Matched against
`bd_diretorio_municipio.csv` (basedosdados: nome, sigla_uf → id_municipio IBGE +
id_municipio_tse) on accent-stripped uppercase name.

- **99.99% of lawsuit volume matched** after a within-UF fuzzy pass (resolves
  TSE↔IBGE spelling variants: Itapajé/Itapagé, Munhoz de Mello/Melo, Santa
  Izabel/Isabel, Florínea/Florínia, Gracho Cardoso, Poxoréu, Iguaraci/y) + one
  manual override (**Assú/RN == Açu**, IBGE 2400208).
- Zero homonym collisions in the directory (name+UF is unique).
- **Only drop:** Boa Esperança do Norte/MT (132 procs) — a municipality whose
  creation was suspended by the STF and never installed, so it has no IBGE code.

Crosswalk written to `data/clean/sig_muni_name_to_ibge.csv` (audit trail).

---

## 3. Two parallel panels built

Builder: `code/02_build/00_sig_lawsuit_panel.py`. Outputs in `data/clean/`:
- `sig_lawsuits_muni_zona_assunto.csv` — year × município × zona × **assunto** (205,829 rows)
- `sig_lawsuits_muni_zona_classe.csv` — year × município × zona × **classe** (106,000 rows)

Coverage: 5,569 municipalities (full universe), ~2,920 zonas, 2020 + 2024.

**Design principle — choices as columns, not baked-in filters.** Each row carries
`n_proc` (all), `n_proc_orig` (Originário = 95.4%), `n_proc_pre_eleic` (filed by
1st-round election day = 90.9%), `n_dec`, `tempo_med_dias`. Mandatory filings are
kept and flagged, not pre-dropped. This keeps every downstream design choice
(originário filter, pre-election cutoff, mandatory exclusion) revisitable without
rebuilding — consistent with the preserve-versions directive. Two taxonomies
(assunto vs classe) kept on purpose so the family scheme is chosen from evidence.

---

## 4. Descriptive evidence

### 4.1 Subject (assunto) composition — `30_sig_subject_shares.py`
National / state / municipality-mean shares. Findings:
- **Registration bureaucracy dominates:** top subjects are RRC (38.5%) + `Cargo –
  Vereador` (36.4%, an *office tag* not a dispute type) + Órgão de Direção (4.9%)
  + DRAP (4.4%). **Top-10 subjects ≈ 90%** of all lawsuits.
- **Adversarial subjects are a sparse tail:** each appears in only 20–40% of
  municipalities — at the municipality unit most subject cells are zero.
- **Large cross-state dispersion that looks like coding practice:** `Cargo –
  Vereador` 0.9%→39.6%, `Requerimento` 0.14%→22.2% across states.
- National > muni-mean for adversarial subjects = concentration in a minority of
  (large) municipalities.

### 4.2 Class (classe) composition — `31_sig_class_shares.py`
Same metrics on the procedural-class panel. Findings:
- Mandatory dominance even higher: RRC 44.3% + Prestação 42.6%; **top-10 ≈ 97%**.
- **The class dimension is far denser at the municipality level:**
  `Representação` is present in **78%** of municipalities (AIJE 46%, Petição Cível
  61%), vs the best adversarial *subject* at only 25%. Big point for class as a
  shift-share basis — fewer zero cells.

### 4.3 Coding compatibility / reconciliation — `32_sig_coding_compatibility.py`
- **A. Nestedness.** U(classe|assunto)=0.885, U(assunto|classe)=0.602 → the two
  fields are ~88% a single hierarchy (assunto refines classe), **not** orthogonal
  rival schemes. "assunto vs classe" is largely a choice of *resolution level*.
- **B. Mandatory reconciliation.** Defining the mandatory bucket independently
  under each field, they **agree for 98.0% of lawsuits** → the drop decision is
  robust to taxonomy choice. Settled.
- **C. Cross-TRE stability.** Mandatory noise floor (RRC) CV = 0.05. All
  adversarial categories sit above it (CV 0.33–3.18), but instability is
  concentrated in **residual/admin** classes (Inquérito 3.18, Petição Cível 1.54,
  Composição de Mesa 0.93); the **core adversarial families are the stablest**
  (Representação 0.36, AIJE 0.33). Mean CV is a near-tie (classe 1.05 vs assunto
  0.91) → stability does not decisively favor either field. Caveat: CV conflates
  genuine geographic variation with coding practice; the floor is the mechanical
  minimum only.
- **D. The genuine incompatibility.** A *propaganda* complaint is split across
  classes — 64% Representação, 19.5% Notícia de Propaganda, 6.2% Direito de
  Resposta — **and the split varies by TRE** (share filed as Representação runs
  23%→86%, median 70%). Same substance, different class label by court.

**Conclusion of §4:** define families on **substance, pooling both fields** —
licensed because they are 88% nested and 98% agree on the drop. This neutralizes
the TRE class-vs-assunto coding choice (D), keeps the stable core (C), inherits
the robust drop (B), and is denser than subject-alone (4.1 vs 4.2).

---

## 5. Keep / drop class decisions — `33_sig_class_subject_breakdown.py`

The partition is **three-way**, not binary (correction logged: "adversarial" had
loosely swept in admin classes). Validated by reading the subjects inside each
class. Three revelations forced the substance-first approach:
1. **`Representação` is mostly propaganda by subject** (extemporânea, notícia
   falsa, internet, redes sociais, pesquisa fraudulenta) — a class-based
   "representação" family is a propaganda bucket in disguise.
2. **`Impugnação ao Registro de Candidatura` (adversarial) is buried inside the
   mandatory `Registro de Candidatura` class** (~0.7%, ~8k cases) — a pure
   class-drop loses it.
3. **`Ausência/Abandono aos Trabalhos Eleitorais`** — the top adversarial-looking
   *subject* in §4.1 — is 91% of `Composição de Mesa` = **poll-worker no-shows**,
   pure admin. Subject-alone would have invented a false family.

| Bucket | Classes | Decision & motivation |
|---|---|---|
| **Mandatory mass-filing — DROP** | Registro de Candidatura, Prestação de Contas, Req. Regularização de Omissão, Filiação Partidária, Lista de Apoiamento | Every candidate/party must file; not judicialization. ~87% of volume. (memory `mandatory_filing_exclusion_rule`) |
| **Administrative — DROP** | Composição de Mesa (91% poll-worker no-shows), Apuração de Eleição (vote tally), Recurso de Alistamento (voter reg.), Cartas Precatórias/de Ordem (procedural letters), Pet-Adm, Processo Administrativo, Execução de Medidas Alternativas | Electoral-management / ancillary procedure, not candidate disputes. |
| **Adversarial — KEEP** | Representação, Notícia de Propaganda, AIJE, Direito de Resposta, Representação Especial, AIME, Tutelas (Cautelar/Antecipada Antecedente) | Candidate-vs-candidate challenges = the judicialization. Tutelas folded into the action they support. |
| **Criminal — KEEP, toggleable** | Ação Penal Eleitoral, Representação Criminal/Notícia de Crime, Inquérito Policial, Termo Circunstanciado | Real electoral crimes (corrupção, vote-buying, boca de urna, falsidade) but **police/MP-initiated** (channel 1), leans "signal" not strategic "noise". Carry as a separate family that can be toggled in/out of the headline. |
| **Judgment calls — RESOLVED** | Petição Cível → DROP (admin requerimentos, most TRE-unstable). Cumprimento de Sentença → DROP (enforcement *downstream* of an already-counted case — double counts; keep aside as optional intensity measure). Suspensão de Órgão Partidário → DROP (party-internal compliance). | Resolved by reading their subjects. |

---

## 6. Substantive family crosswalk + aggregation ladder (BUILT, audited 2026-06-24)

Decision (2026-06-24): family granularity is **not fixed** — a whole aggregation
**ladder** is tested as robustness; **criminal is in the headline** (not toggled
out). Built by `code/02_build/01_family_crosswalk.py`: one substance-based
`(classe, assunto) → family_micro` map (the floor) plus a ladder that collapses
it upward, so the same base map drives every robustness rung.

### 6.1 Architecture = WHITELIST (the §5.5 audit corrected a blacklist)
The first build *blacklisted* mandatory/admin classes and treated everything else
as adversarial. The audit found this swept ~40 minor procedural/fiscal/admin
classes **and** downstream criminal-enforcement incidents into the kept set. The
build now **whitelists** the kept classes and drops everything else (logging the
dropped tail). Three audit corrections (all implemented):
- **criminal = ORIGINATING accusations only, by CLASS.** Kept: Ação Penal Eleitoral,
  Representação Criminal/Notícia de Crime, Inquérito Policial, Termo Circunstanciado,
  **PIC-MP** (added). Downstream enforcement (Auto de Prisão, Execução da Pena,
  Habeas Corpus, …) now **drops** — same anti-double-count logic as Cumprimento de
  Sentença.
- **No subject-keyword crime routing.** Criminal status follows the procedural
  vehicle (class), never a subject word. Fixes `Captação Ilícita de Sufrágio`
  (art. 41-A is **civil**-electoral, prosecuted via AIME/AIJE/Representação,
  art. 22 LC64) → now `abuse_economic`, not criminal.
- **Mandado de Segurança Cível dropped** (procedural remedy, ~833) and the
  procedural/fiscal tail dropped via the whitelist (see audit trail in script).

### 6.2 Assignment rules (pooling both fields — the reconciliation)
- rescue `Impugnação ao Registro de Candidatura` (from RRC *and* Petição Cível)
  → `candidacy_challenge`;
- class ∈ originating-criminal whitelist → criminal subfamily (by crime substance);
- class ∈ core-adversarial whitelist → routed by **assunto** substance, priority:
  poll → disinfo → right-of-reply → propaganda-conduct → finance → abuse-econ →
  abuse-pol → challenge → residual;
- everything else → `drop`.

### 6.3 The floor is a 12-family MICRO level (more families, where breakable)
Per request (2026-06-24), several families split into doctrinally meaningful
subfamilies at the floor; thinner families (polls, finance, candidacy, residual)
have no defensible sub-axis and stay whole. `micro12` coverage (both years,
2,582,707 processos; `output/tables/descriptives/sig_family_coverage.csv`):

| micro family | n | % | fine7 parent | substance |
|---|---|---|---|---|
| propaganda_conduct | 84,999 | 3.29% | propaganda_disinfo | medium/timing violations (internet, redes, extemporânea, banner) — *noise* |
| disinformation | 18,435 | 0.71% | propaganda_disinfo | notícia sabidamente falsa, fatos inverídicos, **pesquisa fraudulenta** — *signal corruption* |
| other_adversarial | 13,364 | 0.52% | other_adversarial | adversarial-class rows tagged only by office/procedure (Cargo-*, Requerimento) |
| abuse_economic | 11,180 | 0.43% | abuse_power | poder econômico, captação ilícita de sufrágio (41-A), candidatura fictícia |
| crime_other | 9,471 | 0.37% | criminal_integrity | criminal accusations outside the vote/speech keyword sets |
| candidacy_challenge | 9,122 | 0.35% | candidacy_challenge | impugnação ao registro (rescued) + inelegibilidade/condição |
| crime_vote | 7,324 | 0.28% | criminal_integrity | corrupção eleitoral, boca de urna, arregimentação, captação de votos |
| abuse_political | 6,858 | 0.27% | abuse_power | poder político/autoridade, conduta vedada, improbidade, uso de meio |
| electoral_polls | 6,270 | 0.24% | electoral_polls | pesquisa registro/metodologia/acesso (non-fraudulent) |
| crime_speech | 6,199 | 0.24% | criminal_integrity | calúnia, difamação, injúria, falsidade ideológica |
| campaign_finance | 4,363 | 0.17% | campaign_finance | doação acima do limite, captação/gasto ilícito |
| right_of_reply | 1,291 | 0.05% | propaganda_disinfo | direito de resposta |

→ **KEPT (instrumented) = 178,876 = 6.93% of all lawsuits** (vs 7.09% pre-audit;
the 0.16 pp drop is the enforcement-incident + MS Cível removal — coverage
essentially intact, families now clean).

### 6.4 Aggregation ladder (floor → coarse; criminal kept until triad3; `drop` never instrumented)

| scheme | # | families |
|---|---|---|
| `micro12` | 12 | the floor above |
| `fine7` | 7 | propaganda_disinfo · electoral_polls · abuse_power · campaign_finance · candidacy_challenge · criminal_integrity · other_adversarial |
| `med6` | 6 | finance folded into abuse |
| `coarse4` | 4 | finance+candidacy→abuse, polls→propaganda → propaganda · abuse · criminal · other |
| `triad3` | 3 | information_env(propaganda+polls) · strategic_attack(abuse+fin+chal+other) · criminal |
| `lump1` | 1 | single `judicialization` shock |

The `micro12` → `fine7` aggregation is exact (propaganda subfamilies sum to
104,725; abuse subfamilies to 18,038; crime subfamilies to 22,994).

Supersedes the class-only `class_folded` (substance-defined and coding-invariant);
`class_folded` retained as a prior version.

**Decided judgment calls (this audit):** poll-registration disputes kept as a
**separate** `electoral_polls` family (fraudulent polls → `disinformation`);
Mandado de Segurança Cível **dropped**.

---

## 7. Decisions ledger

| # | Decision | Motivation | Status |
|---|---|---|---|
| D1 | SIG = main lawsuit source; old zona/component build → stale | resolves zona-nesting; enables true municipality unit | DONE (old builder archived) |
| D2 | Build at município unit via name+UF→IBGE crosswalk | 99.99% match; drops only a non-installed muni | DONE |
| D3 | Carry originário/pre-election/mandatory as columns, not filters | keep every choice revisitable (unsettled design) | DONE |
| D4 | Mandatory drop is taxonomy-independent | 98% class/subject agreement | CONFIRMED |
| D5 | Three-way class partition (mandatory/admin/adversarial+criminal) | subject content of each class | CONFIRMED |
| D6 | Families defined on substance pooling both fields | nestedness 0.88 + propaganda split by TRE | BUILT (`01_family_crosswalk.py`) |
| D7 | Family granularity not fixed → aggregation ladder (micro12…lump1) tested as robustness | design unsettled; granularity is itself a spec choice | DECIDED |
| D8 | criminal_integrity IN the headline | treat full litigation climate as the judicialization shock | DECIDED |
| D9 | WHITELIST architecture; criminal = originating accusations only (PIC-MP added, enforcement incidents dropped); no subject-keyword crime routing; MS Cível dropped | audit: blacklist swept procedural/fiscal tail + double-counted enforcement; 41-A is civil | DONE (rebuilt, KEPT 6.93%) |
| D10 | `micro12` floor adds subfamilies (propaganda: disinfo/conduct/reply; abuse: econ/pol; crime: vote/speech/other) | request: a more-granular rung where doctrinally breakable; signal-vs-noise axis | DONE |
| D11 | Canonical join key = minted integer `pair_id` (1 per distinct classe×assunto); long names live only in the crosswalk dictionary; official `cod_classe`/`cod_assunto` attached reference-only (99.4%/91.2% exact match, never a merge key) | SIG ships NO codes (names only); don't carry ~50-char strings as keys through panels/estimation; partial official-code match must not corrupt the instrument | DONE (joint panel + bridge now key on `pair_id`; muni already on IBGE/TSE codes) |
| D12 | Split the archived `02_bartik_inputs.py` outcome half into a live outcomes-only builder `03_candidate_composition.py` (composition functions verbatim; instrument code dropped); rename `03_vote_outcomes.py`→`03b_vote_outcomes.py` | reproducibility: outcomes were rooted in an archived script; the live pipeline must regenerate them with no archived dependency | DONE (5,571 munis, 5-char keys; numbers unchanged) |
| D13 | Stage-3 assemble rewired to the SIG family IV: long `municipality_bartik_iv.csv` pivoted WIDE (one `bartik_iv_<rung>` per muni) before a one-to-one merge; every join carries explicit `validate=` + a row-in/row-out ledger; headline alias = `fine7`; `cluster_id` = state; family-split IV (`01c_family_ivs.py`) reads `municipality_family_components.csv` at the headline rung | user requirement: no many-to-many, no duplication; pivot-then-join is the structural guard, `validate=` the hard check | DONE (exec 5,571 / leg 5,389; 173 munis no instrument, logged) |

The full ordered build→assemble→merge chain now lives in `docs/PIPELINE.md`.

---

## 8. Open items / next steps

1. **Re-run §4 share + cross-TRE CV on the families** — the propaganda-family CV
   should fall sharply vs the class split if the reconciliation works (test of the
   whole approach).
2. Build the municipality-level Bartik components on each ladder rung; first stage
   at the municipality unit; weak-IV-robust inference.
3. 2016 pre-period: decide source or alternative placebo.
4. Port/archive the old component-instrument pipeline once the new design is set.

## 9. Scripts produced this session
- `code/02_build/00_sig_lawsuit_panel.py` — build the two municipality panels + crosswalk
- `code/02_build/01_family_crosswalk.py` — substance-based (classe,assunto)→family map + aggregation ladder
- `code/04_analysis/30_sig_subject_shares.py` — subject shares (nat/state/muni-mean)
- `code/04_analysis/31_sig_class_shares.py` — class shares (same metrics)
- `code/04_analysis/32_sig_coding_compatibility.py` — nestedness, mandatory reconciliation, cross-TRE CV, propaganda split
- `code/04_analysis/33_sig_class_subject_breakdown.py` — subjects within every keep/drop class
