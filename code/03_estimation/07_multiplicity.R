#!/usr/bin/env Rscript
# 07_multiplicity.R
# Family-wise multiple-testing correction for the primary executive outcome
# family. The headline flags a handful of significant 2SLS effects against a
# wide band of nulls; a referee will ask whether the significant ones survive
# a multiplicity adjustment. We report:
#   * Holm step-down (controls FWER under ANY dependence structure)
#   * Benjamini-Hochberg (controls FDR under positive dependence)
# from the committed cluster-robust 2SLS p-values. (Romano-Wolf would be less
# conservative but needs the joint bootstrap draws, which are not saved.)
#
# Input : output/tables/regressions/executive_margin_iv_fixest.csv
# Output: output/tables/regressions/multiplicity_adjusted.csv
#
# The FAMILY is the set of primary CONFIRMATORY executive outcomes: closeness,
# field concentration, the mayoral ballot, and descriptive representation.
# Excluded by design: pretrend_* falsifications, the council (vereador) ballot
# and the turnout-profile disaggregation (separate hypotheses / placebo families).

suppressWarnings(suppressMessages({
  library(readr)
}))

# Robust path resolution whether run via Rscript or sourced.
args_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
here <- if (length(args_file)) dirname(normalizePath(args_file)) else getwd()
ROOT <- normalizePath(file.path(here, "..", ".."))
REG  <- file.path(ROOT, "output", "tables", "regressions")

iv <- read_csv(file.path(REG, "executive_margin_iv_fixest.csv"),
               show_col_types = FALSE)

# --- Define the primary confirmatory executive family --------------------------
FAMILY <- c(
  # closeness / top-two contest
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_vote_share_2024_2020",
  "delta_runnerup_vote_share_2024_2020",
  "delta_winner_majority_2024_2020",
  # field concentration ladder
  "delta_effective_n_candidates_vote_2024_2020",
  "delta_vote_hhi_candidate_2024_2020",
  "delta_top2_vote_share_2024_2020",
  # candidate pool
  "delta_log1p_n_candidates_with_votes_2024_2020",
  # mayoral ballot (voter behaviour)
  "delta_blank_rate_2024_2020",
  "delta_null_rate_2024_2020",
  "delta_valid_vote_rate_2024_2020",
  "delta_turnout_rate_2024_2020",
  # descriptive representation
  "delta_female_vote_share_2024_2020",
  "delta_female_share_2024_2020",
  "delta_nonwhite_vote_share_2024_2020",
  "delta_winner_is_female_2024_2020",
  "delta_new_candidate_vote_share_2024_2020",
  "delta_incumbent_candidate_vote_share_2024_2020"
)

d <- iv[iv$spec == "baseline" & iv$variant == "adversarial" &
        iv$outcome %in% FAMILY, c("outcome", "coef", "se", "p")]
stopifnot(nrow(d) == length(FAMILY))

d$p_holm <- p.adjust(d$p, method = "holm")
d$p_bh   <- p.adjust(d$p, method = "BH")
d <- d[order(d$p), ]

d$sig_raw_5  <- as.integer(d$p      < 0.05)
d$sig_holm_5 <- as.integer(d$p_holm < 0.05)
d$sig_bh_5   <- as.integer(d$p_bh   < 0.05)

out <- file.path(REG, "multiplicity_adjusted.csv")
write_csv(d, out)

cat(sprintf("Family size: %d primary executive outcomes\n", nrow(d)))
cat(sprintf("Significant at 5%%:  raw=%d  Holm=%d  BH=%d\n",
            sum(d$sig_raw_5), sum(d$sig_holm_5), sum(d$sig_bh_5)))
print(d[, c("outcome", "p", "p_holm", "p_bh")], n = nrow(d))
cat(sprintf("\nSaved: %s\n", out))
