# Mechanical Defect Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair three confirmed mechanical defects in the estimation pipeline — a share-balance test that is arithmetically zero, a robustness spec that silently does nothing, and three "change" outcomes whose 2020 term is identically zero — and record how each repaired number compares to the result it replaces.

**Architecture:** Three independent defects in three different files, each fixed at its source and then propagated by re-running the affected stage. Task 4 collects the before/after numbers into one comparison table, which is the actual deliverable: none of these fixes is interesting on its own, only the delta against what we currently report. Tasks 1–3 can be done in any order; Task 4 depends on all three.

**Tech Stack:** Python 3.13 (`C:\Users\naral\AppData\Local\Programs\Python\Python313\python.exe`), R 4.6.0 / `fixest` (`C:\Program Files\R\R-4.6.0\bin\Rscript.exe`), pandas, numpy, scipy.

## Global Constraints

- All regression output (coef/SE/F that could reach a slide or the paper) runs in **R/fixest, never Python**. Python is for data construction and descriptives only.
- `csv` is the source of truth; a `.tex` is only its deck rendering. Never hand-edit a generated `.tex`.
- **Never** draft prose into `output/paper/paper.tex` or `output/paper/extended_abstract.tex`. Nara writes the paper.
- Nothing under `exploration/` is ever deleted. Design versions are preserved, never deleted.
- Commit only when Nara asks. **Never** add a `Co-Authored-By: Claude` trailer.
- Figures carry no baked-in titles/captions; producing scripts source `code/utils/figure_style.R` and use the shared `PAL` palette. Never hard-code hex colors.
- `municipality_id_tse` is a zero-padded 5-character string everywhere. Never coerce to integer.
- `slides_report.tex` is UTF-8 **with BOM** — read with `encoding='utf-8-sig'`, and plain `grep` returns 0 matches (`grep -a` required). CSVs also read with `utf-8-sig`.
- FRAMING.md vocabulary lock applies to any text this plan produces: *consolidation* (never "concentration") for the top-two margin, *judicialization* never "rising/growing", American spelling.

**Testing deviation, stated up front:** this repo has no unit-test suite — it is an R/Python research pipeline whose house convention is `00_verify_*` gates plus `code/utils/audit_pipeline.py`. Adding a test framework is out of scope. Each task therefore substitutes a **verification command with a documented current (failing) value and a required post-fix value**. Every such command below has been run against the current tree; the "currently prints" figures are real, not predicted.

---

## The three defects

### Defect 1 — the GPS margin pre-trend balance test is arithmetically zero

`code/04_analysis/04_iv_diagnostics.py:281-285` residualizes each pre-trend outcome on `W`, and `W` (built at `:277-279`) contains the module-level `BASELINE_CONTROLS` from `:45-51`. The margin pre-trend outcome is defined at `:190` as

```
("delta_margin_2020_2016",  "margin_top1_top2_2020", "margin_2016")
```

i.e. `margin_top1_top2_2020 − margin_2016`. **Both endpoints are in `W`** (`margin_2016` and `margin_top1_top2_2020` both appear in that control list). Residualizing a linear combination of two included regressors on the regressors that contain them returns machine zero. Verified: across all 223 topics in `output/tables/descriptives/gps_balance_tests.csv`, `max|beta_margin| = 7.15e-16`, `median|beta_margin| = 5.2e-17`. The test cannot reject and has never been capable of rejecting.

Two further problems live in the same block:

- **Off-spec control set.** `04_iv_diagnostics.py:45-51` uses `margin_top1_top2_2020` + `log1p_total_candidates_2020` and omits `higher_educ_share_2010`. That is the **V1 stance** which `code/03_estimation/02_iv_main.R:264` explicitly labels legacy and rejects on Lord's-paradox grounds. Because `BASELINE_CONTROLS` is module-level and also feeds `rotemberg_weights()`, **every α_k, K_eff and balance p currently in the deck was computed for a specification the paper does not estimate.**
- **Broken Frisch–Waugh.** At `:299-300` the topic share `s_raw` is residualized on `fe_dummies` **only**, while the outcome is residualized on the full `W`. The reported β is therefore not the conditional coefficient it is presented as. Both sides must be residualized on the same matrix.

### Defect 2 — the `broader_treatment` spec is a no-op

`code/03_estimation/02_iv_main.R:481` declares

```r
list("broader_treatment", c(BASELINE_CONTROLS, "log1p_lawsuits_no_rrc_2020"), "SG_UF", FALSE, NULL, "ancova2016"),
```

`log1p_lawsuits_no_rrc_2020` **does not exist** in `data/estimation/executive_margin_design.csv` (345 columns; the file has `lawsuits_no_rrc_2020` and `delta_log1p_lawsuits_no_rrc_2024_2020`, but not the 2020 log level). The helper `avail()` at `02_iv_main.R:359` is

```r
avail <- function(controls, data) controls[controls %in% names(data)]
```

