# 05_validation.R — headline-estimator validation (merged)
# ===========================================================================
# PURPOSE: the two checks that justify the ANCOVA-2016 headline (decision
# 2026-06-28). Two sections, each writing its own CSV:
#
#   [A] fd_vs_ancova()      — FD vs ANCOVA-2016 vs ANCOVA-2020: how the
#         baseline-conditioning choice moves the 2SLS effect.
#         -> regressions/fd_vs_ancova_comparison.csv
#
#   [B] ancova_validation() — falsification gate for ANCOVA-2016:
#         (1) pre-trend reduced form (Z must not predict the 2016->2020 change),
#         (2) non-adversarial placebo IV in ANCOVA form (should be null).
#         -> regressions/ancova_validation.csv
#
# All regression output in R/fixest (standing rule). The former Lord's-paradox
# diagnostic (13_lagged_dv_diagnostic.R) was dropped: its LDV verdict was
# REVERSED — the consolidation result survives the clean 2016 baseline, so the
# ANCOVA-2016 vs ANCOVA-2020 contrast in [A] carries what mattered.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ── paths ─────────────────────────────────────────────────────────────────────
args      <- commandArgs(trailingOnly = FALSE)
file_arg  <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else getwd()
ROOT        <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
DESIGN_PATH <- file.path(ROOT, "data", "estimation", "executive_margin_design.csv")
OUT_DIR     <- file.path(ROOT, "output", "tables", "regressions")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

# ── shared load ───────────────────────────────────────────────────────────────
df <- as.data.frame(fread(
  DESIGN_PATH,
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
# Match 02_iv_main.R: state -> SG_UF (FE), municipality_id_tse -> SG_UE
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]

INSTRUMENT        <- "bartik_iv_2020_2024"
ENDOGENOUS        <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL            <- "SG_UF"
BASELINE_CONTROLS <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
                       "higher_educ_share_2010", "log1p_total_valid_votes_2020",
                       "margin_2016")

avail    <- function(cols) cols[cols %in% names(df)]
ctrl_rhs <- paste(avail(BASELINE_CONTROLS), collapse = " + ")


