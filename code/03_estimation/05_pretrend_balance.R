# ============================================================
# 05_pretrend_balance.R  —  Instrument pre-trend / balance falsification
# ------------------------------------------------------------
# Standalone diagnostic (deliberately NOT in 02_iv_main.R). Asks a single
# question the headline design cannot answer on its own:
#
#   Does the shift-share instrument load on municipalities that were ALREADY
#   moving — in the outcome direction — BEFORE treatment could operate?
#
# Data structure. We have essentially a CROSS-SECTION with two usable
# differences per municipality: a PRE difference (2016->2020) and a TREATMENT
# difference (2020->2024). Lawsuit microdata exist only for 2020 and 2024 (the
# 2016 panel is missing), so we CANNOT build a lagged instrument and CANNOT
# trace a dynamic event-study of leads. The only falsification the data admit
# is therefore a SINGLE pre-period placebo: regress the observed 2016->2020
# outcome change on the SAME instrument that drives the 2020->2024 treatment.
# A clean, share-exogenous design wants this ~ 0 — the shock should not predict
# a change that predates it. This is a placebo-in-time / GP share-balance test,
# not a panel parallel-trends test; the comment stays honest about that.
#
# ------------------------------------------------------------
# CONTROL SET (the whole point of the 2026-07-01 rewrite).
# The balance test conditions ONLY on strictly PRE-DETERMINED covariates —
# the 2010 Census structure (population, urbanisation, income p.c., schooling).
# These predate the 2016->2020 pre-window entirely, so partialling them out
# cannot manufacture or mask a pre-trend.
#
# It deliberately DROPS the two controls the headline set carries that are NOT
# admissible in a balance test on a 2016->2020 change:
#   * margin_2016             — the 2016 BASELINE of the consolidation ladder.
#       Conditioning on it while the LHS is (margin_2020 - margin_2016) is
#       Lord's-paradox / regression-to-the-mean: it MANUFACTURES a pre-trend.
#       (Diagnosed 2026-07-01: with margin_2016 in the set, margin balance
#        p=.019; without it, p=.94. The "pre-trend" was the control.)
#   * log1p_total_valid_votes_2020 — a 2020 (END-of-pre-window) quantity, and
#       mechanically tied to valid_vote_rate_2020, itself part of some LHS.
# The FULL headline set is retained as a SENSITIVITY column (rf_full_*), printed
# side-by-side in the CSV precisely to document that dropping margin_2016 is what
# clears the apparent pre-trend. This mirrors 02_iv_main's own control philosophy
# (it already excludes 2020 competition LEVELS as Lord's-paradox territory).
#
# Two estimators, reported side by side:
#   (RF)  Reduced form / balance:  dY_pre ~ Z + X_predet | UF        [PRIMARY]
#         The transparent object: is the instrument Z correlated with the
#         pre-period trend, conditional on predetermined covariates + state FE?
#         This is exactly the shares-exogeneity check a shift-share referee
#         wants (Goldsmith-Pinkham et al. 2020), stated in instrument units.
#   (PL)  2SLS placebo:  dY_pre ~ X_predet | UF | D ~ Z
#         The instrumented-treatment version. In a just-identified design its
#         t-stat (hence p-value) EQUALS the RF t-stat on Z up to finite-sample
#         cluster scaling — the Wald ratio only rescales the point estimate.
#         Reported so the two are visibly the same test; RF is the one to read.
#
# Coverage EXTENDS the 02_iv_main table (which covered only the 4 consolidation
# outcomes) to the VOTER-DISENGAGEMENT outcomes (blank / null / valid, mayoral
# AND council) and a few composition placebos.
#
# All pretrend_* columns are PRECOMPUTED in the estimation design
# (dY_pre = Y_2020 - Y_2016), so no data construction happens here.
#
# Outputs:
#   output/tables/regressions/pretrend_balance.csv      (all outcomes, RF predet + RF full + PL)
#   output/figures/pretrend_coefplot.pdf        (standardized balance coefplot)
# ============================================================

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
  library(ggplot2)
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
REG_DIR        <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
FIG_DIR        <- file.path(PROJECT_ROOT, "output", "figures")
dir.create(REG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

# shared palette + theme (matches the deck; blanks title/subtitle/caption)
UTILS <- file.path(PROJECT_ROOT, "code", "utils")
source(file.path(UTILS, "figure_style.R"))   # PAL, theme_report()

# ============================================================
# 1. LOAD  (mirror 02_iv_main's load + rename so specs match exactly)
# ============================================================
df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
if ("state" %in% names(df)) names(df)[names(df) == "state"] <- "SG_UF"

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "SG_UF"

# PRIMARY: strictly pre-determined (2010 Census) covariates only.
PREDET_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010"
)
# SENSITIVITY: the full headline set (adds the two inadmissible controls). Used
# ONLY to document that margin_2016 is what conjures the apparent pre-trend.
FULL_CONTROLS <- c(
  PREDET_CONTROLS, "log1p_total_valid_votes_2020", "margin_2016"
)
avail <- function(v, data) v[v %in% names(data)]

