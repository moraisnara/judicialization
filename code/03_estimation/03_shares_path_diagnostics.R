# ============================================================
# Shares-path (GPSS) diagnostics for the adversarial Bartik IV.
#
# Identification framework: Borusyak, Hull & Jaravel (2025, JEP), exogenous-SHARES
# path. With K_eff ~ 3 effective shocks and leave-own-state-out shifts absorbed by
# state FE, identification runs through the 2020 litigation-subject SHARES under a
# per-share parallel-trends assumption. This script produces the full shares-path
# evidence base:
#
#   (1) Shift / share descriptives + effective number of shocks  (1/HHI)
#   (2) Rotemberg-weight decomposition  -- DEMEANED-shift variant (BHJ fn 9,
#       required because the shares are complete: sum_k s_mk = 1)
#   (3) Balance on the high-Rotemberg shares: covariate balance + 2016->2020
#       pre-trend placebos (cluster-robust, fixest)
#   (4) Over-identification suite: per-subject just-identified beta_k, F_k,
#       reduced-form delta_k, first-stage pi_k (GPSS scatter + visual-IV plot),
#       Hansen J treating the top-J shares as separate instruments, and
#       drop-the-dominant-share sensitivity (Card-Mexico check)
#
# All regression objects are produced in R/fixest. Reproduces the committed
# instrument exactly (shares = baseline_share_2020, component = share * shock).
# Controls: the V3 COMMON set (no per-outcome 2016 lag) so the Rotemberg identity
# sum_k alpha_k * tau_k = tau_IV holds against a single baseline spec.
# ============================================================

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- paths ----
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0)
  dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
PROJECT_ROOT <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))

DESIGN_PATH <- file.path(PROJECT_ROOT, "data", "estimation", "executive_margin_design.csv")
COMP_PATH   <- file.path(PROJECT_ROOT, "data", "clean", "municipality_bartik_components.csv")
DESC_DIR    <- file.path(PROJECT_ROOT, "output", "tables", "descriptives")
REG_DIR     <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
FIG_DIR     <- file.path(PROJECT_ROOT, "output", "figures")
for (d in c(DESC_DIR, REG_DIR, FIG_DIR)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

# ---- spec constants (mirror 02_iv_main.R, V3 common set) ----
INSTRUMENT <- "bartik_iv_2020_2024"
ENDOG      <- "delta_log1p_competition_lawsuits_2024_2020"
FE_COL     <- "state"
CLUSTER    <- "cluster_id"
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020", "margin_2016"
)
# Outcomes to decompose (headline competition set + the lone voter survivor)
DECOMP_OUTCOMES <- c(
  "delta_margin_top1_top2_2024_2020",
  "delta_winner_vote_share_2024_2020",
  "delta_runnerup_vote_share_2024_2020",
  "delta_winner_majority_2024_2020"
)
# Pre-trend placebos for the balance tests (already in the design)
PRETREND_COLS <- c(
  "pretrend_margin_top1_top2_2020_2016",
  "pretrend_winner_vote_share_2020_2016",
  "pretrend_log1p_n_candidates_with_votes_2020_2016"
)
N_TOP <- 12L   # top subjects by |alpha| for balance + overid

# Lee et al. (2022) tF 5% critical-value table (abbreviated)
tf_tab <- data.frame(
  F  = c(0, 4.00, 4.63, 5.00, 6.00, 8.00, 10.00, 12.00, 16.00, 20.00, 24.00, 100),
  cv = c(Inf, 18.66, 9.95, 6.89, 4.20, 2.95, 2.46, 2.26, 2.06, 1.99, 1.96, 1.96))
tF_cv <- function(F) if (is.na(F)) NA_real_ else approx(tf_tab$F, tf_tab$cv, xout = F, rule = 2)$y

