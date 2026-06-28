# 02c_act_iv.R — second-stage 2SLS on the ACT-BASED 10-family instrument (fixest).
#
# New instrument version (2026-06-26) run in parallel to the production IV
# (_archive/03_estimation/02_iv_main.R). Reads data/estimation/act_design.csv,
# assembled by 03_estimation/01d_act_family_ivs.py (Python = data construction only;
# all estimation here is R/fixest per the regressions-in-R rule).
#
#   instrument : bartik_iv_act
#   endogenous : delta_log1p_act_lawsuits
#   controls   : 5 baseline controls (spec_config.json) + per-outcome lagged DV
#                (the documented "option 1a" baseline; read from the config, not
#                 hard-coded — earlier this script ran an off-spec 7-control set
#                 with NO lagged DV, which inflated the turnout result).
#   formula    : y ~ controls | state FE | endog ~ instrument
#   clustering : state (cluster_id = SG_UF, ~27 UFs)
#   + Lee et al. (2022) tF weak-IV correction.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0)
  dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)

# Canonical design (control list + per-outcome lagged DV) from code/spec_config.json.
# This is the documented "option 1a" baseline: 5 pre-determined controls + the
# outcome's own 2020 level as a lagged DV. Do NOT hard-code the control list here.
source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
cat(sprintf("Loaded act_design: %d municipalities\n", nrow(df)))

INSTRUMENT <- spec_instrument()    # bartik_iv_act
ENDOGENOUS <- spec_endogenous()    # delta_log1p_act_lawsuits

# 5 pre-determined controls (config). A per-outcome lagged DV (the outcome's own
# 2020 level, spec_lagged_dv()) is APPENDED per outcome below. The inherited
# margin_top1_top2_2020 / log1p_total_candidates_2020 were removed by the config
# (arbitrary outcome-levels) and must NOT be re-added here.
BASELINE_CONTROLS <- spec_baseline_controls()

OUTCOME_FAMILY <- c(
  delta_runnerup_vote_share_2024_2020              = "primary",
  delta_margin_top1_top2_2024_2020                 = "primary",
  delta_winner_vote_share_2024_2020                = "secondary",
  delta_winner_majority_2024_2020                  = "secondary",
  delta_others_vote_share_2024_2020                = "secondary",
  delta_log1p_n_candidates_with_votes_2024_2020    = "secondary",
  delta_female_vote_share_2024_2020                = "composition",
  delta_female_share_2024_2020                     = "composition",
  delta_nonwhite_vote_share_2024_2020              = "composition",
  delta_new_candidate_vote_share_2024_2020         = "composition",
  delta_incumbent_candidate_vote_share_2024_2020   = "composition",
  delta_winner_is_female_2024_2020                 = "composition",
  delta_winner_is_new_vs_2020_2024_2020            = "composition",
  delta_turnout_rate_2024_2020                     = "voter_behavior",
  delta_null_rate_2024_2020                        = "voter_behavior",
  delta_blank_rate_2024_2020                       = "voter_behavior",
  delta_valid_vote_rate_2024_2020                  = "voter_behavior",
  delta_share_first_time_candidates_2024_2020      = "entry",
  delta_share_serial_challenger_2024_2020          = "entry",
  delta_share_cross_cycle_returner_2024_2020       = "entry",
  delta_effective_n_candidates_vote_2024_2020      = "fragmentation",
  delta_effective_n_parties_vote_2024_2020         = "fragmentation",
  delta_effective_party_count_candidates_2024_2020 = "fragmentation",
  delta_vote_hhi_candidate_2024_2020               = "fragmentation",
  delta_vote_hhi_party_2024_2020                   = "fragmentation",
  delta_candidate_hhi_party_2024_2020              = "fragmentation",
  delta_top2_vote_share_2024_2020                  = "fragmentation"
)
ALL_OUTCOMES <- names(OUTCOME_FAMILY)
avail <- function(v, data) v[v %in% names(data)]

# ---- Lee et al. (2022) tF critical values (5% two-sided, K=1) ----
tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,2.39,
            2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) {
  if (is.na(f) || f >= 23.1) return(1.96)
  if (f <= 2) return(13.99)
  approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y
}

# ---- headline first stage (baseline-controls sample; the reported design F) ----
fs_ctrls <- avail(BASELINE_CONTROLS, df)
fs_req   <- unique(c(INSTRUMENT, ENDOGENOUS, "cluster_id", "state", fs_ctrls))
fs_samp  <- df[complete.cases(df[, fs_req, drop = FALSE]), ]
fs_fml   <- as.formula(sprintf("%s ~ %s | state",
                               ENDOGENOUS, paste(c(INSTRUMENT, fs_ctrls), collapse = " + ")))
