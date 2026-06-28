# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: reads municipality_family_components.csv filtered to rung=="theme9".
# ===========================================================================
# 05_cluster_robustness.R
# -----------------------------------------------------------------------------
# Alternative-inference table for the HEADLINE FIRST STAGE (Bartik IV -> kept-
# litigation delta), mirroring Ash, Morelli & Vannoni (2025, Table A.19). The
# 2SLS point estimate and the first-stage coefficient are invariant to the choice
# of standard error; only SE / t / implied F / p move. For a single instrument the
# effective first-stage F equals the squared robust t-stat on the instrument, so
# this table shows directly how the weak-IV verdict depends on the inference
# choice -- the input to the frame-23 discussion (keep state clustering as primary?
# add one of these as a column?).
#
# Schemes (all on the SAME baseline first-stage spec and sample):
#   1. State-clustered (27 UFs)            -- HEADLINE; the shift is constant
#                                             within state, so this is the level
#                                             at which the instrument varies (AKM).
#   2. Heteroskedasticity-robust (HC1)     -- no clustering; what clustering costs.
#   3. Region-clustered (5 macro-regions)  -- coarser geography (very few clusters).
#   4. k-means on family-share vectors (16)-- AMV's exposure-similarity clustering.
#   5. Wild cluster bootstrap (state)      -- Cameron-Gelbach-Miller null-imposed
#                                             Rademacher WCB; the correct few-
#                                             clusters correction for 27 clusters.
#
# NOTE on AKM/BHJ exposure-robust SE: that is a property of the 2SLS *estimator*
# variance (Rotemberg decomposition over families), not a first-stage-coefficient
# SE, so it lives in 22_exposure_robust_se.R (second-stage robustness), not here.
#
# Outputs:
#   output/tables/regressions/first_stage_cluster_robustness.csv
#   output/tables/tex/first_stage_cluster_robustness.tex
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
CLEAN   <- file.path(ROOT, "data", "clean")
REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
TEX_DIR <- file.path(ROOT, "output", "tables", "tex")

INSTR <- spec_instrument()
ENDOG <- spec_endogenous()
CL    <- spec_cluster_col()
BASE  <- spec_baseline_controls()
FE    <- "state"
B_WCB <- 999L
KMEANS_G <- 16L
set.seed(20240625)  # reproducible k-means + bootstrap

