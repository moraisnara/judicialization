# 25_first_stage_sign_diagnostic.R — why is the first stage NEGATIVE, and is that
# theory-consistent for us?
#
# AMV (JPE 2025) EXPECT psi<0: legislative diffusion is catch-up — states with low
# prior detail on a topic borrow most when it grows nationally. OUR theory is the
# opposite: judicialization AMPLIFICATION — a municipality exposed to an
# adversarial-litigation family that is growing nationally should file MORE of it,
# so we expect psi>0. We nonetheless estimate psi~-1.08. This script diagnoses
# which force is operating, with three checks:
#   (A) first stage with vs without state FE (is the sign within- or between-state?)
#   (B) instrument vs baseline 2020 litigation level (convergence/level confound)
#   (C) DECISIVE: family-level local growth on the national leave-state shift
#       (delta_log1p_family ~ shift_leavestate). Positive => amplification (Bartik
#       works, psi>0 expected). Negative => mean-reversion/convergence (AMV force).
#
# Console-only diagnostic (no table feeds a slide yet). Reads act_design.csv +
# municipality_act_components.csv.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

args      <- commandArgs(trailingOnly = FALSE)
file_arg  <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0)
  dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))
ROOT       <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION <- file.path(ROOT, "data", "estimation")
CLEAN      <- file.path(ROOT, "data", "clean")

ENDOG  <- spec_endogenous()
IV     <- spec_instrument()
CTRLS  <- spec_baseline_controls()

df <- as.data.frame(fread(
  file.path(ESTIMATION, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
df$municipality_id_tse <- sprintf("%05d", as.integer(df$municipality_id_tse))

cmp <- as.data.frame(fread(
  file.path(CLEAN, "municipality_act_components.csv"),
  colClasses = list(character = "id_municipio_tse")))
cmp$id_municipio_tse <- sprintf("%05d", as.integer(cmp$id_municipio_tse))

# baseline 2020 total lawsuits per muni (sum of family levels)
base <- aggregate(L2020 ~ id_municipio_tse, cmp, sum)
names(base)[2] <- "tot2020"
base$log_tot2020 <- log1p(base$tot2020)
df <- merge(df, base, by.x = "municipality_id_tse",
            by.y = "id_municipio_tse", all.x = TRUE)

avail <- function(v) v[v %in% names(df)]
ctrls <- avail(CTRLS)

cat("=== (A) first stage: with vs without state FE ===\n")
f_nofe <- feols(as.formula(sprintf("%s ~ %s", ENDOG, IV)), df,
                cluster = ~cluster_id)
f_fe   <- feols(as.formula(sprintf("%s ~ %s | state", ENDOG, IV)), df,
                cluster = ~cluster_id)
f_full <- feols(as.formula(sprintf("%s ~ %s + %s | state", ENDOG, IV,
                paste(ctrls, collapse = " + "))), df, cluster = ~cluster_id)
cat(sprintf("  no FE        psi = %+.3f (t=%.1f)\n",
            coef(f_nofe)[IV], coef(f_nofe)[IV] / se(f_nofe)[IV]))
cat(sprintf("  state FE     psi = %+.3f (t=%.1f)\n",
            coef(f_fe)[IV], coef(f_fe)[IV] / se(f_fe)[IV]))
cat(sprintf("  state FE+ctl psi = %+.3f (t=%.1f)\n",
            coef(f_full)[IV], coef(f_full)[IV] / se(f_full)[IV]))

cat("\n=== (B) instrument vs baseline 2020 litigation level ===\n")
b_lvl <- feols(as.formula(sprintf("%s ~ log_tot2020 | state", IV)), df,
               cluster = ~cluster_id)
cat(sprintf("  corr(IV, log_tot2020) raw         = %+.3f\n",
            cor(df[[IV]], df$log_tot2020, use = "complete.obs")))
cat(sprintf("  IV ~ log_tot2020 | state: slope   = %+.4f (t=%.1f)\n",
            coef(b_lvl)["log_tot2020"],
            coef(b_lvl)["log_tot2020"] / se(b_lvl)["log_tot2020"]))

cat("\n=== (C) DECISIVE: local family growth on national leave-state shift ===\n")
cmp2 <- merge(cmp, df[, c("municipality_id_tse", "state", "cluster_id")],
              by.x = "id_municipio_tse", by.y = "municipality_id_tse")
# pool muni x family; family FE soaks up each shock's mean, muni FE soaks scale
g_raw <- feols(delta_log1p_family ~ shift_leavestate, cmp2, cluster = ~cluster_id)
g_fam <- feols(delta_log1p_family ~ shift_leavestate | family, cmp2,
               cluster = ~cluster_id)
g_mf  <- feols(delta_log1p_family ~ shift_leavestate | family + id_municipio_tse,
               cmp2, cluster = ~cluster_id)
cat(sprintf("  raw                  beta = %+.4f (t=%.1f)\n",
            coef(g_raw)[2], coef(g_raw)[2] / se(g_raw)[2]))
cat(sprintf("  + family FE          beta = %+.4f (t=%.1f)\n",
            coef(g_fam)[1], coef(g_fam)[1] / se(g_fam)[1]))
cat(sprintf("  + family + muni FE   beta = %+.4f (t=%.1f)\n",
            coef(g_mf)[1], coef(g_mf)[1] / se(g_mf)[1]))
cat("\n(+ => amplification, psi>0 expected; - => convergence/reversion, AMV force)\n")
