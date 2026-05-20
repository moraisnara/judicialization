# GPS (2020) Section V.C — Overidentification test (Sargan-Hansen J) and
# LIML comparison, using all K=29 topic-component vectors as separate instruments.
#
# Both strategies require an overidentified system (K instruments, one endog.
# variable -> K-1 overidentifying restrictions).
#
# Method:
#   Run feols(y ~ controls | FE | d ~ z_1 + z_2 + ... + z_K)
#   where z_k = s_ik * g_k (topic-k Bartik component) after excluding RRC+DRAP.
#   Sargan-Hansen J: fitstat(fit, "sargan") in fixest.
#   LIML: k-class estimator with k = smallest eigenvalue of (Z'X, Z'Z) system.
#
# Under GPS identification (share exogeneity), the J test should NOT reject:
# all topic-specific IV estimates tau_k should be consistent for the same tau.
# A rejection indicates some shares are endogenous.
#
# Inputs:
#   data/estimation/executive_margin_design.csv
#   data/clean/municipality_bartik_components.csv
#
# Outputs:
#   output/tables/regressions/overid_jtest.csv
#   output/tables/regressions/liml_comparison.csv
#   output/tables/regressions/overid_liml_summary.md

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- Path detection ----
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
CLEAN_DIR      <- file.path(PROJECT_ROOT, "data", "clean")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)

EXCLUDE_CODES <- c("11618", "12044")   # RRC + DRAP

BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
)

# Primary outcomes for the J test (to keep run-time manageable)
PRIMARY_OUTCOMES <- c(
  "delta_runnerup_vote_share_2024_2020",
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_vote_share_2024_2020",
  "delta_winner_majority_2024_2020"
)

ENDOGENOUS <- "delta_log1p_lawsuits_no_rrc_drap_2024_2020"
FE_COL     <- "SG_UF"


# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================

cat("Loading design matrix...\n")
df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
# Handle column rename (state -> SG_UF)
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
if ("municipality_id_tse" %in% names(df))
  df$municipality_id_tse <- formatC(as.integer(df$municipality_id_tse),
                                     width = 5, flag = "0")

cat("Loading Bartik components...\n")
comp <- as.data.frame(fread(
  file.path(CLEAN_DIR, "municipality_bartik_components.csv"),
  colClasses = list(character = c("municipality_id_tse", "main_subject_code"))
))
comp$municipality_id_tse <- formatC(
  as.integer(comp$municipality_id_tse), width = 5, flag = "0"
)
# Exclude RRC and DRAP
comp <- comp[!comp$main_subject_code %in% EXCLUDE_CODES, ]
comp$n_lawsuits   <- as.numeric(comp$n_lawsuits)
comp$n_lawsuits[is.na(comp$n_lawsuits)] <- 0
comp$shock <- as.numeric(comp$shock_log_growth_2020_2024)
comp$shock[is.na(comp$shock)] <- 0

# Re-normalise shares after exclusion
tot <- tapply(comp$n_lawsuits, comp$municipality_id_tse, sum)
comp$share <- comp$n_lawsuits / tot[comp$municipality_id_tse]
comp$share[is.nan(comp$share) | is.infinite(comp$share)] <- NA
comp$z_component <- comp$share * comp$shock

# Pivot: municipality x topic share matrix (instrument components)
topic_codes <- sort(unique(comp$main_subject_code))
K <- length(topic_codes)
cat(sprintf("Topics after exclusion: %d\n", K))

pivot_list <- lapply(topic_codes, function(k) {
  sub <- comp[comp$main_subject_code == k, c("municipality_id_tse", "z_component")]
  sub$z_component[is.na(sub$z_component)] <- 0
  sub
})
names(pivot_list) <- paste0("z_", topic_codes)

# Build wide data.table
muni_ids <- unique(comp$municipality_id_tse)
wide <- data.table(municipality_id_tse = muni_ids)
for (k_idx in seq_along(topic_codes)) {
  k    <- topic_codes[k_idx]
  col  <- paste0("z_", k)
  sub  <- comp[comp$main_subject_code == k, c("municipality_id_tse", "z_component")]
  setDT(sub)
  setnames(sub, "z_component", col)
  wide <- merge(wide, sub, by = "municipality_id_tse", all.x = TRUE)
  wide[[col]][is.na(wide[[col]])] <- 0
}

