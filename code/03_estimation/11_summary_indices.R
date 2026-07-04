# Summary indices + Romano-Wolf stepdown -- multiplicity WITHOUT a family cut (R)
# -----------------------------------------------------------------------------
# The headline flags a handful of significant 2SLS effects against a wide band of
# nulls. A referee asks: do the stars survive multiple testing? Holm/BH on the
# full 18-outcome family kill everything; on a tight "closeness-4" family they
# survive (07_multiplicity.R). That answer depends entirely on where you draw the
# confirmatory-family line -- a judgment call we deliberately DO NOT force here.
#
# This script sidesteps the family cut two decision-free ways:
#   (1) SUMMARY INDICES (Anderson 2008 ICW + Kling-Liebman-Katz 2007 standardized
#       average). Each THEORY-DECLARED family is collapsed into ONE index and
#       tested once -- no within-family multiplicity at all. The pattern ACROSS
#       families (barrier families move, placebo families don't) is the story,
#       and it does not hinge on which outcomes are "primary".
#   (2) ROMANO-WOLF stepdown (Romano-Wolf 2005/2016; Clarke-Romano-Wolf 2020),
#       computed by a JOINT wild-cluster bootstrap on the reduced forms so the
#       cross-outcome correlation is used -- strictly less conservative than the
#       Holm/BH already reported, and weak-IV-robust (it tests the reduced form,
#       i.e. the Anderson-Rubin object, not the 2SLS ratio).
#
# Indices are built on the pure FIRST-DIFFERENCE basis so all outcomes share one
# scale; because FD over-differences a barely-persistent outcome (see the ANCOVA
# headline decision), the FD index is a CONSERVATIVE lower bound on the ANCOVA
# effect. Same instrument / controls / state FE / state cluster as the headline.
#
# Input : data/estimation/executive_margin_design.csv
# Output: output/tables/regressions/summary_indices_fixest.csv
#         output/tables/regressions/romano_wolf_stepdown.csv
#         output/tables/tex/summary_indices.tex

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- path detection (RStudio + Rscript) ----
if (exists("rstudioapi") && tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE)) {
  SCRIPT_DIR <- dirname(rstudioapi::getSourceEditorContext()$path)
} else {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0) {
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  } else getwd()
}
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
TEX_DIR        <- file.path(PROJECT_ROOT, "output", "tables", "tex")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR,       recursive = TRUE, showWarnings = FALSE)

set.seed(20240703)  # Rademacher draws (Date.now-free reproducibility)

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "state"
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020", "margin_2016"
)

# ============================================================
# 1. THEORY-DECLARED FAMILIES  (sign = +1 orients toward "barrier/consolidation")
# ============================================================
# Each entry: outcome -> orientation sign so that a POSITIVE oriented value means
# "the barrier is operating" (contest consolidates / voters withdraw / field
# concentrates / the pool is less inclusive). Signs are fixed by theory ex ante,
# NOT by which way the estimate came out.
FAMILIES <- list(
  closeness = c(
    delta_margin_top1_top2_2024_2020    =  1,  # winner pulls away
    delta_winner_vote_share_2024_2020   =  1,
    delta_runnerup_vote_share_2024_2020 = -1,  # runner-up falls back
    delta_winner_majority_2024_2020     =  1   # winner clears 50%
  ),
  concentration = c(
    delta_effective_n_candidates_vote_2024_2020   = -1,  # fewer effective names
    delta_vote_hhi_candidate_2024_2020            =  1,  # more concentrated
    delta_top2_vote_share_2024_2020               =  1,
    delta_log1p_n_candidates_with_votes_2024_2020 = -1
  ),
  disengagement = c(
    delta_blank_rate_2024_2020      =  1,  # voters exit the ballot
    delta_null_rate_2024_2020       =  1,
    delta_valid_vote_rate_2024_2020 = -1,  # fewer valid votes
    delta_turnout_rate_2024_2020    = -1
  ),
  representation = c(  # NULL family: compositional neutrality is the finding.
    delta_female_vote_share_2024_2020             = -1,  # oriented as "exclusion"
    delta_female_share_2024_2020                  = -1,
    delta_nonwhite_vote_share_2024_2020           = -1,
    delta_winner_is_female_2024_2020              = -1,
    delta_new_candidate_vote_share_2024_2020      = -1,  # newcomers squeezed
    delta_incumbent_candidate_vote_share_2024_2020 =  1  # incumbents entrench
  ),
  council_placebo = c(  # PLACEBO office: council ballot should not move
    delta_blank_rate_vereador_2024_2020      =  1,
    delta_null_rate_vereador_2024_2020       =  1,
    delta_valid_vote_rate_vereador_2024_2020 = -1
  )
)
# The overall BARRIER index pools the three executive barrier families (not
# representation, which is a null, nor the council placebo).
BARRIER_FAMILIES <- c("closeness", "concentration", "disengagement")