# ============================================================
# 1. LOAD
# ============================================================
df <- as.data.frame(fread(DESIGN_PATH,
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
if (!(CLUSTER %in% names(df))) df[[CLUSTER]] <- df[[FE_COL]]
df$municipality_id_tse <- sprintf("%05s", df$municipality_id_tse)

avail <- function(v) v[v %in% names(df)]
ctrls <- avail(BASELINE_CONTROLS)

# Estimation sample: complete on instrument, endog, controls, FE, cluster
need <- unique(c(INSTRUMENT, ENDOG, FE_COL, CLUSTER, ctrls))
samp <- df[complete.cases(df[, need]), ]
samp <- samp[is.finite(samp[[INSTRUMENT]]) & samp[[INSTRUMENT]] != 0 |
             samp[[INSTRUMENT]] == 0, ]   # keep all complete rows
rownames(samp) <- NULL
N <- nrow(samp)
cat(sprintf("Estimation sample: %d municipalities, %d state clusters\n",
            N, length(unique(samp[[CLUSTER]]))))

comp <- as.data.frame(fread(COMP_PATH,
  colClasses = list(character = c("municipality_id_tse", "main_subject_code"))))
comp$municipality_id_tse <- sprintf("%05s", comp$municipality_id_tse)
comp <- comp[comp$municipality_id_tse %in% samp$municipality_id_tse, ]
comp$share     <- as.numeric(comp$baseline_share_2020)
comp$shock     <- as.numeric(comp$shock_log_growth_2020_2024)
comp$component <- as.numeric(comp$bartik_component)
comp$share[is.na(comp$share)]         <- 0
comp$shock[is.na(comp$shock)]         <- 0
comp$component[is.na(comp$component)] <- 0

subj_name <- unique(comp[, c("main_subject_code", "main_subject_name", "topic_family")])
subj_name <- subj_name[!duplicated(subj_name$main_subject_code), ]

# ============================================================
# 2. BUILD muni x subject MATRICES (aligned to samp row order)
# ============================================================
mids   <- samp$municipality_id_tse
subj   <- sort(unique(comp$main_subject_code))
idx_m  <- match(comp$municipality_id_tse, mids)
idx_k  <- match(comp$main_subject_code, subj)
S <- matrix(0, N, length(subj), dimnames = list(NULL, subj))  # shares
Zc <- matrix(0, N, length(subj), dimnames = list(NULL, subj)) # raw components s*g
S[cbind(idx_m, idx_k)]  <- comp$share
Zc[cbind(idx_m, idx_k)] <- comp$component

# sanity: shares complete; recomputed instrument matches the design column
share_sum <- rowSums(S)
z_recomp  <- rowSums(Zc)
cat(sprintf("Shares complete: mean(sum_k s)=%.4f (rows with any caseload: %d)\n",
            mean(share_sum[share_sum > 0]), sum(share_sum > 0)))
cat(sprintf("max|recomputed z - design instrument| = %.2e\n",
            max(abs(z_recomp - samp[[INSTRUMENT]]))))

# Rotemberg basis = RAW components. The fn-9 demeaned-shift refinement applies
# only when shares are complete for EVERY unit; here ~1,150 municipalities have
# zero adversarial caseload (sum_k s = 0, not 1), so the shares are incomplete
# sample-wide and demeaning would inject a caseload indicator that does not cancel,
# breaking the decomposition identity sum_k z_k = instrument. Raw components sum
# to the instrument exactly, so sum_k alpha_k * tau_k = tau_IV holds. gbar is
# reported as a descriptive only.
gbar <- mean(z_recomp)
Zd   <- Zc              # raw components (sum exactly to the committed instrument)
cat(sprintf("Importance-weighted mean shift gbar = %.4f (descriptive only)\n", gbar))

# ============================================================
# 3. RESIDUALISER on V3 common controls + state FE
# ============================================================
W <- model.matrix(as.formula(paste0("~ ", paste(ctrls, collapse = " + "),
                                     " + factor(", FE_COL, ")")), data = samp)
qrW <- qr(W)
resid_cols <- function(M) M - W %*% qr.coef(qrW, M)   # column-wise residuals

x_t  <- as.numeric(resid_cols(matrix(samp[[ENDOG]], N, 1)))
Zd_t <- resid_cols(Zd)
keep_k <- which(apply(Zd_t, 2, function(c) sd(c) > 0))
Zd_t   <- Zd_t[, keep_k, drop = FALSE]
subj_k <- subj[keep_k]
cat(sprintf("Subjects with non-degenerate residual component: %d / %d\n",
            length(subj_k), length(subj)))

# ============================================================
# 4. ROTEMBERG WEIGHTS (demeaned) + per-subject just-identified stats
# ============================================================
Zx   <- as.numeric(crossprod(Zd_t, x_t))         # z_k' x  (numerator of FS / alpha)
Zsum <- sum(Zx)                                  # = (sum_k z_k)' x
alpha <- Zx / Zsum                               # GPSS Rotemberg weights, sum=1
ZZ   <- colSums(Zd_t^2)                           # z_k' z_k
pi_k <- Zx / ZZ                                   # just-id first-stage coef
# homoskedastic just-id F_k (through origin on residualised vars)
ssr_k <- sum(x_t^2) - Zx^2 / ZZ
s2_k  <- ssr_k / (N - 1)
F_k   <- pi_k^2 * ZZ / s2_k

# per-outcome tau_k and reduced-form delta_k
out_resid <- list()
for (y in DECOMP_OUTCOMES) if (y %in% names(samp))
  out_resid[[y]] <- as.numeric(resid_cols(matrix(samp[[y]], N, 1)))

tau <- delta <- matrix(NA_real_, length(subj_k), length(out_resid),
                       dimnames = list(subj_k, names(out_resid)))
for (j in seq_along(out_resid)) {
  yt <- out_resid[[j]]
  Zy <- as.numeric(crossprod(Zd_t, yt))
  delta[, j] <- Zy / ZZ          # reduced-form coef on z_k
  tau[, j]   <- Zy / Zx          # just-id IV estimate tau_k
}

rot <- data.frame(
  subject_code = subj_k,
  subject_name = subj_name$main_subject_name[match(subj_k, subj_name$main_subject_code)],
  family       = subj_name$topic_family[match(subj_k, subj_name$main_subject_code)],
  s_bar        = colMeans(S[, subj_k, drop = FALSE]),
  alpha        = alpha,
  F_k          = F_k,
  pi_k         = pi_k,
  stringsAsFactors = FALSE
)
for (y in names(out_resid)) {
  short <- sub("delta_", "", sub("_2024_2020", "", y))
  rot[[paste0("tau_", short)]]   <- tau[, y]
  rot[[paste0("delta_", short)]] <- delta[, y]
}
rot <- rot[order(-abs(rot$alpha)), ]
rot$cum_alpha <- cumsum(rot$alpha)
rownames(rot) <- NULL

hhi   <- sum(rot$alpha^2)
hhi_s <- sum(rot$s_bar^2)
k_eff <- 1 / hhi_s
cat(sprintf("\nRotemberg HHI(alpha)=%.4f | importance HHI(s_bar)=%.4f -> K_eff=%.2f\n",
            hhi, hhi_s, k_eff))
cat(sprintf("sum(alpha)=%.6f | top-1=%.3f top-3 cum=%.3f\n",
            sum(rot$alpha), rot$alpha[1], rot$cum_alpha[3]))
# verify identity sum_k alpha_k tau_k = baseline IV (for first outcome)
y1 <- names(out_resid)[1]
iv1 <- feols(as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
        y1, paste(ctrls, collapse = " + "), FE_COL, ENDOG, INSTRUMENT)),
        data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
tau_iv1 <- coef(iv1)[paste0("fit_", ENDOG)]
recon   <- sum(rot$alpha * rot[[paste0("tau_", sub("delta_","",sub("_2024_2020","",y1)))]])
cat(sprintf("Rotemberg identity check (%s): IV=%.5f  sum a_k tau_k=%.5f\n",
            y1, tau_iv1, recon))

fwrite(rot, file.path(DESC_DIR, "rotemberg_weights.csv"))

# ---- shift descriptives (item 5) ----
shockmat <- matrix(NA_real_, length(subj), 1, dimnames = list(subj, NULL))
g_stats <- do.call(rbind, lapply(subj, function(k) {
  g <- comp$shock[comp$main_subject_code == k]
  data.frame(subject_code = k,
             g_mean = mean(g), g_sd = sd(g),
             g_p10 = quantile(g, .10, names = FALSE),
             g_p50 = median(g),
             g_p90 = quantile(g, .90, names = FALSE))
}))
shift_desc <- merge(
  data.frame(subject_code = subj,
             subject_name = subj_name$main_subject_name[match(subj, subj_name$main_subject_code)],
             family       = subj_name$topic_family[match(subj, subj_name$main_subject_code)],
             s_bar = colMeans(S)),
  g_stats, by = "subject_code")
shift_desc$hhi_contrib <- shift_desc$s_bar^2 / sum(shift_desc$s_bar^2)
shift_desc <- shift_desc[order(-shift_desc$s_bar), ]
attr(shift_desc, "k_eff") <- k_eff
fwrite(shift_desc, file.path(DESC_DIR, "shift_descriptives.csv"))

# ============================================================
# 5. BALANCE on the high-Rotemberg shares (cluster-robust, fixest)
# ============================================================
top_subj <- rot$subject_code[seq_len(min(N_TOP, nrow(rot)))]
bal_rows <- list()
for (k in top_subj) {
  sk <- S[, k]
  samp$.share_k <- sk
  # covariate balance: share ~ controls | FE  (R^2, joint F)
  cov_fit <- feols(as.formula(sprintf(".share_k ~ %s | %s",
                   paste(ctrls, collapse = " + "), FE_COL)),
                   data = samp, warn = FALSE, notes = FALSE)
  r2cov <- r2(cov_fit, "r2"); wald <- fitstat(cov_fit, "wald")$wald
  row <- data.frame(
    subject_code = k,
    subject_name = subj_name$main_subject_name[match(k, subj_name$main_subject_code)],
    alpha = rot$alpha[match(k, rot$subject_code)],
    r2_cov = as.numeric(r2cov),
    F_cov  = as.numeric(wald$stat),
    p_cov  = as.numeric(wald$p),
    stringsAsFactors = FALSE)
  # pre-trend placebos: pretrend ~ share + V3 controls | FE (cluster-robust)
  for (pt in PRETREND_COLS) if (pt %in% names(samp)) {
    pf <- feols(as.formula(sprintf("%s ~ .share_k + %s | %s",
                pt, paste(ctrls, collapse = " + "), FE_COL)),
                data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    sh <- sub("pretrend_", "", sub("_2020_2016", "", pt))
    row[[paste0("b_", sh)]] <- coef(pf)[".share_k"]
    row[[paste0("p_", sh)]] <- pvalue(pf)[".share_k"]
  }
  bal_rows[[length(bal_rows) + 1]] <- row
}
balance <- do.call(rbind, bal_rows)
samp$.share_k <- NULL
fwrite(balance, file.path(DESC_DIR, "share_balance_tests.csv"))
np <- grep("^p_", names(balance), value = TRUE)
n_fail <- sum(sapply(np, function(c) sum(balance[[c]] < 0.05, na.rm = TRUE)))
cat(sprintf("Balance: %d / %d pre-trend coefs significant at 5%% across top-%d shares\n",
            n_fail, length(np) * nrow(balance), N_TOP))

# ============================================================
# 6. OVER-IDENTIFICATION SUITE
# ============================================================
# (a) Hansen J: top-J subject components as SEPARATE instruments
top_comp_cols <- paste0("zk_", seq_along(top_subj))
for (j in seq_along(top_subj)) samp[[top_comp_cols[j]]] <- Zd[, top_subj[j]]
overid_rows <- list()
for (y in DECOMP_OUTCOMES) if (y %in% names(samp)) {
  fml <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
           y, paste(ctrls, collapse = " + "), FE_COL, ENDOG,
           paste(top_comp_cols, collapse = " + ")))
  ofit <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  sarg <- tryCatch(fitstat(ofit, "sargan"), error = function(e) NULL)
  jb   <- coef(ofit)[paste0("fit_", ENDOG)]
  overid_rows[[length(overid_rows) + 1]] <- data.frame(
    outcome = y, beta_overid = as.numeric(jb),
    se_overid = as.numeric(se(ofit)[paste0("fit_", ENDOG)]),
    sargan = if (!is.null(sarg)) as.numeric(sarg$sargan$stat) else NA_real_,
    sargan_p = if (!is.null(sarg)) as.numeric(sarg$sargan$p) else NA_real_,
    n_instr = length(top_comp_cols), stringsAsFactors = FALSE)
}
overid <- do.call(rbind, overid_rows)

