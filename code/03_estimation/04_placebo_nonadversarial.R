# Non-adversarial intensity control + placebo shift-share (BHJ generic-shares test)
# ---------------------------------------------------------------------------
# BHJ (2025) warn that a shift-share instrument can fail when the EXPOSURE SHARES
# proxy something generic (here: a municipality's overall litigiousness / court
# presence) rather than the tailored channel of interest (adversarial-litigation
# growth). This script runs the three responses recorded in the identification
# draft (writing/identification_strategy_draft.md, sec. 3):
#
#   (1) Intensity control   - re-estimate the main IV adding the 2020 LEVEL of
#       NON-adversarial (mandatory/administrative) filing volume, so the
#       instrument leverages adversarial *composition* conditional on overall
#       litigation intensity. The main coefficients should barely move.
#   (2) Placebo shift-share  - a Bartik built the SAME way over the EXCLUDED
#       (non-adversarial) filings. Its reduced form on electoral outcomes should
#       be null: exposure to mandatory-filing growth must not predict electoral
#       change. A significant placebo would indicate generic shares.
#   (3) Conditioning on the placebo - add the placebo Bartik as an exogenous
#       control to the main IV; the main coefficient should survive.
#
# Columns built at the build stage (02_shift_share_design.py):
#   placebo_bartik_iv_2020_2024                       (placebo instrument)
#   delta_log1p_nonadversarial_lawsuits_2024_2020     (placebo endogenous)
#   log1p_nonadversarial_lawsuits_2020                (intensity control, 2020 level)
#
# All regression output in R/fixest (project standing rule). Outputs:
#   output/tables/regressions/nonadversarial_placebo.csv      (tidy, for macros)
#   output/tables/tex/nonadversarial_placebo_rf.tex           (placebo reduced form)
#   output/tables/tex/nonadversarial_robustness.tex           (main vs conditioned)

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
  SCRIPT_DIR <- if (length(file_arg) > 0)
    dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
}
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
TEX_DIR        <- file.path(PROJECT_ROOT, "output", "tables", "tex")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR,       recursive = TRUE, showWarnings = FALSE)


# ============================================================
# 1. LOAD DATA  (mirrors 02_iv_main.R)
# ============================================================
df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE",
                municipality_name = "NM_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))


# ============================================================
# 2. CONFIG  (V3 controls, identical to 02_iv_main.R baseline)
# ============================================================
INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "SG_UF"

PLACEBO_IV    <- "placebo_bartik_iv_2020_2024"
PLACEBO_ENDOG <- "delta_log1p_nonadversarial_lawsuits_2024_2020"
INTENSITY_CTRL <- "log1p_nonadversarial_lawsuits_2020"

BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020", "margin_2016"
)

# Headline = ANCOVA on the 2016 pre-window baseline. Map each delta key to
# c(2024 level LHS, 2016 lag control) so this placebo/intensity robustness is run
# on the SAME estimator as the headline 2SLS (02_iv_main.R). Outcomes with no
# 2016 analog fall back to the delta LHS with no own-lag (pure first difference).
ANCOVA_MAP <- list(
  delta_runnerup_vote_share_2024_2020 = c("runnerup_vote_share_2024", "runnerup_vote_share_2016"),
  delta_margin_top1_top2_2024_2020    = c("margin_top1_top2_2024",    "margin_top1_top2_2016"),
  delta_winner_vote_share_2024_2020   = c("winner_vote_share_2024",   "winner_vote_share_2016"),
  delta_winner_majority_2024_2020     = c("winner_majority_2024",     "winner_majority_2016"),
  delta_female_vote_share_2024_2020   = c("female_vote_share_2024",   "female_vote_share_2016"),
  delta_nonwhite_vote_share_2024_2020 = c("nonwhite_vote_share_2024", "nonwhite_vote_share_2016"),
  delta_turnout_rate_2024_2020        = c("turnout_rate_2024",        "turnout_rate_2016"),
  delta_blank_rate_2024_2020          = c("blank_rate_2024",          "blank_rate_2016")
)
resolve_lhs <- function(y) {
  pair <- ANCOVA_MAP[[y]]
  if (!is.null(pair) && all(pair %in% names(df)))
    return(list(lhs = pair[1], lag = pair[2]))
  list(lhs = y, lag = NULL)
}