which drops the missing name **silently**. Result: `broader_treatment` is byte-identical to `baseline` — margin `0.0615274293613547`, se `0.0230443563478367`, N `5560`, to the last digit. We have been reporting a robustness spec that is a copy of the headline.

`01_assemble_design.py:197-199` already computes `np.log1p(wide["lawsuits_no_rrc_2020"])` inline to build the delta, then discards it — so the missing column is one line away.

### Defect 3 — three "change" variables whose 2020 term is identically zero

`code/02_build/02_shift_share_design.py:696-707` gates both flags on the 2024 election:

```python
candidates["is_new_candidate_vs_2020"] = (
    (candidates["ANO_ELEICAO"] == 2024)
    & candidates["person_key"].ne("")
    & (candidates["ran_in_2020"] == 0)
).astype(int)
candidates["is_incumbent_from_2020"] = (
    (candidates["ANO_ELEICAO"] == 2024)
    & candidates["person_key"].ne("")
    & (candidates["elected_in_2020"] == 1)
).astype(int)
```

These aggregate to `new_candidate_share` / `incumbent_candidate_share` at `:752-753`, so the 2020 rows are **0 by construction**. Verified on `data/estimation/executive_margin_design.csv` (5,571 rows): `new_candidate_share_2020` has **0 nonzero values**, `incumbent_candidate_share_2020` has **0 nonzero values**. The delta built at `02_iv_main.R:73-78` is therefore `X_2024 − 0 = X_2024`.

Consequences: `delta_new_candidate_share_2024_2020` and `delta_incumbent_candidate_share_2024_2020` are reported as changes in `CANDIDATE_SUPPLY_OUTCOMES` (`02_iv_main.R:124-130`) and `CANDIDATE_POOL_OUTCOMES` (`02b_iv_legislative.R`), and `output/tables/tex/legislative_iv_candidate_pool.tex` prints a **2024 level under a "Mean of dep. var." row on a Δ-labelled outcome**.

Third variable, same class: `share_career_politicians_2020` has **0 nonzero values** across all 5,571 rows (`04_candidate_history.py:40` opens the lookback window in 2012, and `is_career` needs ≥3 prior cycles, unreachable before 2024). It is nonetheless a robustness control (`01_assemble_design.py:228`, `02_iv_main.R:266-273`), where it contributes zero information and costs 6 observations through `complete.cases`.

**The fix is feasible, not a retraction.** `consulta_cand_2016/consulta_cand_2016_BRASIL.csv` exists in `data/raw/` with the same layout as 2020/2024, and the loader at `02_shift_share_design.py:594-595` is already parameterized by year. The 2020 flags can be built against 2016 exactly as the 2024 flags are built against 2020.

---

## Baseline — the numbers as they stand today

Every figure below was read from the committed tree on 2026-08-12 and is what the "after" column in Task 4 must be compared against.

| Quantity | Source | Current value |
|---|---|---|
| Headline margin (baseline, ANCOVA-2016) | `executive_margin_iv_fixest.csv` | 0.0615 (0.0230), p=.0131, N=5560 |
| First-stage F (full sample) | `zero_exposure_robustness.csv` | 102.29 |
| `broader_treatment` margin | `executive_margin_iv_fixest.csv` | 0.0615 (0.0230) — identical to baseline |
| GPS balance `max\|beta_margin\|` | `gps_balance_tests.csv` | 7.15e-16 (machine zero) |
| GPS balance median `p_margin` | `gps_balance_tests.csv` | 0.758 (meaningless) |
| Rotemberg topics / Σα | `rotemberg_weights.csv` | 223 topics, Σα = 1.000 |
| Negative-α topics | `rotemberg_weights.csv` | 78, summing to −0.252 |
| Propaganda share of α | `rotemberg_weights.csv` | 91.4% of net (73.0% of positive) |
| Exec Δ new-cand. share | `executive_margin_iv_fixest.csv` | 0.0142 (0.0293), p=.632 |
| Exec Δ incumbent-cand. share | `executive_margin_iv_fixest.csv` | −0.0064 (0.0234), p=.788 |
| Leg. Δ new-cand. share | `legislative_iv_fixest.csv` | −0.0017 (0.0078), p=.828 |
| Leg. Δ incumbent-cand. share | `legislative_iv_fixest.csv` | 0.0009 (0.0056), p=.869 |
| `new_candidate_share_2020` nonzero | `executive_margin_design.csv` | 0 / 5,571 |
| `incumbent_candidate_share_2020` nonzero | `executive_margin_design.csv` | 0 / 5,571 |
| `share_career_politicians_2020` nonzero | `executive_margin_design.csv` | 0 / 5,571 |

---

## File structure

