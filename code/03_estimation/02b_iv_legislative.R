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
  "delta_higher_education_share_2024_2020",
  "delta_mean_age_2024_2020",
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
# V2 control philosophy (2026-06-28), mirroring the executive design: common
# pre-determined controls only. The 2020 *levels* of legislative field size and
# party count are dropped from baseline because two outcomes
# (delta_log1p_total_candidates, delta_effective_party_count_candidates) are
# 2024-2020 changes of those same quantities -- conditioning on their 2020 base
# level is Lord's-paradox bias. The legislative design has NO 2016 candidate-
# composition levels, so a per-outcome 2016 lag (executive V3) is infeasible here.
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020"         # electorate size (not a comp. outcome)
)

# OLD ANCOVA stance (V1): the two 2020 legislative levels back in, for a labelled
# stance-check spec so the bias is visible in the results file.
ANCOVA_2020_LEVELS <- c("log1p_total_candidates_2020_leg",
                        "effective_party_count_candidates_2020")



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
  list("baseline",          BASELINE_CONTROLS,                                       "SG_UF", FALSE, NULL),
  list("single_zone",       BASELINE_CONTROLS,                                       "SG_UF", TRUE,  NULL),
  list("extended_controls", c(BASELINE_CONTROLS,
    "female_share_2020", "nonwhite_share_2020",
    "incumbent_candidate_share_2020", "new_candidate_share_2020"
  ),                                                                                 "SG_UF", FALSE, NULL),
  list("broader_treatment", c(BASELINE_CONTROLS, "log1p_lawsuits_no_rrc_2020"),      "SG_UF", FALSE, NULL),
  list("ancova_2020lvl",    c(BASELINE_CONTROLS, ANCOVA_2020_LEVELS),                "SG_UF", FALSE, NULL)
)

cat(sprintf("Running %d variants x %d specs x %d outcomes\n\n",
    length(VARIANTS), length(specs), length(ALL_OUTCOMES)))


# ============================================================
# 5. ESTIMATION LOOP
# ============================================================

fs_rows <- list()
iv_rows <- list()

# Model objects for etable() tex fragments (Section 8)
# Keys are outcome names; only baseline spec stored
tex_cand_pool_fits <- list()   # candidate pool outcomes
tex_elected_fits   <- list()   # elected composition outcomes
tex_party_fits     <- list()   # party competition outcomes
tex_leg_fs_fit     <- NULL     # first stage (single model)

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
      if (spec_name == "baseline") tex_leg_fs_fit <<- fs_fit
    }, error = function(e) message("  FS error [", spec_name, "]: ", conditionMessage(e)))

    # 2SLS for each outcome
    for (y in ALL_OUTCOMES) {
      if (!(y %in% names(samp))) next
      if (sum(!is.na(samp[[y]])) < 20L) next
      family <- if (y %in% CANDIDATE_POOL_OUTCOMES) "candidate_pool"
                else if (y %in% ELECTED_COMP_OUTCOMES) "elected_comp"
                else "party_comp"
      iv_fit_y <- NULL
      tryCatch({
        iv_fit_y <- run_iv(samp, y, controls, fe_col, instrument, endogenous)
        iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
          iv_fit_y, var_name, spec_name, family, y, n_obs, n_cl, endogenous)
      }, error = function(e)
        message("  IV error [", spec_name, ", ", y, "]: ", conditionMessage(e)))
      # Store model objects for tex generation outside tryCatch to avoid scoping issues
      if (!is.null(iv_fit_y) && spec_name == "baseline") {
        if (y %in% CANDIDATE_POOL_OUTCOMES)      tex_cand_pool_fits[[y]] <- iv_fit_y
        else if (y %in% ELECTED_COMP_OUTCOMES)   tex_elected_fits[[y]]   <- iv_fit_y
        else                                      tex_party_fits[[y]]     <- iv_fit_y
      }
    }
  }
}

