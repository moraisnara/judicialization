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
# build stage (DROP_CLASSES + DROP_SUBJECTS in 02_shift_share_design.py).
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
  "delta_winner_is_new_2024_2020"
)
# Entry typology outcomes: change in share of each entrant type in the candidate pool
ENTRY_OUTCOMES <- c(
  "delta_share_first_time_candidates_2024_2020",
  "delta_share_serial_challenger_2024_2020",
  "delta_share_cross_cycle_returner_2024_2020"
)
# Field-concentration ladder (the candidate-side "winner consolidation" spine):
# whole-distribution measures of how concentrated the vote is, NOT just the top
# two. Under consolidation the effective field shrinks (eff. N candidates down),
# the vote concentrates (HHI up), while the top-2 bloc's COMBINED share need not
# move (the winner pulls away from the runner-up rather than the duo capturing
# more). Party-concentration twins (effective_n_parties, vote_hhi_party) are
# byte-identical to the candidate versions in mayoral races (one candidate per
# party) so they are intentionally omitted here; they matter only in the
# legislative (proportional) design.
CONCENTRATION_OUTCOMES <- c(
  "delta_effective_n_candidates_vote_2024_2020",
  "delta_vote_hhi_candidate_2024_2020",
  "delta_top2_vote_share_2024_2020"
)
# Pre-trend falsification: the 2016->2020 change in each headline competition /
# concentration outcome, regressed on the (instrumented) 2020->2024 treatment. A
# future shock cannot cause a past change, so a clean design wants these ~0. They
# carry no ANCOVA map entry, so run_iv estimates them as pure first differences
# (the pretrend column IS the LHS). Reported as an openly-shown falsification.
PRETREND_OUTCOMES <- c(
  "pretrend_margin_top1_top2_2020_2016",
  "pretrend_effective_n_candidates_vote_2020_2016",
  "pretrend_vote_hhi_candidate_2020_2016",
  "pretrend_top2_vote_share_2020_2016"
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
                  VOTER_DISAGG_OUTCOMES, ENTRY_OUTCOMES,
                  CONCENTRATION_OUTCOMES, PRETREND_OUTCOMES)

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
# the common set only (V2).
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020",
  "margin_2016"
)

# Strictly PRE-DETERMINED (2010 Census) subset. Used for the PRETREND_OUTCOMES
# only: a balance test on a 2016->2020 change must NOT condition on margin_2016
# (the 2016 baseline of the consolidation ladder -> Lord's-paradox / regression-
# to-the-mean, which MANUFACTURES a pre-trend) nor on log1p_total_valid_votes_2020
# (an end-of-pre-window 2020 quantity). Diagnosed 2026-07-01: with margin_2016 in
# the set, margin balance p=.019; on the predetermined set, p=.94 -- the apparent
# pre-trend was the control, not the data. Standalone falsification + coefplot in
# code/03_estimation/05_pretrend_balance.R. See also the control philosophy note above,
# which already bars 2020 competition LEVELS on the same Lord's-paradox grounds.
PREDET_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010"
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
# (code/04_analysis/05_validation.R). The first-difference (FD) estimates
# are retained as a labelled robustness column (spec "fd"). See
# code/04_analysis/05_validation.R for the full FD-vs-ANCOVA comparison.
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
  delta_new_candidate_vote_share_2024_2020      = c("new_candidate_vote_share_2024",       "new_candidate_vote_share_2016"),
  delta_incumbent_candidate_vote_share_2024_2020 = c("incumbent_candidate_vote_share_2024", "incumbent_candidate_vote_share_2016"),
  delta_winner_is_new_2024_2020                 = c("winner_is_new_2024",      "winner_is_new_2016"),
  delta_blank_rate_2024_2020                    = c("blank_rate_2024",         "blank_rate_2016"),
  delta_null_rate_2024_2020                     = c("null_rate_2024",          "null_rate_2016"),
  delta_turnout_rate_2024_2020                  = c("turnout_rate_2024",       "turnout_rate_2016"),
  delta_valid_vote_rate_2024_2020               = c("valid_vote_rate_2024",    "valid_vote_rate_2016"),
  delta_blank_rate_vereador_2024_2020           = c("blank_rate_vereador_2024","blank_rate_vereador_2016"),
  delta_null_rate_vereador_2024_2020            = c("null_rate_vereador_2024", "null_rate_vereador_2016"),
  delta_valid_vote_rate_vereador_2024_2020      = c("valid_vote_rate_vereador_2024", "valid_vote_rate_vereador_2016"),
  delta_effective_n_candidates_vote_2024_2020   = c("effective_n_candidates_vote_2024", "effective_n_candidates_vote_2016"),
  delta_vote_hhi_candidate_2024_2020            = c("vote_hhi_candidate_2024",  "vote_hhi_candidate_2016"),
  delta_top2_vote_share_2024_2020               = c("top2_vote_share_2024",     "top2_vote_share_2016")
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
  # the over-differencing is visible (see 05_validation.R).
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
BLANK_SUBGROUP_SPECS <- c("baseline", "open_seat", "contested_seat")