| File | Responsibility | Touched by |
|---|---|---|
| `code/04_analysis/04_iv_diagnostics.py` | Rotemberg weights + GPS share-balance tests | Task 1 |
| `code/03_estimation/01_assemble_design.py` | Assembles the estimation matrix; owns the no-RRC block | Task 2 |
| `code/03_estimation/02_iv_main.R` | Executive IV; owns `avail()`, the spec list, outcome lists | Tasks 2, 3 |
| `code/02_build/02_shift_share_design.py` | Builds candidate panels; owns `add_candidate_history_flags` | Task 3 |
| `code/03_estimation/02b_iv_legislative.R` | Legislative twin; consumes the same delta columns | Task 3 |
| `docs/superpowers/plans/2026-08-12-mechanical-defect-comparison.md` | The before/after record | Task 4 (create) |

---

### Task 1: Real GPS pre-trend balance test, on the headline specification

**Files:**
- Modify: `code/04_analysis/04_iv_diagnostics.py:45-51` (control sets), `:277-285` (residualization), `:296-300` (Frisch–Waugh)
- Output changed: `output/tables/descriptives/gps_balance_tests.csv`, `output/tables/descriptives/rotemberg_weights.csv`

**Interfaces:**
- Consumes: `data/estimation/executive_margin_design.csv`, `data/clean/municipality_bartik_components.csv`
- Produces: `gps_balance_tests.csv` with columns `beta_margin`, `se_margin`, `p_margin` (unchanged names) now carrying non-degenerate values; `rotemberg_weights.csv` recomputed on the headline control set.

- [x] **Step 1: Record the current (degenerate) value so the comparison is anchored**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/descriptives/gps_balance_tests.csv',encoding='utf-8-sig')))
v=[abs(float(r['beta_margin'])) for r in rows if r['beta_margin'] not in ('','NA')]
print('n topics      :', len(v))
print('max|beta|     : %.3e' % max(v))
print('median|beta|  : %.3e' % sorted(v)[len(v)//2])
"
```

Expected (current tree): `n topics : 223`, `max|beta| : 7.154e-16`, `median|beta| : 5.216e-17`.

- [x] **Step 2: Replace the control-set block**

In `code/04_analysis/04_iv_diagnostics.py`, replace lines 45–51:

```python
BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
    "margin_2016",
    "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
    "log1p_total_candidates_2020",
]
```

with:

```python
# Mirrors BASELINE_CONTROLS in code/03_estimation/02_iv_main.R exactly. The old
# set here was the V1 stance (2020 competition LEVELS, no higher_educ_share_2010),
# which 02_iv_main.R:264 labels legacy and rejects on Lord's-paradox grounds. Every
# alpha_k and balance p reported out of this script was therefore computed for a
# specification the paper does not estimate. Diagnosed 2026-08-12.
BASELINE_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
    "log1p_total_valid_votes_2020",
    "margin_2016",
]

# Strictly PRE-DETERMINED (2010 Census) subset, mirroring PREDET_CONTROLS in
# 02_iv_main.R:257. Used ONLY to residualize the pre-trend outcomes: a 2016->2020
# change must never be residualized on either of its own endpoints. With margin_2016
# in the matrix, delta_margin_2020_2016 is a linear combination of included
# regressors and beta is machine zero for every topic (max|beta| = 7e-16).
PREDET_CONTROLS = [
    "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
]
```

- [x] **Step 3: Build a separate design matrix for pre-trend residualization**

In the same file, replace lines 277–285:

```python
    fe_dummies = pd.get_dummies(samp[FE_COL], drop_first=True).astype(float).values
    ctrl_mat   = samp[BASELINE_CONTROLS].astype(float).values
    W = np.hstack([fe_dummies, ctrl_mat])

    pretrend_resid = {}
    for col in pretrend_cols:
        y_raw = samp[col].astype(float).values
        coef, _, _, _ = np.linalg.lstsq(W, y_raw, rcond=None)
        pretrend_resid[col] = y_raw - W @ coef
```

with:

```python
    fe_dummies = pd.get_dummies(samp[FE_COL], drop_first=True).astype(float).values
    ctrl_mat   = samp[BASELINE_CONTROLS].astype(float).values
    W = np.hstack([fe_dummies, ctrl_mat])

    # W contains margin_2016, an endpoint of delta_margin_2020_2016. The pre-trend
    # balance test must partial out the PRE-DETERMINED set only, or it is identically
    # zero by construction. Both the outcome and the share are residualized on the
    # SAME matrix (Frisch-Waugh); residualizing the share on FE alone, as this script
    # previously did, does not deliver the conditional coefficient it reports.
    predet_mat = samp[PREDET_CONTROLS].astype(float).values
    W_pre = np.hstack([fe_dummies, predet_mat])

    pretrend_resid = {}
    for col in pretrend_cols:
        y_raw = samp[col].astype(float).values
        coef, _, _, _ = np.linalg.lstsq(W_pre, y_raw, rcond=None)
        pretrend_resid[col] = y_raw - W_pre @ coef
```

- [x] **Step 4: Residualize the share on the same matrix**

In the same file, replace lines 299–300:

```python
        coef_fe_s, _, _, _ = np.linalg.lstsq(fe_dummies, s_raw, rcond=None)
        s_tilde = s_raw - fe_dummies @ coef_fe_s