FAMILY_LABEL <- c(
  closeness       = "Closeness (mayoral)",
  concentration   = "Field concentration",
  disengagement   = "Voter disengagement",
  representation  = "Descriptive representation",
  council_placebo = "Council ballot (placebo)",
  barrier_overall = "Overall barrier index"
)

# ANCOVA-2016 map (mirrors 02_iv_main.R): delta-outcome -> c(2024 level, 2016 lag).
# The index/RW SIGNAL for a mapped outcome is Y_2024 residualized on its own 2016
# level -- i.e. the headline ANCOVA basis, NOT the first difference (which over-
# differences a barely-persistent outcome and washes the result out). Outcomes
# with no clean 2016 analog fall back to their first difference.
ANCOVA_MAP <- list(
  delta_margin_top1_top2_2024_2020              = c("margin_top1_top2_2024",   "margin_top1_top2_2016"),
  delta_winner_vote_share_2024_2020             = c("winner_vote_share_2024",  "winner_vote_share_2016"),
  delta_runnerup_vote_share_2024_2020           = c("runnerup_vote_share_2024","runnerup_vote_share_2016"),
  delta_winner_majority_2024_2020               = c("winner_majority_2024",    "winner_majority_2016"),
  delta_effective_n_candidates_vote_2024_2020   = c("effective_n_candidates_vote_2024", "effective_n_candidates_vote_2016"),
  delta_vote_hhi_candidate_2024_2020            = c("vote_hhi_candidate_2024",  "vote_hhi_candidate_2016"),
  delta_top2_vote_share_2024_2020               = c("top2_vote_share_2024",     "top2_vote_share_2016"),
  delta_log1p_n_candidates_with_votes_2024_2020 = c("log1p_n_candidates_with_votes_2024", "log1p_n_candidates_with_votes_2016"),
  delta_blank_rate_2024_2020                    = c("blank_rate_2024",         "blank_rate_2016"),
  delta_null_rate_2024_2020                     = c("null_rate_2024",          "null_rate_2016"),
  delta_valid_vote_rate_2024_2020               = c("valid_vote_rate_2024",    "valid_vote_rate_2016"),
  delta_turnout_rate_2024_2020                  = c("turnout_rate_2024",       "turnout_rate_2016"),
  delta_female_vote_share_2024_2020             = c("female_vote_share_2024",  "female_vote_share_2016"),
  delta_nonwhite_vote_share_2024_2020           = c("nonwhite_vote_share_2024","nonwhite_vote_share_2016"),
  delta_winner_is_female_2024_2020              = c("winner_is_female_2024",   "winner_is_female_2016"),
  delta_new_candidate_vote_share_2024_2020      = c("new_candidate_vote_share_2024",       "new_candidate_vote_share_2016"),
  delta_incumbent_candidate_vote_share_2024_2020 = c("incumbent_candidate_vote_share_2024", "incumbent_candidate_vote_share_2016"),
  delta_blank_rate_vereador_2024_2020           = c("blank_rate_vereador_2024","blank_rate_vereador_2016"),
  delta_null_rate_vereador_2024_2020            = c("null_rate_vereador_2024", "null_rate_vereador_2016"),
  delta_valid_vote_rate_vereador_2024_2020      = c("valid_vote_rate_vereador_2024", "valid_vote_rate_vereador_2016")
)

