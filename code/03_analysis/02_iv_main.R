# IV estimation for electoral judicialization — fixest (R)
# Follows Ash, Morelli & Vannoni (2025, JPE) Stata structure.
# Loads pre-assembled design matrix from Python pipeline, runs 2SLS via feols().
#
# fixest formula: y ~ controls | FE | endogenous ~ instrument
# Clustering: by principal electoral zone (within-municipality; avoids spatial correlation).
# Benchmark: ivreghdfe y (endog = instr), absorb(state) cl(zone)

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- path detection (RStudio + Rscript) ----
if (exists("rstudioapi") && tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE)) {
  SCRIPT_DIR <- dirname(rstudioapi::getSourceEditorContext()$path)
} else {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0) {
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  } else {
    getwd()
  }
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
  colClasses = list(character = c("SG_UF", "SG_UE", "cluster_id"))
))
df$code_micro <- as.character(df$code_micro)
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================

INSTRUMENT <- "bartik_iv_no_rrc"
ENDOGENOUS <- "delta_log1p_lawsuits_no_rrc_2024_2020"
THRESHOLD_200K <- 200000L  # Art. 29-II CF/88 — second-round eligibility

PRIMARY_OUTCOMES <- c(
  "delta_runnerup_vote_share_2024_2020",
  "delta_margin_top1_top2_2024_2020"
)
SECONDARY_OUTCOMES <- c("delta_winner_vote_share_2024_2020")
VOTER_BEHAVIOR_OUTCOMES <- c(
  "delta_turnout_rate_2024_2020",
  "delta_null_share_2024_2020",
  "delta_blank_share_2024_2020"
)
ALL_OUTCOMES <- c(PRIMARY_OUTCOMES, SECONDARY_OUTCOMES, VOTER_BEHAVIOR_OUTCOMES)

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
  "turnout_rate_2020", "null_share_2020",
  "share_first_time_candidates_2020", "share_career_politicians_2020"
)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

avail <- function(controls, data) controls[controls %in% names(data)]

build_sample <- function(data, controls, outcomes, fe_col,
                         single_zone = FALSE, aptos_filter = NULL) {
  ctrls <- avail(controls, data)
  outs  <- intersect(outcomes, names(data))
  req   <- unique(c(INSTRUMENT, ENDOGENOUS, "cluster_id", fe_col, ctrls, outs))
  req   <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  if (single_zone && "n_zones_in_municipality" %in% names(samp))
    samp <- samp[samp$n_zones_in_municipality == 1L, ]
  if (!is.null(aptos_filter) && "qt_aptos_2024" %in% names(samp)) {
    if (aptos_filter == "le200k") samp <- samp[samp$qt_aptos_2024 <= THRESHOLD_200K, ]
    if (aptos_filter == "gt200k") samp <- samp[samp$qt_aptos_2024 >  THRESHOLD_200K, ]
  }
  rownames(samp) <- NULL
  samp
}

