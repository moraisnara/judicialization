# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: expects per-family bartik_iv_* cols in the design for BHJ/AKM SEs.
# ===========================================================================
# 22_exposure_robust_se.R
# -----------------------------------------------------------------------------
# BHJ (2024) / AKM (2019) exposure-robust standard errors for the headline
# (voter-behaviour) 2SLS estimate, computed self-contained in R so the
# denominator and sample match 03_voter_behavior_iv.R exactly.
#
# Logic. The Bartik 2SLS estimate decomposes into family-level just-identified
# IVs weighted by Rotemberg weights:
#     tau_2SLS = sum_f alpha_f * tau_f,
# where tau_f uses bartik_iv_f alone as the instrument and alpha_f is the
# Rotemberg weight (read from rotemberg_weights.csv, built by 05). The
# exposure-robust SE treats the F families as the unit of observation:
#     SE_BHJ = sqrt( sum_f [alpha_f (tau_f - tau_2SLS)]^2 ) / sum_f alpha_f^2
#     SE_AKM = SE_BHJ * sqrt(K/(K-1))        (finite-K correction)
#
# CAVEAT. BHJ asymptotics need K_eff >> 1; here Rotemberg K_eff ~ 2.1 (HHI ~ 0.47). These
# SEs are a sensitivity bound, not a replacement for the cluster-robust SE.
# This replaces the stale Python 11_exposure_robust_se.py, which read the
# archived 02_iv_main.R outputs and an obsolete outcome list.
#
# Outputs:
#   output/tables/regressions/exposure_robust_se.csv
#   output/tables/tex/exposure_robust_se.tex
# -----------------------------------------------------------------------------

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(data.table)
  library(fixest)
})

SCRIPT_DIR <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  dirname(normalizePath(sub("^--file=", "", grep("^--file=", args, value = TRUE)[1])))
}, error = function(e) getwd())

source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))

ROOT    <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
EST_DIR <- file.path(ROOT, "data", "estimation")
REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
TEX_DIR <- file.path(ROOT, "output", "tables", "tex")