# (b) drop-the-dominant-share sensitivity (Card-Mexico check)
mk_instr <- function(drop_codes) rowSums(Zc[, setdiff(colnames(Zc), drop_codes), drop = FALSE])
samp$.iv_drop1 <- mk_instr(rot$subject_code[1])
samp$.iv_drop2 <- mk_instr(rot$subject_code[1:2])
drop_rows <- list()
for (y in DECOMP_OUTCOMES) if (y %in% names(samp)) {
  base_fit <- feols(as.formula(sprintf("%s ~ %s | %s | %s ~ %s",
                y, paste(ctrls, collapse=" + "), FE_COL, ENDOG, INSTRUMENT)),
                data = samp, cluster = ~cluster_id, warn=FALSE, notes=FALSE)
  d1 <- feols(as.formula(sprintf("%s ~ %s | %s | %s ~ .iv_drop1",
                y, paste(ctrls, collapse=" + "), FE_COL, ENDOG)),
                data = samp, cluster = ~cluster_id, warn=FALSE, notes=FALSE)
  d2 <- feols(as.formula(sprintf("%s ~ %s | %s | %s ~ .iv_drop2",
                y, paste(ctrls, collapse=" + "), FE_COL, ENDOG)),
                data = samp, cluster = ~cluster_id, warn=FALSE, notes=FALSE)
  cf <- function(f) as.numeric(coef(f)[paste0("fit_", ENDOG)])
  drop_rows[[length(drop_rows)+1]] <- data.frame(
    outcome = y,
    beta_full  = cf(base_fit),
    beta_drop1 = cf(d1),
    beta_drop2 = cf(d2),
    F_drop1 = as.numeric(fitstat(d1, "ivf1")$ivf1$stat),
    F_drop2 = as.numeric(fitstat(d2, "ivf1")$ivf1$stat),
    stringsAsFactors = FALSE)
}
dropdom <- do.call(rbind, drop_rows)
overid <- merge(overid, dropdom, by = "outcome")
fwrite(overid, file.path(REG_DIR, "shares_overid_suite.csv"))
cat("\n==== Over-identification suite ====\n"); print(overid, digits = 3)

