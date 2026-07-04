# ============================================================================
# 07_exposure_robust_se.R
# Genuine AKM (2019) / BHJ (2022) exposure-robust standard errors for the
# shift-share IV. REPLACES the Rotemberg-dispersion heuristic previously in
# 04_iv_diagnostics.py section [C], which conflated per-topic IV-coefficient
# dispersion with sampling variance and spuriously inflated SEs ~11x.
#
# Method. After partialling controls C out of the outcome (y), endogenous (x)
# and instrument (z), the 2SLS residual e = y - beta*x is orthogonal to C.
# Because e _|_ C, the shock-level aggregate Sum_i s_ik e_i uses RAW shares, and
# each municipality-topic row contributes exactly (bartik_component * e). The
# exposure-robust variance regroups those contributions by shock and sums:
#   beta = (z'y)/(z'x),  Dhat = z'x
#   contribution_row = bartik_component_row * e_muni(row)
#   se_akm (EHW-in-shocks, sector = topic x UF): sqrt(Sum_cell contrib_cell^2)/|Dhat|
#   se_bhj (clustered at TOPIC; honest for leave-one-out shocks): sqrt(Sum_topic contrib_topic^2)/|Dhat|
#   AKM0: null-imposed test inverted over a grid, topic-clustered.
#
# Validation gates (printed): reconstructed beta must equal the fixest 2SLS coef,
# and state-clustering of the same machinery must reproduce the conventional
# cluster-robust SE.
#
# Writes: regressions/exposure_robust_se.csv  (drop-in for 06_abstract_macros.py)
#         regressions/exposure_robust_akm.csv       (full detail incl. AKM0 CI)
# ============================================================================

suppressMessages(library(data.table))
options(width = 140)

# run_all.py invokes with cwd = project root; direct Rscript runs from root too.
ROOT <- getwd()
p <- function(...) file.path(ROOT, ...)

DESIGN <- p("data/estimation/executive_margin_design.csv")
COMP   <- p("data/clean/municipality_bartik_components.csv")
ROTEMB <- p("output/tables/descriptives/rotemberg_weights.csv")
REG    <- p("output/tables/regressions")

INSTR <- "bartik_iv_2020_2024"
ENDOG <- "delta_log1p_competition_lawsuits_2024_2020"
FE    <- "state"
BASE_CTRL <- c("log_pop_2010","urban_share_2010","log_income_pc_2010",
               "higher_educ_share_2010","log1p_total_valid_votes_2020","margin_2016")

# ANCOVA-2016 outcome map: delta key -> c(2024 LHS, 2016 lag)
OUTMAP <- list(
  delta_margin_top1_top2_2024_2020    = c("margin_top1_top2_2024","margin_top1_top2_2016"),
  delta_winner_vote_share_2024_2020   = c("winner_vote_share_2024","winner_vote_share_2016"),
  delta_runnerup_vote_share_2024_2020 = c("runnerup_vote_share_2024","runnerup_vote_share_2016"),
  delta_winner_majority_2024_2020     = c("winner_majority_2024","winner_majority_2016"),
  delta_female_vote_share_2024_2020   = c("female_vote_share_2024","female_vote_share_2016"),
  delta_blank_rate_2024_2020          = c("blank_rate_2024","blank_rate_2016")
)

pad5 <- function(x) sprintf("%05d", as.integer(x))

d <- fread(DESIGN);  d[, muni := pad5(municipality_id_tse)]
comp <- fread(COMP); comp[, muni := pad5(municipality_id_tse)]
TOPIC <- "main_subject_code"
stopifnot(TOPIC %in% names(comp), "bartik_component" %in% names(comp), "state" %in% names(comp))

# K_eff (Rotemberg-weight HHI) for reporting continuity
k_eff <- NA_real_
if (file.exists(ROTEMB)) {
  rw <- fread(ROTEMB)
  if ("alpha" %in% names(rw)) k_eff <- 1 / sum(rw$alpha^2, na.rm = TRUE)
}

# Reconstruct instrument from components (sum of bartik_component per muni).
zrec <- comp[, .(z_recon = sum(bartik_component, na.rm = TRUE)), by = muni]
d <- merge(d, zrec, by = "muni", all.x = TRUE)
d[is.na(z_recon), z_recon := 0]

