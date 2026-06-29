# ============================================================
# 15_ancova_validation.R
# Validation gate for the ANCOVA-2016 headline (decision 2026-06-28).
#
# Before adopting ANCOVA-2016 (Y_2024 ~ D + Y_2016 + X | FE | D ~ Z) as the
# headline, two falsification checks must pass, BOTH run in the ANCOVA form so
# they speak to the spec we actually intend to report:
#
#   TEST 1 - Pre-trend falsification (the ANCOVA-relevant balance test).
#     The instrument is a 2020->2024 shock. It must NOT predict the PRE-window
#     2016->2020 change in the outcome. We run the reduced form
#         pretrend_y_2020_2016 ~ Z + X | FE
#     and read the coefficient on Z. A significant Z means the exposure shares
#     track pre-existing outcome trends -> ANCOVA's selection-on-baseline
#     assumption is unsafe. (Available for every outcome with a 2016 level,
#     which - after adding detalhe_votacao_munzona_2016 - now includes the
#     voter outcomes.)
#
#   TEST 2 - Non-adversarial placebo IV, ANCOVA form.
#     A Bartik built over the EXCLUDED (mandatory/administrative) filings, with
#     its own endogenous non-adversarial filing growth, plugged into the SAME
#     ANCOVA outcome equation. Its 2SLS coefficient should be null. A
#     significant placebo would indicate generic exposure shares rather than the
#     adversarial-litigation channel.
#
# All regression output in R/fixest (standing rule). Output:
#   output/tables/regressions/ancova_validation.csv
# ============================================================

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

PROJECT_ROOT <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
DESIGN_PATH  <- file.path(PROJECT_ROOT, "data", "estimation",
                          "executive_margin_design.csv")
OUT_DIR      <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

df <- as.data.frame(fread(
  DESIGN_PATH,
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]

INSTRUMENT       <- "bartik_iv_2020_2024"
ENDOGENOUS       <- "delta_log1p_competition_lawsuits_2024_2020"
PLACEBO_INSTR    <- "placebo_bartik_iv_2020_2024"
PLACEBO_ENDOG    <- "delta_log1p_nonadversarial_lawsuits_2024_2020"
FE_COL           <- "SG_UF"
BASELINE_CONTROLS <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
                       "higher_educ_share_2010", "log1p_total_valid_votes_2020",
                       "margin_2016")

# stem -> (2024 level, 2016 level, pretrend col, label, family)
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

avail    <- function(cols) cols[cols %in% names(df)]
ctrl_rhs <- paste(avail(BASELINE_CONTROLS), collapse = " + ")
# The pre-trend LHS is a 2020-2016 change, so it already nets out the 2016
# level. margin_2016 is (up to definition) the competition outcomes' OWN 2016
# level; conditioning on it inside a pre-trend RF mechanically manufactures a
# correlation with Z. Drop it from the pre-trend test (keep the predetermined
# 2010 structure + 2020 electorate scale).
PRETREND_CONTROLS <- setdiff(BASELINE_CONTROLS, "margin_2016")
pretrend_ctrl_rhs <- paste(avail(PRETREND_CONTROLS), collapse = " + ")

# Reduced form of a left-hand variable on an instrument (OLS, no first stage).
rf_cell <- function(samp, y, z) {
  fml <- as.formula(sprintf("%s ~ %s + %s | %s", y, z, pretrend_ctrl_rhs, FE_COL))
  fit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  list(coef = unname(coef(fit)[z]), se = unname(se(fit)[z]),
       p = unname(pvalue(fit)[z]), n = nobs(fit))
}

# 2SLS cell: y ~ lag + X | FE | d ~ z
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

  # Reconstruct 2024 level if only delta + 2020 stored.
  if (!(y24 %in% names(df)) && dcol %in% names(df) && d20 %in% names(df))
    df[[y24]] <- df[[d20]] + df[[dcol]]

  needed <- avail(c(INSTRUMENT, ENDOGENOUS, PLACEBO_INSTR, PLACEBO_ENDOG,
                    "cluster_id", FE_COL, BASELINE_CONTROLS, y24, y16, ptr))
  samp <- df[complete.cases(df[, needed, drop = FALSE]), ]

  # TEST 1: pre-trend reduced form (real instrument)
  if (ptr %in% names(samp)) {
    t1 <- rf_cell(samp, ptr, INSTRUMENT)
    rows[[length(rows) + 1]] <- data.frame(
      outcome = lab, family = fam, test = "pretrend_RF",
      coef = t1$coef, se = t1$se, p = t1$p, F = NA_real_, nobs = t1$n,
      stringsAsFactors = FALSE)
  }
  # TEST 2: non-adversarial placebo IV, ANCOVA-2016 form
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
fwrite(res, file.path(OUT_DIR, "ancova_validation.csv"))

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
cat(sprintf("\nSaved: %s\n", file.path(OUT_DIR, "ancova_validation.csv")))