# ANCOVA signal for one outcome: residual of Y_2024 on its 2016 lag (both levels
# present), else the raw first difference. Residualizing only the OWN lag (not the
# common controls, which enter the index/RF regression) keeps the per-outcome
# baseline adjustment the headline uses while still allowing one pooled index.
ancova_signal <- function(data, outcome) {
  pr <- ANCOVA_MAP[[outcome]]
  if (is.null(pr) || !all(pr %in% names(data))) return(data[[outcome]])  # FD fallback
  y <- data[[pr[1]]]; x <- data[[pr[2]]]
  s <- rep(NA_real_, length(y))
  ok <- is.finite(y) & is.finite(x)
  s[ok] <- residuals(lm(y[ok] ~ x[ok]))
  s
}

# ============================================================
# 2. LOAD
# ============================================================
df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
cat(sprintf("Loaded design: %d munis x %d cols\n", nrow(df), ncol(df)))

avail <- function(controls, data) controls[controls %in% names(data)]

# ============================================================
# 3. SUMMARY INDICES  (Anderson ICW + KLK standardized average)
# ============================================================
# Build one index column per family on the complete-case sample for that family,
# then fit the same 2SLS as the headline. Two aggregators:
#   KLK  : simple mean of sign-oriented z-scores (equal weight).
#   ICW  : GLS/inverse-covariance weights w = Sigma^{-1} 1, index = (Zc w)/(1'w);
#          down-weights outcomes that are redundant (highly correlated).
build_index <- function(data, spec, ctrls) {
  outs  <- names(spec); signs <- unname(spec)
  # per-outcome ANCOVA signal, then sign-orient
  Sg    <- vapply(outs, function(o) ancova_signal(data, o), numeric(nrow(data)))
  Sg    <- sweep(Sg, 2, signs, `*`)
  base  <- data.frame(Sg, check.names = FALSE)
  keep  <- c(INSTRUMENT, ENDOGENOUS, FE_COL, "cluster_id", ctrls)
  for (cc in keep) base[[cc]] <- data[[cc]]
  req   <- c(outs, keep); req <- req[req %in% names(base)]
  samp  <- base[complete.cases(base[, req, drop = FALSE]), ]
  Zs    <- scale(as.matrix(samp[, outs, drop = FALSE]))  # standardize each to sd 1
  samp$idx_klk <- rowMeans(Zs)                           # KLK equal-weight
  S     <- cov(Zs)
  w     <- tryCatch(solve(S, rep(1, ncol(Zs))), error = function(e) rep(1, ncol(Zs)))
  samp$idx_icw <- as.numeric(Zs %*% w) / sum(w)          # Anderson ICW
  list(samp = samp, k = length(outs))
}

fit_index <- function(samp, idx_col, ctrls) {
  rhs <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                            idx_col, rhs, FE_COL, ENDOGENOUS, INSTRUMENT))
  feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
}

ctrls <- avail(BASELINE_CONTROLS, df)
idx_specs <- c(as.list(FAMILIES),
               list(barrier_overall = do.call(c, unname(FAMILIES[BARRIER_FAMILIES]))))