```

with:

```python
        coef_pre_s, _, _, _ = np.linalg.lstsq(W_pre, s_raw, rcond=None)
        s_tilde = s_raw - W_pre @ coef_pre_s
```

- [x] **Step 5: Re-run the diagnostics**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/04_analysis/04_iv_diagnostics.py
```

Expected: completes, reprints the topic table, writes both CSVs.

- [x] **Step 6: Verify the test is no longer degenerate**

Re-run the Step 1 command. Required: `max|beta| > 1e-6`. A value still at 1e-15 means an endpoint is still in `W_pre` — re-check Step 2.

Then record how many topics now reject, which is the number that did not exist before:

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/descriptives/gps_balance_tests.csv',encoding='utf-8-sig')))
p=[(float(r['p_margin']), r['topic_name'], float(r['alpha'])) for r in rows if r['p_margin'] not in ('','NA')]
print('topics with p_margin < .05 :', sum(1 for x in p if x[0]<.05), '/', len(p))
print('topics with p_margin < .10 :', sum(1 for x in p if x[0]<.10), '/', len(p))
print()
print('highest-alpha topics and their balance p:')
for pv,nm,a in sorted(p, key=lambda x:-abs(x[2]))[:8]:
    print('  %-46s alpha=%+.4f  p=%.4f' % (nm[:46], a, pv))
"
```

- [x] **Step 7: Record the Rotemberg drift**

The control-set change also moves the Rotemberg weights, which the deck quotes.

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/descriptives/rotemberg_weights.csv',encoding='utf-8-sig')))
a=[float(r['alpha']) for r in rows if r['alpha'] not in ('','NA')]
neg=[x for x in a if x<0]
pos=sum(x for x in a if x>0)
prop=sum(float(r['alpha']) for r in rows if 'ropaganda' in r.get('topic_name','') or 'ropaganda' in r.get('topic_family',''))
print('topics        :', len(a))
print('sum alpha     : %.4f' % sum(a))
print('negative alpha: %d summing to %.4f' % (len(neg), sum(neg)))
print('propaganda    : %.1f%% of net, %.1f%% of positive' % (100*prop/sum(a), 100*prop/pos))
"
```

Compare against the baseline table: 223 topics, Σα = 1.000, 78 negative summing to −0.252, propaganda 91.4% of net / 73.0% of positive. **Any movement here changes claims already on `app:rotemberg` and `app:exposure`** — carry the numbers to Task 4, do not edit the frames in this task.

- [x] **Step 8: Commit**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
git add code/04_analysis/04_iv_diagnostics.py output/tables/descriptives/gps_balance_tests.csv output/tables/descriptives/rotemberg_weights.csv
git commit -m "diagnostics: fix the mechanically-zero pre-trend balance test and run on-spec

The margin pre-trend outcome was residualized on a matrix containing both of
its own endpoints, forcing beta to machine zero for all 223 topics. Partial out
the pre-determined set only, and residualize the share on the same matrix so the
reported coefficient is the conditional one. Also aligns the control set to
BASELINE_CONTROLS in 02_iv_main.R; the script had been running the rejected V1
stance, so every alpha_k and balance p was computed off-spec."
```

---

### Task 2: Make `broader_treatment` do something, and stop `avail()` failing silently

**Files:**
- Modify: `code/03_estimation/01_assemble_design.py:197-207` (emit the missing column)
- Modify: `code/03_estimation/02_iv_main.R:359` (`avail()` warns), `:481` (spec list)
- Output changed: `data/estimation/executive_margin_design.csv`, `output/tables/regressions/executive_margin_iv_fixest.csv`

**Interfaces:**
- Consumes: `lawsuits_no_rrc_2020` (already in `wide`), `log1p_competition_lawsuits_2020` (already in the design, verified present)
- Produces: new design column `log1p_lawsuits_no_rrc_2020`; two spec rows in the results CSV, `broader_treatment` (now genuinely distinct) and `base_conditioned` (new).

**Scope note:** Steps 5–6 add a spec that is *not* part of the literal defect. The defect is that `broader_treatment` silently did nothing; the reason that matters is that we have **no** estimate conditioning on the 2020 litigation base, which is the single control the identification critique asks for. Fixing the no-op without adding that spec leaves the question the no-op was hiding still unanswered. Flag it to Nara rather than folding it in silently.

- [x] **Step 1: Confirm the spec is currently a no-op**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/regressions/executive_margin_iv_fixest.csv',encoding='utf-8-sig')))
for r in rows:
    if r['outcome']=='delta_margin_top1_top2_2024_2020' and r['spec'] in ('baseline','broader_treatment'):
        print('%-20s coef=%s se=%s N=%s' % (r['spec'], r['coef'], r['se'], r['nobs']))
"
```

Expected: two lines, both `coef=0.0615274293613547`, both `se=0.0230443563478367`, both `N=5560`. Byte-identical is the bug.

