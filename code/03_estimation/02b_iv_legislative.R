# IV estimation for electoral judicialization — legislative outcomes (vereadores)
#
# Same instrument as executive analysis: adversarial Bartik shift-share IV
# (administrative and procedural classes/subjects excluded at build stage).
#
# fixest formula: y ~ controls | FE | endogenous ~ instrument
# Clustering: by principal electoral zone (same as executive spec).
#
# Outcome families:
#   candidate_pool — who runs: total candidates, field diversity, party count
#   elected_comp   — who wins: elected female/nonwhite/education/age shares, reelection
#   party_comp     — party competition: party count, coalition count, HHI

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
  file.path(ESTIMATION_DIR, "legislative_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
cat(sprintf("Loaded legislative design: %d municipalities\n", nrow(df)))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================

VARIANTS <- list(
  list(
    name       = "adversarial",
    instrument = "bartik_iv_2020_2024",
    endogenous = "delta_log1p_competition_lawsuits_2024_2020"
  )
)

# Candidate pool — who chooses to run
CANDIDATE_POOL_OUTCOMES <- c(
  "delta_log1p_total_candidates_2024_2020",
  "delta_female_share_2024_2020",
  "delta_nonwhite_share_2024_2020",
  "delta_new_candidate_share_2024_2020",
  "delta_incumbent_candidate_share_2024_2020",
  "delta_effective_party_count_candidates_2024_2020",
  "delta_candidate_hhi_party_2024_2020"
)

# Elected composition — who wins seats
ELECTED_COMP_OUTCOMES <- c(
  "delta_elected_female_share_2024_2020",
  "delta_elected_nonwhite_share_2024_2020",
  "delta_elected_higher_ed_share_2024_2020",
  "delta_elected_mean_age_2024_2020",
  "delta_incumbent_reelected_share_2024_2020"
)

# Party-level competition
PARTY_COMP_OUTCOMES <- c(
  "delta_party_count_2024_2020",
  "delta_coalition_count_2024_2020"
)

ALL_OUTCOMES <- c(CANDIDATE_POOL_OUTCOMES, ELECTED_COMP_OUTCOMES, PARTY_COMP_OUTCOMES)

# Baseline controls: demographic + legislative electoral baseline
# Note: margin_2016 is executive margin, used here as a municipality-level
# political-environment control (competitiveness of the local political arena).
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020",        # electorate size
  "log1p_total_candidates_2020_leg",     # baseline legislative field size
  "effective_party_count_candidates_2020" # baseline party count
)

THRESHOLD_200K <- 200000L


# ============================================================
# 3. HELPER FUNCTIONS  (identical to executive script)
# ============================================================

avail <- function(controls, data) controls[controls %in% names(data)]

build_sample <- function(data, controls, outcomes, fe_col, instrument, endogenous,
                         single_zone = FALSE, aptos_filter = NULL) {
  ctrls <- avail(controls, data)
  req   <- unique(c(instrument, endogenous, "cluster_id", fe_col, ctrls))
  req   <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  if (single_zone && "n_zones_in_municipality" %in% names(samp))
    samp <- samp[samp$n_zones_in_municipality == 1L, ]
  if (!is.null(aptos_filter) && "log1p_total_valid_votes_2020" %in% names(samp)) {
    thresh <- log1p(THRESHOLD_200K)
    if (aptos_filter == "le200k") samp <- samp[samp$log1p_total_valid_votes_2020 <= thresh, ]
  }
  rownames(samp) <- NULL
  samp
}

run_first_stage <- function(samp, controls, fe_col, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(instrument, ctrls), collapse = " + ") else instrument
  fml      <- as.formula(sprintf("%s ~ %s | %s", endogenous, ctrl_rhs, fe_col))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

run_iv <- function(samp, outcome, controls, fe_col, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s", outcome, ctrl_rhs, fe_col, endogenous, instrument
  ))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

extract_fs_row <- function(fit, variant, spec, n_obs, n_cl, instrument) {
  b  <- coef(fit)[instrument]
  se <- se(fit)[instrument]
  t  <- tstat(fit)[instrument]
  p  <- pvalue(fit)[instrument]
  data.frame(variant = variant, spec = spec, coef = b, se = se, t = t, p = p,
             first_stage_F = t^2, nobs = n_obs, n_clusters = n_cl,
             stringsAsFactors = FALSE)
}

extract_iv_row <- function(fit, variant, spec, family, outcome, n_obs, n_cl, endogenous) {
  iv_name <- paste0("fit_", endogenous)
  b  <- unname(coef(fit)[iv_name])
  se <- unname(se(fit)[iv_name])
  t  <- unname(tstat(fit)[iv_name])
  p  <- unname(pvalue(fit)[iv_name])
  fstat <- tryCatch(fitstat(fit, type = "ivf")[[1]]$stat, error = function(e) NA_real_)
  data.frame(variant = variant, spec = spec, family = family, outcome = outcome,
             coef = b, se = se, t = t, p = p, ivf = fstat,
             nobs = n_obs, n_clusters = n_cl, stringsAsFactors = FALSE)
}


# ============================================================
# 4. SPECIFICATION LIST
# ============================================================