rows <- list()
for (fam in names(idx_specs)) {
  bi   <- build_index(df, idx_specs[[fam]], ctrls)
  samp <- bi$samp
  for (agg in c("idx_klk", "idx_icw")) {
    m  <- fit_index(samp, agg, ctrls)
    ivc <- coef(m)[paste0("fit_", ENDOGENOUS)]
    ivs <- se(m)[paste0("fit_", ENDOGENOUS)]
    ivp <- pvalue(m)[paste0("fit_", ENDOGENOUS)]
    fs <- tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
    rows[[length(rows) + 1]] <- data.frame(
      family = fam, aggregator = ifelse(agg == "idx_klk", "KLK", "ICW"),
      k_outcomes = bi$k, coef_sd = unname(ivc), se = unname(ivs), p = unname(ivp),
      first_stage_F = fs, nobs = nobs(m),
      stringsAsFactors = FALSE)
  }
}
idx_res <- do.call(rbind, rows)
idx_path <- file.path(ESTIMATES_DIR, "summary_indices_fixest.csv")
write.csv(idx_res, idx_path, row.names = FALSE)
cat("  Wrote:", idx_path, "\n")
print(idx_res[idx_res$aggregator == "ICW",
              c("family", "k_outcomes", "coef_sd", "se", "p", "nobs")], row.names = FALSE)

# ============================================================
# 4. ROMANO-WOLF STEPDOWN  (joint wild-cluster bootstrap on reduced forms)
# ============================================================
# Correct FWER across the SAME 18 executive outcomes 07_multiplicity.R uses, so
# the numbers slot next to its Holm/BH. We test the REDUCED FORM (y ~ Z + X | FE)
# rather than the 2SLS ratio: with one instrument this is the Anderson-Rubin
# object (weak-IV-robust) and it bootstraps as a clean OLS. The bootstrap is
# RESTRICTED (impose the RF null b_Z = 0) and JOINT (one Rademacher draw per
# cluster, shared across all outcomes) so cross-outcome dependence is preserved.
RW_OUTCOMES <- do.call(c, unname(FAMILIES[c("closeness", "concentration",
                                            "disengagement", "representation")]))
rw_outs <- names(RW_OUTCOMES)
B <- 9999L

# Per-outcome ANCOVA reduced form: LHS = 2024 level (own 2016 lag in W), or the
# first difference where no lag exists. One COMMON complete-case sample so the
# shared cluster weights align row-wise across outcomes.
# mapped only when BOTH the 2024 level and 2016 lag exist (else FD fallback)
mapped  <- function(o) !is.null(ANCOVA_MAP[[o]]) && all(ANCOVA_MAP[[o]] %in% names(df))
lhs_of <- vapply(rw_outs, function(o) if (mapped(o)) ANCOVA_MAP[[o]][1] else o, "")
lag_of <- vapply(rw_outs, function(o) if (mapped(o)) ANCOVA_MAP[[o]][2] else NA_character_, "")
allvars <- unique(c(lhs_of, na.omit(lag_of), INSTRUMENT, FE_COL, "cluster_id", ctrls))
allvars <- allvars[allvars %in% names(df)]
samp <- df[complete.cases(df[, allvars, drop = FALSE]), ]
G    <- length(unique(samp$cluster_id)); Ncc <- nrow(samp)
gidx <- as.integer(factor(samp$cluster_id))
ssf  <- (G / (G - 1)) * ((Ncc - 1) / (Ncc - length(ctrls) - G))  # ~ fixest CR scale
cat(sprintf("\nRomano-Wolf (ANCOVA RF): %d outcomes, N=%d, G=%d clusters, B=%d\n",
            length(rw_outs), Ncc, G, B))

