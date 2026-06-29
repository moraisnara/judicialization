# ============================================================
# Lagged-dependent-variable diagnostic for the headline competition result.
#
# The universal baseline control set includes two 2020 *levels* of competition
# outcomes (margin_top1_top2_2020, log1p_total_candidates_2020). Because the
# headline outcomes are 2024-2020 *changes* of those same quantities, including
# their 2020 base level on the RHS is Lord's-paradox territory (the base level
# is mechanically inside the change). This script asks whether the consolidation
# finding survives three control stances:
#
#   V1 current        : 7 baseline controls (incl. the two 2020 levels)
#   V2 drop 2020 lvls : remove margin_top1_top2_2020 + log1p_total_candidates_2020
#   V3 2016 per-outcome lag : V2 + each outcome's OWN 2016 level (pre-window, no
#                             Lord bias) -- the principled lagged-DV frame 3 promised
#
# Read-only: does NOT alter the committed spec. Writes a comparison table.
# ============================================================

suppressMessages({
  library(fixest)
  library(data.table)
})

PROJECT_ROOT <- getwd()
if (!dir.exists(file.path(PROJECT_ROOT, "data")))
  stop("Run this script from the project root (judicialization/).")
DESIGN_PATH <- file.path(PROJECT_ROOT, "data", "estimation", "executive_margin_design.csv")
OUT_DIR     <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "state"        # state (UF); main script renames this to SG_UF
CLUSTER    <- "cluster_id"

NONCOMP <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
             "log1p_total_valid_votes_2020")
LEVELS_2020 <- c("margin_top1_top2_2020", "log1p_total_candidates_2020")

# Headline consolidation outcomes -> their own 2016 pre-window level
HEADLINE <- list(
  delta_winner_vote_share_2024_2020   = "winner_vote_share_2016",
  delta_runnerup_vote_share_2024_2020 = "runnerup_vote_share_2016",
  delta_margin_top1_top2_2024_2020    = "margin_top1_top2_2016",
  delta_top2_vote_share_2024_2020     = "top2_vote_share_2016"
)

df <- as.data.frame(fread(DESIGN_PATH))
if (!(CLUSTER %in% names(df))) df[[CLUSTER]] <- df[[FE_COL]]

# Lee et al. (2022) tF critical-value lookup (5% level), abbreviated table.
tf_tab <- data.frame(
  F  = c(0, 4.00, 4.63, 5.00, 6.00, 8.00, 10.00, 12.00, 16.00, 20.00, 24.00, 100),
  cv = c(Inf, 18.66, 9.95, 6.89, 4.20, 2.95, 2.46, 2.26, 2.06, 1.99, 1.96, 1.96)
)
get_tF_cv <- function(Fstat) {
  if (is.na(Fstat)) return(NA_real_)
  approx(tf_tab$F, tf_tab$cv, xout = Fstat, rule = 2)$y
}

avail <- function(v, d) v[v %in% names(d) & vapply(v, function(c) {
  x <- d[[c]]; is.numeric(x) && sd(x, na.rm = TRUE) > 0
}, logical(1))]

run_one <- function(outcome, controls, label) {
  ctrls <- avail(controls, df)
  rhs   <- if (length(ctrls)) paste(ctrls, collapse = " + ") else "1"
  iv_fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                               outcome, rhs, FE_COL, ENDOGENOUS, INSTRUMENT))
  fs_fml <- as.formula(sprintf("%s ~ %s + %s | %s",
                               ENDOGENOUS, INSTRUMENT, rhs, FE_COL))
  # common estimation sample (rows with the outcome + all controls present)
  keep <- complete.cases(df[, c(outcome, ctrls, INSTRUMENT, ENDOGENOUS, FE_COL)])
  d <- df[keep, ]
  iv <- feols(iv_fml, data = d, cluster = as.formula(paste0("~", CLUSTER)),
              warn = FALSE, notes = FALSE)
  fs <- feols(fs_fml, data = d, cluster = as.formula(paste0("~", CLUSTER)),
              warn = FALSE, notes = FALSE)
  tstat_fs <- coef(fs)[INSTRUMENT] / se(fs)[INSTRUMENT]
  Fcr <- as.numeric(tstat_fs^2)
  b  <- coef(iv)[paste0("fit_", ENDOGENOUS)]
  se_b <- se(iv)[paste0("fit_", ENDOGENOUS)]
  data.frame(
    outcome  = outcome,
    variant  = label,
    n        = nobs(iv),
    n_ctrl   = length(ctrls),
    coef     = as.numeric(b),
    se       = as.numeric(se_b),
    t        = as.numeric(b / se_b),
    p        = as.numeric(pvalue(iv)[paste0("fit_", ENDOGENOUS)]),
    fs_F     = Fcr,
    tF_cv    = get_tF_cv(Fcr),
    tF_sig   = abs(as.numeric(b / se_b)) > get_tF_cv(Fcr),
    stringsAsFactors = FALSE
  )
}

rows <- list()
for (y in names(HEADLINE)) {
  lag16 <- HEADLINE[[y]]
  rows[[length(rows) + 1]] <- run_one(y, c(NONCOMP, "margin_2016", LEVELS_2020),
                                      "V1_current")
  rows[[length(rows) + 1]] <- run_one(y, c(NONCOMP, "margin_2016"),
                                      "V2_drop_2020_levels")
  rows[[length(rows) + 1]] <- run_one(y, c(NONCOMP, "margin_2016", lag16),
                                      "V3_2016_peroutcome_lag")
}
res <- do.call(rbind, rows)
res$signif <- ifelse(res$p < .01, "**", ifelse(res$p < .05, "*",
                ifelse(res$p < .10, "+", "")))

fwrite(res, file.path(OUT_DIR, "lagged_dv_diagnostic.csv"))

cat("\n==== Lagged-DV diagnostic: headline consolidation outcomes ====\n")
cat("(tF_sig = survives the Lee et al. tF weak-IV correction)\n\n")
for (y in names(HEADLINE)) {
  cat(sprintf("--- %s ---\n", y))
  sub <- res[res$outcome == y, ]
  print(format(sub[, c("variant", "n", "n_ctrl", "coef", "se", "p",
                       "signif", "fs_F", "tF_cv", "tF_sig")],
               digits = 3), row.names = FALSE)
  cat("\n")
}
cat("Saved:", file.path(OUT_DIR, "lagged_dv_diagnostic.csv"), "\n")