# Merge with design matrix
df_merged <- merge(df, wide, by = "municipality_id_tse", all.x = FALSE)
cat(sprintf("Merged sample: %d municipalities\n", nrow(df_merged)))

z_cols   <- paste0("z_", topic_codes)
controls <- BASELINE_CONTROLS[BASELINE_CONTROLS %in% names(df_merged)]


# ============================================================
# 2. BUILD ESTIMATION SAMPLE
# ============================================================

req <- unique(c(ENDOGENOUS, FE_COL, "cluster_id", controls, PRIMARY_OUTCOMES, z_cols))
req <- req[req %in% names(df_merged)]
samp <- df_merged[complete.cases(df_merged[, req, drop = FALSE]), ]
cat(sprintf("Estimation sample: %d municipalities\n", nrow(samp)))


# ============================================================
# 3. SARGAN-HANSEN J TEST via fixest
# ============================================================

cat("\nRunning overidentified 2SLS (all K topics as instruments)...\n")
ctrl_rhs <- paste(controls, collapse = " + ")
instr_rhs <- paste(z_cols, collapse = " + ")

j_rows <- list()
liml_rows <- list()

for (y in PRIMARY_OUTCOMES) {
  if (!(y %in% names(samp))) next
  cat(sprintf("  Outcome: %s\n", y))

  # 2SLS overidentified
  fml_2sls <- as.formula(sprintf(
    "%s ~ %s | %s | %s ~ %s",
    y, ctrl_rhs, FE_COL, ENDOGENOUS, instr_rhs
  ))
  fit_2sls <- tryCatch(
    feols(fml_2sls, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE),
    error = function(e) { message("  2SLS error: ", conditionMessage(e)); NULL }
  )

  if (!is.null(fit_2sls)) {
    iv_name <- paste0("fit_", ENDOGENOUS)
    b_2sls  <- unname(coef(fit_2sls)[iv_name])
    se_2sls <- unname(se(fit_2sls)[iv_name])

    # Sargan-Hansen J test
    sargan <- tryCatch(
      fitstat(fit_2sls, type = "sargan"),
      error = function(e) list(stat = NA, p = NA)
    )
    j_stat  <- tryCatch(sargan[[1]]$stat,  error = function(e) NA)
    j_pval  <- tryCatch(sargan[[1]]$p,     error = function(e) NA)
    j_df    <- K - 1   # K instruments, 1 endogenous -> K-1 over-id restrictions

    j_rows[[length(j_rows) + 1]] <- data.frame(
      outcome    = y,
      b_2sls_overid = b_2sls,
      se_2sls_overid = se_2sls,
      j_stat     = j_stat,
      j_df       = j_df,
      j_pval     = j_pval,
      nobs       = nrow(samp),
      stringsAsFactors = FALSE
    )
    cat(sprintf("    2SLS(overid): coef=%.4f  J=%.2f  p=%.3f\n",
                b_2sls, j_stat, j_pval))
  }
}

j_results <- if (length(j_rows) > 0) do.call(rbind, j_rows) else data.frame()


# ============================================================
# 4. LIML via k-class estimator
#    k = smallest eigenvalue of the system (Anderson-Rubin k_LIML)
# ============================================================
# LIML = k-class with k = k_LIML = lambda_min of a 2x2 matrix W.
# Implementation following Hayashi (2000) Appendix 8.C.

# We compute LIML for each primary outcome using the Bartik aggregate
# (just-identified case: LIML = 2SLS when K_instruments = 1).
# For the overidentified case (K=29 instruments), LIML != 2SLS.

cat("\nRunning LIML (k-class, overidentified system)...\n")

# Build model matrices for LIML calculation
ctrl_cols <- controls[controls %in% names(samp)]
fe_dummies <- model.matrix(~ 0 + samp[[FE_COL]])
W_mat <- cbind(fe_dummies, as.matrix(samp[, ctrl_cols, drop = FALSE]))
Z_mat <- as.matrix(samp[, z_cols, drop = FALSE])   # instruments (N x K)

# Annihilator matrix for W_mat
M_W <- function(x) {
  coef_w <- qr.solve(W_mat, x)
  x - W_mat %*% coef_w
}

