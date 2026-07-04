# ============================================================================
# 08_mean_reversion.R
# Split-sample falsification of the first stage (audit finding #10).
#
# CONCERN: municipality exposure shares are built from ~9 filings/muni, and the
# 2020 filing count sits in BOTH the Bartik share denominator (share_{m,k,2020} =
# n_{m,k,2020} / N_{m,2020}) AND the endogenous base (delta_log1p = log1p(N_2024)
# - log1p(N_2020)). Transitory small-count noise in N_{m,2020} could therefore
# manufacture the ("convergence") first stage mechanically, absent any real signal.
#
# TEST: split each municipality's adversarial docket at the FILING level into two
# disjoint random halves (binomial draw on the muni x subject x year counts).
# Build the instrument Z^A from half A's 2020 filings; build litigation growth
# from the DISJOINT half B. A and B share no filings, so the noise in the share
# denominator is independent of the noise in the growth base -- the mechanical
# channel is severed. If Z^A still predicts half-B growth (same sign, F away from
# weak) across many random splits, the first stage reflects a real cross-muni
# signal, not small-count mean reversion.
#
# Mirrors the headline first stage exactly: Y ~ Z + baseline controls | state,
# clustered by state (see run_first_stage() / BASELINE_CONTROLS in 02_iv_main.R).
#
# Inputs : data/clean/municipality_competition_subject_panel.csv (adversarial,
#            muni x subject x {2020,2024} counts -- the disaggregation of the
#            endogenous delta_log1p_competition_lawsuits)
#          data/clean/municipality_bartik_components.csv (leave-UF-out shifts)
#          data/estimation/executive_margin_design.csv (controls, FE, cluster,
#            full-sample benchmark instrument + endogenous)
# Outputs: output/tables/regressions/mean_reversion_splitsample.csv (per split)
#          output/tables/regressions/mean_reversion_splitsample_summary.csv
#          output/figures/firststage_splitsample.pdf
# ============================================================================

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(ggplot2)
})

ROOT    <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
PANEL   <- file.path(ROOT, "data/clean/municipality_competition_subject_panel.csv")
COMP    <- file.path(ROOT, "data/clean/municipality_bartik_components.csv")
DESIGN  <- file.path(ROOT, "data/estimation/executive_margin_design.csv")
OUT_CSV <- file.path(ROOT, "output/tables/regressions/mean_reversion_splitsample.csv")
OUT_SUM <- file.path(ROOT, "output/tables/regressions/mean_reversion_splitsample_summary.csv")
OUT_FIG <- file.path(ROOT, "output/figures/firststage_splitsample.pdf")

source(file.path(ROOT, "code/utils/figure_style.R"))  # theme_report(), PAL

set.seed(20260702L)
N_SPLITS <- 200L
CTRL <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
          "higher_educ_share_2010", "log1p_total_valid_votes_2020", "margin_2016")
FS_RHS <- paste(CTRL, collapse = " + ")
fs_fml <- function(lhs) as.formula(sprintf("%s ~ Z + %s | state", lhs, FS_RHS))

fs_stats <- function(fit) {
  ct <- fit$coeftable                    # clustered (cluster set at fit time)
  b  <- ct["Z", "Estimate"]; se <- ct["Z", "Std. Error"]
  list(beta = b, se = se, t = b / se, F = (b / se)^2)
}

# ---- load ---------------------------------------------------------------
panel  <- fread(PANEL,  colClasses = list(character = "municipality_id_tse"))
comp   <- fread(COMP,   colClasses = list(character = "municipality_id_tse"))
design <- fread(DESIGN, colClasses = list(character = "municipality_id_tse"))

# Leave-UF-out shift per (muni, subject), held FIXED across splits.
shift <- unique(comp[, .(municipality_id_tse, main_subject_code,
                         shock = shock_log_growth_2020_2024)],
                by = c("municipality_id_tse", "main_subject_code"))

# Estimation slice: keys + FE(state) + cluster + controls + full-sample benchmark.
dcols <- c("municipality_id_tse", "state", "cluster_id",
           "bartik_iv_2020_2024", "delta_log1p_competition_lawsuits_2024_2020", CTRL)
d <- design[, ..dcols]
keep <- complete.cases(d[, c(CTRL, "bartik_iv_2020_2024",
                             "delta_log1p_competition_lawsuits_2024_2020"), with = FALSE])