- [x] **Step 2: Emit the missing column**

In `code/03_estimation/01_assemble_design.py`, after line 199 (the closing paren of the `delta_log1p_lawsuits_no_rrc_2024_2020` assignment), insert:

```python
    # The 2020 log level is computed inline above to build the delta, then thrown
    # away. 02_iv_main.R's broader_treatment spec asks for it by name; without it
    # avail() dropped the control and the spec silently reproduced the baseline.
    wide["log1p_lawsuits_no_rrc_2020"] = np.log1p(wide["lawsuits_no_rrc_2020"])
```

Then in the `fillna(0)` list at lines 202–206, add the new name:

```python
    for col in [
        "bartik_iv_no_rrc", "baseline_lawsuits_no_rrc_2020",
        "baseline_subjects_no_rrc_2020", "lawsuits_no_rrc_2020",
        "lawsuits_no_rrc_2024", "delta_log1p_lawsuits_no_rrc_2024_2020",
        "log1p_lawsuits_no_rrc_2020",
    ]:
```

- [x] **Step 3: Make `avail()` announce what it drops**

In `code/03_estimation/02_iv_main.R`, replace line 359:

```r
avail <- function(controls, data) controls[controls %in% names(data)]
```

with:

```r
# Drops controls the design does not carry. This MUST be loud: a silently dropped
# control turns a robustness spec into a copy of the headline with no visible
# symptom (broader_treatment reproduced baseline to the last digit for exactly this
# reason). Warn rather than stop -- some variants legitimately lack a control.
avail <- function(controls, data) {
  missing <- setdiff(controls, names(data))
  if (length(missing) > 0)
    warning("avail(): controls absent from the design and DROPPED: ",
            paste(missing, collapse = ", "), call. = FALSE, immediate. = TRUE)
  controls[controls %in% names(data)]
}
```

- [x] **Step 4: Rebuild the design matrix**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/03_estimation/01_assemble_design.py
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
h=next(csv.reader(open('data/estimation/executive_margin_design.csv',encoding='utf-8-sig')))
print('log1p_lawsuits_no_rrc_2020 present:', 'log1p_lawsuits_no_rrc_2020' in h)
print('log1p_competition_lawsuits_2020 present:', 'log1p_competition_lawsuits_2020' in h)
print('total cols:', len(h))
"
```

Expected: both `True`; column count 346 (was 345).

- [x] **Step 5: Add the base-conditioned spec**

In `code/03_estimation/02_iv_main.R`, in the `specs` list, insert immediately after the `broader_treatment` line (`:481`):

```r
  # Conditions on the 2020 LEVEL of the endogenous variable itself. Z is a function
  # of the 2020 base (baseline_share_2020 x shock), and Z = 0 for 20.7% of
  # municipalities -- exactly those with no recorded 2020 adversarial filing. This
  # spec asks whether the reduced form survives holding that base fixed. It is a
  # diagnostic, not a preferred spec: log1p_competition_lawsuits_2020 is a 2020
  # LEVEL and so carries the Lord's-paradox caveat that bars ANCOVA_2020_LEVELS
  # from the headline. Report it beside the headline, do not replace it.
  list("base_conditioned",  c(BASELINE_CONTROLS, "log1p_competition_lawsuits_2020"), "SG_UF", FALSE, NULL, "ancova2016"),
```

- [x] **Step 6: Re-run the executive IV and read the two new specs**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/02_iv_main.R
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/regressions/executive_margin_iv_fixest.csv',encoding='utf-8-sig')))
print('%-20s %10s %10s %8s %7s %9s' % ('spec','coef','se','p','N','FS F'))
for r in rows:
    if r['outcome']=='delta_margin_top1_top2_2024_2020' and r['spec'] in ('baseline','broader_treatment','base_conditioned'):
        print('%-20s %10.4f %10.4f %8.4f %7s %9s' % (r['spec'],float(r['coef']),float(r['se']),float(r['p']),r['nobs'],r.get('first_stage_F_lookup','')[:7]))
"
```

Required: `broader_treatment` is **no longer identical** to `baseline`. Record all three rows for Task 4. If the R run emits `avail(): controls absent...` warnings for other specs, record them — that is the hardening finding its next case.

- [x] **Step 7: Commit**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
git add code/03_estimation/01_assemble_design.py code/03_estimation/02_iv_main.R data/estimation/executive_margin_design.csv output/tables/regressions/
git commit -m "iv: repair the no-op broader_treatment spec, add a base-conditioned spec

