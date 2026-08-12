# Family-split IV analysis — fixest 2SLS
#
# Each topic family has its own Bartik IV (sum of bartik_component restricted to
# topics in that family). Each family IV instruments its FAMILY-SPECIFIC endogenous
# variable delta_log1p_{family}_2024_2020 for a clean family-level LATE.
#
# GPS Section V.C: family split decomposes the aggregate LATE by mechanism.
#
# Prerequisites: run 01c_patch_family_ivs.py first to add bartik_iv_{family} and
#   delta_log1p_{family}_2024_2020 columns to executive_margin_design.csv.
#
# Outputs:
#   output/tables/regressions/family_iv_results.csv

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
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0) {
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  } else getwd()
}
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "exploration", "output", "tables", "regressions")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)


# ============================================================
# 1. LOAD DATA
# ============================================================

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================

# Detect family IV columns: bartik_iv_{family} only — exclude aggregate and old no_rrc variants
family_iv_cols <- grep("^bartik_iv_", names(df), value = TRUE)
family_iv_cols <- family_iv_cols[!grepl("(no_rrc|2020_2024)", family_iv_cols)]

if (length(family_iv_cols) == 0) {
  stop("No family IV columns found in design. Run 01c_patch_family_ivs.py first.")
}
cat(sprintf("Family IV columns: %s\n\n", paste(family_iv_cols, collapse = ", ")))

get_family_label    <- function(col) sub("^bartik_iv_", "", col)
get_family_endog    <- function(family_label) paste0("delta_log1p_", family_label, "_2024_2020")

PRIMARY_OUTCOMES <- c(
  "delta_runnerup_vote_share_2024_2020",
  "delta_margin_top1_top2_2024_2020"
)
SECONDARY_OUTCOMES <- c(
  "delta_winner_vote_share_2024_2020",
  "delta_winner_majority_2024_2020",
  "delta_log1p_n_candidates_with_votes_2024_2020"
)
ALL_OUTCOMES <- c(PRIMARY_OUTCOMES, SECONDARY_OUTCOMES)

# V3 control philosophy (2026-06-28), identical to 02_iv_main.R: common pre-
# determined controls + each outcome's own 2016 level (per-outcome lagged DV),
# NO 2020 levels of competition outcomes (Lord's-paradox avoidance).
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020",
  "margin_2016"
)

LAG16_MAP <- c(
  delta_runnerup_vote_share_2024_2020            = "runnerup_vote_share_2016",
  delta_margin_top1_top2_2024_2020               = "margin_top1_top2_2016",
  delta_winner_vote_share_2024_2020              = "winner_vote_share_2016",
  delta_winner_majority_2024_2020                = "winner_majority_2016",
  delta_log1p_n_candidates_with_votes_2024_2020  = "n_candidates_with_votes_2016"
)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

avail <- function(controls, data) controls[controls %in% names(data)]

run_first_stage <- function(samp, controls, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(instrument, ctrls), collapse = " + ") else instrument
  fml      <- as.formula(sprintf("%s ~ %s | SG_UF", endogenous, ctrl_rhs))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

run_iv <- function(samp, outcome, controls, instrument, endogenous, lag_col = NULL) {
  ctrls    <- avail(c(controls, lag_col), samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | SG_UF | %s ~ %s", outcome, ctrl_rhs, endogenous, instrument
  ))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

extract_iv_row <- function(fit, family, outcome, n_obs, n_cl, endogenous) {
  iv_name <- paste0("fit_", endogenous)
  b  <- unname(coef(fit)[iv_name])
  se <- unname(se(fit)[iv_name])
  t  <- unname(tstat(fit)[iv_name])
  p  <- unname(pvalue(fit)[iv_name])
  fstat <- tryCatch(fitstat(fit, type = "ivf")[[1]]$stat, error = function(e) NA_real_)
  data.frame(
    family     = family,
    outcome    = outcome,
    coef       = b,
    se         = se,
    t          = t,
    p          = p,
    ivf        = fstat,
    nobs       = n_obs,
    n_clusters = n_cl,
    stringsAsFactors = FALSE
  )
}


# ============================================================
# 4. BUILD SHARED COVARIATE SAMPLE (controls + FE complete cases)
# ============================================================

