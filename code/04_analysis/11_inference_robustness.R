# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: reconstructs bartik_iv_theme9 from the old municipality_bartik inputs.
# ===========================================================================
# 11_inference_robustness.R
# -----------------------------------------------------------------------------
# Spec / inference robustness battery for the shift-share IV.
#
# For each headline outcome it reports the 2SLS coefficient and its standard
# error under several inference choices, so we can SEE whether the theme9
# significance is an artifact of any single choice:
#
#   (1) state-cluster   -- current headline (27 clusters == states)
#   (2) HC1 (no cluster)-- "should we cluster at all?" floor
#   (3) pairs-cluster bootstrap over the 27 states -- few-cluster correction
#   (4) BHJ/AKM exposure-robust -- the theoretically-correct SE for a
#       shift-share instrument (Adao-Kolesar-Morales 2019; Borusyak-Hull-
#       Jaravel 2022), computed via the GPS shock-level decomposition.
#
# and across three control/FE specs:
#   baseline (state FE, 5 controls + lagged DV)
#   extended (state FE, + extended controls)
#   meso     (mesoregion FE, baseline controls)
#
# Exposure-robust SE is a property of the instrument structure and is reported
# for the baseline spec only. Output: a tidy CSV + console table.
# -----------------------------------------------------------------------------

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(data.table)
  library(fixest)
})

# robust ROOT resolution (works under Rscript and source())
args_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
SCRIPT_DIR <- if (length(args_file)) dirname(normalizePath(args_file)) else getwd()
ROOT    <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
source(file.path(ROOT, "code", "utils", "spec_config.R"))

REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
dir.create(REG_DIR, recursive = TRUE, showWarnings = FALSE)

set.seed(20260624)
B_BOOT <- 499

# ---- load design ------------------------------------------------------------
design <- as.data.frame(fread(
  file.path(ROOT, "data", "estimation", "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
if ("code_meso" %in% names(design)) design$code_meso <- as.character(design$code_meso)

# ---- bartik components (long muni x family) -> wide instrument matrix --------
# Use the CURRENT build: municipality_family_components.csv, rung == theme9, whose
# per-family bartik_component sums EXACTLY to design$bartik_iv_theme9 (verified
# corr 1.0). The older municipality_bartik_components.csv is a stale taxonomy.
comp <- fread(file.path(ROOT, "data", "clean", "municipality_family_components.csv"),
              colClasses = list(character = "id_municipio_tse"))
comp <- comp[rung == "theme9"]
comp[, municipality_id_tse := sprintf("%05d", as.integer(id_municipio_tse))]
setnames(comp, "family", "topic_family")
# one bartik_component per muni x family (collapse over any duplicate rows)
comp_u <- comp[!is.na(bartik_component),
               .(bartik_component = bartik_component[1]),
               by = .(municipality_id_tse, topic_family)]
fam_levels <- sort(unique(comp_u$topic_family))
comp_w <- dcast(comp_u, municipality_id_tse ~ topic_family,
                value.var = "bartik_component", fill = 0)
zcols <- paste0("Z_", make.names(fam_levels))
setnames(comp_w, fam_levels, zcols)
design <- merge(design, comp_w, by = "municipality_id_tse", all.x = TRUE)
cat(sprintf("Components: %d families (%s)\n", length(fam_levels),
            paste(fam_levels, collapse = ", ")))

# ---- spec pieces ------------------------------------------------------------
INSTR <- spec_instrument(); ENDOG <- spec_endogenous(); CL <- spec_cluster_col()
BASE  <- spec_baseline_controls(); EXT <- spec_extended_controls()
avail <- function(v) v[v %in% names(design)]

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y
star <- function(p) if (is.na(p)) "" else if (p < .01) "***" else
                    if (p < .05) "**" else if (p < .10) "*" else ""

# ---- headline outcomes (all resident in the design file) --------------------
OUTCOMES <- c(
  "delta_winner_vote_share_2024_2020",
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_majority_2024_2020",
  "delta_new_candidate_vote_share_2024_2020",
  "delta_incumbent_candidate_vote_share_2024_2020",
  "delta_winner_is_new_vs_2020_2024_2020",
  "delta_vote_hhi_candidate_2024_2020",
  "delta_elected_nonwhite_share_2024_2020",
  "delta_female_vote_share_2024_2020",
  "delta_turnout_rate_2024_2020",
  "delta_blank_rate_2024_2020",
  "delta_null_rate_2024_2020")
OUTCOMES <- OUTCOMES[OUTCOMES %in% names(design)]

# ---- 2SLS fit for one outcome / spec ----------------------------------------
fit_iv <- function(dep, ctr0, fe) {
  lag <- spec_lagged_dv(dep); ctr <- avail(c(ctr0, lag))
  req <- unique(c(dep, ENDOG, INSTR, CL, fe, ctr, zcols))
  d   <- design[complete.cases(design[, req, drop = FALSE]), ]
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                            dep, paste(ctr, collapse = " + "), fe, ENDOG, INSTR))
  list(m = feols(fml, data = d, cluster = as.formula(paste0("~", CL)),
                 warn = FALSE, notes = FALSE),
       d = d, ctr = ctr, fe = fe, dep = dep)
}
iv_row <- function(m) {
  ct <- coeftable(m); r <- ct[paste0("fit_", ENDOG), ]
  list(coef = unname(r["Estimate"]), se = unname(r["Std. Error"]),
       p = unname(r["Pr(>|t|)"]),
       F = tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_))
}

