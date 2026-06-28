# 27_institutional_push_prototype.R — does an INSTITUTIONAL-PUSH instrument restore
# a theory-consistent (psi>0) AMPLIFICATION first stage?
#
# Diagnosis from 25/26: the on-spec shock g_k = realized leave-own-state growth is an
# OUTCOME, dominated by demand-side spatial SUBSTITUTION (test C: within-family local
# growth moves OPPOSITE to leave-state growth, beta~-4.8) -> the first stage identifies
# convergence, not amplification. No re-normalization of exposure (26) or endogenous (26)
# flips it, because the substitution lives in the SHOCK.
#
# This prototype replaces the realized-growth shock with a SUPPLY-SIDE institutional push:
#   push_k = intensity of national TSE rule/jurisprudence expansion of family k, 2020->2024
#            (data/clean/act_family_push.csv; concentrated on fraude / direito_resposta /
#             honra / abuso -- gender-quota enforcement, disinformation/deepfake regime, VPM).
# Instrument: Z_i = sum_k E_ik * push_k, with E_ik = baseline-2020 exposure (share or level).
# A POSITIVE first stage = amplification: munis more exposed at baseline to the families TSE
# later expanded filed MORE after the push. Exogeneity now rests on push_k being a national
# TSE decision (BHJ shock-exogeneity), not on realized counts.
#
# Falsification built in: exposure to the push=0 families (Z_placebo) should NOT predict
# growth. If it does, Z is just proxying baseline litigation scale, not the push.
#
# Console-only prototype (a candidate design VARIANT; preserve, do not overwrite the on-spec
# share design). Reads act_design.csv + municipality_act_components.csv + act_family_push.csv.

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

push <- as.data.frame(fread(file.path(CLEAN, "act_family_push.csv")))
cat("=== institutional push table (push_k) ===\n")
print(push[order(-push$push_intensity), c("family", "push_intensity", "source_norma")],
      row.names = FALSE)

# attach push to components; flag any family without a push code
cmp <- merge(cmp, push[, c("family", "push_intensity")], by = "family", all.x = TRUE)
miss <- unique(cmp$family[is.na(cmp$push_intensity)])
if (length(miss)) stop("families with no push code: ", paste(miss, collapse = ", "))

# placebo push: 1 for the families TSE did NOT touch, 0 for the pushed ones
cmp$push_placebo <- as.integer(cmp$push_intensity == 0)

# build instruments: Z = sum_k E_ik * push_k, exposure E_ik = share or level
agg <- data.table(cmp)[, .(
  z_push_share = sum(share2020 * push_intensity),   # composition x push (scale-free)
  z_push_level = sum(L2020     * push_intensity),   # intensity x push (un-normalized)
  z_plac_share = sum(share2020 * push_placebo),     # falsification: untouched families
  n20          = sum(L2020),
  n24          = sum(L2024)
), by = id_municipio_tse]
df <- merge(df, as.data.frame(agg), by.x = "municipality_id_tse",
            by.y = "id_municipio_tse", all.x = TRUE)

df$endo_dlog   <- df$delta_log1p_act_lawsuits
df$endo_dlevel <- df$n24 - df$n20
for (z in c("z_push_share", "z_push_level", "z_plac_share"))
  df[[paste0(z, "_z")]] <- scale(df[[z]])[, 1]

avail   <- function(v) v[v %in% names(df)]
ctrls   <- avail(CTRLS)
ctl_str <- paste(ctrls, collapse = " + ")

