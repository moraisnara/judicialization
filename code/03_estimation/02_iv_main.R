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
# log1p candidate-count levels for the ANCOVA form (the outcome is log1p-scaled).
for (yr in c("2016", "2024")) {
  src <- paste0("n_candidates_with_votes_", yr)
  if (src %in% names(df))
    df[[paste0("log1p_n_candidates_with_votes_", yr)]] <- log1p(df[[src]])
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
  "delta_female_share_2024_2020",
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
# Voter behaviour, split BY OFFICE SOUGHT. Turnout is office-invariant (a voter
# shows up once for both ballots) so it is single; ballot composition (blank, null,
# valid) is reported separately for the mayoral (prefeito, base names) and council
# (vereador, _vereador suffix) ballots.
VOTER_BEHAVIOR_OUTCOMES <- c(
  "delta_turnout_rate_2024_2020",
  "delta_null_rate_2024_2020",
  "delta_blank_rate_2024_2020",
  "delta_valid_vote_rate_2024_2020",
  "delta_null_rate_vereador_2024_2020",
  "delta_blank_rate_vereador_2024_2020",
  "delta_valid_vote_rate_vereador_2024_2020"
)
# Elastic turnout margins (disaggregated): under compulsory voting the aggregate
# turnout null is mechanical; these are where a voter-engagement effect would surface.
VOTER_DISAGG_OUTCOMES <- c(
  "delta_facultative_turnout_2024_2020",
  "delta_compulsory_turnout_2024_2020",
  "delta_low_ed_turnout_2024_2020",
  "delta_high_ed_turnout_2024_2020",
  "delta_analfabeto_turnout_2024_2020",
  "delta_education_turnout_gap_2024_2020",
  "delta_sex_turnout_gap_2024_2020"
)
ALL_OUTCOMES <- c(PRIMARY_OUTCOMES, SECONDARY_OUTCOMES,
                  COMPOSITION_OUTCOMES, VOTER_BEHAVIOR_OUTCOMES,
                  VOTER_DISAGG_OUTCOMES, ENTRY_OUTCOMES)

# ---- Control philosophy (V3, adopted 2026-06-28) ----
# BASELINE_CONTROLS are pre-determined and COMMON to every outcome:
#   * 2010 Census structure (population, urbanisation, income p.c., schooling)
#   * electorate scale in the base year (log valid-vote volume, 2020)
#   * general pre-window competitiveness (2016 victory margin)
# They deliberately EXCLUDE the 2020 *levels* of competition outcomes
# (margin_top1_top2_2020, log1p_total_candidates_2020). Because every headline
# outcome is a 2024-2020 CHANGE, conditioning on the 2020 base level of the same
# quantity is Lord's-paradox territory (the base level is mechanically inside the
# change). The principled pre-window anchor is instead each outcome's OWN 2016
# level, added per-outcome via LAG16_MAP below (V3). Where no clean 2016 analog
# exists (voter behaviour, extensive candidate shares) the outcome falls back to
# the common set only (V2). See code/04_analysis/13_lagged_dv_diagnostic.R.
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020",
  "margin_2016"
)

# The OLD ANCOVA stance (V1): adds the two 2020 competition levels back, no 2016
# own-lag. Kept as a labelled robustness spec so the headline's stance-dependence
# is visible in the results file.
ANCOVA_2020_LEVELS <- c("margin_top1_top2_2020", "log1p_total_candidates_2020")

ROBUSTNESS_CONTROLS <- c(
  BASELINE_CONTROLS,
  "enp_2016",
  "female_vote_share_2020", "nonwhite_vote_share_2020", "higher_education_vote_share_2020",
  "log1p_party_count_2020", "log1p_coalition_count_2020",
  "turnout_rate_2020", "null_rate_2020",
  "share_first_time_candidates_2020", "share_career_politicians_2020"
)

# Per-outcome pre-window (2016) lagged dependent variable. Only outcomes with a
# clean 2016 analog appear here; all others fall back to common controls (V2).
LAG16_MAP <- c(
  delta_runnerup_vote_share_2024_2020            = "runnerup_vote_share_2016",
  delta_margin_top1_top2_2024_2020               = "margin_top1_top2_2016",
  delta_winner_vote_share_2024_2020              = "winner_vote_share_2016",
  delta_winner_majority_2024_2020                = "winner_majority_2016",
  delta_others_vote_share_2024_2020              = "others_vote_share_2016",
  delta_log1p_n_candidates_with_votes_2024_2020  = "n_candidates_with_votes_2016",
  delta_female_vote_share_2024_2020              = "female_vote_share_2016",
  delta_nonwhite_vote_share_2024_2020            = "nonwhite_vote_share_2016",
  delta_winner_is_female_2024_2020               = "winner_is_female_2016"
)