# Partial out W from D, Z, and Y
D_tilde <- M_W(samp[[ENDOGENOUS]])
Z_tilde <- apply(Z_mat, 2, M_W)   # N x K matrix

# k_LIML = smallest eigenvalue of inv(D'D) * D'P_Z D (where P_Z is projection onto Z)
# More precisely: k_LIML is the smallest eigenvalue of W in Hayashi (2000).
# For the augmented matrix [D, Y]' M_W Z (Z' M_W Z)^-1 Z' M_W [D, Y]:
# We use the 1x1 version: k_LIML = smallest eigenvalue of
#   [D' P_Z D]^{-1} [D' D]   -- no, this isn't right either.
# Correct formula (Hayashi 2000, p.530):
#   k_LIML satisfies: det(A - k*B) = 0 where
#   A = [D,Y]' P_Z [D,Y], B = [D,Y]' M_W M_Z [D,Y], and P_Z = Z(Z'Z)^-1 Z'

# For each outcome y
for (y in PRIMARY_OUTCOMES) {
  if (!(y %in% names(samp))) next
  Y_tilde <- M_W(samp[[y]])

  # P_Z_tilde : projection onto Z_tilde column space
  ZtZ_inv <- solve(t(Z_tilde) %*% Z_tilde + diag(1e-12, ncol(Z_tilde)))
  P_Z <- Z_tilde %*% ZtZ_inv %*% t(Z_tilde)

  # Build 2x2 matrices for [D, Y]
  DY <- cbind(D_tilde, Y_tilde)
  A  <- t(DY) %*% P_Z %*% DY              # [D,Y]' P_Z [D,Y]
  B  <- t(DY) %*% (diag(nrow(DY)) - P_Z) %*% DY  # [D,Y]' M_Z [D,Y]

  # k_LIML = smallest eigenvalue of B^{-1} A
  # (i.e. solve the generalised eigenproblem A v = k B v)
  eig_vals <- tryCatch({
    B_inv_A  <- solve(B + diag(1e-10, 2)) %*% A
    sort(Re(eigen(B_inv_A)$values))
  }, error = function(e) c(NA, NA))
  k_liml <- eig_vals[1]

  if (is.na(k_liml) || k_liml < 1) {
    cat(sprintf("  %s: k_LIML=%.3f (< 1, using 2SLS k=1)\n", y, k_liml))
    k_liml <- 1   # fallback to 2SLS
  }

  # k-class estimator: b_k = (D' (I - k M_Z) D)^{-1} D' (I - k M_Z) Y
  M_Z <- diag(nrow(samp)) - P_Z
  ImkMZ <- diag(nrow(samp)) - k_liml * M_Z
  b_liml <- as.numeric(
    solve(t(D_tilde) %*% ImkMZ %*% D_tilde + 1e-12) *
    (t(D_tilde) %*% ImkMZ %*% Y_tilde)
  )

  # Residuals and SE (conventional homoskedastic)
  e_liml  <- Y_tilde - b_liml * D_tilde
  s2_liml <- as.numeric(t(e_liml) %*% e_liml) / (nrow(samp) - 1)
  DtD_inv <- 1 / as.numeric(t(D_tilde) %*% ImkMZ %*% D_tilde)
  se_liml <- sqrt(s2_liml * DtD_inv)

  # Compare to just-identified 2SLS (Bartik aggregate)
  bartik_instr <- "bartik_iv_no_rrc_drap"
  b_2sls_ji <- NA; se_2sls_ji <- NA
  if (bartik_instr %in% names(samp)) {
    B_tilde <- M_W(samp[[bartik_instr]])
    b_2sls_ji  <- as.numeric((t(B_tilde) %*% Y_tilde) / (t(B_tilde) %*% D_tilde))
    e_2sls     <- Y_tilde - b_2sls_ji * D_tilde
    s2_2sls    <- as.numeric(t(e_2sls) %*% e_2sls) / (nrow(samp) - 1)
    Bvar       <- as.numeric(t(B_tilde) %*% B_tilde)
    Bd         <- as.numeric(t(B_tilde) %*% D_tilde)
    se_2sls_ji <- sqrt(s2_2sls * Bvar / Bd^2)
  }

  liml_rows[[length(liml_rows) + 1]] <- data.frame(
    outcome    = y,
    k_liml     = k_liml,
    b_liml     = b_liml,
    se_liml    = se_liml,
    b_2sls_ji  = b_2sls_ji,
    se_2sls_ji = se_2sls_ji,
    b_diff     = b_liml - b_2sls_ji,
    nobs       = nrow(samp),
    stringsAsFactors = FALSE
  )
  cat(sprintf("  %s: k=%.3f  LIML=%.4f (SE=%.4f)  2SLS_JI=%.4f (SE=%.4f)\n",
              y, k_liml, b_liml, se_liml, b_2sls_ji, se_2sls_ji))
}

