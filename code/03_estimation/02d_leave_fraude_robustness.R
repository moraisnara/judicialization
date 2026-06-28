# 02d_leave_fraude_robustness.R — Rotemberg leave-one-family-out robustness.
#
# The act instrument's Rotemberg weights are dominated by ONE shock: fraude carries
# ~64% of the positive alpha (pesquisa_adv ~51%, abuso ~38%, offset by 5 negative
# families). This script asks the BHJ/Goldsmith-Pinkham question: does the headline
# survive if the high-weight family is removed from the instrument?
#
# It rebuilds the instrument leaving fraude out (and, for context, each of the top-3
# positive families individually) from the per-family bartik_component in
# data/clean/municipality_act_components.csv, then re-runs the ON-SPEC 2SLS
# (5 baseline controls + per-outcome lagged DV; state FE; state-clustered; Lee tF)
# for every outcome. The endogenous (realized total act-lawsuit growth) is held
# fixed — only the instrument's family composition changes.
#
# Writes output/tables/regressions/act_iv_leave_family_out.csv (long: instrument x
# outcome) and prints a focused comparison of the surviving headline outcomes.

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

comp <- fread(file.path(CLEAN_DIR, "municipality_act_components.csv"),
              colClasses = list(character = "id_municipio_tse"))
comp <- comp[rung == "act"]
comp[, id_municipio_tse := sprintf("%05d", as.integer(id_municipio_tse))]

# ---- rebuild the instrument, full and leave-one-family-out -------------------
# bartik_iv_act = sum over families of bartik_component. A leave-k-out instrument
# drops family k's component from that sum.
full_iv <- comp[, .(iv_rebuilt = sum(bartik_component)), by = id_municipio_tse]
mk_leaveout <- function(fam)
  comp[family != fam, .(iv = sum(bartik_component)), by = id_municipio_tse]

LEAVE_OUT <- c("fraude", "pesquisa_adv", "abuso")   # top-3 positive Rotemberg weights
ivs <- list(full = full_iv[, .(id_municipio_tse, iv = iv_rebuilt)])
for (f in LEAVE_OUT) ivs[[paste0("no_", f)]] <- mk_leaveout(f)

# merge all instrument variants onto the design
for (nm in names(ivs)) {
  v <- ivs[[nm]]; setnames(v, "iv", paste0("biv_", nm))
  df <- merge(df, v, by.x = "municipality_id_tse", by.y = "id_municipio_tse", all.x = TRUE)
}

# sanity: rebuilt full instrument must match the stored bartik_iv_act
if ("bartik_iv_act" %in% names(df)) {
  ok <- df[!is.na(df$bartik_iv_act) & !is.na(df$biv_full), ]
  cat(sprintf("Sanity: cor(stored bartik_iv_act, rebuilt) = %.6f ; max|diff| = %.2e\n",
              cor(ok$bartik_iv_act, ok$biv_full),
              max(abs(ok$bartik_iv_act - ok$biv_full))))
}

ENDOGENOUS <- spec_endogenous()
BASELINE_CONTROLS <- spec_baseline_controls()
avail <- function(v, data) v[v %in% names(data)]

OUTCOME_FAMILY <- c(
  delta_runnerup_vote_share_2024_2020 = "primary",
  delta_margin_top1_top2_2024_2020 = "primary",
  delta_winner_vote_share_2024_2020 = "secondary",
  delta_winner_majority_2024_2020 = "secondary",
  delta_others_vote_share_2024_2020 = "secondary",
  delta_log1p_n_candidates_with_votes_2024_2020 = "secondary",
  delta_female_vote_share_2024_2020 = "composition",
  delta_female_share_2024_2020 = "composition",
  delta_nonwhite_vote_share_2024_2020 = "composition",
  delta_new_candidate_vote_share_2024_2020 = "composition",
  delta_incumbent_candidate_vote_share_2024_2020 = "composition",
  delta_winner_is_female_2024_2020 = "composition",
  delta_winner_is_new_vs_2020_2024_2020 = "composition",
  delta_turnout_rate_2024_2020 = "voter_behavior",
  delta_null_rate_2024_2020 = "voter_behavior",
  delta_blank_rate_2024_2020 = "voter_behavior",
  delta_valid_vote_rate_2024_2020 = "voter_behavior",
  delta_share_first_time_candidates_2024_2020 = "entry",
  delta_share_serial_challenger_2024_2020 = "entry",
  delta_share_cross_cycle_returner_2024_2020 = "entry",
  delta_effective_n_candidates_vote_2024_2020 = "fragmentation",
  delta_effective_party_count_candidates_2024_2020 = "fragmentation",
  delta_vote_hhi_candidate_2024_2020 = "fragmentation",
  delta_candidate_hhi_party_2024_2020 = "fragmentation",
  delta_top2_vote_share_2024_2020 = "fragmentation")