design <- as.data.frame(fread(
  file.path(EST_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))

# ---- macro-region (5) from UF ----------------------------------------------
REGION <- c(
  AC="N",AP="N",AM="N",PA="N",RO="N",RR="N",TO="N",
  AL="NE",BA="NE",CE="NE",MA="NE",PB="NE",PE="NE",PI="NE",RN="NE",SE="NE",
  DF="CO",GO="CO",MT="CO",MS="CO",
  ES="SE",MG="SE",RJ="SE",SP="SE",
  PR="S",RS="S",SC="S")
design$region <- REGION[design$cluster_id]

# ---- k-means on the 2020 family-share vectors (theme9) ----------------------
comp <- fread(file.path(CLEAN, "municipality_family_components.csv"),
              colClasses = list(character = "id_municipio_tse"))
comp <- comp[rung == "theme9"]
comp[, SG_UE := sprintf("%05s", trimws(id_municipio_tse))]
comp[, SG_UE := gsub(" ", "0", SG_UE)]
shares <- dcast(comp, SG_UE ~ family, value.var = "share2020", fill = 0)
share_cols <- setdiff(names(shares), "SG_UE")
km <- kmeans(as.matrix(shares[, ..share_cols]), centers = KMEANS_G, nstart = 25, iter.max = 50)
shares[, kmeans_grp := paste0("k", km$cluster)]
design <- merge(design, shares[, .(SG_UE, kmeans_grp)],
                by.x = "municipality_id_tse", by.y = "SG_UE", all.x = TRUE)

# ---- baseline first-stage sample (match the frame-23 baseline column) -------
ctr <- BASE[BASE %in% names(design)]
req <- unique(c(ENDOG, INSTR, ctr, FE, CL, "region", "kmeans_grp"))
samp <- design[complete.cases(design[, req, drop = FALSE]), ]
rhs  <- paste(c(INSTR, ctr), collapse = " + ")
fml  <- as.formula(sprintf("%s ~ %s | %s", ENDOG, rhs, FE))

row_of <- function(m, scheme, n_clust) {   # robust t on the instrument -> one row
  ct <- coeftable(m)[INSTR, ]
  est <- unname(ct["Estimate"]); se <- unname(ct["Std. Error"]); tt <- est / se
  data.table(scheme = scheme, n_clust = n_clust, coef = est, se = se,
             t = tt, F_eff = tt^2, p = 2 * pnorm(-abs(tt)))
}

# ---- analytic schemes -------------------------------------------------------
m_state  <- feols(fml, samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
m_hc     <- feols(fml, samp, vcov = "hetero",       warn = FALSE, notes = FALSE)
m_region <- feols(fml, samp, cluster = ~region,     warn = FALSE, notes = FALSE)
m_kmean  <- feols(fml, samp, cluster = ~kmeans_grp, warn = FALSE, notes = FALSE)

rows <- rbindlist(list(
  row_of(m_state,  "State (27 UFs)",            uniqueN(samp$cluster_id)),
  row_of(m_hc,     "Heteroskedasticity-robust", NA_integer_),
  row_of(m_region, "Region (5)",                uniqueN(samp$region)),
  row_of(m_kmean,  sprintf("k-means shares (%d)", KMEANS_G), uniqueN(samp$kmeans_grp))
))

# ---- wild cluster bootstrap (state), null-imposed Rademacher ----------------
ct_state <- coeftable(m_state)[INSTR, ]
coef_state <- unname(ct_state["Estimate"])
t_obs   <- unname(ct_state["Estimate"] / ct_state["Std. Error"])
m_restr <- feols(as.formula(sprintf("%s ~ %s | %s", ENDOG, paste(ctr, collapse = " + "), FE)),
                 samp, warn = FALSE, notes = FALSE)
fit_r   <- predict(m_restr)
res_r   <- samp[[ENDOG]] - fit_r
cl_id   <- samp$cluster_id
clusters <- unique(cl_id)
t_star <- numeric(B_WCB)
for (b in seq_len(B_WCB)) {
  w <- setNames(sample(c(-1, 1), length(clusters), replace = TRUE), clusters)
  ystar <- fit_r + w[cl_id] * res_r
  sb <- samp; sb[[ENDOG]] <- ystar
  mb <- feols(fml, sb, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  cb <- coeftable(mb)[INSTR, ]
  t_star[b] <- unname(cb["Estimate"] / cb["Std. Error"])
}
p_wcb <- (1 + sum(abs(t_star) >= abs(t_obs))) / (B_WCB + 1)
rows <- rbind(rows, data.table(
  scheme = sprintf("Wild cluster bootstrap (state, B=%d)", B_WCB),
  n_clust = uniqueN(samp$cluster_id),
  coef = coef_state, se = NA_real_, t = t_obs,
  F_eff = NA_real_, p = p_wcb), fill = TRUE)

fwrite(rows, file.path(REG_DIR, "first_stage_cluster_robustness.csv"))

# ---- LaTeX ------------------------------------------------------------------
f3 <- function(x) ifelse(is.na(x), "\\multicolumn{1}{c}{--}", sprintf("%.3f", x))
f1 <- function(x) ifelse(is.na(x), "\\multicolumn{1}{c}{--}", sprintf("%.1f", x))
fp <- function(x) ifelse(is.na(x), "\\multicolumn{1}{c}{--}",
                         ifelse(x < 0.001, "<0.001", sprintf("%.3f", x)))
fc <- function(x) ifelse(is.na(x), "\\multicolumn{1}{c}{--}", sprintf("%d", as.integer(x)))
body <- paste0(
  rows$scheme, " & ", fc(rows$n_clust), " & ", f3(rows$se), " & ",
  sprintf("%.2f", rows$t), " & ", f1(rows$F_eff), " & ", fp(rows$p), " \\\\")
tex <- c(
  "% Auto-generated by code/03_estimation/05_cluster_robustness.R -- do not edit.",
  "\\begin{tabular}{l D{.}{.}{-1} D{.}{.}{-1} D{.}{.}{-1} D{.}{.}{-1} D{.}{.}{-1}}",
  "\\hline\\hline",
  sprintf(" & \\multicolumn{1}{c}{Clusters} & \\multicolumn{1}{c}{SE} & \\multicolumn{1}{c}{$t$} & \\multicolumn{1}{c}{$F$} & \\multicolumn{1}{c}{$p$} \\\\"),
  "\\hline",
  body,
  "\\hline\\hline",
  sprintf("\\multicolumn{6}{l}{\\emph{First-stage coef.\\ on standardized $Z$ = %.3f; single instrument, so $F=t^2$.}} \\\\",
          rows$coef[1]),
  "\\end{tabular}")
writeLines(tex, file.path(TEX_DIR, "first_stage_cluster_robustness.tex"))

cat("\n==== FIRST-STAGE CLUSTER ROBUSTNESS (baseline spec, N =", nrow(samp), ") ====\n")
print(rows[, .(scheme, n_clust, coef = round(coef,3), se = round(se,3),
               t = round(t,2), F_eff = round(F_eff,1), p = round(p,4))])
cat("\nWrote:\n  ", file.path(REG_DIR, "first_stage_cluster_robustness.csv"),
    "\n  ", file.path(TEX_DIR, "first_stage_cluster_robustness.tex"), "\n")