# First-stage OLS: endogenous ~ instrument + controls | FE
run_first_stage <- function(samp, controls, fe_col) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(INSTRUMENT, ctrls), collapse = " + ") else INSTRUMENT
  fml      <- as.formula(sprintf("%s ~ %s | %s", ENDOGENOUS, ctrl_rhs, fe_col))
  feols(fml, data = samp,
        cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

# 2SLS: outcome ~ controls | FE | endogenous ~ instrument
run_iv <- function(samp, outcome, controls, fe_col) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s", outcome, ctrl_rhs, fe_col, ENDOGENOUS, INSTRUMENT
  ))
  feols(fml, data = samp,
        cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

extract_fs_row <- function(fit, spec, n_obs, n_cl) {
  b  <- coef(fit)[INSTRUMENT]
  se <- se(fit)[INSTRUMENT]
  t  <- tstat(fit)[INSTRUMENT]
  p  <- pvalue(fit)[INSTRUMENT]
  data.frame(
    spec          = spec,
    coef          = b,
    se            = se,
    t             = t,
    p             = p,
    first_stage_F = t^2,
    nobs          = n_obs,
    n_clusters    = n_cl,
    stringsAsFactors = FALSE
  )
}

extract_iv_row <- function(fit, spec, family, outcome, n_obs, n_cl) {
  # fixest prefixes the endogenous variable with "fit_" in IV output
  iv_name <- paste0("fit_", ENDOGENOUS)
  b  <- unname(coef(fit)[iv_name])
  se <- unname(se(fit)[iv_name])
  t  <- unname(tstat(fit)[iv_name])
  p  <- unname(pvalue(fit)[iv_name])
  fstat <- tryCatch(
    fitstat(fit, type = "ivf")[[1]]$stat,
    error = function(e) NA_real_
  )
  data.frame(
    spec       = spec,
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
# 4. SPECIFICATION LIST
# ============================================================
# Each entry: list(name, controls, fe_col, single_zone, aptos_filter)

n_micro <- if ("code_micro" %in% names(df))
             length(unique(df$code_micro[!is.na(df$code_micro)])) else 0L

specs <- list(
  list("baseline_state_fe",         BASELINE_CONTROLS,   "SG_UF",      FALSE, NULL),
  list("baseline_state_fe_sz",      BASELINE_CONTROLS,   "SG_UF",      TRUE,  NULL),
  list("robustness_full_controls",  ROBUSTNESS_CONTROLS, "SG_UF",      FALSE, NULL),
  list("robustness_microregion_fe", BASELINE_CONTROLS,   "code_micro", FALSE, NULL),
  list("subsample_le200k",          BASELINE_CONTROLS,   "SG_UF",      FALSE, "le200k"),
  list("subsample_gt200k",          BASELINE_CONTROLS,   "SG_UF",      FALSE, "gt200k")
)

if (n_micro < 10) {
  specs <- specs[sapply(specs, function(s) s[[3]] != "code_micro")]
  cat("NOTE: code_micro not available; skipping microregion FE spec.\n")
}

cat(sprintf("Running %d specifications x %d outcomes\n\n", length(specs), length(ALL_OUTCOMES)))


# ============================================================
# 5. ESTIMATION LOOP
# ============================================================

fs_rows <- list()
iv_rows <- list()

for (sp in specs) {
  spec_name    <- sp[[1]]
  controls     <- sp[[2]]
  fe_col       <- sp[[3]]
  single_zone  <- sp[[4]]
  aptos_filter <- sp[[5]]

  samp  <- build_sample(df, controls, ALL_OUTCOMES, fe_col, single_zone, aptos_filter)
  n_obs <- nrow(samp)
  n_cl  <- length(unique(samp$cluster_id))
  cat(sprintf("  %s: N=%d, clusters=%d\n", spec_name, n_obs, n_cl))

  # First stage
  tryCatch({
    fs_fit <- run_first_stage(samp, controls, fe_col)
    fs_rows[[length(fs_rows) + 1]] <- extract_fs_row(fs_fit, spec_name, n_obs, n_cl)
  }, error = function(e) message("  FS error [", spec_name, "]: ", conditionMessage(e)))

  # 2SLS for each outcome
  for (y in ALL_OUTCOMES) {
    if (!(y %in% names(samp))) next
    if (sum(!is.na(samp[[y]])) < 20L) next
    family <- if (y %in% PRIMARY_OUTCOMES)         "primary"
              else if (y %in% SECONDARY_OUTCOMES)  "secondary"
              else                                  "voter_behavior"
    tryCatch({
      iv_fit <- run_iv(samp, y, controls, fe_col)
      iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(iv_fit, spec_name, family, y, n_obs, n_cl)
    }, error = function(e)
      message("  IV error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
  }
}

first_stage <- do.call(rbind, fs_rows)
iv_results  <- do.call(rbind, iv_rows)


# ============================================================
# 6. SAVE OUTPUTS
# ============================================================

fwrite(first_stage, file.path(ESTIMATES_DIR, "executive_margin_first_stage_fixest.csv"))
fwrite(iv_results,  file.path(ESTIMATES_DIR, "executive_margin_iv_fixest.csv"))

# Markdown helpers
fmt4 <- function(x) ifelse(is.na(x), "", sprintf("%.4f", as.numeric(x)))
fmt2 <- function(x) ifelse(is.na(x), "", sprintf("%.2f",  as.numeric(x)))

df_to_md <- function(df) {
  cols   <- names(df)
  header <- paste0("| ", paste(cols, collapse = " | "), " |")
  sep    <- paste0("| ", paste(rep("---", length(cols)), collapse = " | "), " |")
  rows   <- apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  paste(c(header, sep, rows), collapse = "\n")
}

fs_fmt <- first_stage
fs_fmt[c("coef", "se", "p")] <- lapply(fs_fmt[c("coef", "se", "p")], fmt4)
fs_fmt[c("t", "first_stage_F")] <- lapply(fs_fmt[c("t", "first_stage_F")], fmt2)

iv_fmt <- iv_results
iv_fmt[c("coef", "se", "p")] <- lapply(iv_fmt[c("coef", "se", "p")], fmt4)
iv_fmt[c("t", "ivf")]        <- lapply(iv_fmt[c("t", "ivf")],        fmt2)

report <- c(
  "# Executive Margin Analysis — fixest 2SLS (R)",
  "",
  "Benchmark: Ash, Morelli & Vannoni (2025, JPE) — `ivreghdfe` → `feols()` in fixest.",
  "Formula: `y ~ controls | FE | Δlog(lawsuits) ~ Bartik_IV`.",
  "SE clustered by principal electoral zone.",
  "",
  "## Specifications",
  "1. **baseline_state_fe** — 7 baseline controls + state FE, all municipalities",
  "2. **baseline_state_fe_sz** — same, single-zone municipalities only",
  "3. **robustness_full_controls** — 14 controls + state FE",
  "4. **robustness_microregion_fe** — 7 baseline controls + microregion FE (~558 cells)",
  "5. **subsample_le200k** — baseline + state FE, ≤200k registered voters (single-round regime, Art. 29-II CF/88)",
  "6. **subsample_gt200k** — baseline + state FE, >200k registered voters (second-round eligible)",
  "",
  "**Note:** `incumbent_ran_2024` is an outcome variable, never a control.",
  "",
  "## First Stage",
  "",
  df_to_md(fs_fmt),
  "",
  "## IV Results",
  "",
  df_to_md(iv_fmt)
)

writeLines(report, file.path(ESTIMATES_DIR, "executive_margin_fixest.md"))

cat("\nResults saved to:\n")
cat("  ", file.path(ESTIMATES_DIR, "executive_margin_first_stage_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "executive_margin_iv_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "executive_margin_fixest.md"), "\n")