# (c) per-subject scatter data (GPSS beta_k vs F_k; visual IV delta_k vs pi_k)
scat <- rot[, c("subject_code", "subject_name", "alpha", "F_k", "pi_k",
                grep("^tau_|^delta_", names(rot), value = TRUE))]
fwrite(scat, file.path(REG_DIR, "shares_pershare_estimates.csv"))

# ---- figures (base R) ----
y_main <- "delta_margin_top1_top2_2024_2020"
sh <- sub("delta_", "", sub("_2024_2020", "", y_main))
pi_col <- rot$pi_k; d_col <- rot[[paste0("delta_", sh)]]; a_col <- abs(rot$alpha)
pdf(file.path(FIG_DIR, "visual_iv_margin.pdf"), width = 6, height = 5)
plot(pi_col, d_col, cex = 0.5 + 6 * a_col / max(a_col),
     pch = 21, bg = rgb(0.2,0.3,0.7,0.5),
     xlab = "First-stage coefficient  pi_k", ylab = "Reduced-form coefficient  delta_k",
     main = "Visual IV: margin (point size ~ |Rotemberg weight|)")
abline(0, tau_iv1, col = "firebrick", lwd = 2)
abline(h = 0, v = 0, col = "grey70", lty = 3)
dev.off()
pdf(file.path(FIG_DIR, "gpss_scatter_margin.pdf"), width = 6, height = 5)
bk <- rot[[paste0("tau_", sh)]]
plot(rot$F_k, bk, cex = 0.5 + 6 * a_col / max(a_col),
     pch = 21, bg = rgb(0.7,0.3,0.2,0.5), log = "x",
     xlab = "Just-identified first-stage F_k (log)", ylab = "Just-identified beta_k",
     main = "GPSS: per-share estimate vs strength (margin)")
abline(h = tau_iv1, col = "firebrick", lwd = 2)
abline(h = 0, col = "grey70", lty = 3)
dev.off()
cat("Saved figures: visual_iv_margin.pdf, gpss_scatter_margin.pdf\n")

cat("\nDONE. Outputs:\n",
    " descriptives/rotemberg_weights.csv\n",
    " descriptives/shift_descriptives.csv\n",
    " descriptives/share_balance_tests.csv\n",
    " regressions/shares_overid_suite.csv\n",
    " regressions/shares_pershare_estimates.csv\n",
    " figures/visual_iv_margin.pdf, gpss_scatter_margin.pdf\n")
