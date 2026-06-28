################################################
## Heterogeneity by pre-treatment poll activity (own_polled_2020)
## Splits main IV sample by n_own_polls_2020 > 0 and re-runs
## baseline spec on all primary outcomes.
## Author: Nara Morais
################################################

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- paths ----
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
CLEAN_DIR      <- file.path(PROJECT_ROOT, "data", "clean")
OUT_DIR        <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)


# ============================================================
# 1. LOAD AND MERGE
# ============================================================

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
rename_map <- c(state = "SG_UF", municipality_id_tse = "SG_UE")
present <- intersect(names(rename_map), names(df))
if (length(present) > 0) names(df)[match(present, names(df))] <- rename_map[present]
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))

polls <- fread(file.path(CLEAN_DIR, "poll_activity_design.csv"))
polls$municipality_id_tse <- sub("^0+", "", as.character(polls$municipality_id_tse))
df$muni_key <- sub("^0+", "", as.character(df$SG_UE))
df <- merge(df, polls[, .(municipality_id_tse, n_own_polls_2020)],
            by.x = "muni_key", by.y = "municipality_id_tse", all.x = TRUE)
df$n_own_polls_2020[is.na(df$n_own_polls_2020)] <- 0L
df$own_polled_2020 <- df$n_own_polls_2020 > 0

cat(sprintf("own_polled_2020 == TRUE:  %d\n", sum(df$own_polled_2020)))
cat(sprintf("own_polled_2020 == FALSE: %d\n", sum(!df$own_polled_2020)))


# ============================================================
# 2. VARIABLE DEFINITIONS
# ============================================================

INSTRUMENT  <- "bartik_iv_act"
ENDOGENOUS  <- "delta_log1p_act_lawsuits"
COEF_KEY    <- paste0("fit_", ENDOGENOUS)
FE_COL      <- "SG_UF"

BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
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
                  COMPOSITION_OUTCOMES, ENTRY_OUTCOMES, VOTER_BEHAVIOR_OUTCOMES)


# ============================================================
# 3. HELPERS
# ============================================================

avail <- function(ctrls, data) ctrls[ctrls %in% names(data)]

run_iv <- function(data, outcome, controls, fe_col, instrument, endogenous) {
  samp  <- data[!is.na(data[[outcome]]), ]
  ctrls <- avail(controls, samp)
  req   <- unique(c(instrument, endogenous, "cluster_id", fe_col, ctrls, outcome))
  samp  <- samp[complete.cases(samp[, req, drop = FALSE]), ]
  if (nrow(samp) < 50) return(NULL)
  ctrl_rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
    outcome, ctrl_rhs, fe_col, endogenous, instrument))
  tryCatch(
    feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE),
    error = function(e) NULL
  )
}


# ============================================================
# 4. RUN HETEROGENEITY SPLIT
# ============================================================

groups <- list(
  polled   = df[df$own_polled_2020, ],
  unpolled = df[!df$own_polled_2020, ]
)

rows <- list()
for (gname in names(groups)) {
  for (oc in ALL_OUTCOMES) {
    m <- run_iv(groups[[gname]], oc, BASELINE_CONTROLS, FE_COL, INSTRUMENT, ENDOGENOUS)
    if (is.null(m)) {
      rows[[length(rows) + 1]] <- list(
        group = gname, outcome = oc,
        coef = NA_real_, se = NA_real_, pval = NA_real_, n = NA_integer_
      )
    } else {
      fstat <- tryCatch(fitstat(m, type = "ivf")[[1]]$stat, error = function(e) NA_real_)
      rows[[length(rows) + 1]] <- list(
        group   = gname,
        outcome = oc,
        coef    = unname(coef(m)[COEF_KEY]),
        se      = unname(se(m)[COEF_KEY]),
        pval    = unname(pvalue(m)[COEF_KEY]),
        ivf     = fstat,
        n       = nobs(m)
      )
    }
  }
}

res <- rbindlist(rows)
wide <- dcast(res, outcome ~ group,
              value.var = c("coef", "se", "pval", "ivf", "n"))


# ============================================================
# 5. SAVE AND PRINT
# ============================================================

fwrite(res,  file.path(OUT_DIR, "heterogeneity_polls_long.csv"))
fwrite(wide, file.path(OUT_DIR, "heterogeneity_polls_wide.csv"))
cat("\nSaved heterogeneity_polls_long.csv and heterogeneity_polls_wide.csv\n")

stars <- function(p) {
  if (is.na(p)) " " else if (p < .01) "***" else if (p < .05) "**" else if (p < .1) "*" else ""
}

cat("\n=== Heterogeneity: own_polled_2020 (n_own_polls>0) vs not ===\n")
cat(sprintf("%-50s  %8s %6s %-3s  %5s  |  %8s %6s %-3s  %5s   N(p/u)\n",
  "outcome", "coef", "se", "", "F", "coef", "se", "", "F"))
cat(strrep("-", 110), "\n")

group_order <- c("primary","secondary","composition","entry","voter_behavior")
outcome_groups <- list(
  primary         = PRIMARY_OUTCOMES,
  secondary       = SECONDARY_OUTCOMES,
  composition     = COMPOSITION_OUTCOMES,
  entry           = ENTRY_OUTCOMES,
  voter_behavior  = VOTER_BEHAVIOR_OUTCOMES
)

for (grp in group_order) {
  cat(sprintf("\n[%s]\n", grp))
  for (oc in outcome_groups[[grp]]) {
    r <- wide[wide$outcome == oc, ]
    if (nrow(r) == 0) next
    cat(sprintf("  %-48s  %8.4f %6.4f %-3s  %5.1f  |  %8.4f %6.4f %-3s  %5.1f   %d/%d\n",
      oc,
      r$coef_polled,   r$se_polled,   stars(r$pval_polled),   r$ivf_polled,
      r$coef_unpolled, r$se_unpolled, stars(r$pval_unpolled), r$ivf_unpolled,
      r$n_polled, r$n_unpolled))
  }
}
