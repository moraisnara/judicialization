# Anderson-Rubin wild cluster restricted bootstrap (G = 26 states)
# ---------------------------------------------------------------------------
# With only G = 26 clusters (states), the conventional cluster-robust normal
# approximation is anti-conservative, and the IV t-ratio is additionally weak-IV
# fragile. The Anderson-Rubin (AR) statistic is robust to weak instruments, and
# the wild cluster RESTRICTED bootstrap (WCR; Roodman et al. 2019, Stata J) is
# robust to few clusters. Combining them gives the inference recommended for this
# design (BHJ 2025, exogenous-shares path: conventional cluster-robust SEs, but
# few-cluster corrected).
#
# Just-identified single instrument => the AR test of H0: beta = b0 is the test
# that the coefficient on the instrument z is zero in the reduced form of
# (y - b0*x) on z, after partialling controls + state FE (FWL). The WCR bootstrap
# resamples cluster-level Rademacher weights on the restricted residuals.
#
# Closed form (all quantities are cluster G-vectors after FWL residualisation):
#   qy_c = sum_{i in c} z~_i y~_i ,  qx_c = sum_{i in c} z~_i x~_i ,  ZZ_c = sum z~_i^2
#   At b0:  q_c(b0) = qy_c - b0*qx_c ,  num = sum_c q_c
#   beta_z = num / sum_c ZZ_c ,  s_c = q_c - beta_z*ZZ_c ,  t = num / sqrt(sum_c s_c^2)
#   Bootstrap b:  num* = sum_c g_c q_c ,  beta_z* = num*/ZZtot ,
#                 s_c* = g_c q_c - beta_z* ZZ_c ,  t* = num* / sqrt(sum_c s_c*^2)
#   p(b0) = mean( |t*| >= |t_obs| ).   2-sided AR CI = { b0 : p(b0) >= 0.05 }.
#
# Output: output/tables/regressions/wild_bootstrap_ar.csv  (per headline outcome:
#   2SLS coef, AR-WCR p at beta=0, AR-WCR 95% CI by grid inversion).

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

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
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)

set.seed(20260628)  # reproducible bootstrap (Date.now-free, fixed seed)
B <- 9999L

df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
names(df)[names(df) == "state"] <- "SG_UF"
cat(sprintf("Loaded design: %d municipalities\n", nrow(df)))

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020", "margin_2016"
)
# Headline = ANCOVA on the 2016 pre-window baseline: the LHS is the 2024 LEVEL
# and the 2016 level enters as a free control. Map each delta key to
# c(2024 level LHS, 2016 lag control) so the weak-IV-robust AR inference is run
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
# Resolve (LHS, lag) for an outcome under the ANCOVA-2016 headline.
resolve_lhs <- function(y) {
  pair <- ANCOVA_MAP[[y]]
  if (!is.null(pair) && all(pair %in% names(df)))
    return(list(lhs = pair[1], lag = pair[2]))
  list(lhs = y, lag = NULL)
}
FOCUS_OUTCOMES <- c(
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_majority_2024_2020",
  "delta_runnerup_vote_share_2024_2020",
  "delta_female_vote_share_2024_2020",
  "delta_turnout_rate_2024_2020",
  "delta_blank_rate_2024_2020"
)
avail <- function(v, d) v[v %in% names(d)]

# Residualise a set of columns on W = [controls, lag, state FE] (FWL).
residualise <- function(samp, cols, ctrls) {
  W  <- model.matrix(~ . , data = samp[, c(ctrls), drop = FALSE])
  Wf <- cbind(W, model.matrix(~ factor(SG_UF) - 1, data = samp))
  qrW <- qr(Wf)
  out <- lapply(cols, function(cc) as.numeric(qr.resid(qrW, samp[[cc]])))
  names(out) <- cols
  out
}