fs_fit   <- feols(fs_fml, data = fs_samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
fs_F     <- tstat(fs_fit)[INSTRUMENT]^2
cat(sprintf("Headline first-stage F (state-clustered): %.1f  -> tF_cv=%.2f  (N=%d)\n",
            fs_F, get_tF_cv(fs_F), nrow(fs_samp)))

first_stage <- data.frame(
  instrument = INSTRUMENT, endogenous = ENDOGENOUS,
  coef = coef(fs_fit)[INSTRUMENT], se = se(fs_fit)[INSTRUMENT],
  t = tstat(fs_fit)[INSTRUMENT], p = pvalue(fs_fit)[INSTRUMENT],
  first_stage_F = fs_F, tF_cv = get_tF_cv(fs_F),
  nobs = nobs(fs_fit), n_clusters = length(unique(fs_samp$cluster_id)),
  row.names = NULL, stringsAsFactors = FALSE)

# ---- 2SLS per outcome (ON-SPEC: 5 baseline controls + per-outcome lagged DV) ----
# Each outcome uses its OWN complete-case sample and its OWN first-stage F, since
# appending the lagged DV shifts the sample slightly. This matches the on-spec
# voter-behaviour lane (03_voter_behavior_iv.R). Outcomes whose 2020 lagged DV is
# not yet built (valid_vote_rate, log1p_n_candidates_with_votes) silently run
# without it (avail() drops the missing column).
rows <- list()
for (y in ALL_OUTCOMES) {
  if (!(y %in% names(df))) next
  lag    <- spec_lagged_dv(y)
  ctrls  <- avail(c(BASELINE_CONTROLS, if (!is.na(lag)) lag), df)
  req    <- unique(c(y, INSTRUMENT, ENDOGENOUS, "cluster_id", "state", ctrls))
  samp   <- df[complete.cases(df[, req, drop = FALSE]), ]
  iv_fml <- as.formula(sprintf("%s ~ %s | state | %s ~ %s",
                               y, paste(ctrls, collapse = " + "), ENDOGENOUS, INSTRUMENT))
  fit <- tryCatch(feols(iv_fml, data = samp, cluster = ~cluster_id,
                        warn = FALSE, notes = FALSE),
                  error = function(e) NULL)
  if (is.null(fit)) next
  fF <- tryCatch(fitstat(fit, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
  cv <- get_tF_cv(fF)
  nm <- paste0("fit_", ENDOGENOUS)
  b  <- unname(coef(fit)[nm]); s <- unname(se(fit)[nm])
  t  <- unname(tstat(fit)[nm]); p <- unname(pvalue(fit)[nm])
  rows[[length(rows) + 1]] <- data.frame(
    family = unname(OUTCOME_FAMILY[y]), outcome = y, coef = b, se = s, t = t, p = p,
    first_stage_F = fF, tF_cv = cv,
    reject_tF_5pct = abs(t) > cv, ci_low_tF = b - cv * s, ci_high_tF = b + cv * s,
    nobs = nobs(fit), n_clusters = length(unique(samp$cluster_id)),
    lagged_dv = if (!is.na(lag)) lag else "",
    stringsAsFactors = FALSE)
}
iv_results <- do.call(rbind, rows)

fwrite(first_stage, file.path(ESTIMATES_DIR, "act_first_stage_fixest.csv"))
fwrite(iv_results,  file.path(ESTIMATES_DIR, "act_iv_results.csv"))

cat("\n=== act-design 2SLS (state-clustered, tF) ===\n")
cat(sprintf("%-14s %-44s %8s %7s %7s %5s\n", "family", "outcome", "coef", "se", "p", "tF*"))
for (i in seq_len(nrow(iv_results))) {
  r <- iv_results[i, ]
  nm <- gsub("_2024_2020", "", gsub("^delta_", "d_", r$outcome))
  cat(sprintf("%-14s %-44s %+8.3f %7.3f %7.3f %5s\n",
              r$family, nm, r$coef, r$se, r$p, ifelse(r$reject_tF_5pct, "*", "")))
}
cat(sprintf("\nWrote:\n  %s\n  %s\n",
            file.path(ESTIMATES_DIR, "act_first_stage_fixest.csv"),
            file.path(ESTIMATES_DIR, "act_iv_results.csv")))
