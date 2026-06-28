# 24b_shock_granularity_fstage.R — does a FINER shock partition buy relevance?
#
# 24_shock_granularity.py rebuilt the leave-own-state-out Bartik instrument at
# three grains (act10 / subject / pair) and showed the effective shock count rises
# from ~6-9 to ~62 (subject) to ~200 (pair). More shocks = a more credible
# shift-exogeneity (BHJ) asymptotic. But finer cells are sparse, so the shocks get
# noisy. This script asks the price of that: for each grain, the on-spec
# first-stage F (single instrument => F = robust t^2) and the headline 2SLS on a
# few representative outcomes, so we can see whether relevance survives and whether
# the (null) second-stage conclusions move.
#
# Reads data/clean/shock_granularity_instruments.csv + data/estimation/act_design.csv.
# Writes output/tables/regressions/shock_granularity_fstage.csv.

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
source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))

PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
CLEAN_DIR      <- file.path(PROJECT_ROOT, "data", "clean")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
df$municipality_id_tse <- sprintf("%05d", as.integer(df$municipality_id_tse))

ivs <- as.data.frame(fread(
  file.path(CLEAN_DIR, "shock_granularity_instruments.csv"),
  colClasses = list(character = "municipality_id_tse")))
ivs$municipality_id_tse <- sprintf("%05d", as.integer(ivs$municipality_id_tse))
df <- merge(df, ivs, by = "municipality_id_tse", all.x = TRUE)

ENDOGENOUS        <- spec_endogenous()
BASELINE_CONTROLS <- spec_baseline_controls()
avail <- function(v, data) v[v %in% names(data)]
GRAINS <- c(act10 = "biv_act10", subject = "biv_subject", pair = "biv_pair")

# representative outcomes: the two marginal 'survivors' + two clean nulls
OUTCOMES <- c(
  delta_others_vote_share_2024_2020          = "others_vote_share_2020",
  delta_log1p_n_candidates_with_votes_2024_2020 = NA,
  delta_turnout_rate_2024_2020               = "turnout_rate_2020",
  delta_female_share_2024_2020               = "female_share_2020")

## ---- first-stage F per grain (outcome-agnostic: baseline controls only) ------
cat("=== first-stage strength by shock grain (state-clustered) ===\n")
cat(sprintf("%-9s %10s %10s %8s\n", "grain", "coef", "se", "F=t^2"))
fs_rows <- list()
for (g in names(GRAINS)) {
  iv <- GRAINS[[g]]
  ctrls <- avail(BASELINE_CONTROLS, df)
  req <- unique(c(ENDOGENOUS, iv, "state", "cluster_id", ctrls))
  samp <- df[complete.cases(df[, req, drop = FALSE]), ]
  fml <- as.formula(sprintf("%s ~ %s + %s | state",
                            ENDOGENOUS, iv, paste(ctrls, collapse = " + ")))
  fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  b <- coef(fit)[iv]; s <- se(fit)[iv]; F <- (b / s)^2
  cat(sprintf("%-9s %10.4f %10.4f %8.1f\n", g, b, s, F))
  fs_rows[[g]] <- data.frame(stage = "first", grain = g, outcome = NA,
                             coef = unname(b), se = unname(s), p = NA,
                             first_stage_F = unname(F), nobs = nobs(fit))
}

## ---- 2SLS per grain x outcome ------------------------------------------------
cat("\n=== headline 2SLS coef (p) [first-stage F] by grain ===\n")
ss_rows <- list()
for (y in names(OUTCOMES)) {
  if (!(y %in% names(df))) next
  cat(sprintf("\n%s\n", gsub("_2024_2020", "", gsub("^delta_", "", y))))
  lag <- OUTCOMES[[y]]
  for (g in names(GRAINS)) {
    iv <- GRAINS[[g]]
    ctrls <- avail(c(BASELINE_CONTROLS, if (!is.na(lag)) lag), df)
    req <- unique(c(y, iv, ENDOGENOUS, "state", "cluster_id", ctrls))
    samp <- df[complete.cases(df[, req, drop = FALSE]), ]
    fml <- as.formula(sprintf("%s ~ %s | state | %s ~ %s",
                              y, paste(ctrls, collapse = " + "), ENDOGENOUS, iv))
    fit <- tryCatch(feols(fml, data = samp, cluster = ~cluster_id,
                          warn = FALSE, notes = FALSE), error = function(e) NULL)
    if (is.null(fit)) { cat(sprintf("  %-9s (failed)\n", g)); next }
    fF <- tryCatch(fitstat(fit, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
    nm <- paste0("fit_", ENDOGENOUS)
    b <- coef(fit)[nm]; p <- pvalue(fit)[nm]
    cat(sprintf("  %-9s %+8.4f (p=%.3f)  F=%.1f\n", g, b, p, fF))
    ss_rows[[length(ss_rows)+1]] <- data.frame(
      stage = "second", grain = g, outcome = y, coef = unname(b),
      se = unname(se(fit)[nm]), p = unname(p), first_stage_F = fF, nobs = nobs(fit))
  }
}

res <- rbind(do.call(rbind, fs_rows), do.call(rbind, ss_rows))
dir.create(ESTIMATES_DIR, showWarnings = FALSE, recursive = TRUE)
fwrite(res, file.path(ESTIMATES_DIR, "shock_granularity_fstage.csv"))
cat(sprintf("\nWrote: %s\n",
            file.path(ESTIMATES_DIR, "shock_granularity_fstage.csv")))