ctrls_avail <- avail(BASELINE_CONTROLS, df)
req_shared  <- unique(c("cluster_id", "SG_UF", ctrls_avail))
req_shared  <- req_shared[req_shared %in% names(df)]
samp_shared <- df[complete.cases(df[, req_shared, drop = FALSE]), ]
rownames(samp_shared) <- NULL
cat(sprintf("Shared covariate sample: N=%d, clusters=%d\n\n",
    nrow(samp_shared), length(unique(samp_shared$cluster_id))))


# ============================================================
# 5. ESTIMATION LOOP
# ============================================================

iv_rows <- list()
fs_rows <- list()

for (iv_col in family_iv_cols) {
  family_label <- get_family_label(iv_col)
  endogenous   <- get_family_endog(family_label)
  cat(sprintf("=== Family: %s ===\n", family_label))

  if (!(iv_col %in% names(samp_shared))) {
    cat("  SKIP: IV column not in design.\n"); next
  }
  if (!(endogenous %in% names(samp_shared))) {
    cat(sprintf("  SKIP: endogenous column '%s' not found.\n", endogenous)); next
  }

  # Family sample: shared covariate complete cases + non-missing IV + non-missing endogenous
  samp <- samp_shared[
    !is.na(samp_shared[[iv_col]]) & !is.na(samp_shared[[endogenous]]),
  ]
  n_obs <- nrow(samp)
  n_cl  <- length(unique(samp$cluster_id))

  # First stage
  tryCatch({
    fs_fit <- run_first_stage(samp, BASELINE_CONTROLS, iv_col, endogenous)
    b_fs   <- coef(fs_fit)[iv_col]
    se_fs  <- se(fs_fit)[iv_col]
    f_fs   <- (b_fs / se_fs)^2
    fs_rows[[length(fs_rows) + 1]] <- data.frame(
      family     = family_label,
      endogenous = endogenous,
      coef_fs    = b_fs,
      se_fs      = se_fs,
      f_stat     = f_fs,
      nobs       = n_obs,
      stringsAsFactors = FALSE
    )
    cat(sprintf("  First stage: coef=%.4f, F=%.1f, N=%d\n", b_fs, f_fs, n_obs))
  }, error = function(e) message("  FS error: ", conditionMessage(e)))

  # 2SLS per outcome
  for (y in ALL_OUTCOMES) {
    if (!(y %in% names(samp))) next
    if (sum(!is.na(samp[[y]])) < 20L) next
    lag_col <- unname(LAG16_MAP[y]); if (is.na(lag_col)) lag_col <- NULL
    tryCatch({
      iv_fit <- run_iv(samp, y, BASELINE_CONTROLS, iv_col, endogenous, lag_col)
      iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
        iv_fit, family_label, y, nobs(iv_fit), n_cl, endogenous
      )
    }, error = function(e)
      message("  IV error [", y, "]: ", conditionMessage(e)))
  }
  cat("\n")
}

iv_results <- do.call(rbind, iv_rows)
fs_results <- do.call(rbind, fs_rows)


# ============================================================
# 6. tF WEAK-INSTRUMENT CORRECTION (Lee et al. 2022, AER)
# ============================================================
# Authoritative table + get_tF_cv() from the shared util (cv reaches 1.96 only
# at F ~ 104.7, not F = 23.1). See code/utils/tf_critical_values.R.
source(file.path(PROJECT_ROOT, "code", "utils", "tf_critical_values.R"))

fs_F_map <- stats::setNames(fs_results$f_stat, fs_results$family)
iv_results$first_stage_F  <- fs_F_map[iv_results$family]
iv_results$tF_cv          <- sapply(iv_results$first_stage_F, get_tF_cv)
iv_results$ci95_low_tF    <- iv_results$coef - iv_results$tF_cv * iv_results$se
iv_results$ci95_high_tF   <- iv_results$coef + iv_results$tF_cv * iv_results$se
iv_results$reject_tF_5pct <- abs(iv_results$t) > iv_results$tF_cv


# ============================================================
# 7. SAVE
# ============================================================

fwrite(iv_results, file.path(ESTIMATES_DIR, "family_iv_results.csv"))

cat("Results saved:\n")
cat("  ", file.path(ESTIMATES_DIR, "family_iv_results.csv"), "\n")