# ---- pairs-cluster bootstrap over states ------------------------------------
boot_se <- function(fit) {
  states <- unique(fit$d[[CL]]); G <- length(states)
  by_state <- split(seq_len(nrow(fit$d)), fit$d[[CL]])
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
            fit$dep, paste(fit$ctr, collapse = " + "), fit$fe, ENDOG, INSTR))
  bs <- replicate(B_BOOT, {
    pick <- sample(states, G, replace = TRUE)
    idx  <- unlist(by_state[pick], use.names = FALSE)
    mb <- tryCatch(feols(fml, data = fit$d[idx, ], warn = FALSE, notes = FALSE),
                   error = function(e) NULL)
    if (is.null(mb)) return(NA_real_)
    unname(coef(mb)[paste0("fit_", ENDOG)])
  })
  bs <- bs[is.finite(bs)]
  list(se = sd(bs), ci = quantile(bs, c(.025, .975), names = FALSE), nrep = length(bs))
}

# ---- BHJ/AKM exposure-robust via GPS shock-level decomposition --------------
# Residualise endog x, outcome y, and each component Z_k on the controls + FE,
# then beta_k = (Z~_k . y~)/(Z~_k . x~), alpha_k = (Z~_k . x~)/sum_j(Z~_j . x~),
# beta_bartik = sum_k alpha_k beta_k (sanity check vs 2SLS). BHJ exposure SE =
# sqrt(sum_k (alpha_k (beta_k - beta))^2)/sum_k alpha_k^2; AKM x sqrt(K/(K-1)).
exposure_robust <- function(fit) {
  d <- fit$d; ctr <- fit$ctr; fe <- fit$fe
  resid_on_W <- function(v) {
    f <- as.formula(sprintf("%s ~ %s | %s", v, paste(ctr, collapse = " + "), fe))
    resid(feols(f, data = d, warn = FALSE, notes = FALSE))
  }
  xt <- resid_on_W(ENDOG); yt <- resid_on_W(fit$dep)
  a <- b <- numeric(length(zcols))
  for (k in seq_along(zcols)) {
    if (sd(d[[zcols[k]]]) == 0) { a[k] <- 0; b[k] <- 0; next }
    zt <- resid_on_W(zcols[k]); a[k] <- sum(zt * xt); b[k] <- sum(zt * yt)
  }
  keep <- a != 0; a <- a[keep]; b <- b[keep]
  beta_k <- b / a; alpha_k <- a / sum(a); beta <- sum(alpha_k * beta_k)
  res_k  <- alpha_k * (beta_k - beta)
  se_bhj <- sqrt(sum(res_k^2)) / sum(alpha_k^2)
  Kk     <- length(alpha_k)
  list(beta_recon = beta, se_bhj = se_bhj,
       se_akm = se_bhj * sqrt(Kk / (Kk - 1)),
       hhi = sum(alpha_k^2), K = Kk)
}