log1p_lawsuits_no_rrc_2020 was never emitted by 01_assemble_design.py, so avail()
dropped it silently and broader_treatment reproduced the baseline to the last
digit. Emit the column, make avail() warn on every drop, and add base_conditioned
(controls for the 2020 level of the endogenous variable) so the reduced form can
be read holding the litigation base fixed."
```

---

### Task 3: Symmetric 2020 candidate-history flags; retire the constant-zero control

**Files:**
- Modify: `code/02_build/02_shift_share_design.py:49` (history years), `:570-600` (loader), `:665-708` (`add_candidate_history_flags`)
- Modify: `code/03_estimation/02_iv_main.R:266-273` (drop the dead control)
- Output changed: `data/clean/office_candidate_outcomes_panel.csv`, `data/estimation/executive_margin_design.csv`, `legislative_design.csv`, both regression CSVs, `output/tables/tex/legislative_iv_candidate_pool.tex`

**Interfaces:**
- Consumes: `data/raw/consulta_cand_2016/consulta_cand_2016_BRASIL.csv` (verified present, same layout as 2020/2024)
- Produces: `new_candidate_share_2020` and `incumbent_candidate_share_2020` with genuine non-zero values, so `delta_new_candidate_share_2024_2020` and `delta_incumbent_candidate_share_2024_2020` become real first differences. Column names are unchanged — downstream consumers need no edits.

- [x] **Step 1: Record the current degeneracy**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('data/estimation/executive_margin_design.csv',encoding='utf-8-sig')))
for c in ['new_candidate_share_2020','new_candidate_share_2024','incumbent_candidate_share_2020','incumbent_candidate_share_2024','share_career_politicians_2020']:
    v=[r[c] for r in rows if r.get(c) not in ('','NA',None)]
    nz=sum(1 for x in v if abs(float(x))>1e-12)
    m=sum(float(x) for x in v)/len(v) if v else float('nan')
    print('%-34s n=%-6d nonzero=%-6d mean=%.4f' % (c,len(v),nz,m))
"
```

Expected: `new_candidate_share_2020` nonzero=0, `incumbent_candidate_share_2020` nonzero=0, `share_career_politicians_2020` nonzero=0; the 2024 twins nonzero (5,035 and 2,833).

- [x] **Step 2: Add a history-only year list**

In `code/02_build/02_shift_share_design.py`, after line 49 (`TARGET_YEARS = [2020, 2024]`), insert:

```python
# Years loaded ONLY to establish prior-cycle candidate history. 2016 rows are used
# to build the 2020 "new candidate" / "incumbent" flags and are dropped before any
# outcome is aggregated, so the estimation panel stays 2020 + 2024. Do NOT fold
# this into TARGET_YEARS: that constant also drives the lawsuit and vote loaders.
HISTORY_YEARS = [2016, 2020, 2024]
```

- [x] **Step 3: Load the history years in the candidate loader**

In the same file, at line 594, change:

```python
    for year in TARGET_YEARS:
        path = RAW_DIR / f"consulta_cand_{year}" / f"consulta_cand_{year}_BRASIL.csv"
```

to:

```python
    for year in HISTORY_YEARS:
        path = RAW_DIR / f"consulta_cand_{year}" / f"consulta_cand_{year}_BRASIL.csv"
```

Leave the loops at lines 238 and 560 on `TARGET_YEARS` — they are the lawsuit and vote loaders and must not gain a 2016 panel.

- [x] **Step 4: Generalize the flags to each year against its prior cycle**

In the same file, replace the whole of `add_candidate_history_flags` (lines 665–708) with:

```python
def add_candidate_history_flags(candidates: pd.DataFrame) -> pd.DataFrame:
    """Flag each candidate as new / incumbent relative to the PRIOR cycle.

    Previously both flags were gated on ANO_ELEICAO == 2024, which made the 2020
    share identically zero and turned delta_new_candidate_share_2024_2020 into a
    2024 level wearing a delta's name. Each target year is now compared against its
    own predecessor (2024 vs 2020, 2020 vs 2016), so the difference is a genuine
    first difference. Diagnosed 2026-08-12.
    """
    if candidates.empty:
        return candidates
    candidates = candidates.copy()
    key_cols = ["SG_UF", "SG_UE", "office_group", "person_key"]

    ran_flag = pd.Series(0, index=candidates.index, dtype=int)
    elected_flag = pd.Series(0, index=candidates.index, dtype=int)

    for year, prior in ((2024, 2020), (2020, 2016)):
        base = candidates[candidates["ANO_ELEICAO"] == prior]
        if base.empty:
            print(f"Warning: no {prior} candidate rows; {year} history flags will be 0")
            continue
        ran_keys = set(
            map(tuple, base.loc[base["person_key"].ne(""), key_cols].drop_duplicates().values)
        )
        elected_keys = set(
            map(tuple, base.loc[base["person_key"].ne("") & (base["is_elected"] == 1),
                                key_cols].drop_duplicates().values)
        )
        tgt = candidates["ANO_ELEICAO"] == year
        tuples = pd.Series(
            list(map(tuple, candidates.loc[tgt, key_cols].values)),
            index=candidates.index[tgt],
        )
        ran_flag.loc[tgt] = tuples.map(lambda t: int(t in ran_keys))
        elected_flag.loc[tgt] = tuples.map(lambda t: int(t in elected_keys))

    candidates["ran_in_prior_cycle"] = ran_flag
    candidates["elected_in_prior_cycle"] = elected_flag
    has_key = candidates["person_key"].ne("")
    in_target = candidates["ANO_ELEICAO"].isin(TARGET_YEARS)

    candidates["is_new_candidate_vs_2020"] = (
        in_target & has_key & (candidates["ran_in_prior_cycle"] == 0)
    ).astype(int)
    candidates["is_incumbent_from_2020"] = (
        in_target & has_key & (candidates["elected_in_prior_cycle"] == 1)
    ).astype(int)
    candidates["is_reelected_incumbent_2024"] = (
        (candidates["is_incumbent_from_2020"] == 1) & (candidates["is_elected"] == 1)
    ).astype(int)
    return candidates
```