# Frisch-Waugh: residualize a vector on the controls (+ optional own lag) and FE.
fe <- samp[[FE_COL]]
resid_on <- function(y, extra) {
  W <- as.matrix(samp[, c(ctrls, extra), drop = FALSE])
  as.numeric(feols(reformulate(colnames(W), "y_"),
    data = data.frame(y_ = y, W, .fe = fe), fixef = ".fe",
    warn = FALSE, notes = FALSE)$residuals)
}
# Per-outcome residualized instrument (Zt_j depends on the outcome's lag) + LHS.
Zt <- matrix(NA_real_, Ncc, length(rw_outs)); Yt <- Zt; ZtZ <- numeric(length(rw_outs))
for (j in seq_along(rw_outs)) {
  extra   <- if (!is.na(lag_of[j])) lag_of[j] else character(0)
  Zt[, j] <- resid_on(samp[[INSTRUMENT]], extra)
  Yt[, j] <- resid_on(samp[[lhs_of[j]]], extra)
  ZtZ[j]  <- sum(Zt[, j]^2)
}

# Vectorized cluster-robust RF t-vector for a matrix of (restricted-null) LHS
# residuals Ym; each column j uses its own residualized instrument Zt[,j].
boot_t <- function(Ym) {
  bb <- colSums(Zt * Ym) / ZtZ
  eb <- Ym - sweep(Zt, 2, bb, `*`)
  sc <- rowsum(Zt * eb, gidx)                  # G x J per-cluster score sums
  vb <- ssf * colSums(sc^2) / (ZtZ^2)
  bb / sqrt(vb)
}
t_obs <- boot_t(Yt); names(t_obs) <- rw_outs   # wg = 1 reproduces observed t

# Joint wild-cluster bootstrap: one Rademacher weight per cluster per draw,
# shared across outcomes (restricted null: yt*_j = yt_j * w_g).
Tb <- matrix(NA_real_, nrow = B, ncol = length(rw_outs))
for (b in seq_len(B)) {
  wg <- sample(c(-1, 1), G, replace = TRUE)[gidx]
  Tb[b, ] <- boot_t(Yt * wg)
}

# Romano-Wolf stepdown on |t| (Clarke-Romano-Wolf 2020, Algorithm).
ord   <- order(abs(t_obs), decreasing = TRUE)
absT  <- abs(t_obs)[ord]
absTb <- abs(Tb[, ord, drop = FALSE])
p_rw  <- numeric(length(ord))
running_max_cols <- ord  # remaining hypotheses = current + less significant
for (s in seq_along(ord)) {
  maxdist <- do.call(pmax, as.data.frame(absTb[, s:length(ord), drop = FALSE]))
  p_rw[s] <- (1 + sum(maxdist >= absT[s])) / (B + 1)
}
p_rw <- cummax(p_rw)                       # enforce monotonicity
# outcome -> family lookup (over the four executive families in the RW set)
fam_of <- unlist(lapply(names(FAMILIES)[1:4],
                        function(f) setNames(rep(f, length(FAMILIES[[f]])),
                                             names(FAMILIES[[f]]))))
rw <- data.frame(
  outcome = rw_outs[ord],
  family  = unname(fam_of[rw_outs[ord]]),
  t = t_obs[ord], p_raw = 2 * pnorm(-absT),
  p_rw = p_rw, stringsAsFactors = FALSE)
rw$p_holm <- p.adjust(rw$p_raw, "holm")
rw$p_bh   <- p.adjust(rw$p_raw, "BH")
rw <- rw[order(rw$p_rw), ]
rw_path <- file.path(ESTIMATES_DIR, "romano_wolf_stepdown.csv")
write.csv(rw, rw_path, row.names = FALSE)
cat("  Wrote:", rw_path, "\n")
cat(sprintf("  Significant at 5%%: raw=%d  Holm=%d  BH=%d  Romano-Wolf=%d\n",
            sum(rw$p_raw < .05), sum(rw$p_holm < .05),
            sum(rw$p_bh < .05), sum(rw$p_rw < .05)))
print(head(rw[, c("outcome", "t", "p_raw", "p_holm", "p_bh", "p_rw")], 6), row.names = FALSE)

