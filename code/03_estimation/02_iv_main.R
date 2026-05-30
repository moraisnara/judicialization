# IV estimation for electoral judicialization — fixest (R)
# Follows Ash, Morelli & Vannoni (2025, JPE) Stata structure.
# Loads pre-assembled design matrix from Python pipeline, runs 2SLS via feols().
#
# Single instrument variant:
#   adversarial  : bartik_iv_2020_2024         / delta_log1p_competition_lawsuits_2024_2020
#   (administrative and procedural classes/subjects excluded at build stage)
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
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
rename_map <- c(
  state = "SG_UF",
  municipality_id_tse = "SG_UE",
  municipality_name = "NM_UE",
  election_year = "ANO_ELEICAO",
  electoral_zone = "zona_eleitoral",
  main_subject_code = "CD_ASSUNTO_PRINCIPAL",
  main_subject_name = "DS_ASSUNTO_PRINCIPAL"
)
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]
if ("code_micro" %in% names(df)) {
  df$code_micro <- as.character(df$code_micro)
}
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================


# ---- Instrument variant ----
# bartik_iv_2020_2024 is built with the adversarial filter applied at the
# build stage (DROP_CLASSES + DROP_SUBJECTS in 02_bartik_inputs.py).
# It is the single coherent instrument for this pipeline.
VARIANTS <- list(
  list(
    name       = "adversarial",
    instrument = "bartik_iv_2020_2024",
    endogenous = "delta_log1p_competition_lawsuits_2024_2020"
  )
)

PRIMARY_OUTCOMES <- c(
  "delta_runnerup_vote_share_2024_2020",
  "delta_margin_top1_top2_2024_2020"
)
SECONDARY_OUTCOMES <- c(
  "delta_winner_vote_share_2024_2020",
  "delta_winner_majority_2024_2020",
  "delta_others_vote_share_2024_2020",
  "delta_log1p_n_candidates_with_votes_2024_2020"
)
COMPOSITION_OUTCOMES <- c(
  "delta_female_vote_share_2024_2020",
  "delta_nonwhite_vote_share_2024_2020",
  "delta_new_candidate_vote_share_2024_2020",
  "delta_incumbent_candidate_vote_share_2024_2020",
  "delta_winner_is_female_2024_2020",
  "delta_winner_is_new_vs_2020_2024_2020"
)
# Entry typology outcomes: change in share of each entrant type in the candidate pool
ENTRY_OUTCOMES <- c(
  "delta_share_first_time_candidates_2024_2020",
  "delta_share_serial_challenger_2024_2020",
  "delta_share_cross_cycle_returner_2024_2020"
)
VOTER_BEHAVIOR_OUTCOMES <- c(
  "delta_turnout_rate_2024_2020",
  "delta_null_rate_2024_2020",
  "delta_blank_rate_2024_2020",
  "delta_valid_vote_rate_2024_2020"
)
ALL_OUTCOMES <- c(PRIMARY_OUTCOMES, SECONDARY_OUTCOMES,
                  COMPOSITION_OUTCOMES, VOTER_BEHAVIOR_OUTCOMES, ENTRY_OUTCOMES)

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



# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

avail <- function(controls, data) controls[controls %in% names(data)]