d <- d[keep]
cat(sprintf("Estimation sample: N=%d munis, %d state clusters\n",
            nrow(d), uniqueN(d$cluster_id)))

# 2020 subject rows carry shares; attach the fixed shift. 2024 rows for growth.
p2020 <- merge(panel[election_year == 2020,
                     .(municipality_id_tse, main_subject_code, n2020 = n_lawsuits)],
               shift, by = c("municipality_id_tse", "main_subject_code"), all.x = TRUE)
p2020[is.na(shock), shock := 0]
p2024 <- panel[election_year == 2024,
               .(municipality_id_tse, main_subject_code, n2024 = n_lawsuits)]
Nfull2024 <- p2024[, .(N2024f = sum(n2024)), by = municipality_id_tse]

# ---- reconstruction check: raw shares x shift must reproduce the instrument
Zfull <- p2020[, .(Z = { tot <- sum(n2020); if (tot > 0) sum((n2020 / tot) * shock) else 0 }),
               by = municipality_id_tse]
Dfull <- merge(p2020[, .(N2020 = sum(n2020)), by = municipality_id_tse],
               p2024[, .(N2024 = sum(n2024)), by = municipality_id_tse],
               by = "municipality_id_tse", all = TRUE)
Dfull[is.na(N2020), N2020 := 0]; Dfull[is.na(N2024), N2024 := 0]
Dfull[, dlog := log1p(N2024) - log1p(N2020)]
chk <- merge(d, Zfull, by = "municipality_id_tse", all.x = TRUE)
chk <- merge(chk, Dfull[, .(municipality_id_tse, dlog)], by = "municipality_id_tse", all.x = TRUE)
chk[is.na(Z), Z := 0]; chk[is.na(dlog), dlog := 0]
# instrument may be standardized in assembly, so compare on correlation (scale-free)
z_cor <- cor(chk$Z, chk$bartik_iv_2020_2024)
d_max <- max(abs(chk$dlog - chk$delta_log1p_competition_lawsuits_2024_2020))
cat(sprintf("Reconstruction: cor(rebuilt Z, stored bartik)=%.4f  max|d rebuilt - stored|=%.2e\n",
            z_cor, d_max))

# ---- full-sample benchmark first stage ----------------------------------
# On the SCALE-MATCHED rebuilt instrument (identical construction to Z^A), so the
# split-sample betas are directly comparable. F is scale-invariant regardless.
# NB: merge on the key so dlog stays bound to its muni -- never positional-assign a
# column into a merge-reordered table.
full <- merge(d, Zfull[, .(municipality_id_tse, Z)],
              by = "municipality_id_tse", all.x = TRUE)