# Each entry: list(name, controls, fe_col, single_zone, aptos_filter)
specs <- list(
  list("baseline_state_fe",           BASELINE_CONTROLS,                              "SG_UF", FALSE, NULL),
  list("baseline_state_fe_sz",        BASELINE_CONTROLS,                              "SG_UF", TRUE,  NULL),
  list("robustness_full_controls",    c(BASELINE_CONTROLS,
    "female_share_2020", "nonwhite_share_2020",
    "incumbent_candidate_share_2020", "new_candidate_share_2020"
  ),                                                                                  "SG_UF", FALSE, NULL),
  list("subsample_le200k",            BASELINE_CONTROLS,                              "SG_UF", FALSE, "le200k"),
  list("robustness_broader_lawsuits", c(BASELINE_CONTROLS, "log1p_lawsuits_no_rrc_2020"), "SG_UF", FALSE, NULL)
)

cat(sprintf("Running %d variants x %d specs x %d outcomes\n\n",
    length(VARIANTS), length(specs), length(ALL_OUTCOMES)))


# ============================================================
# 5. ESTIMATION LOOP
# ============================================================

fs_rows <- list()
iv_rows <- list()

for (vr in VARIANTS) {
  var_name   <- vr$name
  instrument <- vr$instrument
  endogenous <- vr$endogenous

  cat(sprintf("\n=== Variant: %s ===\n", var_name))

  if (!(instrument %in% names(df))) {
    cat(sprintf("  SKIP: column '%s' not found in design.\n", instrument)); next
  }
  if (!(endogenous %in% names(df))) {
    cat(sprintf("  SKIP: column '%s' not found in design.\n", endogenous)); next
  }

  for (sp in specs) {
    spec_name   <- sp[[1]]
    controls    <- sp[[2]]
    fe_col      <- sp[[3]]
    single_zone <- sp[[4]]
    aptos_filter <- sp[[5]]

    samp  <- build_sample(df, controls, ALL_OUTCOMES, fe_col, instrument, endogenous,
                          single_zone = single_zone, aptos_filter = aptos_filter)
    n_obs <- nrow(samp)
    n_cl  <- length(unique(samp$cluster_id))
    cat(sprintf("  %s: N=%d, clusters=%d\n", spec_name, n_obs, n_cl))

    # First stage
    tryCatch({
      fs_fit <- run_first_stage(samp, controls, fe_col, instrument, endogenous)
      fs_rows[[length(fs_rows) + 1]] <- extract_fs_row(
        fs_fit, var_name, spec_name, n_obs, n_cl, instrument)
      cat(sprintf("    First stage F = %.1f\n",
          coef(fs_fit)[instrument]^2 / se(fs_fit)[instrument]^2))
    }, error = function(e) message("  FS error [", spec_name, "]: ", conditionMessage(e)))

    # 2SLS for each outcome
    for (y in ALL_OUTCOMES) {
      if (!(y %in% names(samp))) next
      if (sum(!is.na(samp[[y]])) < 20L) next
      family <- if (y %in% CANDIDATE_POOL_OUTCOMES) "candidate_pool"
                else if (y %in% ELECTED_COMP_OUTCOMES) "elected_comp"
                else "party_comp"
      tryCatch({
        iv_fit <- run_iv(samp, y, controls, fe_col, instrument, endogenous)
        iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
          iv_fit, var_name, spec_name, family, y, n_obs, n_cl, endogenous)
      }, error = function(e)
        message("  IV error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
    }
  }
}

first_stage <- do.call(rbind, fs_rows)
iv_results  <- do.call(rbind, iv_rows)


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
  if (f <= 2)               return(13.99)
  approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y
}

fs_F_map <- stats::setNames(
  first_stage$first_stage_F,
  paste(first_stage$variant, first_stage$spec, sep = ":::")
)
iv_results$first_stage_F_lookup <- fs_F_map[
  paste(iv_results$variant, iv_results$spec, sep = ":::")
]
iv_results$tF_cv          <- sapply(iv_results$first_stage_F_lookup, get_tF_cv)
iv_results$ci95_low_tF    <- iv_results$coef - iv_results$tF_cv * iv_results$se
iv_results$ci95_high_tF   <- iv_results$coef + iv_results$tF_cv * iv_results$se
iv_results$reject_tF_5pct <- abs(iv_results$t) > iv_results$tF_cv

first_stage$tF_cv <- sapply(first_stage$first_stage_F, get_tF_cv)


# ============================================================
# 7. SAVE OUTPUTS
# ============================================================

fwrite(first_stage, file.path(ESTIMATES_DIR, "legislative_first_stage_fixest.csv"))
fwrite(iv_results,  file.path(ESTIMATES_DIR, "legislative_iv_fixest.csv"))

# Markdown report
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
fs_fmt[c("coef","se","p")] <- lapply(fs_fmt[c("coef","se","p")], fmt4)
fs_fmt[c("t","first_stage_F")] <- lapply(fs_fmt[c("t","first_stage_F")], fmt2)

iv_fmt <- iv_results
iv_fmt[c("coef","se","p")] <- lapply(iv_fmt[c("coef","se","p")], fmt4)
iv_fmt[c("t","ivf")]        <- lapply(iv_fmt[c("t","ivf")], fmt2)

report <- c(
  "# Legislative Analysis — fixest 2SLS (R)",
  "",
  "Adversarial Bartik shift-share IV. Same instrument as executive analysis.",
  "Formula: `y ~ controls | state FE | Δlog(lawsuits) ~ Bartik_IV`.",
  "SE clustered by principal electoral zone.",
  "",
  "## First Stage",
  "",
  df_to_md(fs_fmt),
  "",
  "## IV Results",
  "",
  df_to_md(iv_fmt)
)
writeLines(report, file.path(ESTIMATES_DIR, "legislative_fixest.md"))

cat("\nResults saved:\n")
cat("  ", file.path(ESTIMATES_DIR, "legislative_first_stage_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "legislative_iv_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "legislative_fixest.md"), "\n")