# ---- outcome dictionary: precomputed pretrend column -> readable label ----
CONSOL <- c(
  pretrend_margin_top1_top2_2020_2016            = "Margin (W$-$RU)",
  pretrend_effective_n_candidates_vote_2020_2016 = "Eff.\\ N cand.",
  pretrend_vote_hhi_candidate_2020_2016          = "Vote HHI",
  pretrend_top2_vote_share_2020_2016             = "Top-2 share"
)
VOTERB <- c(
  pretrend_blank_rate_2020_2016                  = "Blank (may.)",
  pretrend_null_rate_2020_2016                   = "Null (may.)",
  pretrend_valid_vote_rate_2020_2016             = "Valid (may.)",
  pretrend_blank_rate_vereador_2020_2016         = "Blank (counc.)",
  pretrend_null_rate_vereador_2020_2016          = "Null (counc.)",
  pretrend_valid_vote_rate_vereador_2020_2016    = "Valid (counc.)"
)
# turnout is the ONE genuine pre-trend survivor -> promote it into the tabled set
# so the caveat is visible, not buried among the "extra" placebos.
TURN <- c(
  pretrend_turnout_rate_2020_2016                = "Turnout"
)
EXTRA <- c(
  pretrend_female_vote_share_2020_2016           = "Female vote share",
  pretrend_nonwhite_vote_share_2020_2016         = "Non-white vote share",
  pretrend_winner_is_female_2020_2016            = "Winner is female"
)
ALL_LAB <- c(CONSOL, VOTERB, TURN, EXTRA)

# ============================================================
# 2. COMMON SAMPLE  (complete cases on instrument + endog + FULL controls + FE + cluster)
#    Sample is fixed across control sets (uses FULL so predet & full compare on
#    identical rows), then further restricted to non-missing on each outcome.
# ============================================================
fctrls <- avail(FULL_CONTROLS, df)
pctrls <- avail(PREDET_CONTROLS, df)
req    <- c(INSTRUMENT, ENDOGENOUS, "cluster_id", FE_COL, fctrls)
base   <- df[complete.cases(df[, req, drop = FALSE]), ]
cat(sprintf("Base sample: N=%d, clusters=%d\n",
            nrow(base), length(unique(base$cluster_id))))
cat("Predetermined controls (PRIMARY):", paste(pctrls, collapse = ", "), "\n")
cat("Full controls (sensitivity)     :", paste(fctrls, collapse = ", "), "\n\n")

p_rhs <- if (length(pctrls) > 0) paste(pctrls, collapse = " + ") else "1"
f_rhs <- if (length(fctrls) > 0) paste(fctrls, collapse = " + ") else "1"