liml_results <- if (length(liml_rows) > 0) do.call(rbind, liml_rows) else data.frame()


# ============================================================
# 5. SAVE OUTPUTS
# ============================================================

if (nrow(j_results) > 0)
  fwrite(j_results,   file.path(ESTIMATES_DIR, "overid_jtest.csv"))
if (nrow(liml_results) > 0)
  fwrite(liml_results, file.path(ESTIMATES_DIR, "liml_comparison.csv"))

# Markdown summary
fmt <- function(x, d=4) ifelse(is.na(x), "—", sprintf(paste0("%.", d, "f"), as.numeric(x)))

md <- c(
  "# Overidentification Tests and LIML — GPS (2020) Section V.C",
  "",
  "Using adversarial-only instrument (no-RRC, no-DRAP), K=29 topic components.",
  sprintf("Estimation sample: N=%d municipalities. State FE + 7 baseline controls.",
          nrow(samp)),
  "",
  "## Sargan-Hansen J Test (2SLS overidentified with all K=29 shares)",
  "",
  paste0("K-1=", K-1, " over-identifying restrictions. Null = all shares are valid instruments."),
  "Under GPS (share exogeneity), J test should NOT reject.",
  "",
  "| Outcome | 2SLS coef | SE | J stat | df | p(J) |",
  "| --- | --- | --- | --- | --- | --- |"
)
for (i in seq_len(nrow(j_results))) {
  r <- j_results[i, ]
  sig <- if (!is.na(r$j_pval) && r$j_pval < 0.05) " **" else ""
  md <- c(md, sprintf("| %s | %s | %s | %s | %s | %s%s |",
    r$outcome,
    fmt(r$b_2sls_overid), fmt(r$se_2sls_overid),
    fmt(r$j_stat, 2), r$j_df,
    fmt(r$j_pval, 3), sig
  ))
}

md <- c(md, "",
  "## LIML vs 2SLS Comparison",
  "",
  "LIML (k-class estimator) reduces many-instrument bias. Large LIML-2SLS gap",
  "signals bias; small gap supports 2SLS reliability.",
  "",
  "| Outcome | k_LIML | LIML coef | SE | 2SLS(JI) coef | SE | Diff |",
  "| --- | --- | --- | --- | --- | --- | --- |"
)
for (i in seq_len(nrow(liml_results))) {
  r <- liml_results[i, ]
  md <- c(md, sprintf("| %s | %s | %s | %s | %s | %s | %s |",
    r$outcome,
    fmt(r$k_liml, 3), fmt(r$b_liml), fmt(r$se_liml),
    fmt(r$b_2sls_ji), fmt(r$se_2sls_ji),
    fmt(r$b_diff)
  ))
}

md <- c(md, "",
  "## Notes",
  "- **J test**: Sargan-Hansen statistic from fixest::fitstat(..., 'sargan').",
  "  Rejection at 5% means some shares predict residuals -> share endogeneity concern.",
  "- **LIML**: k-class estimator; k_LIML = smallest eigenvalue of B^{-1}A.",
  "  2SLS(JI) = just-identified 2SLS using the Bartik aggregate as single instrument.",
  "  k_LIML = 1 -> LIML = 2SLS; k_LIML > 1 -> LIML more robust to many-instrument bias.",
  "- SE are conventional (homoskedastic), not clustered; use as comparison only."
)

writeLines(md, file.path(ESTIMATES_DIR, "overid_liml_summary.md"))

cat("\nSaved:\n")
cat("  ", file.path(ESTIMATES_DIR, "overid_jtest.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "liml_comparison.csv"), "\n")
cat("  ", file.path(ESTIMATES_DIR, "overid_liml_summary.md"), "\n")