# Pre-draw the Rademacher cluster weights once (reused across outcomes/grid).
run_outcome <- function(y) {
  r_lhs   <- resolve_lhs(y)
  y_lhs   <- r_lhs$lhs
  lag_col <- r_lhs$lag
  ctrls <- avail(c(BASELINE_CONTROLS, lag_col), df)
  req <- unique(c(INSTRUMENT, ENDOGENOUS, "cluster_id", "SG_UF", ctrls, y_lhs))
  s <- df[complete.cases(df[, req, drop = FALSE]), ]
  rv <- residualise(s, c(y_lhs, ENDOGENOUS, INSTRUMENT), ctrls)
  yt <- rv[[y_lhs]]; xt <- rv[[ENDOGENOUS]]; zt <- rv[[INSTRUMENT]]
  cl <- factor(s$cluster_id)
  G  <- nlevels(cl); idx <- as.integer(cl)

  # Cluster-robust 2SLS SE (for grid scaling only): quick feols IV fit.
  rhs <- paste(ctrls, collapse = " + ")
  fml <- as.formula(sprintf("%s ~ %s | SG_UF | %s ~ %s", y, rhs, ENDOGENOUS, INSTRUMENT))
  ivf <- feols(fml, data = s, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  se_iv <- unname(se(ivf)[paste0("fit_", ENDOGENOUS)])

  # Cluster sums
  qy  <- as.numeric(tapply(zt * yt, cl, sum)); qy[is.na(qy)] <- 0
  qx  <- as.numeric(tapply(zt * xt, cl, sum)); qx[is.na(qx)] <- 0
  ZZc <- as.numeric(tapply(zt * zt, cl, sum)); ZZc[is.na(ZZc)] <- 0
  ZZtot <- sum(ZZc)

  beta2sls <- sum(qy) / sum(qx)

  # Bootstrap weights G x B (Rademacher)
  Wmat <- matrix(sample(c(-1, 1), G * B, replace = TRUE), nrow = G, ncol = B)

  # p-value at a given b0 (vectorised over B)
  pval_at <- function(b0) {
    q   <- qy - b0 * qx                 # G-vector
    num_obs <- sum(q)
    bz_obs  <- num_obs / ZZtot
    s_obs   <- q - bz_obs * ZZc
    t_obs   <- num_obs / sqrt(sum(s_obs^2))
    gq      <- Wmat * q                 # G x B  (g_c * q_c)
    num_b   <- colSums(gq)              # B
    bz_b    <- num_b / ZZtot
    s_b     <- gq - outer(ZZc, bz_b)    # G x B  (g_c q_c - bz* ZZ_c)
    t_b     <- num_b / sqrt(colSums(s_b^2))
    list(p = mean(abs(t_b) >= abs(t_obs)), t_obs = t_obs)
  }

  p0 <- pval_at(0)

  # AR 95% CI by grid inversion, scaled to the actual cluster-robust 2SLS SE so the
  # grid resolves precisely-estimated outcomes. Fine spacing (1201 pts over +/-12 SE).
  hw   <- 12 * (if (is.finite(se_iv) && se_iv > 0) se_iv else abs(beta2sls) + 0.1)
  grid <- seq(beta2sls - hw, beta2sls + hw, length.out = 1201)
  pg   <- vapply(grid, function(b) pval_at(b)$p, numeric(1))
  inside <- grid[pg >= 0.05]
  ci_lo <- if (length(inside)) min(inside) else NA_real_
  ci_hi <- if (length(inside)) max(inside) else NA_real_
  # Flag an AR set that runs into the grid edge (possible unbounded/disconnected set).
  ci_at_edge <- length(inside) > 0 &&
    (ci_lo <= grid[2] || ci_hi >= grid[length(grid) - 1])

  data.frame(
    outcome = y, nobs = nrow(s), n_clusters = G,
    coef_2sls = beta2sls, ar_t_at0 = p0$t_obs,
    se_2sls = se_iv,
    ar_wcr_p_at0 = p0$p, ar_wcr_ci_lo = ci_lo, ar_wcr_ci_hi = ci_hi,
    ci_excludes_0 = !(ci_lo <= 0 & ci_hi >= 0), ci_at_grid_edge = ci_at_edge,
    stringsAsFactors = FALSE
  )
}

rows <- list()
for (y in FOCUS_OUTCOMES) {
  if (!(y %in% names(df))) next
  r <- run_outcome(y)
  rows[[length(rows) + 1]] <- r
  cat(sprintf("  %-44s 2SLS=% .4f  AR-WCR p(beta=0)=%.3f  95%% CI=[% .3f, % .3f]\n",
              y, r$coef_2sls, r$ar_wcr_p_at0, r$ar_wcr_ci_lo, r$ar_wcr_ci_hi))
}
res <- do.call(rbind, rows)
fwrite(res, file.path(ESTIMATES_DIR, "wild_bootstrap_ar.csv"))
cat("\nSaved:", file.path(ESTIMATES_DIR, "wild_bootstrap_ar.csv"), "\n")
cat(sprintf("B = %d bootstrap reps, seed = 20260628\n", B))