# Focused, report-facing outcome panel: competition + composition + voter behaviour.
FOCUS_OUTCOMES <- c(
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_majority_2024_2020",
  "delta_runnerup_vote_share_2024_2020",
  "delta_female_vote_share_2024_2020",
  "delta_turnout_rate_2024_2020",
  "delta_blank_rate_2024_2020"
)
# ANCOVA-2016 LHS is the 2024 level (2016 level conditioned on), so no "$\\Delta$".
OUTCOME_LABELS <- c(
  delta_margin_top1_top2_2024_2020    = "Margin (W$-$RU)",
  delta_winner_majority_2024_2020     = "Winner majority",
  delta_runnerup_vote_share_2024_2020 = "Runner-up share",
  delta_female_vote_share_2024_2020   = "Female vote share",
  delta_turnout_rate_2024_2020        = "Turnout rate",
  delta_blank_rate_2024_2020          = "Blank vote rate"
)

avail <- function(controls, data) controls[controls %in% names(data)]


# ============================================================
# 3. ESTIMATION HELPERS
# ============================================================
# Common-sample IV so the four columns are strictly comparable per outcome.
make_sample <- function(outcome) {
  r <- resolve_lhs(outcome)
  req <- unique(c(INSTRUMENT, ENDOGENOUS, PLACEBO_IV, PLACEBO_ENDOG,
                  INTENSITY_CTRL, "cluster_id", FE_COL,
                  avail(c(BASELINE_CONTROLS, r$lag), df), r$lhs))
  req <- req[req %in% names(df)]
  s <- df[complete.cases(df[, req, drop = FALSE]), ]
  rownames(s) <- NULL
  s
}

iv_fit <- function(samp, outcome, extra_ctrls = character(0)) {
  r       <- resolve_lhs(outcome)
  ctrls   <- avail(c(BASELINE_CONTROLS, r$lag, extra_ctrls), samp)
  rhs     <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                            r$lhs, rhs, FE_COL, ENDOGENOUS, INSTRUMENT))
  fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  attr(fit, "mean_delta") <- mean(samp[[r$lhs]], na.rm = TRUE)
  fit
}