build_sample <- function(data, controls, outcomes, fe_col, instrument, endogenous,
                         single_zone = FALSE, aptos_filter = NULL) {
  ctrls <- avail(controls, data)
  outs  <- intersect(outcomes, names(data))
  req   <- unique(c(instrument, endogenous, "cluster_id", fe_col, ctrls, outs))
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

# First-stage OLS: endogenous ~ instrument + controls | FE
run_first_stage <- function(samp, controls, fe_col, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(c(instrument, ctrls), collapse = " + ") else instrument
  fml      <- as.formula(sprintf("%s ~ %s | %s", endogenous, ctrl_rhs, fe_col))
  feols(fml, data = samp,
        cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

# 2SLS: outcome ~ controls | FE | endogenous ~ instrument
run_iv <- function(samp, outcome, controls, fe_col, instrument, endogenous) {
  ctrls    <- avail(controls, samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s", outcome, ctrl_rhs, fe_col, endogenous, instrument
  ))
  feols(fml, data = samp,
        cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

extract_fs_row <- function(fit, variant, spec, n_obs, n_cl, instrument) {
  b  <- coef(fit)[instrument]
  se <- se(fit)[instrument]
  t  <- tstat(fit)[instrument]
  p  <- pvalue(fit)[instrument]
  data.frame(
    variant       = variant,
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

extract_iv_row <- function(fit, variant, spec, family, outcome, n_obs, n_cl, endogenous,
                           estimator = "2sls") {
  # fixest prefixes the endogenous variable with "fit_" in IV output
  iv_name <- paste0("fit_", endogenous)
  b  <- unname(coef(fit)[iv_name])
  se <- unname(se(fit)[iv_name])
  t  <- unname(tstat(fit)[iv_name])
  p  <- unname(pvalue(fit)[iv_name])
  fstat <- tryCatch(
    fitstat(fit, type = "ivf")[[1]]$stat,
    error = function(e) NA_real_
  )
  data.frame(
    variant    = variant,
    spec       = spec,
    estimator  = estimator,
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
  list("baseline",          BASELINE_CONTROLS,                                       "SG_UF", FALSE, NULL),
  list("single_zone",       BASELINE_CONTROLS,                                       "SG_UF", TRUE,  NULL),
  list("extended_controls", ROBUSTNESS_CONTROLS,                                     "SG_UF", FALSE, NULL),
  list("open_seat",         BASELINE_CONTROLS,                                       "SG_UF", FALSE, "open_seat"),
  list("contested_seat",    BASELINE_CONTROLS,                                       "SG_UF", FALSE, "no_open_seat"),
  list("broader_treatment", c(BASELINE_CONTROLS, "log1p_lawsuits_no_rrc_2020"),      "SG_UF", FALSE, NULL)
)

cat(sprintf("Running %d variants x %d specifications x %d outcomes\n\n",
    length(VARIANTS), length(specs), length(ALL_OUTCOMES)))


# ============================================================
# 5. ESTIMATION LOOP (outer: variants; inner: specs x outcomes)
# ============================================================

fs_rows   <- list()
iv_rows   <- list()
liml_rows <- list()

# Model objects stored for etable() LaTeX generation (Section 9)
FS_TEX_SPECS       <- c("baseline", "single_zone", "extended_controls", "broader_treatment")
ROBUSTNESS_TEX_SPECS <- c("baseline", "single_zone", "extended_controls", "broader_treatment")
BLANK_SUBGROUP_SPECS <- c("baseline", "open_seat", "contested_seat")

tex_fs_fits       <- list()   # [spec_name] = feols (first stage)
tex_base_iv_fits  <- list()   # [outcome]   = feols (baseline IV)
tex_robust_iv_fits <- list()  # [spec_name] = feols (winner majority, robustness specs)
tex_blank_sub_fits <- list()  # [spec_name] = feols (blank rate, subgroup specs)

for (vr in VARIANTS) {
  var_name   <- vr$name
  instrument <- vr$instrument
  endogenous <- vr$endogenous

  cat(sprintf("\n=== Variant: %s ===\n", var_name))
  cat(sprintf("    Instrument : %s\n", instrument))
  cat(sprintf("    Endogenous : %s\n\n", endogenous))

  if (!(instrument %in% names(df))) {
    cat(sprintf("  SKIP: column '%s' not found in design.\n", instrument))
    next
  }
  if (!(endogenous %in% names(df))) {
    cat(sprintf("  SKIP: column '%s' not found in design.\n", endogenous))
    next
  }

  for (sp in specs) {
    spec_name    <- sp[[1]]
    controls     <- sp[[2]]
    fe_col       <- sp[[3]]
    single_zone  <- sp[[4]]
    aptos_filter <- sp[[5]]

    samp  <- build_sample(df, controls, ALL_OUTCOMES, fe_col, instrument, endogenous,
                          single_zone, aptos_filter)
    n_obs <- nrow(samp)
    n_cl  <- length(unique(samp$cluster_id))
    cat(sprintf("  %s: N=%d, clusters=%d\n", spec_name, n_obs, n_cl))

    # First stage
    fs_fit <- NULL
    tryCatch({
      fs_fit <- run_first_stage(samp, controls, fe_col, instrument, endogenous)
      fs_rows[[length(fs_rows) + 1]] <- extract_fs_row(
        fs_fit, var_name, spec_name, n_obs, n_cl, instrument
      )
      if (spec_name %in% FS_TEX_SPECS)
        tex_fs_fits[[spec_name]] <- fs_fit
    }, error = function(e) message("  FS error [", spec_name, "]: ", conditionMessage(e)))

    # 2SLS for each outcome
    for (y in ALL_OUTCOMES) {
      if (!(y %in% names(samp))) next
      if (sum(!is.na(samp[[y]])) < 20L) next
      family <- if (y %in% PRIMARY_OUTCOMES)          "primary"
                else if (y %in% SECONDARY_OUTCOMES)  "secondary"
                else if (y %in% COMPOSITION_OUTCOMES) "composition"
                else if (y %in% ENTRY_OUTCOMES)       "entry"
                else                                  "voter_behavior"
      tryCatch({
        iv_fit <- run_iv(samp, y, controls, fe_col, instrument, endogenous)
        iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
          iv_fit, var_name, spec_name, family, y, n_obs, n_cl, endogenous
        )
        # Store model objects for tex generation
        if (spec_name == "baseline")
          tex_base_iv_fits[[y]] <- iv_fit
        if (y == "delta_winner_majority_2024_2020" && spec_name %in% ROBUSTNESS_TEX_SPECS)
          tex_robust_iv_fits[[spec_name]] <- iv_fit
        if (y == "delta_blank_rate_2024_2020" && spec_name %in% BLANK_SUBGROUP_SPECS)
          tex_blank_sub_fits[[spec_name]] <- iv_fit
      }, error = function(e)
        message("  IV error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
    }

    # LIML for baseline spec (K=1 instrument — no eigenvalue issue)
    if (spec_name == "baseline") {
      for (y in ALL_OUTCOMES) {
        if (!(y %in% names(samp))) next
        if (sum(!is.na(samp[[y]])) < 20L) next
        family <- if (y %in% PRIMARY_OUTCOMES)          "primary"
                  else if (y %in% SECONDARY_OUTCOMES)  "secondary"
                  else if (y %in% COMPOSITION_OUTCOMES) "composition"
                  else if (y %in% ENTRY_OUTCOMES)       "entry"
                  else                                  "voter_behavior"
        tryCatch({
          ctrls_l    <- avail(controls, samp)
          ctrl_rhs_l <- if (length(ctrls_l) > 0) paste(ctrls_l, collapse = " + ") else "1"
          fml_l      <- as.formula(sprintf(
            "%s ~ %s | %s | %s ~ %s", y, ctrl_rhs_l, fe_col, endogenous, instrument
          ))
          liml_fit <- feols(fml_l, data = samp, cluster = ~cluster_id,
                            estimator = "liml", warn = FALSE, notes = FALSE)
          liml_rows[[length(liml_rows) + 1]] <- extract_iv_row(
            liml_fit, var_name, spec_name, family, y, n_obs, n_cl, endogenous,
            estimator = "liml"
          )
        }, error = function(e)
          message("  LIML error [", y, "]: ", conditionMessage(e)))
      }
    }
  }
}

first_stage <- do.call(rbind, fs_rows)
iv_results  <- do.call(rbind, iv_rows)


# ============================================================
# 6. SAVE OUTPUTS
# ============================================================

# Combined (all variants)
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

# Build and write markdown report
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
  "## Instrument",
  "- **adversarial** : bartik_iv_2020_2024 / delta_log1p_competition_lawsuits_2024_2020",
  "  (adversarial class/subject filter applied at build stage in 02_bartik_inputs.py)",
  "",
  "## Specifications",
  "1. **baseline** — 7 baseline controls + state FE",
  "2. **single_zone** — baseline, single-zone municipalities only",
  "3. **extended_controls** — 14 controls + state FE",
  "4. **open_seat** — baseline, open-seat municipalities (2020 winner term-limited)",
  "5. **contested_seat** — baseline, contested-seat municipalities",
  "6. **broader_treatment** — baseline + log1p_lawsuits_no_rrc_2020 as additional control",
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


# ============================================================
# 7. tF WEAK-INSTRUMENT CORRECTION (Lee et al. 2022, RESTUD)
# ============================================================
# For first-stage F < 23.1, the standard normal critical value (1.96) is
# anti-conservative. The tF procedure uses a larger critical value that
# achieves correct 5% size when F = F_hat.
# Reference: Lee, McCrary, Moreira & Porter (2022) "Valid t-ratio Inference
# for IV", RESTUD (forthcoming). Table 1, alpha=0.05.

# Lookup table from Lee et al. (2022) Table 1 (5% two-sided, K1=1 instrument)
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

# Look up first-stage F for each variant x spec
fs_F_map <- stats::setNames(
  first_stage$first_stage_F,
  paste(first_stage$variant, first_stage$spec, sep = ":::")
)

# Add tF-corrected 95% CI to IV results
iv_results$first_stage_F_lookup <- fs_F_map[
  paste(iv_results$variant, iv_results$spec, sep = ":::")
]
iv_results$tF_cv          <- sapply(iv_results$first_stage_F_lookup, get_tF_cv)
iv_results$ci95_low_tF    <- iv_results$coef - iv_results$tF_cv * iv_results$se
iv_results$ci95_high_tF   <- iv_results$coef + iv_results$tF_cv * iv_results$se
iv_results$reject_tF_5pct <- abs(iv_results$t) > iv_results$tF_cv

# Add tF CV to first-stage too (for reference)
first_stage$tF_cv <- sapply(first_stage$first_stage_F, get_tF_cv)

cat("\ntF correction summary (baseline):\n")
tF_summary <- iv_results[iv_results$spec == "baseline", ]
for (vn in sapply(VARIANTS, `[[`, "name")) {
  f_val <- mean(first_stage$first_stage_F[first_stage$spec == "baseline" &
                                          first_stage$variant == vn], na.rm = TRUE)
  cv    <- mean(tF_summary$tF_cv[tF_summary$variant == vn], na.rm = TRUE)
  cat(sprintf("  Variant %-20s: F=%4.1f -> tF_cv=%.2f\n", vn, f_val, cv))
}

# Re-save IV results with tF columns
fwrite(iv_results,  file.path(ESTIMATES_DIR, "executive_margin_iv_fixest.csv"))
fwrite(first_stage, file.path(ESTIMATES_DIR, "executive_margin_first_stage_fixest.csv"))
cat("  (Re-saved with tF correction columns)\n")


# ============================================================
# 8. LIML vs 2SLS COMPARISON  (baseline spec only)
# ============================================================
# With K=1 instrument, LIML is numerically identical to 2SLS (no eigenvalue issue).
# A large LIML–2SLS divergence would signal many-instrument or weak-instrument bias.

if (length(liml_rows) > 0) {
  liml_results <- do.call(rbind, liml_rows)

  # Add tF correction
  liml_results$first_stage_F_lookup <- fs_F_map[
    paste(liml_results$variant, liml_results$spec, sep = ":::")
  ]
  liml_results$tF_cv          <- sapply(liml_results$first_stage_F_lookup, get_tF_cv)
  liml_results$ci95_low_tF    <- liml_results$coef - liml_results$tF_cv * liml_results$se
  liml_results$ci95_high_tF   <- liml_results$coef + liml_results$tF_cv * liml_results$se
  liml_results$reject_tF_5pct <- abs(liml_results$t) > liml_results$tF_cv

  # Side-by-side comparison for primary/secondary outcomes
  iv_base  <- iv_results[iv_results$spec == "baseline" &
                         iv_results$family %in% c("primary", "secondary"),
                         c("outcome", "coef", "se", "p", "ivf")]
  names(iv_base)[2:5] <- paste0(names(iv_base)[2:5], "_2sls")

  liml_base <- liml_results[liml_results$family %in% c("primary", "secondary"),
                             c("outcome", "coef", "se", "p")]
  names(liml_base)[2:4] <- paste0(names(liml_base)[2:4], "_liml")
  liml_base$p_liml <- liml_base$p_liml  # already renamed

  comparison <- merge(iv_base, liml_base, on = "outcome", all = TRUE)

  fwrite(comparison,    file.path(ESTIMATES_DIR, "liml_comparison.csv"))
  cat("\nLIML results saved:\n")
  cat("  ", file.path(ESTIMATES_DIR, "liml_comparison.csv"), "\n")

  max_div <- max(abs(comparison$coef_2sls - comparison$coef_liml), na.rm = TRUE)
  cat(sprintf("  Max |2SLS - LIML| across primary/secondary outcomes: %.4f\n", max_div))
} else {
  cat("\nNo LIML results collected.\n")
}


# ============================================================
# 9. LaTeX TABLE FRAGMENTS via etable()  (output/tables/tex/)
# ============================================================

TEX_DIR <- file.path(PROJECT_ROOT, "output", "tables", "tex")
dir.create(TEX_DIR, recursive = TRUE, showWarnings = FALSE)

OUTCOME_LABELS <- c(
  delta_runnerup_vote_share_2024_2020               = "$\\Delta$ Runner-up vote share",
  delta_margin_top1_top2_2024_2020                  = "$\\Delta$ Margin (W$-$RU)",
  delta_winner_vote_share_2024_2020                 = "$\\Delta$ Winner vote share",
  delta_winner_majority_2024_2020                   = "$\\Delta$ Winner majority (P50)",
  delta_log1p_n_candidates_with_votes_2024_2020     = "$\\Delta$ Log n candidates",
  delta_female_vote_share_2024_2020                 = "$\\Delta$ Female vote share",
  delta_nonwhite_vote_share_2024_2020               = "$\\Delta$ Nonwhite vote share",
  delta_new_candidate_vote_share_2024_2020          = "$\\Delta$ New-cand.\\ vote share",
  delta_incumbent_candidate_vote_share_2024_2020    = "$\\Delta$ Incumbent vote share",
  delta_winner_is_female_2024_2020                  = "$\\Delta$ Winner is female",
  delta_winner_is_new_vs_2020_2024_2020             = "$\\Delta$ Winner is new entrant",
  delta_turnout_rate_2024_2020                      = "$\\Delta$ Turnout rate",
  delta_null_rate_2024_2020                         = "$\\Delta$ Null vote rate",
  delta_blank_rate_2024_2020                        = "$\\Delta$ Blank vote rate",
  delta_valid_vote_rate_2024_2020                   = "$\\Delta$ Valid vote rate",
  delta_share_first_time_candidates_2024_2020       = "$\\Delta$ New entrant share",
  delta_share_serial_challenger_2024_2020           = "$\\Delta$ Serial challenger",
  delta_share_cross_cycle_returner_2024_2020        = "$\\Delta$ Cross-cycle returner"
)

SPEC_LABELS <- c(
  baseline          = "Baseline",
  single_zone       = "Single-zone municipalities",
  extended_controls = "Extended controls",
  open_seat         = "Open seat",
  contested_seat    = "Contested seat",
  broader_treatment = "Broader treatment measure"
)

# etable() dict: original fixest coef name -> display label
ETABLE_DICT <- c(
  "fit_delta_log1p_competition_lawsuits_2024_2020" = "$\\Delta$ Log(lawsuits)",
  "bartik_iv_2020_2024"                            = "Bartik IV"
)

ETABLE_SIGNIF <- c("**" = .01, "*" = .05, "\\dagger" = .10)

# Write just the \begin{tabular}...\end{tabular} block from etable(tex=TRUE) output
write_etable_frag <- function(out, path) {
  if (length(out) == 1L) out <- strsplit(out, "\n", fixed = TRUE)[[1]]
  i1 <- which(grepl("\\begin{tabular}", out, fixed = TRUE))
  i2 <- which(grepl("\\end{tabular}",   out, fixed = TRUE))
  frag <- if (length(i1) && length(i2)) out[i1[1L]:i2[length(i2)]] else out
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  writeLines(c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    frag
  ), con = path)
  cat("  Wrote:", path, "\n")
}

# Shared etable() options (overridable per-table)
etab_base <- list(
  tex          = TRUE,
  dict         = ETABLE_DICT,
  signif.code  = ETABLE_SIGNIF,
  digits       = 3,
  digits.stats = 1,
  notes        = "SE clustered by electoral zone.",
  style.tex    = style.tex(arraystretch = 1.2)
)

# Convenience: filter NULLs and apply spec/outcome labels to a model sub-list
label_mods <- function(store, keys, labels) {
  mods <- Filter(Negate(is.null), store[keys])
  setNames(mods, labels[names(mods)])
}

# ---- 9a. First Stage (cols = specs) ----
{
  # Use original spec keys to compute extra rows before renaming
  valid_fs <- intersect(FS_TEX_SPECS, names(Filter(Negate(is.null), tex_fs_fits)))
  fs_F_row  <- unname(sapply(valid_fs, function(s)
    sprintf("%.1f", tstat(tex_fs_fits[[s]])[instrument]^2)))
  fs_tF_row <- unname(sapply(valid_fs, function(s)
    sprintf("%.2f", get_tF_cv(tstat(tex_fs_fits[[s]])[instrument]^2))))
  fs_N_row  <- unname(sapply(valid_fs, function(s)
    formatC(nobs(tex_fs_fits[[s]]), format = "d", big.mark = ",")))
  mods <- setNames(tex_fs_fits[valid_fs], SPEC_LABELS[valid_fs])
  out <- do.call(etable, c(list(
    mods,
    keep_raw   = paste0("^", instrument, "$"),
    fitstat    = ~ n + ivf,
    extralines = list(
      "First-stage $F$"          = fs_F_row,
      "tF$_{\\text{cv}}$ (5\\%)" = fs_tF_row,
      "$N$"                      = fs_N_row
    )
  ), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "first_stage.tex"))
}

# IV coef name as stored by fixest (fit_<endogenous>)
iv_keep_raw <- paste0("^fit_", endogenous, "$")

# ---- 9b. Electoral Competition (cols = outcomes, baseline spec) ----
{
  outs <- c(
    "delta_runnerup_vote_share_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_winner_majority_2024_2020",
    "delta_log1p_n_candidates_with_votes_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "executive_iv_competition.tex"))
}

# ---- 9c. Voter Behavior (cols = outcomes) ----
{
  outs <- c(
    "delta_turnout_rate_2024_2020",
    "delta_null_rate_2024_2020",
    "delta_blank_rate_2024_2020",
    "delta_valid_vote_rate_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "executive_iv_voter_behavior.tex"))
}

# ---- 9d. Composition (cols = outcomes) ----
{
  outs <- c(
    "delta_female_vote_share_2024_2020",
    "delta_nonwhite_vote_share_2024_2020",
    "delta_new_candidate_vote_share_2024_2020",
    "delta_incumbent_candidate_vote_share_2024_2020",
    "delta_winner_is_female_2024_2020",
    "delta_winner_is_new_vs_2020_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "executive_iv_composition.tex"))
}

# ---- 9e. Entrant Typology (cols = outcomes) ----
{
  outs <- c(
    "delta_share_first_time_candidates_2024_2020",
    "delta_share_serial_challenger_2024_2020",
    "delta_share_cross_cycle_returner_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "entrant_typology.tex"))
}

# ---- 9f. Blank Rate — open-seat heterogeneity (cols = subgroup specs) ----
{
  sub_labels <- c(
    baseline      = "All municipalities",
    open_seat     = "Open seat",
    contested_seat = "Contested seat"
  )
  mods <- label_mods(tex_blank_sub_fits, BLANK_SUBGROUP_SPECS, sub_labels)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "open_seat_blank_rate.tex"))
}

# ---- 9g. Robustness — Winner Majority (cols = specs) ----
{
  mods <- label_mods(tex_robust_iv_fits, ROBUSTNESS_TEX_SPECS, SPEC_LABELS)
  out  <- do.call(etable, c(list(mods, keep_raw = iv_keep_raw, fitstat = ~ ivf + n), etab_base))
  write_etable_frag(out, file.path(TEX_DIR, "robustness_winner_majority.tex"))
}

cat("\nLaTeX fragments written to", TEX_DIR, "\n")