fs <- function(endo, ivz) {
  f <- feols(as.formula(sprintf("%s ~ %s + %s | state", endo, ivz, ctl_str)),
             df, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  b <- coef(f)[ivz]; t <- b / se(f)[ivz]
  sprintf("%+8.3f (t=%+5.1f, F=%5.1f)", b, t, t^2)
}

cat("\n=== first stage: endogenous (rows) x institutional-push instrument (cols) ===\n")
cat("    (state FE + 5 controls; + => AMPLIFICATION, - => convergence/saturation)\n")
cat(sprintf("%-14s %-26s %-26s\n", "endogenous", "PUSH x SHARE", "PUSH x LEVEL"))
cat(sprintf("%-14s %-26s %-26s\n", "log-growth",
            fs("endo_dlog",   "z_push_share_z"), fs("endo_dlog",   "z_push_level_z")))
cat(sprintf("%-14s %-26s %-26s\n", "level-change",
            fs("endo_dlevel", "z_push_share_z"), fs("endo_dlevel", "z_push_level_z")))

cat("\n=== FALSIFICATION: exposure to UN-pushed families should NOT predict growth ===\n")
cat(sprintf("  placebo (push=0 families) x share: %s\n",
            fs("endo_dlog", "z_plac_share_z")))

cat("\n=== exogeneity flag: does each instrument just proxy size/population? ===\n")
for (z in c("z_push_share", "z_push_level", "z_plac_share")) {
  zz <- paste0(z, "_z")
  r <- cor(df[[zz]], df$log_pop_2010, use = "complete.obs")
  cat(sprintf("  %-13s corr(IV, log_pop_2010) = %+.3f\n", z, r))
}

# ── DECISIVE: family-level diff-in-diff isolating push x exposure ──────────────
# The muni-level first stages above are contaminated by panel-wide mean-reversion
# (the placebo proves it). To test amplification cleanly, go to the muni x family
# cell and ask: do PUSHED families grow MORE where baseline exposure was high,
# RELATIVE to un-pushed families? muni FE absorbs each muni's overall reversion;
# family FE absorbs each family's mean shock; the interaction push_k x baseline_ik
# is the amplification estimand. beta>0 = amplification; beta<0 = saturation.
cmp2 <- merge(cmp, df[, c("municipality_id_tse", "state", "cluster_id")],
              by.x = "id_municipio_tse", by.y = "municipality_id_tse")
cmp2$dlevel    <- cmp2$L2024 - cmp2$L2020          # absolute change (no log reversion)
cmp2$base_lvl  <- cmp2$L2020
cmp2$base_shr  <- cmp2$share2020
cmp2$pushed    <- as.integer(cmp2$push_intensity > 0)   # binary pushed vs not

cat("\n=== DECISIVE: family-level push x baseline-exposure interaction ===\n")
cat("    DV = L2024 - L2020 (absolute change); + interaction => AMPLIFICATION\n")

# (i) continuous push intensity x baseline level, muni + family FE
m1 <- feols(dlevel ~ push_intensity:base_lvl + base_lvl |
              id_municipio_tse + family, cmp2, cluster = ~cluster_id,
            warn = FALSE, notes = FALSE)
# (ii) binary pushed x baseline level (cleaner DiD reading)
m2 <- feols(dlevel ~ pushed:base_lvl + base_lvl |
              id_municipio_tse + family, cmp2, cluster = ~cluster_id,
            warn = FALSE, notes = FALSE)
# (iii) binary pushed x baseline SHARE (scale-free exposure)
m3 <- feols(dlevel ~ pushed:base_shr + base_shr |
              id_municipio_tse + family, cmp2, cluster = ~cluster_id,
            warn = FALSE, notes = FALSE)
pr <- function(m, term, lab) {
  b <- coef(m)[term]; t <- b / se(m)[term]
  cat(sprintf("  %-34s beta = %+9.4f (t=%+5.1f)\n", lab, b, t))
}
pr(m1, "push_intensity:base_lvl", "push_intensity x baseline LEVEL")
pr(m2, "pushed:base_lvl",         "pushed(0/1)    x baseline LEVEL")
pr(m3, "pushed:base_shr",         "pushed(0/1)    x baseline SHARE")
cat("  (baseline main effect = generic reversion; interaction = differential push)\n")