# OLS reduced form of an instrument on an outcome (placebo: should be null).
# Run on the SAME ANCOVA LHS (2024 level + 2016 lag control) as the headline.
rf_fit <- function(samp, outcome, instr) {
  r       <- resolve_lhs(outcome)
  ctrls   <- avail(c(BASELINE_CONTROLS, r$lag), samp)
  rhs     <- paste(c(instr, ctrls), collapse = " + ")
  fml <- as.formula(sprintf("%s ~ %s | %s", r$lhs, rhs, FE_COL))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

# First-stage OLS (any endogenous ~ any instrument), returns cluster-robust F = t^2.
fs_F <- function(samp, endog, instr, extra_ctrls = character(0)) {
  ctrls <- avail(c(BASELINE_CONTROLS, extra_ctrls), samp)
  rhs   <- paste(c(instr, ctrls), collapse = " + ")
  fml   <- as.formula(sprintf("%s ~ %s | %s", endog, rhs, FE_COL))
  fit   <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  unname(tstat(fit)[instr]^2)
}

ivcoef <- function(fit) {
  nm <- paste0("fit_", ENDOGENOUS)
  c(coef(fit)[nm], se(fit)[nm], tstat(fit)[nm], pvalue(fit)[nm])
}
rfcoef <- function(fit, instr) {
  c(coef(fit)[instr], se(fit)[instr], tstat(fit)[instr], pvalue(fit)[instr])
}


# ============================================================
# 4. RUN: per outcome, four estimates + diagnostics
# ============================================================
rows <- list()
# Model stores for etable
main_fits      <- list()   # main IV
intens_fits    <- list()   # + intensity control
plac_ctrl_fits <- list()   # + placebo control
plac_rf_fits   <- list()   # placebo reduced form (OLS)

for (y in FOCUS_OUTCOMES) {
  if (!(y %in% names(df))) { cat("  skip (absent):", y, "\n"); next }
  samp <- make_sample(y)
  n_obs <- nrow(samp); n_cl <- length(unique(samp$cluster_id))

  f_main   <- iv_fit(samp, y)
  f_intens <- iv_fit(samp, y, extra_ctrls = INTENSITY_CTRL)
  f_pctrl  <- iv_fit(samp, y, extra_ctrls = PLACEBO_IV)
  f_prf    <- rf_fit(samp, y, PLACEBO_IV)

  main_fits[[y]]      <- f_main
  intens_fits[[y]]    <- f_intens
  plac_ctrl_fits[[y]] <- f_pctrl
  plac_rf_fits[[y]]   <- f_prf

  Fmain   <- fs_F(samp, ENDOGENOUS, INSTRUMENT)
  Fintens <- fs_F(samp, ENDOGENOUS, INSTRUMENT, extra_ctrls = INTENSITY_CTRL)
  Fpctrl  <- fs_F(samp, ENDOGENOUS, INSTRUMENT, extra_ctrls = PLACEBO_IV)
  Fplac   <- fs_F(samp, PLACEBO_ENDOG, PLACEBO_IV)   # placebo instrument relevance

  cm <- ivcoef(f_main); ci <- ivcoef(f_intens); cc <- ivcoef(f_pctrl)
  cr <- rfcoef(f_prf, PLACEBO_IV)

  rows[[length(rows) + 1]] <- data.frame(
    outcome = y, nobs = n_obs, n_clusters = n_cl,
    mean_dep = mean(samp[[y]], na.rm = TRUE),
    main_coef = cm[1], main_se = cm[2], main_t = cm[3], main_p = cm[4], main_F = Fmain,
    intensity_coef = ci[1], intensity_se = ci[2], intensity_p = ci[4], intensity_F = Fintens,
    placebo_ctrl_coef = cc[1], placebo_ctrl_se = cc[2], placebo_ctrl_p = cc[4], placebo_ctrl_F = Fpctrl,
    placebo_rf_coef = cr[1], placebo_rf_se = cr[2], placebo_rf_t = cr[3], placebo_rf_p = cr[4],
    placebo_first_stage_F = Fplac,
    stringsAsFactors = FALSE
  )
  cat(sprintf("  %-44s main=% .4f (F=%.1f)  +intens=% .4f  +plac=% .4f  placeboRF=% .4f (p=%.3f)\n",
              y, cm[1], Fmain, ci[1], cc[1], cr[1], cr[4]))
}

res <- do.call(rbind, rows)
fwrite(res, file.path(ESTIMATES_DIR, "nonadversarial_placebo.csv"))
cat("\nSaved:", file.path(ESTIMATES_DIR, "nonadversarial_placebo.csv"), "\n")


# ============================================================
# 5. LaTeX FRAGMENTS  (table conventions: readable labels, mean row)
# ============================================================
ETABLE_SIGNIF <- c("**" = .01, "*" = .05, "\\dagger" = .10)
ETABLE_DICT <- c(
  "fit_delta_log1p_competition_lawsuits_2024_2020" = "$\\Delta$ Log(adversarial lawsuits)",
  "placebo_bartik_iv_2020_2024"                    = "Placebo Bartik (non-adv.)",
  "SG_UF" = "State (UF)", "cluster_id" = "state"
)
etab_base <- list(
  tex = TRUE, dict = c(ETABLE_DICT, OUTCOME_LABELS),
  signif.code = ETABLE_SIGNIF, digits = 3, digits.stats = 1,
  style.tex = style.tex(arraystretch = 1.2)
)
write_frag <- function(out, path, gen) {
  if (length(out) == 1L) out <- strsplit(out, "\n", fixed = TRUE)[[1]]
  i1 <- which(grepl("\\begin{tabular}", out, fixed = TRUE))
  i2 <- which(grepl("\\end{tabular}",   out, fixed = TRUE))
  frag <- if (length(i1) && length(i2)) out[i1[1L]:i2[length(i2)]] else out
  writeLines(c(paste0("% Auto-generated by ", gen),
               "% Do not edit manually -- rerun the generating script to update",
               "", frag), con = path)
  cat("  Wrote:", path, "\n")
}
mean_row <- function(mods)
  unname(vapply(mods, function(m) sprintf("%.3f", attr(m, "mean_delta")), character(1)))
label_mods <- function(store, keys, labels) {
  mods <- Filter(Negate(is.null), store[keys])
  setNames(mods, labels[names(mods)])
}

# ---- 5a. Placebo reduced form (cols = outcomes): the key generic-shares null ----
# OLS of each electoral outcome on the placebo (non-adversarial) Bartik. A null
# reduced form is the BHJ generic-shares evidence: exposure to mandatory/admin
# filing growth does NOT predict electoral change. (Discriminant-validity aside:
# the placebo's own first stage on non-adversarial growth is F ~ 0.3 -- the
# leave-state-out shift that powers the REAL instrument, F ~ 28, has no purchase
# on mandatory filings -- reported in nonadversarial_placebo.csv, not here, since
# this table is about outcomes, not relevance.)
{
  mods <- label_mods(plac_rf_fits, FOCUS_OUTCOMES, OUTCOME_LABELS)
  out <- do.call(etable, c(list(
    mods, keep = "Placebo Bartik", fitstat = ~ n + r2
  ), etab_base))
  write_frag(out, file.path(TEX_DIR, "nonadversarial_placebo_rf.tex"),
             "code/03_estimation/04_placebo_nonadversarial.R")
}

# ---- 5b. Main vs intensity-conditioned vs placebo-conditioned -------------------
# Hand-built so rows = outcomes, columns = the three IV specs + placebo RF, each a
# single coefficient. Shows the main estimate is unmoved and the placebo is null.
{
  star <- function(p) if (is.na(p)) "" else if (p < .01) "$^{**}$" else
                      if (p < .05) "$^{*}$" else if (p < .10) "$^{\\dagger}$" else ""
  cell <- function(b, se, p) sprintf("%.3f%s\\\\(%.3f)", b, star(p), se)
  lines <- c(
    "% Auto-generated by code/03_estimation/04_placebo_nonadversarial.R",
    "% Do not edit manually -- rerun the generating script to update",
    "",
    "\\begin{tabular}{lcccc}",
    "\\toprule",
    " & Main IV & + Non-adv. & + Placebo & Placebo \\\\",
    " & & intensity & Bartik ctrl & reduced form \\\\",
    "\\midrule"
  )
  for (y in FOCUS_OUTCOMES) {
    r <- res[res$outcome == y, ]
    if (nrow(r) == 0) next
    lab <- OUTCOME_LABELS[y]
    c1 <- cell(r$main_coef, r$main_se, r$main_p)
    c2 <- cell(r$intensity_coef, r$intensity_se, r$intensity_p)
    c3 <- cell(r$placebo_ctrl_coef, r$placebo_ctrl_se, r$placebo_ctrl_p)
    c4 <- cell(r$placebo_rf_coef, r$placebo_rf_se, r$placebo_rf_p)
    splitcell <- function(s) strsplit(s, "\\\\\\\\", perl = TRUE)[[1]]
    p1 <- splitcell(c1); p2 <- splitcell(c2); p3 <- splitcell(c3); p4 <- splitcell(c4)
    lines <- c(lines,
      sprintf("%s & %s & %s & %s & %s \\\\", lab, p1[1], p2[1], p3[1], p4[1]),
      sprintf(" & %s & %s & %s & %s \\\\[2pt]", p1[2], p2[2], p3[2], p4[2]))
  }
  Frow <- res[match(FOCUS_OUTCOMES, res$outcome), ]
  lines <- c(lines,
    "\\midrule",
    sprintf("First-stage $F$ & %s & & & \\\\",
            paste0(sprintf("%.1f", mean(Frow$main_F, na.rm = TRUE)))),
    sprintf("$N$ & %s & & & \\\\",
            formatC(max(Frow$nobs, na.rm = TRUE), format = "d", big.mark = ",")),
    "\\bottomrule",
    "\\end{tabular}")
  writeLines(lines, file.path(TEX_DIR, "nonadversarial_robustness.tex"))
  cat("  Wrote:", file.path(TEX_DIR, "nonadversarial_robustness.tex"), "\n")
}

cat("\nDone.\n")