# ============================================================================
# [A] FD vs ANCOVA-2016 vs ANCOVA-2020
# ----------------------------------------------------------------------------
# Three estimators of the SAME causal object (all IV, same instrument):
#   (1) FD          : (Y24 - Y20) ~ D + X | FE | D ~ Z   (baseline lag pinned to 1;
#                     assumption: parallel trends)
#   (2) ANCOVA-2016 : Y24 ~ D + Y16 + X | FE | D ~ Z      (lag free; clean PRE-window
#                     2016 baseline; assumption: selection on the 2016 level)
#   (3) ANCOVA-2020 : Y24 ~ D + Y20 + X | FE | D ~ Z      (lag free; 2020 baseline is
#                     contemporaneous with the instrument shares -> possible bad control)
# FD and ANCOVA bracket the true effect under opposite selection regimes (MHE ch. 5).
# ============================================================================
fd_vs_ancova <- function() {
  # stem -> (delta col, level stem, label, family)
  OUTCOMES <- list(
    list("delta_margin_top1_top2_2024_2020",   "margin_top1_top2",     "Margin (W-RU)",       "competition"),
    list("delta_winner_vote_share_2024_2020",  "winner_vote_share",    "Winner vote share",   "competition"),
    list("delta_runnerup_vote_share_2024_2020","runnerup_vote_share",  "Runner-up vote share","competition"),
    list("delta_winner_majority_2024_2020",    "winner_majority",      "Winner majority",     "competition"),
    list("delta_female_vote_share_2024_2020",  "female_vote_share",    "Female vote share",   "composition"),
    list("delta_winner_is_female_2024_2020",   "winner_is_female",     "Winner is female",    "composition"),
    list("delta_blank_rate_2024_2020",         "blank_rate",           "Blank rate (mayoral)","voter"),
    list("delta_null_rate_2024_2020",          "null_rate",            "Null rate (mayoral)", "voter"),
    list("delta_turnout_rate_2024_2020",       "turnout_rate",         "Turnout (any ballot)","voter")
  )

  iv_cell <- function(samp, y, extra_ctrl = NULL) {
    rhs <- if (is.null(extra_ctrl)) ctrl_rhs else paste(extra_ctrl, ctrl_rhs, sep = " + ")
    fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                              y, rhs, FE_COL, ENDOGENOUS, INSTRUMENT))
    fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    iv_name <- paste0("fit_", ENDOGENOUS)
    Fstat <- tryCatch(fitstat(fit, "ivf")[[1]]$stat, error = function(e) NA_real_)
    lag_g <- if (!is.null(extra_ctrl) && extra_ctrl %in% names(coef(fit)))
               unname(coef(fit)[extra_ctrl]) else NA_real_
    list(coef = unname(coef(fit)[iv_name]), se = unname(se(fit)[iv_name]),
         p = unname(pvalue(fit)[iv_name]), F = Fstat, lag_gamma = lag_g, n = nobs(fit))
  }

  rows <- list()
  for (o in OUTCOMES) {
    dcol <- o[[1]]; stem <- o[[2]]; lab <- o[[3]]; fam <- o[[4]]
    y24 <- paste0(stem, "_2024"); y20 <- paste0(stem, "_2020"); y16 <- paste0(stem, "_2016")

    if (!(y24 %in% names(df)) && dcol %in% names(df) && y20 %in% names(df))
      df[[y24]] <- df[[y20]] + df[[dcol]]

    has16 <- y16 %in% names(df); has24 <- y24 %in% names(df); has20 <- y20 %in% names(df)

    needed <- avail(c(INSTRUMENT, ENDOGENOUS, "cluster_id", FE_COL,
                      BASELINE_CONTROLS, dcol, y24, y20, if (has16) y16))
    samp <- df[complete.cases(df[, needed, drop = FALSE]), ]

    fd  <- if (dcol %in% names(samp)) iv_cell(samp, dcol) else NULL
    v3  <- if (has16) iv_cell(samp, dcol, y16) else NULL
    a16 <- if (has16 && has24) iv_cell(samp, y24, y16) else NULL
    a20 <- if (has20 && has24) iv_cell(samp, y24, y20) else NULL

    for (sp in list(list("FD", fd), list("FD+2016_V3", v3),
                    list("ANCOVA_2016", a16), list("ANCOVA_2020", a20))) {
      if (is.null(sp[[2]])) next
      c2 <- sp[[2]]
      rows[[length(rows) + 1]] <- data.frame(
        outcome = lab, family = fam, estimator = sp[[1]],
        coef = c2$coef, se = c2$se, p = c2$p,
        first_stage_F = c2$F, lag_gamma = c2$lag_gamma, nobs = c2$n,
        stringsAsFactors = FALSE)
    }
  }

  res <- do.call(rbind, rows)
  res$sig <- ifelse(res$p < .01, "***", ifelse(res$p < .05, "**",
              ifelse(res$p < .10, "*", "")))
  out_csv <- file.path(OUT_DIR, "fd_vs_ancova_comparison.csv")
  fwrite(res, out_csv)

  cat("\n=== FD vs ANCOVA-2016 vs ANCOVA-2020 (2SLS treatment effect) ===\n\n")
  for (lab in unique(res$outcome)) {
    cat(sprintf("%-22s\n", lab))
    sub <- res[res$outcome == lab, ]
    for (i in seq_len(nrow(sub))) {
      g <- sub[i, ]
      cat(sprintf("   %-12s  beta=%+.4f%-3s (se %.4f, p=%.3f)  F=%5.1f  lag.gamma=%s\n",
                  g$estimator, g$coef, g$sig, g$se, g$p, g$first_stage_F,
                  ifelse(is.na(g$lag_gamma), "  --  ", sprintf("%+.3f", g$lag_gamma))))
    }
    cat("\n")
  }
  cat(sprintf("Saved: %s\n", out_csv))
}