# ---- ANCOVA-2016 headline (adopted 2026-06-28) ----
# The headline estimator is ANCOVA on the 2016 pre-window baseline:
#     Y_2024 ~ D + Y_2016 + X | FE | D ~ Z
# (the 2016 level enters as a FREE lag, unlike the first-difference form which
# pins it to 1). Rationale: municipal vote margins barely persist across cycles
# (estimated lag ~0.04), so the first-difference form's implicit unit-root
# assumption is empirically rejected and over-differences the signal. ANCOVA-2016
# uses a CLEAN pre-treatment baseline (2016 levels predate the 2020 instrument
# shares), and a pre-trend falsification + non-adversarial placebo both pass
# (code/04_analysis/15_ancova_validation.R). The first-difference (FD) estimates
# are retained as a labelled robustness column (spec "fd"). See
# code/04_analysis/14_fd_vs_ancova.R for the full FD-vs-ANCOVA comparison.
#
# ANCOVA_MAP: delta-outcome key -> c(<2024 level LHS>, <2016 lag>). Only outcomes
# with BOTH a 2016 and a 2024 level appear; the rest stay first-difference.
ANCOVA_MAP <- list(
  delta_margin_top1_top2_2024_2020              = c("margin_top1_top2_2024",   "margin_top1_top2_2016"),
  delta_winner_vote_share_2024_2020             = c("winner_vote_share_2024",  "winner_vote_share_2016"),
  delta_runnerup_vote_share_2024_2020           = c("runnerup_vote_share_2024","runnerup_vote_share_2016"),
  delta_winner_majority_2024_2020               = c("winner_majority_2024",    "winner_majority_2016"),
  delta_others_vote_share_2024_2020             = c("others_vote_share_2024",  "others_vote_share_2016"),
  delta_log1p_n_candidates_with_votes_2024_2020 = c("log1p_n_candidates_with_votes_2024", "log1p_n_candidates_with_votes_2016"),
  delta_female_vote_share_2024_2020             = c("female_vote_share_2024",  "female_vote_share_2016"),
  delta_nonwhite_vote_share_2024_2020           = c("nonwhite_vote_share_2024","nonwhite_vote_share_2016"),
  delta_winner_is_female_2024_2020              = c("winner_is_female_2024",   "winner_is_female_2016"),
  delta_blank_rate_2024_2020                    = c("blank_rate_2024",         "blank_rate_2016"),
  delta_null_rate_2024_2020                     = c("null_rate_2024",          "null_rate_2016"),
  delta_turnout_rate_2024_2020                  = c("turnout_rate_2024",       "turnout_rate_2016"),
  delta_valid_vote_rate_2024_2020               = c("valid_vote_rate_2024",    "valid_vote_rate_2016"),
  delta_blank_rate_vereador_2024_2020           = c("blank_rate_vereador_2024","blank_rate_vereador_2016"),
  delta_null_rate_vereador_2024_2020            = c("null_rate_vereador_2024", "null_rate_vereador_2016"),
  delta_valid_vote_rate_vereador_2024_2020      = c("valid_vote_rate_vereador_2024", "valid_vote_rate_vereador_2016")
)

# Resolve the LHS + lag for a given outcome and form.
#   form "ancova2016": ANCOVA-able outcomes use (2024 level LHS, free 2016 lag);
#                      outcomes with no 2016 analog fall back to pure first
#                      difference (delta, no own-lag).
#   form "fd"        : pure first difference (delta LHS, no own-lag) for every
#                      outcome -- the labelled robustness bracket.
# Returns list(lhs, lag, is_ancova). `lag` is NULL except for ANCOVA outcomes.
resolve_lhs <- function(outcome, form, data) {
  if (form == "ancova2016" && !is.null(ANCOVA_MAP[[outcome]])) {
    pair <- ANCOVA_MAP[[outcome]]
    if (all(pair %in% names(data)))
      return(list(lhs = pair[1], lag = pair[2], is_ancova = TRUE))
  }
  list(lhs = outcome, lag = NULL, is_ancova = FALSE)
}



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