design <- as.data.frame(fread(
  file.path(EST_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
admin <- fread(file.path(ROOT, "data", "clean", "electoral_admin_outcomes.csv"))
admin[, null_share_cast    := null_votes  / total_votes]
admin[, invalid_share_cast := (blank_votes + null_votes) / total_votes]
w <- dcast(admin, municipality_id_tse ~ election_year,
           value.var = c("null_share_cast", "invalid_share_cast"))
# pad TSE integer codes to the canonical zero-filled 5-char key (see 03_voter_behavior_iv.R)
w[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
w[, delta_null_share_cast_2024_2020    := null_share_cast_2024    - null_share_cast_2020]
w[, delta_invalid_share_cast_2024_2020 := invalid_share_cast_2024 - invalid_share_cast_2020]
dt <- merge(design, w, by = "municipality_id_tse", all.x = TRUE)

INSTR <- spec_instrument()
ENDOG <- spec_endogenous()
CL    <- spec_cluster_col()
BASE  <- spec_baseline_controls()
FE    <- "state"
avail <- function(controls, data) controls[controls %in% names(data)]

# Rotemberg weights (family-level alpha) from 05.
rw <- fread(file.path(ROOT, "output", "tables", "descriptives", "rotemberg_weights.csv"))
fam_col <- if ("topic_code" %in% names(rw)) "topic_code" else "topic_name"
FAMILIES <- rw[[fam_col]]
alpha    <- rw[["alpha"]]
K        <- length(FAMILIES)
fam_ivs  <- paste0("bartik_iv_", FAMILIES)
stopifnot(all(fam_ivs %in% names(dt)))

OUTCOMES <- list(
  null_share_cast    = c("delta_null_share_cast_2024_2020",    "null_share_cast_2020",    "Null share (cast)"),
  invalid_share_cast = c("delta_invalid_share_cast_2024_2020", "invalid_share_cast_2020", "Non-valid share (cast)")
)

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

iv_fit <- function(data, zcol, dep, ctr) {
  rhs <- paste(ctr, collapse = " + ")
  feols(as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, FE, ENDOG, zcol)),
        data = data, cluster = as.formula(paste0("~", CL)), warn = FALSE, notes = FALSE)
}

rows <- list()
for (k in names(OUTCOMES)) {
  dep <- OUTCOMES[[k]][1]; lagdv <- OUTCOMES[[k]][2]; lab <- OUTCOMES[[k]][3]
  ctr <- avail(c(BASE, lagdv), dt)
  req <- unique(c(dep, ENDOG, INSTR, fam_ivs, CL, FE, ctr))
  samp <- dt[complete.cases(dt[, req, drop = FALSE]), ]

  # full 2SLS (conventional cluster-robust SE)
  mfull <- iv_fit(samp, INSTR, dep, ctr)
  rf <- coeftable(mfull)[paste0("fit_", ENDOG), ]
  tau_2sls <- unname(rf["Estimate"]); se_conv <- unname(rf["Std. Error"])
  p_conv <- unname(rf["Pr(>|t|)"])
  Ffull <- tryCatch(fitstat(mfull, "ivwald1")[[1]]$stat, error = function(e) NA_real_)

  # family-level just-identified taus on the SAME sample
  tau_f <- vapply(fam_ivs, function(z) {
    m <- tryCatch(iv_fit(samp, z, dep, ctr), error = function(e) NULL)
    if (is.null(m)) return(NA_real_)
    unname(coeftable(m)[paste0("fit_", ENDOG), "Estimate"])
  }, numeric(1))

  ok      <- is.finite(tau_f)
  a       <- alpha[ok]; tf <- tau_f[ok]; Kv <- sum(ok)
  tau_hat <- sum(a * tf) / sum(a^2)                     # weighted reconstruction
  se_bhj  <- sqrt(sum((a * (tf - tau_2sls))^2)) / sum(a^2)
  se_akm  <- if (Kv > 1) se_bhj * sqrt(Kv / (Kv - 1)) else NA_real_
  tF_cv   <- get_tF_cv(Ffull)

  rows[[length(rows) + 1]] <- data.table(
    outcome = lab, okey = k, tau_2sls = tau_2sls, recon_tau = tau_hat,
    se_conv = se_conv, p_conv = p_conv, se_bhj = se_bhj, se_akm = se_akm,
    ratio_bhj = se_bhj / se_conv, ratio_akm = se_akm / se_conv,
    t_bhj = tau_2sls / se_bhj, tF_cv = tF_cv,
    sig_conv = abs(tau_2sls / se_conv) > tF_cv,
    sig_bhj  = abs(tau_2sls / se_bhj) > tF_cv,
    K = Kv, first_F = Ffull, N = mfull$nobs)
}
res <- rbindlist(rows)
fwrite(res, file.path(REG_DIR, "exposure_robust_se.csv"))

# ---- LaTeX ----
f3 <- function(x) sprintf("%.3f", x); f2 <- function(x) sprintf("%.2f", x)
tex <- c(
  "% Auto-generated by code/04_analysis/22_exposure_robust_se.R -- do not edit.",
  "\\begin{tabular}{lrrrrr}",
  "\\hline\\hline",
  " & \\multicolumn{1}{c}{$\\hat\\tau$} & \\multicolumn{1}{c}{SE$_{\\text{clust}}$} & \\multicolumn{1}{c}{SE$_{\\text{BHJ}}$} & \\multicolumn{1}{c}{SE$_{\\text{AKM}}$} & \\multicolumn{1}{c}{BHJ/clust} \\\\",
  "\\hline",
  paste0(res$outcome, " & ", sprintf("$%s$", f3(res$tau_2sls)), " & ",
         sprintf("$%s$", f3(res$se_conv)), " & ", sprintf("$%s$", f3(res$se_bhj)), " & ",
         sprintf("$%s$", f3(res$se_akm)), " & ", f2(res$ratio_bhj), " \\\\"),
  "\\hline\\hline",
  "\\end{tabular}"
)
writeLines(tex, file.path(TEX_DIR, "exposure_robust_se.tex"))

cat("\n==== EXPOSURE-ROBUST SE (BHJ/AKM), headline voter outcomes ====\n")
cat(sprintf("K families = %d | Rotemberg HHI = %.3f | K_eff = %.2f\n",
            K, sum(alpha^2), 1/sum(alpha^2)))
print(res[, .(outcome, tau = round(tau_2sls,4), se_conv = round(se_conv,4),
              se_bhj = round(se_bhj,4), se_akm = round(se_akm,4),
              ratio_bhj = round(ratio_bhj,2), first_F = round(first_F,1), N)])
cat("\nWrote:\n  ", file.path(REG_DIR, "exposure_robust_se.csv"),
    "\n  ", file.path(TEX_DIR, "exposure_robust_se.tex"), "\n")