# ============================================================================
# [B] ANCOVA-2016 VALIDATION GATE
# ----------------------------------------------------------------------------
#   TEST 1 - pre-trend falsification: reduced form pretrend_y_2020_2016 ~ Z + X | FE.
#            A significant Z means exposure shares track pre-existing trends.
#   TEST 2 - non-adversarial placebo IV in ANCOVA-2016 form: a Bartik over the
#            EXCLUDED (mandatory/administrative) filings should give a null 2SLS.
# PASS = both checks null for every outcome.
# ============================================================================
ancova_validation <- function() {
  PLACEBO_INSTR <- "placebo_bartik_iv_2020_2024"
  PLACEBO_ENDOG <- "delta_log1p_nonadversarial_lawsuits_2024_2020"

  OUTCOMES <- list(
    list("margin_top1_top2",    "Margin (W-RU)",        "competition"),
    list("winner_vote_share",   "Winner vote share",    "competition"),
    list("runnerup_vote_share", "Runner-up vote share", "competition"),
    list("winner_majority",     "Winner majority",      "competition"),
    list("female_vote_share",   "Female vote share",    "composition"),
    list("winner_is_female",    "Winner is female",     "composition"),
    list("blank_rate",          "Blank rate (mayoral)", "voter"),
    list("null_rate",           "Null rate (mayoral)",  "voter"),
    list("turnout_rate",        "Turnout (any ballot)", "voter")
  )

  # The pre-trend LHS is a 2020-2016 change, already netting out the 2016 level.
  # margin_2016 is the competition outcomes' OWN 2016 level; conditioning on it
  # inside a pre-trend RF mechanically manufactures correlation with Z. Drop it.
  PRETREND_CONTROLS <- setdiff(BASELINE_CONTROLS, "margin_2016")
  pretrend_ctrl_rhs <- paste(avail(PRETREND_CONTROLS), collapse = " + ")

  rf_cell <- function(samp, y, z) {
    fml <- as.formula(sprintf("%s ~ %s + %s | %s", y, z, pretrend_ctrl_rhs, FE_COL))
    fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    list(coef = unname(coef(fit)[z]), se = unname(se(fit)[z]),
         p = unname(pvalue(fit)[z]), n = nobs(fit))
  }
  iv_cell <- function(samp, y, lag, d, z) {
    rhs <- paste(lag, ctrl_rhs, sep = " + ")
    fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s", y, rhs, FE_COL, d, z))
    fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    iv_name <- paste0("fit_", d)
    F <- tryCatch(fitstat(fit, "ivf")[[1]]$stat, error = function(e) NA_real_)
    list(coef = unname(coef(fit)[iv_name]), se = unname(se(fit)[iv_name]),
         p = unname(pvalue(fit)[iv_name]), F = F, n = nobs(fit))
  }

  rows <- list()
  for (o in OUTCOMES) {
    stem <- o[[1]]; lab <- o[[2]]; fam <- o[[3]]
    y24 <- paste0(stem, "_2024"); y16 <- paste0(stem, "_2016")
    d20 <- paste0(stem, "_2020"); dcol <- paste0("delta_", stem, "_2024_2020")
    ptr <- paste0("pretrend_", stem, "_2020_2016")

    if (!(y24 %in% names(df)) && dcol %in% names(df) && d20 %in% names(df))
      df[[y24]] <- df[[d20]] + df[[dcol]]

    needed <- avail(c(INSTRUMENT, ENDOGENOUS, PLACEBO_INSTR, PLACEBO_ENDOG,
                      "cluster_id", FE_COL, BASELINE_CONTROLS, y24, y16, ptr))
    samp <- df[complete.cases(df[, needed, drop = FALSE]), ]

    if (ptr %in% names(samp)) {
      t1 <- rf_cell(samp, ptr, INSTRUMENT)
      rows[[length(rows) + 1]] <- data.frame(
        outcome = lab, family = fam, test = "pretrend_RF",
        coef = t1$coef, se = t1$se, p = t1$p, F = NA_real_, nobs = t1$n,
        stringsAsFactors = FALSE)
    }
    if (all(c(y24, y16, PLACEBO_INSTR, PLACEBO_ENDOG) %in% names(samp))) {
      t2 <- iv_cell(samp, y24, y16, PLACEBO_ENDOG, PLACEBO_INSTR)
      rows[[length(rows) + 1]] <- data.frame(
        outcome = lab, family = fam, test = "placebo_ANCOVA2016",
        coef = t2$coef, se = t2$se, p = t2$p, F = t2$F, nobs = t2$n,
        stringsAsFactors = FALSE)
    }
  }

  res <- do.call(rbind, rows)
  res$sig <- ifelse(res$p < .01, "***", ifelse(res$p < .05, "**",
              ifelse(res$p < .10, "*", "")))
  out_csv <- file.path(OUT_DIR, "ancova_validation.csv")
  fwrite(res, out_csv)

  cat("\n=== ANCOVA-2016 validation ===\n")
  cat("PASS = both checks NULL (instrument does not predict pre-trend;",
      "placebo IV insignificant)\n\n")
  for (lab in unique(res$outcome)) {
    sub <- res[res$outcome == lab, ]
    cat(sprintf("%-22s\n", lab))
    for (i in seq_len(nrow(sub))) {
      g <- sub[i, ]
      cat(sprintf("   %-20s beta=%+.4f%-3s (se %.4f, p=%.3f)%s\n",
                  g$test, g$coef, g$sig, g$se, g$p,
                  ifelse(is.na(g$F), "", sprintf("  F=%.1f", g$F))))
    }
  }
  flag <- res[res$p < .10, ]
  cat("\n", if (nrow(flag) == 0) "ALL CLEAR: no pre-trend or placebo flags at 10%.\n"
          else sprintf("FLAGS (%d at p<.10): %s\n", nrow(flag),
                       paste(unique(paste0(flag$outcome, "[", flag$test, "]")),
                             collapse = "; ")), sep = "")
  cat(sprintf("\nSaved: %s\n", out_csv))
}

fd_vs_ancova()
ancova_validation()