# ---- estimators ----------------------------------------------------------
# RF: reduced form of the instrument on the pre-period change (balance test).
fit_rf <- function(y, data, rhs) {
  fml <- as.formula(sprintf("%s ~ %s + %s | %s", y, INSTRUMENT, rhs, FE_COL))
  feols(fml, data = data, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}
# PL: 2SLS placebo — instrument the (future) treatment, regress the past change.
fit_pl <- function(y, data, rhs) {
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                            y, rhs, FE_COL, ENDOGENOUS, INSTRUMENT))
  feols(fml, data = data, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}
# Standardized balance beta (for the coefplot): SD of pre-change per SD of Z,
# predetermined controls partialled out, state FE. Comparable across outcomes.
fit_std <- function(y, data) {
  d <- data
  d[["._y"]] <- as.numeric(scale(d[[y]]))
  d[["._z"]] <- as.numeric(scale(d[[INSTRUMENT]]))
  fml <- as.formula(sprintf("._y ~ ._z + %s | %s", p_rhs, FE_COL))
  feols(fml, data = d, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

# ============================================================
# 3. RUN  (RF predet [primary] + RF full [sensitivity] + PL predet, per outcome)
# ============================================================
rows   <- list()
rf_fit <- list()   # predetermined-control RF fits, for the tex tables
std_fit <- list()  # standardized fits, for the coefplot
for (y in names(ALL_LAB)) {
  if (!(y %in% names(base))) { cat("  skip (absent):", y, "\n"); next }
  d  <- base[!is.na(base[[y]]), ]
  if (nrow(d) < 50L) { cat("  skip (n<50):", y, "\n"); next }

  mrf  <- fit_rf(y, d, p_rhs)   # PRIMARY (predetermined)
  mrff <- fit_rf(y, d, f_rhs)   # SENSITIVITY (full headline set)
  mpl  <- fit_pl(y, d, p_rhs)
  rf_fit[[y]]  <- mrf
  std_fit[[y]] <- fit_std(y, d)

  z_b  <- coef(mrf)[INSTRUMENT];  z_se <- se(mrf)[INSTRUMENT]
  z_t  <- tstat(mrf)[INSTRUMENT]; z_p  <- pvalue(mrf)[INSTRUMENT]
  zf_b <- coef(mrff)[INSTRUMENT]; zf_p <- pvalue(mrff)[INSTRUMENT]
  pl_k <- grep("^fit_", names(coef(mpl)))[1L]
  pl_b <- coef(mpl)[pl_k];  pl_se <- se(mpl)[pl_k]; pl_p <- pvalue(mpl)[pl_k]

  rows[[length(rows) + 1]] <- data.frame(
    outcome        = y,
    label          = ALL_LAB[[y]],
    group          = if (y %in% names(CONSOL)) "consolidation"
                     else if (y %in% names(VOTERB)) "voter_behavior"
                     else if (y %in% names(TURN))   "turnout" else "other",
    nobs           = nobs(mrf),
    n_clusters     = length(unique(d$cluster_id)),
    pretrend_mean  = mean(d[[y]], na.rm = TRUE),
    # PRIMARY: predetermined-control reduced-form balance on Z
    rf_coef_on_Z   = unname(z_b),
    rf_se          = unname(z_se),
    rf_t           = unname(z_t),
    rf_p           = unname(z_p),
    # SENSITIVITY: full-headline-control reduced form (documents the artifact)
    rf_full_coef   = unname(zf_b),
    rf_full_p      = unname(zf_p),
    # 2SLS placebo (predetermined controls)
    placebo2sls_coef = unname(pl_b),
    placebo2sls_se   = unname(pl_se),
    placebo2sls_p    = unname(pl_p),
    stringsAsFactors = FALSE
  )
  cat(sprintf("  %-46s  RF predet b(Z)=%+.4f (p=%.3f)   [full-ctrl p=%.3f]\n",
              y, z_b, z_p, zf_p))
}
res <- do.call(rbind, rows)
csv_path <- file.path(REG_DIR, "pretrend_balance.csv")
write.csv(res, csv_path, row.names = FALSE)
cat("\nWrote:", csv_path, "\n")

# verdict to the console — the whole reason for the exercise
cat("\n---- Verdict (RF balance on Z, predetermined controls, cluster-robust p) ----\n")
verdict <- function(g) {
  s <- res[res$group == g, ]
  for (i in seq_len(nrow(s)))
    cat(sprintf("  [%-13s] %-16s b(Z)=%+.4f  p=%.3f  %s\n",
                g, s$label[i], s$rf_coef_on_Z[i], s$rf_p[i],
                ifelse(s$rf_p[i] < .10, "<-- PRE-TREND", "clean")))
}
verdict("consolidation"); verdict("voter_behavior"); verdict("turnout")

# ============================================================
# 5. BALANCE COEFPLOT  (standardized beta of Z on each pre-period change)
#    One dot per outcome, 95% CI, zero line. Predetermined controls, state FE.
#    A clean design has every interval straddling zero. Outcomes that DO trend
#    (turnout) are highlighted so the one honest caveat is visible.
# ============================================================
# colors from the shared palette (never ad-hoc hex); title/footnote go on the frame
COL_BLUE <- unname(PAL["blue"]); COL_GRAY <- unname(PAL["gray"]); COL_RED <- unname(PAL["red"])

# assemble standardized coefs in a fixed, readable order (group blocks; turnout last)
PLOT_ORDER <- c(names(CONSOL), names(VOTERB), names(TURN))
pd <- do.call(rbind, lapply(PLOT_ORDER, function(k) {
  if (is.null(std_fit[[k]])) return(NULL)
  m <- std_fit[[k]]
  b <- coef(m)["._z"]; s <- se(m)["._z"]; p <- pvalue(m)["._z"]
  data.frame(outcome = k,
             lab = ALL_LAB[[k]],
             group = if (k %in% names(CONSOL)) "Consolidation ladder"
                     else if (k %in% names(TURN)) "Turnout"
                     else "Ballot composition",
             beta = unname(b), se = unname(s), p = unname(p),
             stringsAsFactors = FALSE)
}))
# strip LaTeX escapes from labels for the figure axis
pd$lab <- gsub("\\\\ ", " ", pd$lab); pd$lab <- gsub("\\$-\\$", "-", pd$lab)
pd$lab <- factor(pd$lab, levels = rev(pd$lab))
pd$group <- factor(pd$group, levels = c("Consolidation ladder", "Ballot composition", "Turnout"))
pd$sig <- pd$p < 0.05
pd$lo95 <- pd$beta - qnorm(0.975) * pd$se
pd$hi95 <- pd$beta + qnorm(0.975) * pd$se
pd$lo90 <- pd$beta - qnorm(0.95)  * pd$se
pd$hi90 <- pd$beta + qnorm(0.95)  * pd$se

p_bal <- ggplot(pd, aes(x = beta, y = lab)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
  geom_errorbarh(aes(xmin = lo95, xmax = hi95), height = 0,
                 color = COL_GRAY, linewidth = 0.6, alpha = 0.6) +
  geom_errorbarh(aes(xmin = lo90, xmax = hi90, color = sig), height = 0, linewidth = 1.4) +
  geom_point(aes(color = sig), size = 3.1) +
  scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE), guide = "none") +
  facet_grid(group ~ ., scales = "free_y", space = "free_y", switch = "y") +
  labs(x = "Standardized balance coefficient (SD of 2016-2020 change per SD of Z)",
       y = NULL) +
  theme_report() +
  theme(panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank(),
        axis.text.y = element_text(size = 10),
        strip.placement = "outside",
        strip.text.y.left = element_text(angle = 0, face = "bold", size = 9, color = "grey25"),
        panel.spacing.y = unit(6, "pt"))

fig_path <- file.path(FIG_DIR, "pretrend_coefplot.pdf")
ggsave(fig_path, p_bal, width = 8, height = 4.4)
cat("  Saved:", fig_path, "\n")

cat("\nDone.\n")