Column names `is_new_candidate_vs_2020` / `is_incumbent_from_2020` are kept **deliberately** — renaming them would force edits across the aggregation block, both R scripts and the `dict` label maps, for no analytical gain. Note the names now mean "vs prior cycle"; the docstring says so.

- [x] **Step 5: Drop the 2016 rows before aggregation**

In the same file at line 975 (`candidates = load_candidates()`), the call chain must drop 2016 after flagging. Immediately after the `add_candidate_history_flags(...)` call in that block, insert:

```python
    # 2016 was loaded only to date the 2020 flags. Drop it before aggregation so the
    # outcome panel stays 2020 + 2024 and no downstream count silently doubles.
    candidates = candidates[candidates["ANO_ELEICAO"].isin(TARGET_YEARS)].copy()
```

- [x] **Step 6: Remove the constant-zero control**

In `code/03_estimation/02_iv_main.R`, replace line 272 of the `ROBUSTNESS_CONTROLS` block:

```r
  "share_first_time_candidates_2020", "share_career_politicians_2020"
```

with:

```r
  # share_career_politicians_2020 REMOVED 2026-08-12: identically 0 for all 5,571
  # municipalities. is_career needs >=3 prior cycles from a window opening in 2012
  # (04_candidate_history.py:40), unreachable before 2024. It carried no information
  # and cost 6 observations through complete.cases.
  "share_first_time_candidates_2020"
```

`share_first_time_candidates_2020` stays — it is genuinely non-zero (0.497). Only the career variable is dead. `ROBUSTNESS_CONTROLS` feeds one spec, `extended_controls` (`:475`); that spec's N should rise by 6 and its coefficient should barely move.

- [x] **Step 7: Re-run the build and both estimation scripts**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/02_build/02_shift_share_design.py
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/03_estimation/01_assemble_design.py
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/02_iv_main.R
"C:/Program Files/R/R-4.6.0/bin/Rscript.exe" code/03_estimation/02b_iv_legislative.R
```

- [x] **Step 8: Verify the 2020 term is now real, and N did not move unexpectedly**

Re-run the Step 1 command. Required: `new_candidate_share_2020` and `incumbent_candidate_share_2020` both have **thousands** of nonzero values with plausible means (the 2024 twins average roughly 0.79 and 0.14 respectively; the 2020 values should be the same order). `share_career_politicians_2020` remains 0 — it is now simply unused.

Then confirm the estimation sample:

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" -c "
import csv
rows=list(csv.DictReader(open('output/tables/regressions/executive_margin_iv_fixest.csv',encoding='utf-8-sig')))
for r in rows:
    if r['spec']=='baseline' and r['outcome']=='delta_margin_top1_top2_2024_2020':
        print('headline margin: %s (%s) p=%s N=%s' % (r['coef'][:8], r['se'][:8], r['p'][:6], r['nobs']))
"
```

Expected: the headline is **unchanged at 0.0615 (0.0230), p=.0131**. N may rise from 5,560 to 5,566 (the six observations the dead control was costing). A headline that moves means Step 6 removed more than intended — re-check.

- [x] **Step 9: Commit**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
git add code/02_build/02_shift_share_design.py code/03_estimation/02_iv_main.R data/clean/ data/estimation/ output/tables/
git commit -m "build: give the 2020 candidate-history flags a real prior cycle

is_new_candidate_vs_2020 and is_incumbent_from_2020 were gated on ANO_ELEICAO ==
2024, so the 2020 share was identically zero across all 5,571 municipalities and
delta_new/incumbent_candidate_share were 2024 levels wearing a delta's name --
including the 'Mean of dep. var.' row of legislative_iv_candidate_pool.tex. Load
2016 as a history-only year and date each cycle against its predecessor. Also
drops share_career_politicians_2020, a constant-zero robustness control."
```

---

### Task 4: The comparison record

**Files:**
- Create: `docs/superpowers/plans/2026-08-12-mechanical-defect-comparison.md`

**Interfaces:**
- Consumes: every "record this" figure from Tasks 1–3 and the Baseline table above.
- Produces: a single markdown document Nara can read against the deck. **No frame, no `FRAMING.md` line, and no `.tex` is edited in this plan** — those touch locked text and are hers to call.

- [x] **Step 1: Write the comparison document**

Create `docs/superpowers/plans/2026-08-12-mechanical-defect-comparison.md` with this exact skeleton, filling the "After" column from the Task 1–3 verification output:

```markdown
# Mechanical defect fixes — before/after

