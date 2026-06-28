# IV mechanism analysis — campaign finance (SPCE)
# Tests whether exogenous litigation increases campaign spending,
# consistent with a cost-raising mechanism.
#
# Two parts:
#   Part A: Balance check — is baseline (2020) spending correlated with the instrument?
#   Part B: IV with delta spending as outcomes (mechanism outcomes)
#
# Follows 02_iv_main.R structure. Same instrument, same specs, same clustering.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- path detection ----
if (exists("rstudioapi") && tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE)) {
  SCRIPT_DIR <- dirname(rstudioapi::getSourceEditorContext()$path)
} else {
  args     <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0)
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  else getwd()
}
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
CLEAN_DIR      <- file.path(PROJECT_ROOT, "data", "clean")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)


# ============================================================
# 1. LOAD AND MERGE DATA
# ============================================================

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))

# Rename legacy column names if present
rename_map <- c(
  state               = "SG_UF",
  municipality_id_tse = "SG_UE",
  municipality_name   = "NM_UE"
)
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]

cat(sprintf("Design matrix: %d municipalities\n", nrow(df)))

# Determine municipality join key in design
muni_key_design <- if ("municipality_id_tse" %in% names(df)) {
  "municipality_id_tse"
} else if ("SG_UE" %in% names(df)) {
  "SG_UE"
} else {
  stop("No municipality key found in design matrix")
}

# Load SPCE executive data
spce <- as.data.frame(fread(
  file.path(CLEAN_DIR, "spce_executive.csv"),
  colClasses = list(character = "municipality_id_tse")
))
spce$municipality_id_tse <- formatC(as.integer(spce$municipality_id_tse),
                                    width = 5, flag = "0")

# Rename SPCE columns to match naming convention (delta_*_2024_2020)
col_map <- c(
  delta_total_per_cand               = "delta_spend_total_per_cand",
  delta_legal_per_cand               = "delta_spend_legal_per_cand",
  delta_marketing_per_cand           = "delta_spend_marketing_per_cand",
  delta_traditional_marketing_per_cand = "delta_spend_trad_marketing_per_cand",
  delta_online_marketing_per_cand    = "delta_spend_online_marketing_per_cand",
  total_per_cand_2020                = "spend_total_per_cand_2020",
  legal_per_cand_2020                = "spend_legal_per_cand_2020",
  marketing_per_cand_2020            = "spend_marketing_per_cand_2020",
  traditional_marketing_per_cand_2020 = "spend_trad_marketing_per_cand_2020",
  online_marketing_per_cand_2020     = "spend_online_marketing_per_cand_2020"
)
for (old_col in names(col_map)) {
  if (old_col %in% names(spce))
    names(spce)[names(spce) == old_col] <- col_map[[old_col]]
}

# Merge SPCE into design on municipality key
spce_cols <- c("municipality_id_tse",
               unname(col_map)[unname(col_map) %in% names(spce)])
df <- merge(df, spce[, spce_cols],
            by.x = muni_key_design, by.y = "municipality_id_tse",
            all.x = TRUE)

cat(sprintf("After SPCE merge: %d municipalities\n", nrow(df)))
cat(sprintf("  Municipalities with SPCE data: %d\n",
            sum(!is.na(df$delta_spend_total_per_cand))))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================

INSTRUMENT <- "bartik_iv_act"
ENDOGENOUS <- "delta_log1p_act_lawsuits"

# Part A: baseline (2020) spending levels — balance check
BALANCE_OUTCOMES <- c(
  "spend_total_per_cand_2020",
  "spend_legal_per_cand_2020",
  "spend_marketing_per_cand_2020",
  "spend_trad_marketing_per_cand_2020",
  "spend_online_marketing_per_cand_2020"
)

# Part B: delta spending outcomes — mechanism IV
MECHANISM_OUTCOMES <- c(
  "delta_spend_total_per_cand",
  "delta_spend_legal_per_cand",
  "delta_spend_marketing_per_cand",
  "delta_spend_trad_marketing_per_cand",
  "delta_spend_online_marketing_per_cand"
)

BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
)

ROBUSTNESS_CONTROLS <- c(
  BASELINE_CONTROLS,
  "enp_2016",
  "female_vote_share_2020", "nonwhite_vote_share_2020", "higher_education_vote_share_2020",
  "log1p_party_count_2020", "log1p_coalition_count_2020",
  "turnout_rate_2020", "null_rate_2020",
  "share_first_time_candidates_2020", "share_career_politicians_2020"
)