full[is.na(Z), Z := 0]
setnames(full, "delta_log1p_competition_lawsuits_2024_2020", "dlog")
m_full  <- feols(fs_fml("dlog"), data = full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
bench   <- fs_stats(m_full)
# also confirm F on the STORED instrument (should be the deck's F=102.3)
full_st <- copy(d); setnames(full_st, "bartik_iv_2020_2024", "Z")
full_st[, dlog := delta_log1p_competition_lawsuits_2024_2020]
m_stored <- feols(fs_fml("dlog"), data = full_st, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
bench_st <- fs_stats(m_stored)
cat(sprintf("Full-sample FS  (rebuilt Z): beta=%.4f se=%.4f t=%.2f F=%.1f\n",
            bench$beta, bench$se, bench$t, bench$F))
cat(sprintf("Full-sample FS  (stored  Z): beta=%.4f se=%.4f t=%.2f F=%.1f  <- deck benchmark\n",
            bench_st$beta, bench_st$se, bench_st$t, bench_st$F))

# ---- split-sample Monte Carlo -------------------------------------------
# Per split: binomial-halve every 2020 and 2024 subject count. Half A's 2020
# filings -> Z^A; half B's filings -> growth. Two growth variants:
#   both : log1p(N^B_2024) - log1p(N^B_2020)         (strictest; 2024 also halved)
#   y20  : log1p(N_2024_full) - log1p(N^B_2020)      (only 2020 split -> more power)
res <- vector("list", N_SPLITS)
for (s in seq_len(N_SPLITS)) {
  p2020[, a := rbinom(.N, n2020, 0.5)]
  p2020[, b := n2020 - a]
  p2024[, b24 := rbinom(.N, n2024, 0.5)]

  ZA     <- p2020[, .(Z = { tot <- sum(a); if (tot > 0) sum((a / tot) * shock) else 0 }),
                  by = municipality_id_tse]
  NB2020 <- p2020[, .(NB2020 = sum(b)),   by = municipality_id_tse]
  NB2024 <- p2024[, .(NB2024 = sum(b24)), by = municipality_id_tse]

  reg <- Reduce(function(x, y) merge(x, y, by = "municipality_id_tse", all.x = TRUE),
                list(copy(d), ZA, NB2020, NB2024, Nfull2024))
  for (col in c("Z", "NB2020", "NB2024", "N2024f"))
    reg[is.na(get(col)), (col) := 0]
  reg[, dlog_both := log1p(NB2024) - log1p(NB2020)]
  reg[, dlog_y20  := log1p(N2024f) - log1p(NB2020)]

  fb <- fs_stats(feols(fs_fml("dlog_both"), data = reg, cluster = ~cluster_id,
                       warn = FALSE, notes = FALSE))
  fy <- fs_stats(feols(fs_fml("dlog_y20"),  data = reg, cluster = ~cluster_id,
                       warn = FALSE, notes = FALSE))
  res[[s]] <- data.table(split = s,
                         beta_both = fb$beta, se_both = fb$se, t_both = fb$t, F_both = fb$F,
                         beta_y20  = fy$beta, se_y20  = fy$se, t_y20  = fy$t, F_y20  = fy$F)
  if (s %% 50 == 0) cat(sprintf("  split %d/%d\n", s, N_SPLITS))
}
res <- rbindlist(res)
fwrite(res, OUT_CSV)

# ---- summary ------------------------------------------------------------
same_sign <- function(x, ref) mean(sign(x) == sign(ref))
summ <- rbindlist(list(
  data.table(quantity = "full_sample_rebuilt", beta = bench$beta,    F = bench$F,    note = "benchmark (scale-matched)"),
  data.table(quantity = "full_sample_stored",  beta = bench_st$beta, F = bench_st$F, note = "deck instrument"),
  data.table(quantity = "split_both_median",   beta = median(res$beta_both), F = median(res$F_both),
             note = sprintf("mean beta=%.4f; same-sign=%.0f%%; F>10 in %.0f%%; F>23.1 in %.0f%%",
                            mean(res$beta_both), 100 * same_sign(res$beta_both, bench$beta),
                            100 * mean(res$F_both > 10), 100 * mean(res$F_both > 23.1))),
  data.table(quantity = "split_y20_median",    beta = median(res$beta_y20),  F = median(res$F_y20),
             note = sprintf("mean beta=%.4f; same-sign=%.0f%%; F>10 in %.0f%%; F>23.1 in %.0f%%",
                            mean(res$beta_y20), 100 * same_sign(res$beta_y20, bench$beta),
                            100 * mean(res$F_y20 > 10), 100 * mean(res$F_y20 > 23.1)))
))
fwrite(summ, OUT_SUM)
cat("\n==== SPLIT-SAMPLE FIRST-STAGE FALSIFICATION ====\n")
print(summ)

# ---- figure: distribution of split-sample first-stage coefficient -------
plt <- rbind(
  data.table(variant = "Split both halves",        beta = res$beta_both),
  data.table(variant = "Split 2020 only (full 2024)", beta = res$beta_y20)
)
p <- ggplot(plt, aes(x = beta, fill = variant, colour = variant)) +
  geom_density(alpha = 0.35, linewidth = 0.6) +
  geom_vline(xintercept = bench$beta, linetype = "dashed", colour = PAL[["gray"]], linewidth = 0.7) +
  geom_vline(xintercept = 0, colour = "grey70", linewidth = 0.4) +
  scale_fill_manual(values = c("Split both halves" = PAL[["blue"]],
                               "Split 2020 only (full 2024)" = PAL[["red"]])) +
  scale_colour_manual(values = c("Split both halves" = PAL[["blue"]],
                                 "Split 2020 only (full 2024)" = PAL[["red"]])) +
  labs(x = "First-stage coefficient on Z (200 random docket splits)", y = "Density",
       fill = NULL, colour = NULL) +
  theme_report() + theme(legend.position = "top")
ggsave(OUT_FIG, p, width = 7, height = 4.2)
cat(sprintf("\nWrote %s\n     %s\n     %s\n", OUT_CSV, OUT_SUM, OUT_FIG))