ALL_OUTCOMES <- names(OUTCOME_FAMILY)

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,2.39,
            2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

run_sweep <- function(instr_col, instr_label) {
  rows <- list()
  for (y in ALL_OUTCOMES) {
    if (!(y %in% names(df))) next
    lag   <- spec_lagged_dv(y)
    ctrls <- avail(c(BASELINE_CONTROLS, if (!is.na(lag)) lag), df)
    req   <- unique(c(y, instr_col, ENDOGENOUS, "cluster_id", "state", ctrls))
    samp  <- df[complete.cases(df[, req, drop = FALSE]), ]
    fml   <- as.formula(sprintf("%s ~ %s | state | %s ~ %s",
                                y, paste(ctrls, collapse = " + "), ENDOGENOUS, instr_col))
    fit <- tryCatch(feols(fml, data = samp, cluster = ~cluster_id,
                          warn = FALSE, notes = FALSE), error = function(e) NULL)
    if (is.null(fit)) next
    fF <- tryCatch(fitstat(fit, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
    cv <- get_tF_cv(fF); nm <- paste0("fit_", ENDOGENOUS)
    b <- unname(coef(fit)[nm]); s <- unname(se(fit)[nm]); t <- unname(tstat(fit)[nm])
    rows[[length(rows) + 1]] <- data.frame(
      instrument = instr_label, family = unname(OUTCOME_FAMILY[y]), outcome = y,
      coef = b, se = s, t = t, p = unname(pvalue(fit)[nm]),
      first_stage_F = fF, tF_cv = cv, reject_tF_5pct = abs(t) > cv,
      nobs = nobs(fit), stringsAsFactors = FALSE)
  }
  do.call(rbind, rows)
}

variants <- c(full = "biv_full", no_fraude = "biv_no_fraude",
              no_pesquisa_adv = "biv_no_pesquisa_adv", no_abuso = "biv_no_abuso")
all_res <- do.call(rbind, Map(function(col, lab) run_sweep(col, lab),
                              variants, names(variants)))
fwrite(all_res, file.path(ESTIMATES_DIR, "act_iv_leave_family_out.csv"))

# ---- first-stage strength of each instrument variant ------------------------
cat("\n=== first-stage F by instrument variant (state-clustered) ===\n")
for (lab in names(variants)) {
  sub <- all_res[all_res$instrument == lab, ]
  cat(sprintf("  %-16s  median F = %.1f  (range %.1f - %.1f)\n",
              lab, median(sub$first_stage_F), min(sub$first_stage_F), max(sub$first_stage_F)))
}

# ---- focused comparison: the headline outcomes ------------------------------
HEAD <- c("delta_valid_vote_rate_2024_2020", "delta_others_vote_share_2024_2020",
          "delta_log1p_n_candidates_with_votes_2024_2020",
          "delta_turnout_rate_2024_2020", "delta_female_vote_share_2024_2020")
cat("\n=== headline outcomes: coef (p) [tF*] across leave-out variants ===\n")
for (y in HEAD) {
  cat(sprintf("\n%s\n", gsub("_2024_2020", "", gsub("^delta_", "", y))))
  for (lab in names(variants)) {
    r <- all_res[all_res$instrument == lab & all_res$outcome == y, ]
    if (nrow(r) == 0) next
    cat(sprintf("  %-16s %+8.4f  (p=%.3f)  F=%.1f  %s\n",
                lab, r$coef, r$p, r$first_stage_F, ifelse(r$reject_tF_5pct, "tF*", "")))
  }
}
cat(sprintf("\nWrote: %s\n", file.path(ESTIMATES_DIR, "act_iv_leave_family_out.csv")))