specs <- list(
  list("baseline",          BASELINE_CONTROLS,                                  "SG_UF", FALSE, NULL),
  list("single_zone",       BASELINE_CONTROLS,                                  "SG_UF", TRUE,  NULL),
  list("extended_controls", ROBUSTNESS_CONTROLS,                                "SG_UF", FALSE, NULL),
  list("open_seat",         BASELINE_CONTROLS,                                  "SG_UF", FALSE, "open_seat"),
  list("contested_seat",    BASELINE_CONTROLS,                                  "SG_UF", FALSE, "no_open_seat")
)


# ============================================================
# 3. HELPER FUNCTIONS  (same as 02_iv_main.R)
# ============================================================

avail <- function(controls, data) controls[controls %in% names(data)]

build_sample <- function(data, controls, outcomes, fe_col, single_zone = FALSE,
                         aptos_filter = NULL) {
  ctrls <- avail(controls, data)
  outs  <- intersect(outcomes, names(data))
  req   <- unique(c(INSTRUMENT, ENDOGENOUS, "cluster_id", fe_col, ctrls, outs))
  req   <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  if (single_zone && "n_zones_in_municipality" %in% names(samp))
    samp <- samp[samp$n_zones_in_municipality == 1L, ]
  if (!is.null(aptos_filter)) {
    if (aptos_filter == "open_seat" && "open_seat_2024" %in% names(samp))
      samp <- samp[!is.na(samp$open_seat_2024) & samp$open_seat_2024 == 1L, ]
    if (aptos_filter == "no_open_seat" && "open_seat_2024" %in% names(samp))
      samp <- samp[!is.na(samp$open_seat_2024) & samp$open_seat_2024 == 0L, ]
  }
  rownames(samp) <- NULL
  samp
}

run_ols <- function(samp, outcome, controls, fe_col) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(INSTRUMENT, ctrls), collapse = " + ") else INSTRUMENT
  fml      <- as.formula(sprintf("%s ~ %s | %s", outcome, ctrl_rhs, fe_col))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

run_first_stage <- function(samp, controls, fe_col) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(INSTRUMENT, ctrls), collapse = " + ") else INSTRUMENT
  fml      <- as.formula(sprintf("%s ~ %s | %s", ENDOGENOUS, ctrl_rhs, fe_col))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

run_iv <- function(samp, outcome, controls, fe_col) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s", outcome, ctrl_rhs, fe_col, ENDOGENOUS, INSTRUMENT
  ))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

extract_ols_row <- function(fit, part, spec, outcome, n_obs, n_cl) {
  b  <- coef(fit)[INSTRUMENT]
  se <- se(fit)[INSTRUMENT]
  t  <- tstat(fit)[INSTRUMENT]
  p  <- pvalue(fit)[INSTRUMENT]
  data.frame(part = part, spec = spec, outcome = outcome,
             coef = b, se = se, t = t, p = p,
             nobs = n_obs, n_clusters = n_cl, stringsAsFactors = FALSE)
}

extract_iv_row <- function(fit, spec, outcome, n_obs, n_cl) {
  iv_name <- paste0("fit_", ENDOGENOUS)
  b  <- unname(coef(fit)[iv_name])
  se <- unname(se(fit)[iv_name])
  t  <- unname(tstat(fit)[iv_name])
  p  <- unname(pvalue(fit)[iv_name])
  fstat <- tryCatch(fitstat(fit, type = "ivf")[[1]]$stat, error = function(e) NA_real_)
  data.frame(spec = spec, outcome = outcome,
             coef = b, se = se, t = t, p = p,
             ivf = fstat, nobs = n_obs, n_clusters = n_cl, stringsAsFactors = FALSE)
}

# tF correction (Lee et al. 2022)
tF_lookup <- data.frame(
  F_val = c(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
            16, 17, 18, 19, 20, 21, 22, 23.1, 25, 30, 40),
  tF_cv = c(13.99, 7.13, 5.24, 4.31, 3.78, 3.44, 3.21, 3.02, 2.86, 2.73,
             2.62, 2.53, 2.46, 2.39, 2.33, 2.28, 2.24, 2.20, 2.17, 2.14,
             2.11, 2.00, 1.96, 1.96, 1.96)
)
get_tF_cv <- function(f) {
  if (is.na(f) || f >= 23.1) return(1.96)
  if (f <= 2) return(13.99)
  approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y
}


# ============================================================
# 4. ESTIMATION
# ============================================================

balance_rows <- list()
fs_rows      <- list()
iv_rows      <- list()