# ---- run battery ------------------------------------------------------------
SPECS <- list(
  baseline = list(ctr = BASE, fe = "state"),
  extended = list(ctr = EXT,  fe = "state"),
  meso     = list(ctr = BASE, fe = "code_meso"))

rows <- list()
for (dep in OUTCOMES) {
  for (sp in names(SPECS)) {
    fit <- fit_iv(dep, SPECS[[sp]]$ctr, SPECS[[sp]]$fe)
    base <- iv_row(fit$m)
    hc1  <- coeftable(fit$m, vcov = "hetero")[paste0("fit_", ENDOG), ]
    bo   <- boot_se(fit)
    tFcv <- get_tF_cv(base$F)
    er   <- if (sp == "baseline") exposure_robust(fit) else
            list(beta_recon = NA, se_bhj = NA, se_akm = NA, hhi = NA, K = NA)
    rows[[length(rows) + 1]] <- data.table(
      outcome = dep, spec = sp, N = fit$m$nobs,
      coef = base$coef, first_F = base$F, tF_cv = tFcv,
      se_cluster = base$se, p_cluster = base$p,
      se_hc1 = unname(hc1["Std. Error"]), p_hc1 = unname(hc1["Pr(>|t|)"]),
      se_boot = bo$se, boot_ci_lo = bo$ci[1], boot_ci_hi = bo$ci[2],
      se_bhj = er$se_bhj, se_akm = er$se_akm, exp_hhi = er$hhi, exp_K = er$K,
      beta_recon = er$beta_recon)
  }
}
res <- rbindlist(rows)

# significance flags: does |coef/se| clear the tF critical value?
res[, t_cluster := coef / se_cluster]
res[, sig_cluster := abs(coef / se_cluster) > tF_cv]
res[, sig_hc1     := abs(coef / se_hc1)     > tF_cv]
res[, sig_boot    := (boot_ci_lo > 0) | (boot_ci_hi < 0)]
res[, sig_akm     := ifelse(is.na(se_akm), NA, abs(coef / se_akm) > tF_cv)]

fwrite(res, file.path(REG_DIR, "inference_robustness.csv"))

# ---- console summary --------------------------------------------------------
short <- function(x) sub("_2024_2020$", "", sub("^delta_", "", x))
cat("\n==== INFERENCE / SPEC ROBUSTNESS (tF-based significance) ====\n")
cat("Significance = |coef/SE| clears the Lee et al. (2022) tF critical value.\n\n")
b <- res[spec == "baseline"]
pr <- b[, .(outcome = short(outcome), coef = round(coef, 4), F = round(first_F, 1),
            se_cl = round(se_cluster, 4), se_hc1 = round(se_hc1, 4),
            se_boot = round(se_boot, 4), se_akm = round(se_akm, 4),
            akm_ratio = round(se_akm / se_cluster, 2),
            cl = ifelse(sig_cluster, "Y", "."), hc1 = ifelse(sig_hc1, "Y", "."),
            boot = ifelse(sig_boot, "Y", "."),
            akm = ifelse(is.na(sig_akm), "?", ifelse(sig_akm, "Y", ".")))]
print(pr, nrow = 100)

cat("\n-- coefficient stability across specs (baseline / extended / meso) --\n")
wide <- dcast(res, outcome ~ spec, value.var = "coef")
wide_se <- dcast(res, outcome ~ spec, value.var = "se_cluster")
st <- data.table(outcome = short(wide$outcome),
                 baseline = round(wide$baseline, 4),
                 extended = round(wide$extended, 4),
                 meso = round(wide$meso, 4))
print(st, nrow = 100)
cat(sprintf("\nExposure-robust K = %d families, HHI = %.3f, mean SE_AKM/SE_cluster = %.2f\n",
            b$exp_K[1], b$exp_hhi[1], mean(b$se_akm / b$se_cluster, na.rm = TRUE)))
cat(sprintf("Saved: %s\n", file.path("output","tables","regressions","inference_robustness.csv")))