# 2SLS in the requested form (ANCOVA-2016 level or pure first difference):
#   ANCOVA:  Y_2024 ~ controls + Y_2016 | FE | endogenous ~ instrument
#   FD:      delta_Y ~ controls        | FE | endogenous ~ instrument
# The fitted object carries the resolved LHS / lag / form as attributes so the
# table and CSV layers can report the right dep-var mean and baseline.
run_iv <- function(samp, outcome, controls, fe_col, instrument, endogenous,
                   form = "fd") {
  r        <- resolve_lhs(outcome, form, samp)
  ctrls    <- avail(c(controls, r$lag), samp)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml      <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s", r$lhs, ctrl_rhs, fe_col, endogenous, instrument
  ))
  fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  attr(fit, "ancova_lhs") <- r$lhs
  attr(fit, "is_ancova")  <- r$is_ancova
  attr(fit, "lag_col")    <- if (is.null(r$lag)) NA_character_ else r$lag
  fit
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

# Each entry: list(name, controls, fe_col, single_zone, aptos_filter, form)
#   form "ancova2016" -> headline ANCOVA on the 2016 baseline (Y_2024 ~ D + Y_2016)
#   form "fd"         -> pure first difference (delta_Y ~ D), the robustness bracket
specs <- list(
  list("baseline",          BASELINE_CONTROLS,                                  "SG_UF", FALSE, NULL,           "ancova2016"),
  list("single_zone",       BASELINE_CONTROLS,                                  "SG_UF", TRUE,  NULL,           "ancova2016"),
  list("extended_controls", ROBUSTNESS_CONTROLS,                                "SG_UF", FALSE, NULL,           "ancova2016"),
  list("open_seat",         BASELINE_CONTROLS,                                  "SG_UF", FALSE, "open_seat",    "ancova2016"),
  list("contested_seat",    BASELINE_CONTROLS,                                  "SG_UF", FALSE, "no_open_seat", "ancova2016"),
  list("broader_treatment", c(BASELINE_CONTROLS, "log1p_lawsuits_no_rrc_2020"), "SG_UF", FALSE, NULL,           "ancova2016"),
  # Robustness bracket: pure first difference (delta outcome, no own-lag). The FD
  # form pins the 2016->2024 persistence to 1; reported alongside the headline so
  # the over-differencing is visible (see 14_fd_vs_ancova.R).
  list("fd",                BASELINE_CONTROLS,                                  "SG_UF", FALSE, NULL,           "fd"),
  # Legacy V1 stance check: delta outcome + 2020 competition levels as controls.
  list("ancova_2020lvl",    c(BASELINE_CONTROLS, ANCOVA_2020_LEVELS),           "SG_UF", FALSE, NULL,           "fd")
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
# Headline first-stage table: baseline + extended controls, then the two seat-type
# subsamples that carry the voter-disengagement result. single_zone / broader_treatment
# are robustness slices reported elsewhere, not in the headline first-stage table.
FS_TEX_SPECS       <- c("baseline", "extended_controls", "open_seat", "contested_seat")
ROBUSTNESS_TEX_SPECS <- c("baseline", "single_zone", "extended_controls", "broader_treatment")
BLANK_SUBGROUP_SPECS <- c("baseline", "open_seat", "contested_seat")

tex_fs_fits       <- list()   # [spec_name] = feols (first stage)
tex_base_iv_fits  <- list()   # [outcome]   = feols (baseline ANCOVA-2016 IV)
tex_fd_iv_fits    <- list()   # [outcome]   = feols (pure first-difference, appendix)
tex_robust_iv_fits <- list()  # [spec_name] = feols (winner majority, robustness specs)
tex_blank_sub_fits <- list()  # [spec_name] = feols (blank rate, subgroup specs)
tex_vb_oc_fits     <- list()  # [spec_name][[outcome]] = feols (voter beh., open/contested)

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
    form         <- if (length(sp) >= 6) sp[[6]] else "fd"

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
        iv_fit  <- run_iv(samp, y, controls, fe_col, instrument, endogenous, form)
        lhs_used <- attr(iv_fit, "ancova_lhs")
        lag_used <- attr(iv_fit, "lag_col")
        # Per-outcome N (the level / own-lag may drop a few rows with missing data)
        y_n  <- nobs(iv_fit)
        keep_cols <- c(lhs_used, avail(controls, samp),
                       if (!is.na(lag_used)) lag_used)
        y_cl <- length(unique(samp$cluster_id[stats::complete.cases(
                  samp[, keep_cols])]))
        # Dep-var mean is the mean of the ACTUAL LHS (2024 level under ANCOVA,
        # delta under FD). For ANCOVA also store the 2016 baseline mean so the
        # table can show both the pre-window baseline and the 2024 level.
        attr(iv_fit, "mean_delta") <- mean(samp[[lhs_used]], na.rm = TRUE)
        attr(iv_fit, "mean_2016")  <- if (!is.na(lag_used) &&
                                          isTRUE(attr(iv_fit, "is_ancova")))
                                        mean(samp[[lag_used]], na.rm = TRUE) else NA_real_
        iv_rows[[length(iv_rows) + 1]] <- extract_iv_row(
          iv_fit, var_name, spec_name, family, y, y_n, y_cl, endogenous
        )
        # Store model objects for tex generation
        if (spec_name == "baseline")
          tex_base_iv_fits[[y]] <- iv_fit
        if (spec_name == "fd")
          tex_fd_iv_fits[[y]] <- iv_fit
        if (y == "delta_winner_majority_2024_2020" && spec_name %in% ROBUSTNESS_TEX_SPECS)
          tex_robust_iv_fits[[spec_name]] <- iv_fit
        if (y == "delta_blank_rate_2024_2020" && spec_name %in% BLANK_SUBGROUP_SPECS)
          tex_blank_sub_fits[[spec_name]] <- iv_fit
        if (spec_name %in% c("open_seat", "contested_seat") &&
            y %in% VOTER_BEHAVIOR_OUTCOMES)
          tex_vb_oc_fits[[spec_name]][[y]] <- iv_fit
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
          r_l        <- resolve_lhs(y, form, samp)
          ctrls_l    <- avail(c(controls, r_l$lag), samp)
          ctrl_rhs_l <- if (length(ctrls_l) > 0) paste(ctrls_l, collapse = " + ") else "1"
          fml_l      <- as.formula(sprintf(
            "%s ~ %s | %s | %s ~ %s", r_l$lhs, ctrl_rhs_l, fe_col, endogenous, instrument
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
  "SE clustered by state (UF); leave-own-state-out shift is constant within state.",
  "",
  "## Instrument",
  "- **adversarial** : bartik_iv_2020_2024 / delta_log1p_competition_lawsuits_2024_2020",
  "  (adversarial class/subject filter applied at build stage in 02_bartik_inputs.py)",
  "",
  "## Specifications (headline = ANCOVA on the 2016 pre-window baseline)",
  "Baseline (V3) controls: 2010 Census structure (log pop, urban share, log income p.c., higher-ed share),",
  "log valid-vote volume (2020), 2016 victory margin, PLUS each outcome's own 2016 level where one exists",
  "(per-outcome lagged DV). No 2020 levels of competition outcomes (avoids Lord's-paradox bias).",
  "",
  "1. **baseline** — ANCOVA-2016: per-outcome 2016 level as free lag + common controls + state FE",
  "2. **single_zone** — baseline, single-zone municipalities only",
  "3. **extended_controls** — baseline + extended 2020 covariates + state FE",
  "4. **open_seat** — baseline, open-seat municipalities (2020 winner term-limited)",
  "5. **contested_seat** — baseline, contested-seat municipalities",
  "6. **broader_treatment** — baseline + log1p_lawsuits_no_rrc_2020 as additional control",
  "7. **fd** — appendix robustness: pure first difference (delta_Y ~ D, persistence pinned to 1)",
  "8. **ancova_2020lvl** — legacy V1 stance check: delta outcome + 2020 competition levels as controls",
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
  delta_turnout_rate_2024_2020                      = "$\\Delta$ Turnout (any ballot)",
  delta_null_rate_2024_2020                         = "$\\Delta$ Null (mayoral)",
  delta_blank_rate_2024_2020                        = "$\\Delta$ Blank (mayoral)",
  delta_valid_vote_rate_2024_2020                   = "$\\Delta$ Valid (mayoral)",
  delta_null_rate_vereador_2024_2020                = "$\\Delta$ Null (council)",
  delta_blank_rate_vereador_2024_2020               = "$\\Delta$ Blank (council)",
  delta_valid_vote_rate_vereador_2024_2020          = "$\\Delta$ Valid (council)",
  delta_share_first_time_candidates_2024_2020       = "$\\Delta$ New entrant share",
  delta_share_serial_challenger_2024_2020           = "$\\Delta$ Serial challenger",
  delta_share_cross_cycle_returner_2024_2020        = "$\\Delta$ Cross-cycle returner"
)

# Under the ANCOVA-2016 headline the LHS is the 2024 LEVEL (the 2016 level enters
# as a free control), so etable renders the 2024-level variable name in the
# dependent-variable header. These labels translate those level names WITHOUT the
# "$\\Delta$" prefix; merged into the dict alongside OUTCOME_LABELS so each column
# is labelled correctly whether the fit is ANCOVA (level LHS) or FD (delta LHS).
ANCOVA_LABELS <- c(
  margin_top1_top2_2024              = "Margin (W$-$RU)",
  winner_vote_share_2024             = "Winner vote share",
  runnerup_vote_share_2024           = "Runner-up vote share",
  winner_majority_2024               = "Winner majority (P50)",
  others_vote_share_2024             = "Others vote share",
  log1p_n_candidates_with_votes_2024 = "Log n candidates",
  female_vote_share_2024             = "Female vote share",
  nonwhite_vote_share_2024           = "Nonwhite vote share",
  winner_is_female_2024              = "Winner is female",
  blank_rate_2024                    = "Blank (mayoral)",
  null_rate_2024                     = "Null (mayoral)",
  turnout_rate_2024                  = "Turnout (any ballot)",
  valid_vote_rate_2024               = "Valid (mayoral)",
  blank_rate_vereador_2024           = "Blank (council)",
  null_rate_vereador_2024            = "Null (council)",
  valid_vote_rate_vereador_2024      = "Valid (council)"
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
# The treatment is litigation intensity, $\Delta\log(1+\text{adversarial lawsuits})$;
# we label it "Judicialization" on tables (the conceptual object the instrument
# proxies) and carry the log-change magnitude in the per-SD interpretation text.
ETABLE_DICT <- c(
  "fit_delta_log1p_competition_lawsuits_2024_2020" = "Judicialization",
  "delta_log1p_competition_lawsuits_2024_2020"     = "Judicialization",
  "bartik_iv_2020_2024"                            = "Predicted judicialization",
  "SG_UF"                                          = "State (UF)",
  "cluster_id"                                     = "state"
)

# Standard convention: *** 1%, ** 5%, * 10%.
ETABLE_SIGNIF <- c("***" = .01, "**" = .05, "*" = .10)

# Write just the \begin{tabular}...\end{tabular} block from etable(tex=TRUE) output
# Background-shade the coefficient cells significant at 5%, so the eye lands on
# the live result. `pvals` is the per-column p-vector in etable column order
# (= model order). Injects \cellcolor{sigshade} into the coefficient row only.
SIG_SHADE_P <- 0.05
shade_sig_cells <- function(frag, pvals) {
  if (is.null(pvals) || !length(pvals)) return(frag)
  # Coefficient row = the (only kept) "Judicialization" row; anchor on it directly
  # so shading is robust to dropping the "Variables" title line.
  crow <- which(grepl("^\\s*Judicialization\\s*&", frag))
  if (!length(crow)) return(frag)
  crow <- crow[1L]
  cells <- strsplit(frag[crow], "&", fixed = TRUE)[[1]]   # [1]=label, [2..]=cols
  for (j in seq_along(pvals)) {
    k <- j + 1L
    if (k > length(cells) || is.na(pvals[j]) || pvals[j] >= SIG_SHADE_P) next
    cells[k] <- sub("^(\\s*)", "\\1\\\\cellcolor{sigshade}", cells[k])
  }
  frag[crow] <- paste(cells, collapse = "&")
  frag
}

# Per-model p-value on the instrumented coefficient (the only "fit_" term).
iv_pval <- function(m) {
  pv <- pvalue(m)
  unname(pv[grep("^fit_", names(pv))][1L])
}

write_etable_frag <- function(out, path, pvals = NULL) {
  if (length(out) == 1L) out <- strsplit(out, "\n", fixed = TRUE)[[1]]
  i1 <- which(grepl("\\begin{tabular}", out, fixed = TRUE))
  i2 <- which(grepl("\\end{tabular}",   out, fixed = TRUE))
  frag <- if (length(i1) && length(i2)) out[i1[1L]:i2[length(i2)]] else out
  frag <- shade_sig_cells(frag, pvals)
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
# Merge the readable outcome labels into the dict so etable() translates the
# dependent-variable names in the header row (not just the model list names).
etab_base <- list(
  tex          = TRUE,
  dict         = c(ETABLE_DICT, OUTCOME_LABELS, ANCOVA_LABELS),
  signif.code  = ETABLE_SIGNIF,
  digits       = 3,
  digits.stats = 1,
  notes        = "SE clustered by state (UF).",
  # Drop the "Variables" section title -- the single coefficient row is labelled
  # "Judicialization" and needs no header above it.
  style.tex    = style.tex(arraystretch = 1.2, var.title = "")
)

# Convenience: filter NULLs and apply spec/outcome labels to a model sub-list
label_mods <- function(store, keys, labels) {
  mods <- Filter(Negate(is.null), store[keys])
  setNames(mods, labels[names(mods)])
}

# Dependent-variable mean row (one value per model) for etable extralines.
# Under ANCOVA this is the mean of the 2024 LEVEL (the LHS); under FD the mean of
# the delta. `mean_2016_row` adds the pre-window 2016 baseline mean for ANCOVA
# columns (blank for FD columns), so the table shows both the baseline and the
# 2024 level the headline conditions on.
mean_row <- function(mods)
  unname(vapply(mods, function(m) sprintf("%.3f", attr(m, "mean_delta")), character(1)))

mean_2016_row <- function(mods)
  unname(vapply(mods, function(m) {
    v <- attr(m, "mean_2016")
    if (is.null(v) || is.na(v)) "" else sprintf("%.3f", v)
  }, character(1)))

# Wrapper: emit an IV etable with the outcome-mean row appended.
# Table conventions: every column carries the same state (UF) fixed effect, so
# the fixed-effects section is dropped from the body and stated in the note. The
# observations row is shown only when N varies across columns; when it is
# constant it is reported once in the note. The homoskedastic ivf F is never
# shown (it understates the cluster-robust weak-IV diagnostic); the dedicated
# first_stage.tex carries the correct cluster-robust first-stage F and tF cv.
# All columns carry the same state (UF) fixed effect, so the fixed-effects
# section is dropped (drop.section = "fixef") and stated in the frame caption.
# The observations row is shown only when N varies across columns; when N is
# constant it is omitted from the table and reported in the caption. (etable's
# `notes` are emitted outside \end{tabular} and stripped by write_etable_frag,
# which is why FE / constant-N facts live in the slide caption, not the note.)
iv_etable <- function(mods, path, note_extra = NULL) {
  ns      <- vapply(mods, function(m) as.integer(nobs(m)), integer(1))
  same_n  <- length(unique(ns)) == 1L
  any_anc <- any(vapply(mods, function(m) isTRUE(attr(m, "is_ancova")), logical(1)))
  # Self-documenting mean rows: spell out that these are the dependent variable's
  # own average in the outcome year (2024) and in the pre-period baseline (2016)
  # that the ANCOVA conditions on -- not a generic "mean of dep. var.".
  extra   <- list("2024 Mean" = mean_row(mods))
  if (any_anc)
    extra[["2016 Mean"]] <- mean_2016_row(mods)
  out <- do.call(etable, c(list(
    mods, keep_raw = iv_keep_raw,
    drop.section = "fixef",
    fitstat = if (same_n) NA else ~ n,
    extralines = extra
  ), etab_base))
  write_etable_frag(out, path, pvals = vapply(mods, iv_pval, numeric(1)))
}

# ---- 9a. First Stage (cols = specs) ----
{
  # Use original spec keys to compute extra rows before renaming
  valid_fs <- intersect(FS_TEX_SPECS, names(Filter(Negate(is.null), tex_fs_fits)))
  fs_F_row  <- unname(sapply(valid_fs, function(s)
    sprintf("%.1f", tstat(tex_fs_fits[[s]])[instrument]^2)))
  fs_N_row  <- unname(sapply(valid_fs, function(s)
    formatC(nobs(tex_fs_fits[[s]]), format = "d", big.mark = ",")))
  # Compact column headers so each of the four designs is NAMED in the table
  # (etable renders `headers`, not the list names, as the column header row).
  FS_SHORT_LABELS <- c(
    baseline          = "Baseline",
    extended_controls = "Ext.\\ controls",
    open_seat         = "Open seats",
    contested_seat    = "Contested"
  )
  mods <- tex_fs_fits[valid_fs]
  out <- do.call(etable, c(list(
    mods,
    headers      = list("Design:" = unname(FS_SHORT_LABELS[valid_fs])),
    keep_raw     = paste0("^", instrument, "$"),
    drop.section = "fixef",
    fitstat      = NA,
    extralines = list(
      "First-stage $F$"          = fs_F_row,
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
  iv_etable(mods, file.path(TEX_DIR, "executive_iv_competition.tex"))
}

# ---- 9c-i. Turnout (office-invariant): one standalone column ----
# Turnout is one comparecimento per voter, so it is office-invariant and stands
# on its own (mean rows + 5%-shading come from iv_etable).
{
  mods <- label_mods(tex_base_iv_fits, "delta_turnout_rate_2024_2020", OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "executive_iv_turnout.tex"))
}

# ---- 9c-ii. Ballot composition: two-panel table (Mayoral / Council) ----
# Panel A = mayoral ballot, Panel B = council ballot; columns = blank/null/valid.
# Hand-built so the two ballots stack as panels with self-documenting mean rows
# ("Avg. rate in 2024 / 2016") and 5%-significant coefficient cells shaded -- the
# contrast (mayoral lights up, council does not) reads off a single table.
{
  iv_name <- paste0("fit_", endogenous)
  star_std <- function(p) {
    if (is.null(p) || is.na(p)) return("")
    if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
  }
  # coefficient cell: shade when significant at 5%
  pcell_coef <- function(fit) {
    if (is.null(fit)) return("---")
    b <- unname(coef(fit)[iv_name]); p <- unname(pvalue(fit)[iv_name])
    shade <- if (!is.na(p) && p < SIG_SHADE_P) "\\cellcolor{sigshade}" else ""
    sprintf("%s$%+.3f$%s", shade, b, star_std(p))
  }
  pcell_se   <- function(fit) if (is.null(fit)) "" else sprintf("(%.3f)", unname(se(fit)[iv_name]))
  pcell_m24  <- function(fit) if (is.null(fit)) "" else sprintf("%.3f", attr(fit, "mean_delta"))
  pcell_m16  <- function(fit) {
    if (is.null(fit)) return("")
    v <- attr(fit, "mean_2016"); if (is.null(v) || is.na(v)) "" else sprintf("%.3f", v)
  }

  ballot_cols <- c("delta_blank_rate", "delta_null_rate", "delta_valid_vote_rate")
  panel_block <- function(title, suffix) {
    fits <- lapply(ballot_cols, function(b)
      tex_base_iv_fits[[paste0(b, suffix, "_2024_2020")]])
    c(
      sprintf("\\multicolumn{4}{l}{\\emph{%s}}\\\\[1pt]", title),
      sprintf("\\quad Judicialization & %s \\\\",
              paste(vapply(fits, pcell_coef, ""), collapse = " & ")),
      sprintf(" & %s \\\\", paste(vapply(fits, pcell_se, ""), collapse = " & ")),
      sprintf("\\quad {\\footnotesize 2024 Mean} & %s \\\\",
              paste(vapply(fits, function(f) paste0("{\\footnotesize ", pcell_m24(f), "}"), ""),
                    collapse = " & ")),
      sprintf("\\quad {\\footnotesize 2016 Mean} & %s \\\\[2pt]",
              paste(vapply(fits, function(f) paste0("{\\footnotesize ", pcell_m16(f), "}"), ""),
                    collapse = " & "))
    )
  }
  n_obs_ballot <- {
    f <- tex_base_iv_fits[["delta_blank_rate_2024_2020"]]
    if (is.null(f)) "" else formatC(as.integer(nobs(f)), format = "d", big.mark = ",")
  }

  tbl <- c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    "\\begin{tabular}{lccc}",
    "\\toprule",
    " & Blank vote & Null vote & Valid vote \\\\",
    "\\midrule",
    panel_block("Panel A. Mayoral (prefeito) ballot", ""),
    "\\midrule",
    panel_block("Panel B. Council (vereador) ballot", "_vereador"),
    "\\midrule",
    sprintf("Municipalities ($N$) & \\multicolumn{3}{c}{%s} \\\\", n_obs_ballot),
    "\\bottomrule",
    "\\end{tabular}"
  )
  out_path <- file.path(TEX_DIR, "executive_iv_ballot_panel.tex")
  writeLines(tbl, con = out_path)
  cat("  Wrote:", out_path, "\n")
}

# ---- 9c-bis. Voter Behavior: office x open-seat heterogeneity (hand-built) ----
# Columns = {Mayoral, Council} x {Open seat, Contested seat}; rows = ballot
# composition (blank/null/valid). Turnout is office-invariant and is reported in
# the by-office table above, so it is omitted here. Built directly from the
# stored 2SLS fits (open_seat / contested_seat specs) so each cell carries its
# own coefficient, cluster-robust SE and subsample dep-var mean.
{
  iv_name <- paste0("fit_", endogenous)
  vb_get <- function(fit) {
    if (is.null(fit)) return(NULL)
    list(coef = unname(coef(fit)[iv_name]),
         se   = unname(se(fit)[iv_name]),
         p    = unname(pvalue(fit)[iv_name]),
         mean = attr(fit, "mean_delta"))
  }
  star_std <- function(p) {
    if (is.null(p) || is.na(p)) return("")
    if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
  }
  cell_coef <- function(g) if (is.null(g)) "---" else sprintf("$%+.3f$%s", g$coef, star_std(g$p))
  cell_se   <- function(g) if (is.null(g)) "" else sprintf("(%.3f)", g$se)
  cell_mean <- function(g) if (is.null(g)) "" else sprintf("%.3f", g$mean)

  # rows: (label, mayoral outcome, council outcome)
  vb_rows <- list(
    c("Blank vote rate", "delta_blank_rate_2024_2020",      "delta_blank_rate_vereador_2024_2020"),
    c("Null vote rate",  "delta_null_rate_2024_2020",       "delta_null_rate_vereador_2024_2020"),
    c("Valid vote rate", "delta_valid_vote_rate_2024_2020", "delta_valid_vote_rate_vereador_2024_2020")
  )
  # column order: mayoral-open, mayoral-contested, council-open, council-contested
  col_specs <- list(
    c("open_seat",      "mayoral"), c("contested_seat", "mayoral"),
    c("open_seat",      "council"), c("contested_seat", "council")
  )
  body <- character(0)
  for (r in vb_rows) {
    lab <- r[[1]]; y_may <- r[[2]]; y_cou <- r[[3]]
    gs <- lapply(col_specs, function(cs) {
      y <- if (cs[2] == "mayoral") y_may else y_cou
      vb_get(tex_vb_oc_fits[[cs[1]]][[y]])
    })
    body <- c(body,
      sprintf("%s & %s \\\\", lab, paste(vapply(gs, cell_coef, ""), collapse = " & ")),
      sprintf(" & %s \\\\", paste(vapply(gs, cell_se, ""), collapse = " & ")),
      sprintf("\\quad {\\footnotesize Mean of dep.\\ var.} & %s \\\\[2pt]",
              paste(vapply(gs, function(g) paste0("{\\footnotesize ", cell_mean(g), "}"), ""),
                    collapse = " & ")))
  }
  # N per column (open vs contested differ); pull from any present fit in that spec
  col_n <- vapply(col_specs, function(cs) {
    fits <- Filter(Negate(is.null), tex_vb_oc_fits[[cs[1]]])
    if (length(fits) == 0) return("")
    formatC(as.integer(nobs(fits[[1]])), format = "d", big.mark = ",")
  }, "")

  tbl <- c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    "\\begin{tabular}{lcccc}",
    "\\toprule",
    " & \\multicolumn{2}{c}{Mayoral ballot} & \\multicolumn{2}{c}{Council ballot} \\\\",
    "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
    " & Open seat & Contested & Open seat & Contested \\\\",
    "\\midrule",
    body,
    "\\midrule",
    sprintf("$N$ & %s \\\\", paste(col_n, collapse = " & ")),
    "\\bottomrule",
    "\\end{tabular}"
  )
  out_path <- file.path(TEX_DIR, "executive_iv_voter_behavior_office_openseat.tex")
  writeLines(tbl, con = out_path)
  cat("  Wrote:", out_path, "\n")
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
  iv_etable(mods, file.path(TEX_DIR, "executive_iv_composition.tex"))
}

# ---- 9e. Entrant Typology (cols = outcomes) ----
{
  outs <- c(
    "delta_share_first_time_candidates_2024_2020",
    "delta_share_serial_challenger_2024_2020",
    "delta_share_cross_cycle_returner_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "entrant_typology.tex"))
}

# ---- 9f. Blank Rate — open-seat heterogeneity (cols = subgroup specs) ----
{
  sub_labels <- c(
    baseline      = "All municipalities",
    open_seat     = "Open seat",
    contested_seat = "Contested seat"
  )
  mods <- label_mods(tex_blank_sub_fits, BLANK_SUBGROUP_SPECS, sub_labels)
  iv_etable(mods, file.path(TEX_DIR, "open_seat_blank_rate.tex"))
}

# ---- 9g. Robustness — Winner Majority (cols = specs) ----
{
  mods <- label_mods(tex_robust_iv_fits, ROBUSTNESS_TEX_SPECS, SPEC_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "robustness_winner_majority.tex"))
}

# ---- 9h. Appendix — pure first-difference bracket (cols = headline outcomes) ----
# The headline is ANCOVA-2016 (Y_2024 ~ D + Y_2016); this appendix table reports
# the SAME outcomes under a pure first difference (delta_Y ~ D), which pins the
# 2016->2024 persistence to one. Municipal margins barely persist, so FD
# over-differences and the consolidation/disengagement coefficients attenuate
# toward zero -- the contrast is the point (see 14_fd_vs_ancova.R). All-FD here,
# so the dep-var means are delta means and no 2016-baseline row is added.
{
  outs <- c(
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020",
    "delta_runnerup_vote_share_2024_2020",
    "delta_winner_majority_2024_2020",
    "delta_blank_rate_2024_2020",
    "delta_null_rate_2024_2020"
  )
  mods <- label_mods(tex_fd_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "appendix_first_difference.tex"))
}

cat("\nLaTeX fragments written to", TEX_DIR, "\n")
