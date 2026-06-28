# 26_level_exposure_prototype.R — does an INTENSITY/level-exposure instrument
# restore a theory-consistent (psi>0) amplification first stage?
#
# The on-spec instrument is SHARE-weighted (Sum_k s_ik g_k, shares sum to 1) and
# scale-free: it ignores HOW judicialized a muni is, encoding only its composition.
# Nara's amplification theory is a LEVEL/intensity story: a more-judicialized muni
# should be pushed more by a national wave. The level-exposure instrument is the
# un-normalized Bartik Sum_k L_ik2020 g_k, which scales with baseline intensity.
# The endogenous also matters: log-growth mechanically mean-reverts (penalizes high
# baselines); an absolute/per-capita change does not. This prototype crosses
# {share, level, level-per-capita} instruments x {log-growth, level-change,
# pc-level-change} endogenous and reports first-stage sign + strength, plus a quick
# exogeneity flag (does the instrument just proxy population/size?).
#
# Console-only prototype (a candidate design VARIANT; preserve, do not overwrite the
# on-spec share design). Reads act_design.csv + municipality_act_components.csv.

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
CTRLS      <- spec_baseline_controls()

df <- as.data.frame(fread(
  file.path(ESTIMATION, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
df$municipality_id_tse <- sprintf("%05d", as.integer(df$municipality_id_tse))

cmp <- as.data.frame(fread(
  file.path(CLEAN, "municipality_act_components.csv"),
  colClasses = list(character = "id_municipio_tse")))
cmp$id_municipio_tse <- sprintf("%05d", as.integer(cmp$id_municipio_tse))

# muni-level aggregates from the family components
agg <- data.table(cmp)[, .(
  z_level = sum(L2020 * shift_leavestate),          # un-normalized (intensity) Bartik
  n20     = sum(L2020),
  n24     = sum(L2024)
), by = id_municipio_tse]
agg <- as.data.frame(agg)
df <- merge(df, agg, by.x = "municipality_id_tse",
            by.y = "id_municipio_tse", all.x = TRUE)

# per-capita scaling (pop_2010 in the design)
df$pop_k        <- df$pop_2010 / 1000
df$z_levelpc    <- df$z_level / df$pop_k
df$z_share      <- df$bartik_iv_act                 # on-spec share instrument
# endogenous variants
df$endo_dlog    <- df$delta_log1p_act_lawsuits      # on-spec (log-growth)
df$endo_dlevel  <- df$n24 - df$n20                  # absolute change in lawsuits
df$endo_dlevelpc<- (df$n24 - df$n20) / df$pop_k     # per-capita change

# standardize instruments for comparability of slopes
for (z in c("z_share", "z_level", "z_levelpc"))
  df[[paste0(z, "_z")]] <- scale(df[[z]])[, 1]

avail <- function(v) v[v %in% names(df)]
ctrls <- avail(CTRLS)
ctl_str <- paste(ctrls, collapse = " + ")

fs <- function(endo, ivz) {
  f <- feols(as.formula(sprintf("%s ~ %s + %s | state", endo, ivz, ctl_str)),
             df, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  b <- coef(f)[ivz]; t <- b / se(f)[ivz]
  sprintf("%+8.3f (t=%+5.1f, F=%5.1f)", b, t, t^2)
}

INSTR <- c(share = "z_share_z", level = "z_level_z", `level_pc` = "z_levelpc_z")
ENDO  <- c(`log-growth` = "endo_dlog", `level-change` = "endo_dlevel",
           `pc-level-change` = "endo_dlevelpc")

cat("=== first stage: endogenous (rows) x instrument (cols), state FE + 5 ctrls ===\n")
cat(sprintf("%-16s %-26s %-26s %-26s\n", "endogenous", "SHARE (on-spec)",
            "LEVEL (intensity)", "LEVEL per-capita"))
for (e in names(ENDO)) {
  cat(sprintf("%-16s %-26s %-26s %-26s\n", e,
              fs(ENDO[[e]], INSTR[["share"]]),
              fs(ENDO[[e]], INSTR[["level"]]),
              fs(ENDO[[e]], INSTR[["level_pc"]])))
}

cat("\n=== exogeneity flag: does each instrument just proxy size/population? ===\n")
for (z in names(INSTR)) {
  zz <- INSTR[[z]]
  r <- cor(df[[zz]], df$log_pop_2010, use = "complete.obs")
  cat(sprintf("  %-9s corr(IV, log_pop_2010) = %+.3f\n", z, r))
}
