# Family-split IV analysis — fixest 2SLS
#
# Each topic family has its own Bartik IV (sum of bartik_component restricted to
# topics in that family). Each family IV instruments its FAMILY-SPECIFIC endogenous
# variable delta_log1p_{family}_2024_2020 for a clean family-level LATE.
#
# GPS Section V.C: family split decomposes the aggregate LATE by mechanism.
#
# Prerequisites: run 05_patch_family_ivs.py first to add bartik_iv_{family} and
#   delta_log1p_{family}_2024_2020 columns to executive_margin_design.csv.
#
# Outputs:
#   output/tables/regressions/family_iv_results.csv
#   output/tables/regressions/family_iv_results.md

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
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
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
  stop("No family IV columns found in design. Run 05_patch_family_ivs.py first.")
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

BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
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

run_iv <- function(samp, outcome, controls, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
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
    tryCatch({
      iv_fit <- run_iv(samp, y, BASELINE_CONTROLS, iv_col, endogenous)
      iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
        iv_fit, family_label, y, n_obs, n_cl, endogenous
      )
    }, error = function(e)
      message("  IV error [", y, "]: ", conditionMessage(e)))
  }
  cat("\n")
}

iv_results <- do.call(rbind, iv_rows)
fs_results <- do.call(rbind, fs_rows)


# ============================================================
# 6. tF WEAK-INSTRUMENT CORRECTION
# ============================================================

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

fmt4 <- function(x) ifelse(is.na(x), "", sprintf("%.4f", as.numeric(x)))
fmt2 <- function(x) ifelse(is.na(x), "", sprintf("%.2f",  as.numeric(x)))
df_to_md <- function(df) {
  cols   <- names(df)
  header <- paste0("| ", paste(cols, collapse = " | "), " |")
  sep    <- paste0("| ", paste(rep("---", length(cols)), collapse = " | "), " |")
  rows   <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(header, sep, rows), collapse = "\n")
}

fs_fmt <- fs_results
fs_fmt[c("coef_fs", "se_fs", "f_stat")] <- lapply(fs_fmt[c("coef_fs", "se_fs", "f_stat")], fmt2)

iv_fmt <- iv_results
iv_fmt[c("coef", "se", "p")] <- lapply(iv_fmt[c("coef", "se", "p")], fmt4)
iv_fmt[c("t", "ivf")]        <- lapply(iv_fmt[c("t", "ivf")], fmt2)

report <- c(
  "# Family-Split IV Analysis — fixest 2SLS",
  "",
  paste0("Each family IV = sum of bartik_component restricted to topics in that family."),
  paste0("Each family IV instruments its family-specific endogenous (delta_log1p_{family}_2024_2020)."),
  "Formula: `y ~ controls | state FE | delta_log1p_{family} ~ bartik_iv_{family}`.",
  "SE clustered by principal electoral zone.",
  "",
  "## First Stage by Family",
  "",
  df_to_md(fs_fmt),
  "",
  "## IV Results by Family x Outcome (family-specific endogenous)",
  "",
  df_to_md(iv_fmt)
)
writeLines(report, file.path(ESTIMATES_DIR, "family_iv_results.md"))

cat("Results saved:\n")
cat("  ", file.path(ESTIMATES_DIR, "family_iv_results.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "family_iv_results.md"), "\n")
