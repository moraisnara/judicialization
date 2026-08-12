# exploration/

Analysis that was run, is worth keeping, and did **not** reach the paper or the
report deck.

The rule for `code/`: a script there must generate an input or a result for the
paper. A script that fails that test but is important enough to survive an easy
drop lives here instead. Nothing in this folder is deleted, and nothing here is
called by `code/run_all.py` — run these by hand.

Layout mirrors the pipeline stages so the depth-2 project-root resolution every
script uses (`parents[2]` in Python, `file.path(SCRIPT_DIR, "..", "..")` in R)
keeps working unchanged. Outputs land in `exploration/output/`, never in
`output/`, so `output/` means "paper assets only".

## What is here and why it stopped short

| Script | What it did | Why it is not in `code/` |
|---|---|---|
| `03_estimation/03_family_iv.R` | IV split by lawsuit family (4 families x outcomes) | `family_iv_results.csv` is cited by no document and read by no script. Superseded by `13_reclassification_robustness.R` (family-level Z) and `11_summary_indices.R` |
| `03_estimation/08_mean_reversion.R` | Split-sample first-stage falsification | Its only asset, `firststage_splitsample.pdf`, was shown on nothing |
| `04_analysis/05_validation.R` | FD-vs-ANCOVA comparison and the ANCOVA falsification gate | **Answers a referee asking "why ANCOVA, not first differences?"** The deck makes that argument (`src:fd`), but from `appendix_first_difference.tex`, which `02_iv_main.R` writes. Section [B] duplicates falsifications that `05_pretrend_balance.R` and `04_placebo_nonadversarial.R` already produce. Decision-evidence for a locked estimator choice, not a paper asset |
| `04_analysis/11_lawsuit_topic_selection.py` | Which adversarial topics the instrument selects on | Decision ledger for the `tse-shift-share` redesign, not a pipeline step |
| `SPECIFICATION_tse_shift_share.md` | Spec for the TSE shift-share redesign | Specifies the *redesign*, not the paper's design. Its own header names the committed propaganda-Bartik/ANCOVA design on `main` as the preserved fallback. At repo root it would advertise itself as the paper's spec |

The last two are one artifact pair from the `tse-shift-share` redesign lane and
travel together.

## Removed diagnostics

The LIML-vs-2SLS comparison was removed from `code/03_estimation/02_iv_main.R`
rather than archived: with `K=1` the estimator is 2SLS ≡ LIML by construction, so
the check confirmed a mechanical identity, and no document ever cited it. If a
referee asks, recover it from git history — it was removed in the commit that
follows `da0191b`.
