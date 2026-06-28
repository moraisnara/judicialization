# 24c_shock_granularity_figure.R — AMV-style "estimate vs. granularity" robustness
#
# Ash-Morelli-Vannoni (JPE 2025) defend their topic count by SHOWING the 2SLS
# estimate is stable as they vary the number of LDA topics K in {6,...,48}, and
# that first-stage relevance survives at every K (their relevance comes from a
# majority of topics). Our litigation data are the mirror image: the NULL is
# grain-invariant, but first-stage RELEVANCE is not — it collapses as the shock
# partition gets finer, because our cells are sparse. This figure makes that
# contrast visual, in the AMV idiom.
#
# Reads output/tables/regressions/shock_granularity_fstage.csv
#   (built by 24_shock_granularity.py + 24b_shock_granularity_fstage.R).
# Writes output/figures/shock_granularity_robustness.pdf.
#
# Panel A: first-stage F by shock grain, with the Olea-Pflueger 23.1 weak-IV bar.
# Panel B: 2SLS coef +/- 95% CI by grain, per representative outcome — coefs stay
#          near zero (null), but CIs explode once the instrument loses relevance.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(ggplot2)
  library(dplyr)
  library(patchwork)
  library(data.table)
})

args      <- commandArgs(trailingOnly = FALSE)
file_arg  <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0)
  dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
ROOT        <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
REGRESSIONS <- file.path(ROOT, "output", "tables", "regressions")
FIG_DIR     <- file.path(ROOT, "output", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

COL_BLUE <- "#1a5276"
COL_GRAY <- "#717d7e"
COL_RED  <- "#c0392b"
WEAK_F   <- 23.1            # Olea-Pflueger (2013) 5% TSLS rule-of-thumb

theme_clean <- function(...) {
  theme_minimal(base_size = 11) +
    theme(panel.grid.minor = element_blank(),
          panel.grid.major.x = element_blank(),
          axis.line.x = element_line(color = "grey40"),
          plot.title = element_text(face = "bold", size = 11),
          plot.caption = element_text(color = "grey50", size = 7, hjust = 0), ...)
}

res <- as.data.frame(fread(file.path(REGRESSIONS, "shock_granularity_fstage.csv")))

# grain ordering + readable labels (cells / K_eff from 24_shock_granularity.py)
grain_lab <- c(act10   = "act10\n(10 cells, K_eff~6)",
               subject = "subject\n(84 cells, K_eff~62)",
               pair    = "pair\n(395 cells, K_eff~200)")
res$grain <- factor(res$grain, levels = names(grain_lab), labels = grain_lab)

out_lab <- c(delta_others_vote_share_2024_2020             = "Others' vote share",
             delta_log1p_n_candidates_with_votes_2024_2020 = "log(N candidates)",
             delta_turnout_rate_2024_2020                  = "Turnout rate",
             delta_female_share_2024_2020                  = "Female cand. share")

# ── Panel A: first-stage F by grain ───────────────────────────────────────────
fs <- res[res$stage == "first", ]
pA <- ggplot(fs, aes(grain, first_stage_F)) +
  geom_hline(yintercept = WEAK_F, linetype = "dashed", color = COL_RED) +
  annotate("text", x = Inf, y = WEAK_F + 4, hjust = 1.05,
           label = "weak-IV bar (F = 23.1)", color = COL_RED, size = 3) +
  geom_col(fill = COL_BLUE, width = 0.6) +
  geom_text(aes(label = sprintf("F = %.1f", first_stage_F)),
            vjust = -0.5, size = 3.4) +
  labs(title = "A. First-stage relevance collapses as the shock partition gets finer",
       x = NULL, y = "First-stage F") +
  theme_clean()

# ── Panel B: 2SLS coef +/- 95% CI by grain, per outcome ───────────────────────
ss <- res[res$stage == "second", ]
ss$lo <- ss$coef - 1.96 * ss$se
ss$hi <- ss$coef + 1.96 * ss$se
ss$outcome <- factor(out_lab[ss$outcome], levels = out_lab)

pB <- ggplot(ss, aes(grain, coef)) +
  geom_hline(yintercept = 0, color = COL_GRAY) +
  geom_pointrange(aes(ymin = lo, ymax = hi), color = COL_BLUE, size = 0.4) +
  facet_wrap(~outcome, scales = "free_y", nrow = 1) +
  labs(title = "B. 2SLS estimate stays near zero, but its CI explodes once relevance is gone",
       x = NULL, y = "2SLS coefficient (95% CI)",
       caption = paste0(
         "Each finer partition raises the effective number of shocks (K_eff 6 -> 62 -> 200) but destroys first-stage relevance ",
         "(F 26.7 -> 0.7 -> 10.4),\nbecause sparse class x subject cells yield noisy national shocks. ",
         "The null is grain-invariant; relevance is not. Mirror image of Ash-Morelli-Vannoni (JPE 2025),\n",
         "whose dense legislative topics keep relevance at every K in {6,...,48}.")) +
  theme_clean(strip.text = element_text(face = "bold", size = 9))

fig <- pA / pB + plot_layout(heights = c(1, 1.1))
out <- file.path(FIG_DIR, "shock_granularity_robustness.pdf")
ggsave(out, fig, width = 10, height = 7.5)
cat(sprintf("Wrote: %s\n", out))
