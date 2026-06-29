# ============================================================
# 14_fd_vs_ancova.R
# FD vs ANCOVA-2016 vs ANCOVA-2020: how the baseline-conditioning
# choice moves the 2SLS treatment effect, and what each implies for
# identification.
#
# Three estimators of the SAME causal object (all IV, same instrument):
#   (1) FD            : (Y24 - Y20) ~ D + X | FE | D ~ Z
#                       baseline lag coefficient CONSTRAINED to 1.
#                       Identifying assumption: parallel trends.
#   (2) ANCOVA-2016   : Y24 ~ D + Y16 + X | FE | D ~ Z
#                       lag coefficient FREE; baseline = clean PRE-window
#                       (2016) level, measured before the 2020 instrument
#                       shares. Assumption: selection on the 2016 level.
#   (3) ANCOVA-2020   : Y24 ~ D + Y20 + X | FE | D ~ Z
#                       lag coefficient FREE; baseline = 2020 level, which
#                       is CONTEMPORANEOUS with the instrument's 2020 shares
#                       -> potential bad control. Assumption: selection on
#                       the 2020 level (the Lord's-paradox / LDV spec).
#
# Note the algebra: FD == "(Y24-Y20) ~ D + Y20" with the Y20 coefficient
# pinned to 1; ANCOVA frees that coefficient. So beta(FD) and beta(ANCOVA)
# differ exactly by how the data want to weight the baseline (gamma). FD and
# ANCOVA bracket the true effect under opposite selection regimes
# (Angrist-Pischke, MHE ch. 5).
# ============================================================

suppressMessages({
  library(fixest)
  library(data.table)
})

PROJECT_ROOT <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"

DESIGN_PATH <- file.path(PROJECT_ROOT, "data", "estimation",
                         "executive_margin_design.csv")
OUT_DIR     <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

df <- as.data.frame(fread(
  DESIGN_PATH,
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
# Match 02_iv_main.R: state -> SG_UF (FE), municipality_id_tse -> SG_UE
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "SG_UF"
BASELINE_CONTROLS <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
                       "higher_educ_share_2010", "log1p_total_valid_votes_2020",
                       "margin_2016")

# Outcome registry: stem -> (delta col, 2024 level, 2020 level, 2016 level|NA, label, family)
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

avail <- function(cols) cols[cols %in% names(df)]
ctrl_rhs <- paste(avail(BASELINE_CONTROLS), collapse = " + ")

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
       p = unname(pvalue(fit)[iv_name]), F = Fstat, lag_gamma = lag_g,
       n = nobs(fit))
}

rows <- list()
for (o in OUTCOMES) {
  dcol <- o[[1]]; stem <- o[[2]]; lab <- o[[3]]; fam <- o[[4]]
  y24 <- paste0(stem, "_2024"); y20 <- paste0(stem, "_2020"); y16 <- paste0(stem, "_2016")

  # Reconstruct the 2024 level where only the delta + 2020 level are stored.
  if (!(y24 %in% names(df)) && dcol %in% names(df) && y20 %in% names(df))
    df[[y24]] <- df[[y20]] + df[[dcol]]

  has16 <- y16 %in% names(df)
  has24 <- y24 %in% names(df)
  has20 <- y20 %in% names(df)

  # Common estimation sample: rows complete on everything any spec needs.
  needed <- avail(c(INSTRUMENT, ENDOGENOUS, "cluster_id", FE_COL,
                    BASELINE_CONTROLS, dcol, y24, y20, if (has16) y16))
  samp <- df[complete.cases(df[, needed, drop = FALSE]), ]

  fd  <- if (dcol %in% names(samp)) iv_cell(samp, dcol) else NULL
  # Current "V3 baseline" form: Delta outcome + 2016 control. Algebraically
  # Y24 ~ D + 1*Y20 + Y16, i.e. FD's pinned-to-1 backbone PLUS a 2016 shift.
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
      stringsAsFactors = FALSE
    )
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
