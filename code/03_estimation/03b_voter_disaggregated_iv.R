# 03b_voter_disaggregated_iv.R — act 2SLS on DISAGGREGATED turnout margins.
#
# The aggregate turnout null (03_voter_behavior_iv.R) is near-mechanical under
# compulsory voting. This script estimates the ELASTIC margins that the
# perfil_comparecimento_abstencao data exposes:
#   facultative turnout (16-17, 70+, illiterate) — the engagement margin
#   low-/high-education turnout, illiterate turnout — the 'confusion' margin
#   female/male turnout and the education / sex turnout GAPS
#
# Outcomes come from data/clean/voter_disaggregated_outcomes.csv (built by
# 05d_voter_disaggregated_outcomes.py), merged onto act_design.csv by
# municipality_id_tse. Spec is identical to the headline: 5 baseline controls +
# the outcome's own 2020 level as lagged DV, state FE, state-clustered SEs, and
# the Lee et al. (2022) tF weak-IV correction.
#
# Writes output/tables/regressions/voter_disaggregated_iv.csv and prints a
# focused table. compulsory_turnout is included as a placebo (should stay null).

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

vd <- as.data.frame(fread(
  file.path(CLEAN_DIR, "voter_disaggregated_outcomes.csv"),
  colClasses = list(character = "municipality_id_tse")))
vd$municipality_id_tse <- sprintf("%05d", as.integer(vd$municipality_id_tse))

new_cols <- setdiff(names(vd), names(df))
df <- merge(df, vd[, c("municipality_id_tse", new_cols)],
            by = "municipality_id_tse", all.x = TRUE)

# leave-fraude-out instrument variant (the headline rests on fraude: dropping it
# crashes F from ~26 to ~4). Rebuild from per-family components so we can ask
# whether any disaggregated positive survives without the dominant shock.
comp <- fread(file.path(CLEAN_DIR, "municipality_act_components.csv"),
              colClasses = list(character = "id_municipio_tse"))
comp <- comp[rung == "act"]
comp[, id_municipio_tse := sprintf("%05d", as.integer(id_municipio_tse))]
no_fraude <- comp[family != "fraude",
                  .(biv_no_fraude = sum(bartik_component)), by = id_municipio_tse]
df <- merge(df, no_fraude, by.x = "municipality_id_tse",
            by.y = "id_municipio_tse", all.x = TRUE)

INSTRUMENT        <- spec_instrument()
ENDOGENOUS        <- spec_endogenous()
BASELINE_CONTROLS <- spec_baseline_controls()
avail <- function(v, data) v[v %in% names(data)]

# outcome -> lagged DV (the outcome's own 2020 level)
OUTCOMES <- c(
  delta_facultative_turnout_2024_2020      = "facultative_turnout_2020",
  delta_compulsory_turnout_2024_2020       = "compulsory_turnout_2020",   # placebo
  delta_low_ed_turnout_2024_2020           = "low_ed_turnout_2020",
  delta_high_ed_turnout_2024_2020          = "high_ed_turnout_2020",
  delta_analfabeto_turnout_2024_2020       = "analfabeto_turnout_2020",
  delta_female_turnout_2024_2020           = "female_turnout_2020",
  delta_male_turnout_2024_2020             = "male_turnout_2020",
  delta_education_turnout_gap_2024_2020     = "education_turnout_gap_2020",
  delta_sex_turnout_gap_2024_2020          = "sex_turnout_gap_2020")

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,2.39,
            2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

run_one <- function(y, instr_col, instr_label) {
  lag   <- OUTCOMES[[y]]
  ctrls <- avail(c(BASELINE_CONTROLS, if (!is.na(lag)) lag), df)
  req   <- unique(c(y, instr_col, ENDOGENOUS, "cluster_id", "state", ctrls))
  samp  <- df[complete.cases(df[, req, drop = FALSE]), ]
  fml   <- as.formula(sprintf("%s ~ %s | state | %s ~ %s",
                              y, paste(ctrls, collapse = " + "),
                              ENDOGENOUS, instr_col))
  fit <- tryCatch(feols(fml, data = samp, cluster = ~cluster_id,
                        warn = FALSE, notes = FALSE), error = function(e) NULL)
  if (is.null(fit)) return(NULL)
  fF <- tryCatch(fitstat(fit, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
  cv <- get_tF_cv(fF); nm <- paste0("fit_", ENDOGENOUS)
  b <- unname(coef(fit)[nm]); s <- unname(se(fit)[nm]); t <- unname(tstat(fit)[nm])
  data.frame(
    instrument = instr_label, outcome = y, lagged_dv = lag, coef = b, se = s,
    t = t, p = unname(pvalue(fit)[nm]), first_stage_F = fF, tF_cv = cv,
    reject_tF_5pct = abs(t) > cv, nobs = nobs(fit),
    sd_outcome = sd(samp[[y]], na.rm = TRUE), stringsAsFactors = FALSE)
}

variants <- c(full = INSTRUMENT, no_fraude = "biv_no_fraude")
rows <- list()
for (y in names(OUTCOMES)) {
  if (!(y %in% names(df))) { cat(sprintf("  (missing outcome %s)\n", y)); next }
  for (lab in names(variants)) {
    r <- run_one(y, variants[[lab]], lab)
    if (!is.null(r)) rows[[length(rows) + 1]] <- r
  }
}
res <- do.call(rbind, rows)
dir.create(ESTIMATES_DIR, showWarnings = FALSE, recursive = TRUE)
fwrite(res, file.path(ESTIMATES_DIR, "voter_disaggregated_iv.csv"))

cat("\n=== act 2SLS on disaggregated turnout margins (on-spec) ===\n")
cat("    full = headline act instrument; no_fraude = drop the dominant shock\n\n")
cat(sprintf("%-26s %-10s %9s %8s %7s %6s %5s\n",
            "outcome", "instr", "coef", "se", "p", "F", "tF*"))
for (y in names(OUTCOMES)) {
  for (lab in names(variants)) {
    r <- res[res$outcome == y & res$instrument == lab, ]
    if (nrow(r) == 0) next
    cat(sprintf("%-26s %-10s %+9.4f %8.4f %7.3f %6.1f %5s\n",
                ifelse(lab == "full",
                       gsub("_2024_2020", "", gsub("^delta_", "", y)), ""),
                lab, r$coef, r$se, r$p, r$first_stage_F,
                ifelse(r$reject_tF_5pct, "yes", "")))
  }
}
cat(sprintf("\nWrote: %s\n",
            file.path(ESTIMATES_DIR, "voter_disaggregated_iv.csv")))