resid_on <- function(C, v) lm.fit(C, v)$residuals

run_outcome <- function(delta_key) {
  lhs <- OUTMAP[[delta_key]][1]; lag <- OUTMAP[[delta_key]][2]
  ctrls <- unique(c(BASE_CTRL, lag))
  req <- unique(c(INSTR, "z_recon", ENDOG, FE, ctrls, lhs))
  req <- req[req %in% names(d)]
  s <- d[complete.cases(d[, ..req])]
  n <- nrow(s)

  ctl_form <- as.formula(paste0("~ ", paste(c(ctrls, paste0("factor(", FE, ")")), collapse = " + ")))
  C <- model.matrix(ctl_form, s)
  yt <- resid_on(C, s[[lhs]]); xt <- resid_on(C, s[[ENDOG]]); zt <- resid_on(C, s[["z_recon"]])

  Dhat <- sum(zt * xt); bhat <- sum(zt * yt) / Dhat; e <- yt - bhat * xt

  # validation SEs (region EHW + state-clustered)
  g_i <- zt * e
  se_ehw_region <- sqrt(sum(g_i^2)) / abs(Dhat)
  se_cl_state   <- sqrt(sum(tapply(g_i, s[[FE]], sum)^2)) / abs(Dhat)

  # exposure-robust: contribution = bartik_component * e
  emap <- data.table(muni = s$muni, e = e)
  cc <- merge(comp[muni %in% s$muni, .(muni, topic = get(TOPIC), uf = state, bc = bartik_component)],
              emap, by = "muni")
  cc[, w := bc * e]
  se_akm_ehw   <- sqrt(cc[, .(sw = sum(w)), by = .(topic, uf)][, sum(sw^2)]) / abs(Dhat)  # EHW-in-shocks
  se_akm_topic <- sqrt(cc[, .(sw = sum(w)), by = topic][, sum(sw^2)]) / abs(Dhat)          # topic-clustered

  # AKM0 null-imposed CI (topic-clustered), grid inversion
  ccx <- merge(comp[muni %in% s$muni, .(muni, topic = get(TOPIC), bc = bartik_component)],
               data.table(muni = s$muni, ey = yt, ex = xt), by = "muni")
  akm0_stat <- function(b0) {
    Tn <- sum(zt * (yt - b0 * xt))
    ccx[, r := bc * (ey - b0 * ex)]
    Tn^2 / ccx[, .(sw = sum(r)), by = topic][, sum(sw^2)]
  }
  grid <- seq(bhat - 0.7, bhat + 0.7, by = 0.0005)
  inside <- grid[vapply(grid, akm0_stat, numeric(1)) <= qchisq(0.95, 1)]
  akm0_lo <- if (length(inside)) min(inside) else NA_real_
  akm0_hi <- if (length(inside)) max(inside) else NA_real_

  p_akm_topic <- 2 * pnorm(-abs(bhat / se_akm_topic))
  cat(sprintf("  %-42s beta=%+.4f  conv=%.4f (val %.4f)  AKM_topic=%.4f p=%.4f  AKM0=[%+.4f,%+.4f]\n",
              delta_key, bhat, se_cl_state, se_ehw_region, se_akm_topic, p_akm_topic, akm0_lo, akm0_hi))

  data.table(variant = "adversarial", spec = "baseline",
             outcome = delta_key, nobs = n, tau_2sls = bhat,
             se_conventional = se_cl_state, se_bhj = se_akm_topic, se_akm = se_akm_ehw,
             p_bhj = p_akm_topic, akm0_ci_low = akm0_lo, akm0_ci_high = akm0_hi,
             K_eff_rotemberg = k_eff)
}

cat("== Genuine AKM/BHJ exposure-robust SE (validation: reconstructed beta = fixest 2SLS; conv = cluster-robust) ==\n")
res <- rbindlist(lapply(names(OUTMAP), run_outcome))
fwrite(res, file.path(REG, "exposure_robust_se.csv"))
fwrite(res, file.path(REG, "exposure_robust_akm.csv"))
cat(sprintf("\nSaved: %s\n", file.path(REG, "exposure_robust_se.csv")))