# ---- Romano-Wolf ladder as a compact deck fragment (top rows by p_rw) --------
RW_LABEL <- c(
  delta_margin_top1_top2_2024_2020    = "Top-two margin",
  delta_runnerup_vote_share_2024_2020 = "Runner-up vote share",
  delta_winner_vote_share_2024_2020   = "Winner vote share",
  delta_vote_hhi_candidate_2024_2020  = "Vote Herfindahl",
  delta_blank_rate_2024_2020          = "Mayoral blank rate",
  delta_null_rate_2024_2020           = "Mayoral null rate")
pstar <- function(p) if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
rw_top <- head(rw, 6)
rwl <- c(
  "% Auto-generated by code/03_estimation/11_summary_indices.R -- do not edit",
  "\\begin{tabular}{lcccc}",
  "\\toprule\\toprule",
  "Outcome & $t$ & $p_{\\text{raw}}$ & $p_{\\text{Holm}}$ & $p_{\\text{RW}}$ \\\\",
  "\\midrule")
for (i in seq_len(nrow(rw_top))) {
  r <- rw_top[i, ]
  lab <- if (!is.na(RW_LABEL[r$outcome])) RW_LABEL[[r$outcome]] else r$outcome
  rwl <- c(rwl, sprintf("%s & %.2f & %.3f%s & %.3f & %.3f%s \\\\",
                        lab, r$t, r$p_raw, pstar(r$p_raw), r$p_holm, r$p_rw, pstar(r$p_rw)))
}
rwl <- c(rwl, "\\bottomrule\\bottomrule", "\\end{tabular}")
rw_tex <- file.path(TEX_DIR, "romano_wolf_stepdown.tex")
writeLines(rwl, con = rw_tex)
cat("  Wrote:", rw_tex, "\n")

# ============================================================
# 5. HOUSE-STYLE TABLE (family index grid; bands the overall-barrier row)
# ============================================================
star <- function(p) {
  if (is.na(p)) return("")
  if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
}
# KLK (Kling-Liebman-Katz mean-of-z-scores) is reported in the grid: its units are
# directly interpretable as an average standardized effect, and it is the more
# conservative headline for the aggregate. Anderson ICW weighting (in the CSV)
# sharpens every p-value but leaves the significance pattern unchanged.
G_ICW <- idx_res[idx_res$aggregator == "KLK", ]
rownames(G_ICW) <- G_ICW$family

order_fam <- c("closeness", "concentration", "disengagement",
               "barrier_overall", "representation", "council_placebo")
lines <- c(
  "% Auto-generated by code/03_estimation/11_summary_indices.R",
  "% Do not edit manually -- rerun the generating script to update",
  "",
  "\\begin{tabular}{lcccc}",
  "\\toprule\\toprule",
  "Family (\\# outcomes) & Index effect & Std.\\ error & $p$ & $N$ \\\\",
  "\\midrule"
)
for (fam in order_fam) {
  r <- G_ICW[fam, ]
  band <- (fam == "barrier_overall")
  lab  <- sprintf("%s (%d)", FAMILY_LABEL[fam], r$k_outcomes)
  coef <- sprintf("%.3f%s", r$coef_sd, star(r$p))
  se   <- sprintf("\\textcolor{mygray}{(%.3f)}", r$se)
  nfmt <- formatC(r$nobs, format = "d", big.mark = ",")
  if (band) lines <- c(lines, "\\midrule")
  lines <- c(lines,
    if (band) "\\rowcolor{mylight}" else NULL,
    sprintf("%s & %s & %s & %.3f & %s \\\\", lab, coef, se, r$p, nfmt))
  if (fam == "barrier_overall") lines <- c(lines, "\\midrule")
}
lines <- c(lines, "\\bottomrule\\bottomrule", "\\end{tabular}")
tex_path <- file.path(TEX_DIR, "summary_indices.tex")
writeLines(lines, con = tex_path)
cat("  Wrote:", tex_path, "\n")

cat("\nDone: summary indices + Romano-Wolf stepdown.\n")