first_stage <- do.call(rbind, fs_rows)
iv_results  <- do.call(rbind, iv_rows)


# ============================================================
# 6. tF WEAK-INSTRUMENT CORRECTION (Lee et al. 2022, AER)
# ============================================================
# Authoritative table + get_tF_cv() from the shared util (cv reaches 1.96 only
# at F ~ 104.7, not F = 23.1). See code/utils/tf_critical_values.R.
source(file.path(PROJECT_ROOT, "code", "utils", "tf_critical_values.R"))

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

cat("\nResults saved:\n")
cat("  ", file.path(ESTIMATES_DIR, "legislative_first_stage_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "legislative_iv_fixest.csv"), "\n")


# ============================================================
# 8. LaTeX TABLE FRAGMENTS via etable()  (output/tables/tex/)
# ============================================================

TEX_DIR <- file.path(PROJECT_ROOT, "output", "tables", "tex")
dir.create(TEX_DIR, recursive = TRUE, showWarnings = FALSE)

LEG_OUTCOME_LABELS <- c(
  delta_log1p_total_candidates_2024_2020          = "$\\Delta$ Log total candidates",
  delta_female_share_2024_2020                    = "$\\Delta$ Female share",
  delta_nonwhite_share_2024_2020                  = "$\\Delta$ Nonwhite share",
  delta_higher_education_share_2024_2020          = "$\\Delta$ Higher-ed.~share",
  delta_mean_age_2024_2020                        = "$\\Delta$ Mean age",
  delta_new_candidate_share_2024_2020             = "$\\Delta$ New candidate share",
  delta_incumbent_candidate_share_2024_2020       = "$\\Delta$ Incumbent share",
  delta_effective_party_count_candidates_2024_2020 = "$\\Delta$ Eff.~party count",
  delta_candidate_hhi_party_2024_2020             = "$\\Delta$ Cand.~HHI (party)",
  delta_elected_female_share_2024_2020            = "$\\Delta$ Elected female",
  delta_elected_nonwhite_share_2024_2020          = "$\\Delta$ Elected nonwhite",
  delta_elected_higher_ed_share_2024_2020         = "$\\Delta$ Elected higher ed",
  delta_elected_mean_age_2024_2020                = "$\\Delta$ Elected mean age",
  delta_incumbent_reelected_share_2024_2020       = "$\\Delta$ Incumbent reelected",
  delta_party_count_2024_2020                     = "$\\Delta$ Party count",
  delta_coalition_count_2024_2020                 = "$\\Delta$ Coalition count"
)

ETABLE_DICT_LEG <- c(
  "fit_delta_log1p_competition_lawsuits_2024_2020" = "Judicialization",
  "delta_log1p_competition_lawsuits_2024_2020"     = "Judicialization",
  "bartik_iv_2020_2024"                            = "Predicted judicialization",
  "SG_UF"                                          = "State (UF)",
  "cluster_id"                                     = "state"
)

# Standard convention: *** 1%, ** 5%, * 10% (matches 02_iv_main.R house style).
ETABLE_SIGNIF <- c("***" = .01, "**" = .05, "*" = .10)

write_etable_frag <- function(out, path) {
  if (length(out) == 1L) out <- strsplit(out, "\n", fixed = TRUE)[[1]]
  i1 <- which(grepl("\\begin{tabular}", out, fixed = TRUE))
  i2 <- which(grepl("\\end{tabular}",   out, fixed = TRUE))
  frag <- if (length(i1) && length(i2)) out[i1[1L]:i2[length(i2)]] else out
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  writeLines(c(
    "% Auto-generated by code/03_estimation/02b_iv_legislative.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    frag
  ), con = path)
  cat("  Wrote:", path, "\n")
}

etab_leg <- list(
  tex          = TRUE,
  # Merge the readable outcome labels into the dict so etable() translates the
  # dependent-variable header row (not just the coefficient name) -- otherwise
  # raw variable names like delta_log1p_total_candidates_2024_2020 leak.
  dict         = c(ETABLE_DICT_LEG, LEG_OUTCOME_LABELS),
  signif.code  = ETABLE_SIGNIF,
  digits       = 3,
  digits.stats = 1,
  fixef_sizes  = FALSE,
  notes        = "SE clustered by state (UF). Baseline spec (state FE, 5 controls).",
  style.tex    = style.tex(arraystretch = 1.2)
)

label_mods <- function(store, keys, labels) {
  mods <- Filter(Negate(is.null), store[keys])
  setNames(mods, labels[names(mods)])
}

iv_keep_raw <- paste0("^fit_", endogenous, "$")

# ---- Hand-built "highlighted-band" table (matches 02_iv_main.R house style) ----
# Bold outcome headers, the single Judicialization coefficient row (with the gray
# SE beneath) shaded in a pale-blue horizontal band via \rowcolor{mylight}, then
# N + dependent-variable-mean rows. The dep-var mean is recovered from the fit
# (fitted + residuals) since the legislative fits do not carry a precomputed mean
# attribute.
hb_star <- function(p) {
  if (is.null(p) || is.na(p)) return("")
  if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
}
hb_row <- function(label, cells)
  paste0(label, " & ", paste(cells, collapse = " & "), " \\\\")

leg_iv_table <- function(mods, path) {
  K  <- length(mods)
  iv <- paste0("fit_", endogenous)
  coef_cells <- vapply(mods, function(m)
    sprintf("%.3f%s", unname(coef(m)[iv]), hb_star(unname(pvalue(m)[iv]))), "")
  se_cells <- vapply(mods, function(m)
    sprintf("\\textcolor{mygray}{(%.3f)}", unname(se(m)[iv])), "")
  n_cells <- vapply(mods, function(m)
    formatC(nobs(m), format = "d", big.mark = ","), "")
  mean_cells <- vapply(mods, function(m)
    sprintf("%.3f", mean(fitted(m) + resid(m), na.rm = TRUE)), "")
  lines <- c(
    sprintf("\\begin{tabular}{l*{%d}{c}}", K),
    "\\toprule\\toprule",
    hb_row("Dep.\\ var.:", sprintf("\\textbf{%s}", names(mods))),
    "\\midrule",
    "\\rowcolor{mylight}",
    hb_row("\\textbf{Judicialization}", coef_cells),
    "\\rowcolor{mylight}",
    hb_row("", se_cells),
    "\\midrule",
    hb_row("$N$", n_cells),
    hb_row("Mean of dep.\\ var.", mean_cells),
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  writeLines(c(
    "% Auto-generated by code/03_estimation/02b_iv_legislative.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    lines
  ), con = path)
  cat("  Wrote:", path, "\n")
}

# ---- 8a. Candidate Pool (cols = outcomes) ----
{
  mods <- label_mods(tex_cand_pool_fits, CANDIDATE_POOL_OUTCOMES, LEG_OUTCOME_LABELS)
  leg_iv_table(mods, file.path(TEX_DIR, "legislative_iv_candidate_pool.tex"))
}

# ---- 8b. Elected Composition (cols = outcomes) ----
{
  mods <- label_mods(tex_elected_fits, ELECTED_COMP_OUTCOMES, LEG_OUTCOME_LABELS)
  leg_iv_table(mods, file.path(TEX_DIR, "legislative_iv_elected_comp.tex"))
}

# ---- 8c. Party Competition (cols = outcomes) ----
{
  mods <- label_mods(tex_party_fits, PARTY_COMP_OUTCOMES, LEG_OUTCOME_LABELS)
  leg_iv_table(mods, file.path(TEX_DIR, "legislative_iv_party_comp.tex"))
}

cat("\nLaTeX fragments written to", TEX_DIR, "\n")