for (sp in specs) {
  spec_name    <- sp[[1]]
  controls     <- sp[[2]]
  fe_col       <- sp[[3]]
  single_zone  <- sp[[4]]
  aptos_filter <- sp[[5]]

  all_outcomes <- c(BALANCE_OUTCOMES, MECHANISM_OUTCOMES)
  samp <- build_sample(df, controls, all_outcomes, fe_col, single_zone, aptos_filter)
  n_obs <- nrow(samp)
  n_cl  <- length(unique(samp$cluster_id))
  cat(sprintf("  %s: N=%d, clusters=%d\n", spec_name, n_obs, n_cl))

  # ---- Part A: OLS balance check (instrument ~ baseline spending level) ----
  for (y in BALANCE_OUTCOMES) {
    if (!(y %in% names(samp)) || sum(!is.na(samp[[y]])) < 20L) next
    tryCatch({
      fit <- run_ols(samp, y, controls, fe_col)
      balance_rows[[length(balance_rows) + 1]] <- extract_ols_row(
        fit, "balance", spec_name, y, n_obs, n_cl
      )
    }, error = function(e) message("  OLS error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
  }

  # ---- First stage ----
  fs_fit <- NULL
  tryCatch({
    fs_fit <- run_first_stage(samp, controls, fe_col)
    b  <- coef(fs_fit)[INSTRUMENT]
    se <- se(fs_fit)[INSTRUMENT]
    t  <- tstat(fs_fit)[INSTRUMENT]
    fs_rows[[length(fs_rows) + 1]] <- data.frame(
      spec = spec_name, coef = b, se = se, t = t,
      first_stage_F = t^2, nobs = n_obs, n_clusters = n_cl
    )
  }, error = function(e) message("  FS error [", spec_name, "]: ", conditionMessage(e)))

  # ---- Part B: 2SLS with mechanism outcomes ----
  for (y in MECHANISM_OUTCOMES) {
    if (!(y %in% names(samp)) || sum(!is.na(samp[[y]])) < 20L) next
    tryCatch({
      fit <- run_iv(samp, y, controls, fe_col)
      iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(fit, spec_name, y, n_obs, n_cl)
    }, error = function(e) message("  IV error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
  }
}

balance_results <- do.call(rbind, balance_rows)
first_stage     <- do.call(rbind, fs_rows)
iv_results      <- do.call(rbind, iv_rows)


# ============================================================
# 5. tF CORRECTION
# ============================================================

first_stage$tF_cv <- sapply(first_stage$first_stage_F, get_tF_cv)

fs_F_map <- stats::setNames(first_stage$first_stage_F, first_stage$spec)

iv_results$first_stage_F <- fs_F_map[iv_results$spec]
iv_results$tF_cv         <- sapply(iv_results$first_stage_F, get_tF_cv)
iv_results$reject_tF_5pct <- abs(iv_results$t) > iv_results$tF_cv
iv_results$ci95_low_tF    <- iv_results$coef - iv_results$tF_cv * iv_results$se
iv_results$ci95_high_tF   <- iv_results$coef + iv_results$tF_cv * iv_results$se


# ============================================================
# 6. SAVE
# ============================================================

fwrite(balance_results, file.path(ESTIMATES_DIR, "mechanism_media_balance.csv"))
fwrite(first_stage,     file.path(ESTIMATES_DIR, "mechanism_media_first_stage.csv"))
fwrite(iv_results,      file.path(ESTIMATES_DIR, "mechanism_media_iv.csv"))

cat("\nResults saved:\n")
cat("  ", file.path(ESTIMATES_DIR, "mechanism_media_balance.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "mechanism_media_first_stage.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "mechanism_media_iv.csv"), "\n")

# ---- Console summary (baseline spec) ----
cat("\n=== PART A: BALANCE CHECK (baseline spec) ===\n")
cat("OLS: instrument ~ baseline spending level + controls + state FE\n")
cat("(Non-zero coef = instrument correlated with pre-treatment spending)\n\n")
bal_base <- balance_results[balance_results$spec == "baseline", ]
for (i in seq_len(nrow(bal_base))) {
  r <- bal_base[i, ]
  cat(sprintf("  %-42s  coef=%8.0f  se=%8.0f  p=%.3f\n",
              r$outcome, r$coef, r$se, r$p))
}

cat("\n=== PART B: IV MECHANISM OUTCOMES (baseline spec) ===\n")
cat(sprintf("First-stage F = %.1f  (tF_cv = %.2f)\n",
    first_stage$first_stage_F[first_stage$spec == "baseline"],
    first_stage$tF_cv[first_stage$spec == "baseline"]))
cat("\n")
iv_base <- iv_results[iv_results$spec == "baseline", ]
for (i in seq_len(nrow(iv_base))) {
  r <- iv_base[i, ]
  star <- if (r$reject_tF_5pct) "*" else ""
  cat(sprintf("  %-42s  coef=%8.0f  se=%8.0f  p=%.3f  tF=%s\n",
              r$outcome, r$coef, r$se, r$p,
              if (r$reject_tF_5pct) "reject" else "no"))
}