Fixed 2026-08-12. Baseline column read from the committed tree before any change.

## Did the headline move?

| Quantity | Before | After | Moved? |
|---|---|---|---|
| Margin, baseline spec | 0.0615 (0.0230) p=.0131 N=5560 | | |
| First-stage F, full sample | 102.29 | | |

## Defect 1 — GPS pre-trend balance test

| Quantity | Before | After |
|---|---|---|
| max\|beta_margin\| | 7.15e-16 (machine zero) | |
| median\|beta_margin\| | 5.22e-17 | |
| topics with p_margin < .05 | 0 (untestable) | |
| Rotemberg topics / sum alpha | 223 / 1.000 | |
| negative-alpha topics | 78, sum -0.252 | |
| propaganda share of net alpha | 91.4% | |

Deck claims that depend on these numbers: `app:rotemberg`, `app:exposure`,
and the supporting text of `src:pretrend`.

## Defect 2 — broader_treatment

| Spec | Before | After |
|---|---|---|
| baseline | 0.0615 (0.0230) p=.0131 | |
| broader_treatment | 0.0615 (0.0230) — identical to baseline | |
| base_conditioned | did not exist | |

The `base_conditioned` row is the new information: it is the first estimate in
this pipeline that holds the 2020 litigation base fixed.

## Defect 3 — candidate-history deltas

| Outcome | Before | After |
|---|---|---|
| Exec Δ new-cand. share | 0.0142 (0.0293) p=.632 | |
| Exec Δ incumbent-cand. share | -0.0064 (0.0234) p=.788 | |
| Leg. Δ new-cand. share | -0.0017 (0.0078) p=.828 | |
| Leg. Δ incumbent-cand. share | 0.0009 (0.0056) p=.869 | |
| Estimation N | 5,560 | |

Before, these regressions had a 2024 level on the left-hand side. After, they
have a first difference. The `Mean of dep. var.` row of
`output/tables/tex/legislative_iv_candidate_pool.tex` was a 2024 level (0.613)
presented as a change; it is now a change.

## What still needs Nara's call

1. The Holm/BH sentence at `src_findings.tex:9` and in the `FRAMING.md` tier
   table claims multiplicity clearance at 5%; `multiplicity_adjusted.csv` gives
   Holm .237 / BH .143 and `MultHolmSig 0`. Unaffected by these fixes.
2. The litigating-subsample reduced form (0.0206, p=.022) with no first stage
   (F=1.12). Unaffected by these fixes.
3. The open-seat pre-trend placebo (0.120, p=.047) exceeding the open-seat
   effect (0.0765, p=.047), which bears on FRAMING D5. Unaffected by these fixes.
```

- [x] **Step 2: Re-run the pipeline audit**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
"C:/Users/naral/AppData/Local/Programs/Python/Python313/python.exe" code/utils/audit_pipeline.py
```

Expected: no script newly classified as dead. This plan adds no scripts and deletes none; a change here means a build step stopped writing an output.

- [x] **Step 3: Commit**

```bash
cd "C:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
git add docs/superpowers/plans/2026-08-12-mechanical-defect-comparison.md
git commit -m "docs: record the before/after for the three mechanical defect fixes"
```

---

## Explicitly out of scope

Each of these is real and evidenced; none is a mechanical defect, so none is fixed here.

- **The entry-typology left-censor.** `share_first_time_candidates` runs 1.000 (2012) → 0.573 (2016) → 0.497 (2020) → 0.420 (2024) in `candidate_experience_panel.csv`: the censoring bias shrinks monotonically as the lookback window fills, so `delta_2024_2020 = −0.077` carries a **mechanical negative trend under the null**. `share_cross_cycle_returner` is structurally 0 in 2012 and 2016 and so trends mechanically upward. `share_serial_challenger` (0.208 / 0.187 / 0.203) is the one clean member. Fixing this means a fixed-width lookback, which changes the definition rather than repairing a bug — Nara's call.
- **The three items listed under "What still needs Nara's call"** in the Task 4 document: the multiplicity sentence, the litigating-subsample reduced form, and the open-seat placebo. All three touch `FRAMING.md` or a results frame.
- **The adversarial filter** (`02_shift_share_design.py:394-397`), where "adversarial" is defined by exclusion and 28.9% of what is kept sits in never-classified subject codes. A definitional question, not a defect.
- **Deck and `.tex` frame updates.** Tasks 1–3 change numbers that `app:rotemberg`, `app:exposure` and `legislative_iv_candidate_pool.tex` display. The regenerated `.tex` fragments follow automatically from re-running the R scripts; the *prose* on the frames does not, and is not edited here.