tex_fs_fits       <- list()   # [spec_name] = feols (first stage)
tex_base_iv_fits  <- list()   # [outcome]   = feols (baseline ANCOVA-2016 IV)
tex_fd_iv_fits    <- list()   # [outcome]   = feols (pure first-difference, appendix)
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

    # Keep the baseline ANCOVA sample + variant around for the tex-stage
    # pre-trend-robustness re-fit (block 9j) -- needs the same rows/instrument.
    if (spec_name == "baseline") { tex_base_samp <- samp; tex_base_variant <- vr }

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
                else if (y %in% CONCENTRATION_OUTCOMES) "concentration"
                else if (y %in% PRETREND_OUTCOMES)    "pretrend"
                else                                  "voter_behavior"
      # Pre-trend/balance outcomes drop the two non-predetermined controls
      # (margin_2016, 2020 vote volume) to avoid Lord's-paradox self-conditioning
      # on the outcome's own 2016 baseline. See PREDET_CONTROLS note above.
      controls_y <- if (y %in% PRETREND_OUTCOMES)
                      intersect(controls, PREDET_CONTROLS) else controls
      tryCatch({
        iv_fit  <- run_iv(samp, y, controls_y, fe_col, instrument, endogenous, form)
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
                  else if (y %in% CONCENTRATION_OUTCOMES) "concentration"
                  else if (y %in% PRETREND_OUTCOMES)    "pretrend"
                  else                                  "voter_behavior"
        tryCatch({
          controls_y <- if (y %in% PRETREND_OUTCOMES)
                          intersect(controls, PREDET_CONTROLS) else controls
          r_l        <- resolve_lhs(y, form, samp)
          ctrls_l    <- avail(c(controls_y, r_l$lag), samp)
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

cat("\nResults saved to:\n")
cat("  ", file.path(ESTIMATES_DIR, "executive_margin_first_stage_fixest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "executive_margin_iv_fixest.csv"), "\n")


# ============================================================
# 7. tF WEAK-INSTRUMENT CORRECTION (Lee et al. 2022, AER)
# ============================================================
# For first-stage F < 104.7, the usual normal critical value (1.96) is
# anti-conservative for the just-identified 2SLS t-test; the tF procedure
# replaces it with a larger, F-dependent critical value that restores correct
# 5% size. Reference: Lee, McCrary, Moreira & Porter (2022) "Valid t-ratio
# Inference for IV", AER 112(10): 3260-90, Table 3 (alpha = 0.05).
# The authoritative table + get_tF_cv() live in the shared util (one source of
# truth; an earlier hand-typed copy wrongly capped the correction at F = 23.1).
source(file.path(PROJECT_ROOT, "code", "utils", "tf_critical_values.R"))

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
  delta_winner_is_new_2024_2020                     = "$\\Delta$ Winner is new entrant",
  delta_turnout_rate_2024_2020                      = "$\\Delta$ Turnout (any ballot)",
  delta_null_rate_2024_2020                         = "$\\Delta$ Null (mayoral)",
  delta_blank_rate_2024_2020                        = "$\\Delta$ Blank (mayoral)",
  delta_valid_vote_rate_2024_2020                   = "$\\Delta$ Valid (mayoral)",
  delta_null_rate_vereador_2024_2020                = "$\\Delta$ Null (council)",
  delta_blank_rate_vereador_2024_2020               = "$\\Delta$ Blank (council)",
  delta_valid_vote_rate_vereador_2024_2020          = "$\\Delta$ Valid (council)",
  delta_share_first_time_candidates_2024_2020       = "$\\Delta$ New entrant share",
  delta_share_serial_challenger_2024_2020           = "$\\Delta$ Serial challenger",
  delta_share_cross_cycle_returner_2024_2020        = "$\\Delta$ Cross-cycle returner",
  delta_effective_n_candidates_vote_2024_2020       = "$\\Delta$ Eff.\\ N candidates",
  delta_vote_hhi_candidate_2024_2020                = "$\\Delta$ Vote HHI",
  delta_top2_vote_share_2024_2020                   = "$\\Delta$ Top-2 vote share",
  pretrend_margin_top1_top2_2020_2016               = "Margin (W$-$RU)",
  pretrend_effective_n_candidates_vote_2020_2016    = "Eff.\\ N candidates",
  pretrend_vote_hhi_candidate_2020_2016             = "Vote HHI",
  pretrend_top2_vote_share_2020_2016                = "Top-2 vote share"
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
  valid_vote_rate_vereador_2024      = "Valid (council)",
  effective_n_candidates_vote_2024   = "Eff.\\ N candidates",
  vote_hhi_candidate_2024            = "Vote HHI",
  top2_vote_share_2024               = "Top-2 vote share"
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
  # Suppress fixed-effect group sizes ("(nb: ...)") so the FE rows read as a
  # clean Yes/Yes -- matches the sectioned house style ported from judicial_bias.
  fixef_sizes  = FALSE,
  notes        = "SE clustered by state (UF).",
  # Keep the sectioned layout (Variables / Fixed-effects / Fit statistics
  # dividers) so each table is self-documenting in the judicial_bias style.
  style.tex    = style.tex(arraystretch = 1.2)
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

# ---- Hand-built "highlighted-band" table (judicial_bias SGD aesthetic) ----
# Horizontal band: the Judicialization coefficient row (and the gray SE beneath
# it) are shaded top-to-bottom in pale blue via \rowcolor{mylight} -- the
# judicial_bias house style, where the finding IS the coefficient row. Bold
# outcome headers, gray SEs beneath the coefficient, booktabs double rules, and
# an N + dependent-variable-mean footer. No Variables/Fixed-effects scaffolding
# -- the uniform state (UF) FE and the state-clustered SE are stated in the slide
# caption. The misleading homoskedastic ivf F is never shown (firststage.tex
# carries the cluster-robust F + tF cv).
hb_star <- function(p) {
  if (is.na(p))      return("")
  if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
}
# Coefficient string ("0.092$^{***}$") and gray SE string for one IV fit.
hb_coef_se <- function(m) {
  cf <- coef(m); se <- se(m); pv <- pvalue(m)
  k  <- grep("^fit_", names(cf))[1L]
  list(coef = sprintf("%.3f%s", cf[[k]], hb_star(pv[[k]])),
       se   = sprintf("(%.3f)", se[[k]]))
}
hb_row <- function(label, cells) paste0(label, " & ", paste(cells, collapse = " & "), " \\\\")

iv_etable <- function(mods, path, note_extra = NULL,
                      coef_label = "\\textbf{Judicialization}",
                      mean_label = "2024 Mean") {
  any_anc <- any(vapply(mods, function(m) isTRUE(attr(m, "is_ancova")), logical(1)))
  K   <- length(mods)
  cs  <- lapply(mods, hb_coef_se)
  hdr <- sprintf("\\textbf{%s}", names(mods))
  coef_cells <- vapply(cs, `[[`, "", "coef")
  se_cells   <- vapply(cs, function(x) sprintf("\\textcolor{mygray}{%s}", x$se), "")
  n_cells    <- vapply(mods, function(m) formatC(nobs(m), format = "d", big.mark = ","), "")
  lines <- c(
    sprintf("\\begin{tabular}{l*{%d}{c}}", K),
    "\\toprule\\toprule",
    hb_row("Dep.\\ var.:", hdr),
    "\\midrule",
    "\\rowcolor{mylight}",
    hb_row(coef_label, coef_cells),
    "\\rowcolor{mylight}",
    hb_row("", se_cells),
    "\\midrule",
    hb_row("$N$", n_cells),
    hb_row(mean_label, mean_row(mods))
  )
  if (any_anc) lines <- c(lines, hb_row("2016 Mean", mean_2016_row(mods)))
  lines <- c(lines, "\\bottomrule\\bottomrule", "\\end{tabular}")
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  writeLines(c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    lines
  ), con = path)
  cat("  Wrote:", path, "\n")
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
  # Hand-built to match the highlighted-band house style: bold design headers,
  # the predicted-judicialization coefficient in a pale-blue band with the gray
  # SE beneath, then the cluster-robust first-stage F and N.
  fs_cs <- lapply(mods, function(m) {
    cf <- coef(m)[instrument]; sev <- se(m)[instrument]; pv <- pvalue(m)[instrument]
    list(coef = sprintf("%.3f%s", cf, hb_star(pv)), se = sprintf("(%.3f)", sev))
  })
  fs_lines <- c(
    sprintf("\\begin{tabular}{l*{%d}{c}}", length(mods)),
    "\\toprule\\toprule",
    hb_row("Design:", sprintf("\\textbf{%s}", unname(FS_SHORT_LABELS[valid_fs]))),
    "\\midrule",
    "\\rowcolor{mylight}",
    hb_row("\\textbf{Predicted judicialization}", vapply(fs_cs, `[[`, "", "coef")),
    "\\rowcolor{mylight}",
    hb_row("", vapply(fs_cs, function(x) sprintf("\\textcolor{mygray}{%s}", x$se), "")),
    "\\midrule",
    hb_row("First-stage $F$", fs_F_row),
    hb_row("$N$", fs_N_row),
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  dir.create(TEX_DIR, showWarnings = FALSE, recursive = TRUE)
  writeLines(c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    fs_lines
  ), con = file.path(TEX_DIR, "firststage.tex"))
  cat("  Wrote:", file.path(TEX_DIR, "firststage.tex"), "\n")
}

# IV coef name as stored by fixest (fit_<endogenous>)
iv_keep_raw <- paste0("^fit_", endogenous, "$")

# ---- 9b. Electoral Competition (cols = outcomes, baseline spec) ----
# Spine 1 = the top two only: runner-up down / margin up / winner up (all ***).
# The binary winner-majority (P50, low-power discretisation of the margin) and the
# raw log-n-candidates (redundant with Eff.\ N in the concentration ladder, 9b-ii)
# are demoted to an appendix robustness table (9b-app) rather than shown here.
{
  outs <- c(
    "delta_runnerup_vote_share_2024_2020",
    "delta_margin_top1_top2_2024_2020",
    "delta_winner_vote_share_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "executive_iv_competition.tex"))
}

# ---- 9b-app. Appendix: binary/raw-count closeness outcomes ----
# Kept on record but off the main spine: winner-majority (P50) is the underpowered
# binary face of the margin; log-n-candidates is the raw-count analog of Eff.\ N.
{
  outs <- c(
    "delta_winner_majority_2024_2020",
    "delta_log1p_n_candidates_with_votes_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "appendix_competition_binary.tex"))
}

# ---- 9b-ii. Field concentration ladder (the winner-consolidation spine) ----
# Whole-distribution concentration: effective number of candidates (field size),
# vote HHI (concentration), and the top-2 combined share. Read with the
# competition table: winner up / runner-up down / margin up, eff. N down, HHI up,
# but top-2 COMBINED share flat == the winner pulls away (winner-take-more), not a
# drift to a two-horse duopoly, and with composition unchanged (see 9d).
{
  outs <- c(
    "delta_effective_n_candidates_vote_2024_2020",
    "delta_vote_hhi_candidate_2024_2020",
    "delta_top2_vote_share_2024_2020"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "executive_iv_concentration.tex"))
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
  # coefficient cell (the whole coef + SE rows are banded in mylight below)
  pcell_coef <- function(fit) {
    if (is.null(fit)) return("---")
    b <- unname(coef(fit)[iv_name]); p <- unname(pvalue(fit)[iv_name])
    sprintf("$%.3f$%s", b, star_std(p))
  }
  pcell_se   <- function(fit) if (is.null(fit)) "" else sprintf("\\textcolor{mygray}{(%.3f)}", unname(se(fit)[iv_name]))
  pcell_m24  <- function(fit) if (is.null(fit)) "" else sprintf("%.3f", attr(fit, "mean_delta"))
  pcell_m16  <- function(fit) {
    if (is.null(fit)) return("")
    v <- attr(fit, "mean_2016"); if (is.null(v) || is.na(v)) "" else sprintf("%.3f", v)
  }

  ballot_cols <- c("delta_blank_rate", "delta_null_rate", "delta_valid_vote_rate")
  # `band` shades the Judicialization coef + SE rows in pale blue (horizontal
  # band, judicial_bias house style). Only the mayoral panel (where the effect
  # lands) is banded; the council panel is left plain for contrast.
  panel_block <- function(title, suffix, band = FALSE) {
    fits <- lapply(ballot_cols, function(b)
      tex_base_iv_fits[[paste0(b, suffix, "_2024_2020")]])
    rc <- if (band) "\\rowcolor{mylight}" else character(0)
    c(
      sprintf("\\multicolumn{4}{l}{\\emph{%s}}\\\\[1pt]", title),
      rc,
      sprintf("\\quad \\textbf{Judicialization} & %s \\\\",
              paste(vapply(fits, pcell_coef, ""), collapse = " & ")),
      rc,
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
    "\\toprule\\toprule",
    " & \\textbf{Blank vote} & \\textbf{Null vote} & \\textbf{Valid vote} \\\\",
    "\\midrule",
    panel_block("Panel A. Mayoral (prefeito) ballot", "", band = TRUE),
    "\\midrule",
    panel_block("Panel B. Council (vereador) ballot", "_vereador", band = FALSE),
    "\\midrule",
    sprintf("Municipalities ($N$) & \\multicolumn{3}{c}{%s} \\\\", n_obs_ballot),
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  out_path <- file.path(TEX_DIR, "executive_iv_ballot_panel.tex")
  writeLines(tbl, con = out_path)
  cat("  Wrote:", out_path, "\n")
}

# ---- 9c-bis. Voter Behavior: office x open-seat heterogeneity (hand-built) ----
# Reframed (2026-06-30): rows = the four office x open/contested SUBSAMPLES,
# columns = ballot composition (blank/null/valid) + N. The gray SE sits STACKED
# beneath each coefficient (house style; Nara, 2026-06-30 -- SE below, not on the
# side), and the per-office 2024 dependent-variable means return as two footer
# rows. Positive coefficients carry NO "+" sign (absence already reads positive).
# Horizontal band: the mayoral-contested coef + SE rows -- where the
# disengagement concentrates -- are shaded via \rowcolor{mylight}.
{
  iv_name <- paste0("fit_", endogenous)
  vb_get <- function(fit) {
    if (is.null(fit)) return(NULL)
    list(coef = unname(coef(fit)[iv_name]),
         se   = unname(se(fit)[iv_name]),
         p    = unname(pvalue(fit)[iv_name]))
  }
  star_std <- function(p) {
    if (is.null(p) || is.na(p)) return("")
    if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
  }
  # coefficient (no + sign) and the gray SE that stacks on the line beneath it
  cell_coef <- function(g) if (is.null(g)) "---" else
    sprintf("$%.3f$%s", g$coef, star_std(g$p))
  cell_se   <- function(g) if (is.null(g)) "" else
    sprintf("\\textcolor{mygray}{(%.3f)}", g$se)

  out_may <- c("delta_blank_rate_2024_2020", "delta_null_rate_2024_2020", "delta_valid_vote_rate_2024_2020")
  out_cou <- c("delta_blank_rate_vereador_2024_2020", "delta_null_rate_vereador_2024_2020", "delta_valid_vote_rate_vereador_2024_2020")

  # two body lines per subsample (office x seat): coef row + SE row beneath;
  # `band` shades both lines of the headline row
  sub_row <- function(office, seat, seatlab, band = FALSE) {
    yv  <- if (office == "mayoral") out_may else out_cou
    gs  <- lapply(yv, function(y) vb_get(tex_vb_oc_fits[[seat]][[y]]))
    nf  <- Filter(Negate(is.null), tex_vb_oc_fits[[seat]])
    n   <- if (length(nf) == 0) "" else formatC(as.integer(nobs(nf[[1]])), format = "d", big.mark = ",")
    lab <- if (band) sprintf("\\quad \\textbf{%s}", seatlab) else sprintf("\\quad %s", seatlab)
    coef_line <- sprintf("%s & %s & %s \\\\", lab,
                         paste(vapply(gs, cell_coef, ""), collapse = " & "), n)
    se_line   <- sprintf(" & %s & \\\\",
                         paste(vapply(gs, cell_se, ""), collapse = " & "))
    rc <- if (band) "\\rowcolor{mylight}" else character(0)
    c(rc, coef_line, rc, se_line)
  }
  # 2024 dependent-variable mean per outcome, by office (full-sample pooled means
  # = the ballot-panel numbers); recovered from the pooled base IV fits.
  mean_cells <- function(yv) paste(vapply(yv, function(y) {
    f <- tex_base_iv_fits[[y]]
    if (is.null(f)) "" else sprintf("%.3f", attr(f, "mean_delta"))
  }, ""), collapse = " & ")

  tbl <- c(
    "% Auto-generated by code/03_estimation/02_iv_main.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    "\\begin{tabular}{lcccc}",
    "\\toprule\\toprule",
    " & \\textbf{Blank vote} & \\textbf{Null vote} & \\textbf{Valid vote} & $N$ \\\\",
    "\\midrule",
    "\\multicolumn{5}{l}{\\emph{Mayoral (prefeito)}}\\\\[1pt]",
    sub_row("mayoral", "open_seat",      "Open seat"),
    sub_row("mayoral", "contested_seat", "Contested", band = TRUE),
    "\\addlinespace[2pt]",
    "\\multicolumn{5}{l}{\\emph{Council (vereador)}}\\\\[1pt]",
    sub_row("council", "open_seat",      "Open seat"),
    sub_row("council", "contested_seat", "Contested"),
    "\\midrule",
    sprintf("\\emph{2024 mean (mayoral)} & %s & \\\\", mean_cells(out_may)),
    sprintf("\\emph{2024 mean (council)} & %s & \\\\", mean_cells(out_cou)),
    "\\bottomrule\\bottomrule",
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
    "delta_winner_is_new_2024_2020"
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

# ---- 9g. Appendix — pure first-difference bracket (cols = headline outcomes) ----
# The headline is ANCOVA-2016 (Y_2024 ~ D + Y_2016); this appendix table reports
# the SAME outcomes under a pure first difference (delta_Y ~ D), which pins the
# 2016->2024 persistence to one. Municipal margins barely persist, so FD
# over-differences and the consolidation/disengagement coefficients attenuate
# toward zero -- the contrast is the point (see 05_validation.R). All-FD here,
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

# ---- 9i. Pre-trend falsification (placebo: future shock on the PAST change) ----
# Each column regresses the 2016->2020 change in a consolidation outcome on the
# (instrumented) 2020->2024 treatment. A future shock cannot cause a past change,
# so a clean design wants ~0. These fits use PREDET_CONTROLS (the 2020->2024 loop
# strips margin_2016 + 2020 vote volume for pretrend outcomes), so the columns
# are the correctly-specified balance test: the WHOLE consolidation ladder is
# falsification-clean (margin/effN/HHI/top-2 all p>.3). The earlier "eff.N/HHI/
# margin carry a pre-trend" reading was an artifact of conditioning on margin_2016
# (Lord's paradox); see the standalone falsification + coefplot in 05_pretrend_balance.R
# and the PREDET_CONTROLS note. The placebo coefficient is NOT a treatment effect,
# so the row is labelled accordingly and the footer mean is the pre-trend mean.
{
  outs <- c(
    "pretrend_margin_top1_top2_2020_2016",
    "pretrend_effective_n_candidates_vote_2020_2016",
    "pretrend_vote_hhi_candidate_2020_2016",
    "pretrend_top2_vote_share_2020_2016"
  )
  mods <- label_mods(tex_base_iv_fits, outs, OUTCOME_LABELS)
  iv_etable(mods, file.path(TEX_DIR, "pretrend_falsification.tex"),
            coef_label = "\\textbf{Placebo (judicialization)}",
            mean_label = "Pre-trend mean")
}

# ---- 9j. Pre-trend-robust consolidation (control for the full pre-trajectory) ----
# Belt-and-suspenders (NOT a rescue): the correctly-specified balance test (9i /
# 05_pretrend_balance.R) already shows the consolidation ladder carries NO pre-trend once
# margin_2016 is dropped. This block goes further and conditions on the 2020
# base-year level IN ADDITION to the 2016 lag, so the coefficient is identified
# off the 2024 deviation from each municipality's OWN pre-treatment path
# ({2016, 2020} levels span the level and the pre-slope). The 2020 level is
# pre-determined w.r.t. the 2020->2024 shock (the instrument's shares are dated
# 2020), so it is a legitimate control. The consolidation survives essentially
# unchanged. Same house style/footer as the 2016-only concentration table.
if (exists("tex_base_samp")) {
  PT_2020_LEVEL <- c(
    delta_margin_top1_top2_2024_2020            = "margin_top1_top2_2020",
    delta_effective_n_candidates_vote_2024_2020 = "effective_n_candidates_vote_2020",
    delta_vote_hhi_candidate_2024_2020          = "vote_hhi_candidate_2020",
    delta_top2_vote_share_2024_2020             = "top2_vote_share_2020"
  )
  ptr_mods <- list()
  for (y in names(PT_2020_LEVEL)) {
    lvl20 <- PT_2020_LEVEL[[y]]
    if (!(lvl20 %in% names(tex_base_samp))) next
    fit <- run_iv(tex_base_samp, y, c(BASELINE_CONTROLS, lvl20), "SG_UF",
                  tex_base_variant$instrument, tex_base_variant$endogenous,
                  form = "ancova2016")
    lhs_used <- attr(fit, "ancova_lhs"); lag_used <- attr(fit, "lag_col")
    attr(fit, "mean_delta") <- mean(tex_base_samp[[lhs_used]], na.rm = TRUE)
    attr(fit, "mean_2016")  <- if (!is.na(lag_used)) mean(tex_base_samp[[lag_used]], na.rm = TRUE) else NA_real_
    ptr_mods[[OUTCOME_LABELS[[y]]]] <- fit
  }
  iv_etable(ptr_mods, file.path(TEX_DIR, "executive_iv_concentration_ptrobust.tex"))
}

cat("\nLaTeX fragments written to", TEX_DIR, "\n")
