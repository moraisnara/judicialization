# 03_result_figures.R — causal-result figures for the deck
# ===========================================================================
# PURPOSE: figures that report the ESTIMATION RESULTS (the instrument's data
# universe is described in 02_descriptive_figures.R). Four blocks:
#
#   [A] First stage, binscatter (cubic)     -> firststage_binscatter.pdf
#   [B] First stage, linear (AMV style)     -> firststage_linear.pdf
#   [C] Voter-behavior forest plot          -> voterbehavior_forest.pdf
#   [D] Null-family coefficient plots       -> representation_coefplot.pdf
#                                              entrant_coefplot.pdf
#                                              turnout_coefplot.pdf
#
# Figure convention (see CLAUDE.md): titles and footnotes live on the Beamer
# frame, NOT in the image. Colors come from code/utils/figure_style.R (PAL) and
# theme_report() blanks title/subtitle/caption. Do not re-add ad-hoc hex or plot
# titles here.
#
# Requires: fixest, binsreg, ggplot2, dplyr, scales, data.table

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(binsreg)
  library(ggplot2)
  library(dplyr)
  library(scales)
  library(data.table)
})

# ── paths ─────────────────────────────────────────────────────────────────────
args      <- commandArgs(trailingOnly = FALSE)
file_arg  <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else getwd()
ROOT        <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
UTILS       <- file.path(ROOT, "code", "utils")
ESTIMATION  <- file.path(ROOT, "data", "estimation")
REGRESSIONS <- file.path(ROOT, "output", "tables", "regressions")
FIG_DIR     <- file.path(ROOT, "output", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

source(file.path(UTILS, "figure_style.R"))   # PAL, PAL_CYCLE, theme_report()
COL_BLUE <- unname(PAL["blue"])
COL_GRAY <- unname(PAL["gray"])
COL_RED  <- unname(PAL["red"])

# ── load design ───────────────────────────────────────────────────────────────
cat("Loading design...\n")
df <- as.data.frame(fread(
  file.path(ESTIMATION, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
if ("municipality_id_tse" %in% names(df) && !"SG_UE" %in% names(df))
  names(df)[names(df) == "municipality_id_tse"] <- "SG_UE"
cat(sprintf("  N = %d municipalities\n", nrow(df)))

ENDOG <- "delta_log1p_competition_lawsuits_2024_2020"
INSTR <- "bartik_iv_2020_2024"
CTRLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
)
ctrls_avail <- intersect(CTRLS, names(df))
req  <- unique(c(ENDOG, INSTR, "cluster_id", "SG_UF", ctrls_avail))
samp <- df[complete.cases(df[, req]), ]
cat(sprintf("  Baseline sample: N = %d\n", nrow(samp)))


# ============================================================================
# [A] BINSCATTER — first stage (cubic, appendix diagnostic)
# ============================================================================
cat("\n[A] Binscatter (first stage)...\n")

ctrl_formula <- paste(c(ctrls_avail, "SG_UF"), collapse = " + ")
resid_endog <- residuals(feols(as.formula(paste(ENDOG, "~", ctrl_formula)),
                               data = samp, warn = FALSE, notes = FALSE))
resid_instr <- residuals(feols(as.formula(paste(INSTR, "~", ctrl_formula)),
                               data = samp, warn = FALSE, notes = FALSE))
bs_df <- data.frame(x = resid_instr, y = resid_endog)

set.seed(42)
bs <- binsreg(y = bs_df$y, x = bs_df$x, nbins = 30,
              line = c(3, 3), ci = c(3, 3), cb = NULL,
              plotxrange = quantile(bs_df$x, c(0.01, 0.99)))
bin_df  <- bs$data.plot$`Group Full Sample`$data.dots
line_df <- bs$data.plot$`Group Full Sample`$data.line

p_bin <- ggplot() +
  geom_ribbon(data = bs$data.plot$`Group Full Sample`$data.ci,
              aes(x = x, ymin = ci.l, ymax = ci.r), fill = COL_BLUE, alpha = 0.15) +
  geom_line(data = line_df, aes(x = x, y = fit), color = COL_BLUE, linewidth = 0.9) +
  geom_point(data = bin_df, aes(x = x, y = fit), color = COL_BLUE, size = 2.2) +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  labs(x = "Bartik IV (residualised on 7 controls + state FE)",
       y = expression(Delta*log(1 + lawsuits) ~ " (residualised)")) +
  theme_report()
ggsave(file.path(FIG_DIR, "firststage_binscatter.pdf"), p_bin, width = 7, height = 4.5)
cat("  Saved firststage_binscatter.pdf\n")


# ============================================================================
# [B] LINEAR FIRST STAGE (Ash–Morelli–Vannoni style)
#     Straight OLS fit with the cluster-robust slope + first-stage F annotated;
#     the slope is read from the saved baseline regression so the figure number
#     matches the paper/prose exactly (a re-fit on binned means would differ).
# ============================================================================
cat("\n[B] Linear first stage (AMV style)...\n")

fs_csv <- read.csv(file.path(REGRESSIONS, "executive_margin_first_stage_fixest.csv"),
                   stringsAsFactors = FALSE)
fs_row  <- fs_csv[fs_csv$variant == "adversarial" & fs_csv$spec == "baseline", ][1, ]
fs_beta <- as.numeric(fs_row$coef)
fs_se   <- as.numeric(fs_row$se)
fs_F    <- as.numeric(fs_row$first_stage_F)

nb <- 25
bs_df$xbin <- cut(bs_df$x,
                  breaks = quantile(bs_df$x, probs = seq(0, 1, length.out = nb + 1),
                                    na.rm = TRUE),
                  include.lowest = TRUE)
binned <- aggregate(cbind(x, y) ~ xbin, data = bs_df, FUN = mean)

xr <- quantile(bs_df$x, c(0.01, 0.99))
line_lin <- data.frame(x = xr, y = fs_beta * xr)   # intercept ~0 in residual space

annot   <- sprintf("hat(beta) == '%.3f'*' ('*'%.3f'*')'", fs_beta, fs_se)
annot_F <- sprintf("'First-stage'~italic(F) == '%.1f'", fs_F)

p_lin <- ggplot() +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_point(data = binned, aes(x = x, y = y), color = COL_BLUE, size = 2.4, alpha = 0.9) +
  geom_line(data = line_lin, aes(x = x, y = y), color = COL_RED, linewidth = 1.0) +
  annotate("text", x = xr[1], y = max(binned$y),
           label = annot,   parse = TRUE, hjust = 0, vjust = 1, size = 3.6) +
  annotate("text", x = xr[1], y = max(binned$y) * 0.82,
           label = annot_F, parse = TRUE, hjust = 0, vjust = 1, size = 3.6) +
  coord_cartesian(xlim = xr) +
  labs(x = "Predicted exposure (Bartik IV, residualised on controls + state FE)",
       y = expression(Delta*log(1 + lawsuits) ~ "(residualised)")) +
  theme_report()
ggsave(file.path(FIG_DIR, "firststage_linear.pdf"), p_lin, width = 7, height = 4.5)
cat(sprintf("  Saved firststage_linear.pdf  (beta=%.3f, se=%.3f, F=%.1f)\n",
            fs_beta, fs_se, fs_F))


# ============================================================================
# [C] VOTER-BEHAVIOR FOREST PLOT
# ============================================================================
cat("\n[C] Voter behavior forest plot...\n")

iv_raw <- as.data.frame(fread(file.path(REGRESSIONS, "executive_margin_iv_fixest.csv")))
spec_col <- if ("spec" %in% names(iv_raw)) "spec" else "sample"
iv_raw$spec_name <- iv_raw[[spec_col]]

vb_outcomes <- c("delta_turnout_rate_2024_2020",
                 "delta_null_rate_2024_2020",
                 "delta_blank_rate_2024_2020")
spec_labels <- c(baseline = "Baseline",
                 open_seat = "Open seat",
                 contested_seat = "Contested seat")
outcome_labels <- c(delta_turnout_rate_2024_2020 = "Turnout rate",
                    delta_null_rate_2024_2020    = "Null vote rate",
                    delta_blank_rate_2024_2020   = "Blank vote rate")

vb_df <- iv_raw %>%
  filter(spec_name %in% names(spec_labels), outcome %in% vb_outcomes) %>%
  mutate(
    spec_label    = factor(spec_labels[spec_name], levels = rev(unname(spec_labels))),
    outcome_label = factor(outcome_labels[outcome], levels = unname(outcome_labels)),
    ci90_lo = coef - qnorm(0.95) * se, ci90_hi = coef + qnorm(0.95) * se,
    ci95_lo = coef - 1.96 * se,        ci95_hi = coef + 1.96 * se)

p_forest <- ggplot(vb_df, aes(x = coef, y = spec_label)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey50", linewidth = 0.5) +
  geom_linerange(aes(xmin = ci95_lo, xmax = ci95_hi),
                 color = COL_BLUE, linewidth = 0.6, alpha = 0.5) +
  geom_linerange(aes(xmin = ci90_lo, xmax = ci90_hi), color = COL_BLUE, linewidth = 1.2) +
  geom_point(aes(color = (p < 0.10)), size = 2.5) +
  scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE),
                     labels = c(`TRUE` = "p < 0.10", `FALSE` = "p ≥ 0.10"), name = NULL) +
  facet_wrap(~ outcome_label, ncol = 3) +
  scale_x_continuous(labels = scales::label_number(accuracy = 0.01)) +
  labs(x = "IV coefficient (2SLS)", y = NULL) +
  theme_report() +
  theme(legend.position = "bottom",
        strip.text = element_text(face = "bold"),
        panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank())
ggsave(file.path(FIG_DIR, "voterbehavior_forest.pdf"), p_forest, width = 9, height = 4.5)
cat("  Saved voterbehavior_forest.pdf\n")


# ============================================================================
# [D] COEFFICIENT PLOTS for the "nothing moves" families
#     One dot per outcome, 90% (thick) + 95% tF (thin) CI, zero line. Significant-
#     at-5% points highlighted; coefficient printed at the point. Titles are set
#     on the Beamer frame (theme_report blanks them), so make_coefplot no longer
#     bakes a title.
# ============================================================================
cat("\n[D] Coefficient plots (null families)...\n")

iv_base <- iv_raw[iv_raw$spec_name == "baseline", ]

make_coefplot <- function(outcomes, xexpand = 0.012) {
  d <- iv_base[match(names(outcomes), iv_base$outcome), ]
  d <- d[!is.na(d$outcome), ]
  d$lab <- factor(unname(outcomes[d$outcome]), levels = rev(unname(outcomes)))
  d$sig <- d$p < 0.05
  d$ci90_lo <- d$coef - qnorm(0.95) * d$se
  d$ci90_hi <- d$coef + qnorm(0.95) * d$se
  lo <- if ("ci95_low_tF"  %in% names(d)) d$ci95_low_tF  else d$coef - 1.96 * d$se
  hi <- if ("ci95_high_tF" %in% names(d)) d$ci95_high_tF else d$coef + 1.96 * d$se
  d$ci95_lo <- lo; d$ci95_hi <- hi
  xr  <- range(c(d$ci95_lo, d$ci95_hi, 0))
  pad <- diff(xr) * 0.18 + xexpand
  ggplot(d, aes(x = coef, y = lab)) +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
    geom_errorbarh(aes(xmin = ci95_lo, xmax = ci95_hi),
                   height = 0, color = COL_GRAY, linewidth = 0.6, alpha = 0.6) +
    geom_errorbarh(aes(xmin = ci90_lo, xmax = ci90_hi, color = sig),
                   height = 0, linewidth = 1.4) +
    geom_point(aes(color = sig), size = 3.1) +
    geom_text(aes(label = sprintf("%+.3f", coef)),
              vjust = -1.0, size = 3.1, color = "grey25") +
    scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE), guide = "none") +
    scale_x_continuous(expand = expansion(mult = 0.02, add = pad),
                       labels = scales::label_number(accuracy = 0.01)) +
    labs(x = expression("2SLS effect of " * Delta * " log(1 + adversarial lawsuits)"),
         y = NULL) +
    theme_report() +
    theme(panel.grid.major.x = element_line(color = "grey90"),
          panel.grid.major.y = element_blank(),
          axis.text.y = element_text(size = 10))
}

# T1 — descriptive representation (vote share of candidates in each position)
rep_outcomes <- c(
  delta_female_vote_share_2024_2020              = "Female vote share",
  delta_nonwhite_vote_share_2024_2020            = "Non-white vote share",
  delta_new_candidate_vote_share_2024_2020       = "New-candidate vote share",
  delta_incumbent_candidate_vote_share_2024_2020 = "Incumbent vote share",
  delta_winner_is_female_2024_2020               = "Winner is female (Pr.)",
  delta_winner_is_new_2024_2020                  = "Winner is new entrant (Pr.)")
ggsave(file.path(FIG_DIR, "representation_coefplot.pdf"),
       make_coefplot(rep_outcomes), width = 8, height = 4.2)
cat("  Saved representation_coefplot.pdf\n")

# T2 — renewal / entrant typology (vote share)
ent_outcomes <- c(
  delta_share_first_time_candidates_2024_2020 = "First-time entrants",
  delta_share_serial_challenger_2024_2020     = "Serial challengers",
  delta_share_cross_cycle_returner_2024_2020  = "Cross-cycle returners")
ggsave(file.path(FIG_DIR, "entrant_coefplot.pdf"),
       make_coefplot(ent_outcomes), width = 8, height = 3.0)
cat("  Saved entrant_coefplot.pdf\n")

# Turnout by voter profile (compulsory vs facultative + education)
turn_outcomes <- c(
  delta_compulsory_turnout_2024_2020     = "Compulsory electorate",
  delta_facultative_turnout_2024_2020    = "Facultative electorate (16-17, 70+)",
  delta_low_ed_turnout_2024_2020         = "Low-education voters",
  delta_high_ed_turnout_2024_2020        = "High-education voters",
  delta_analfabeto_turnout_2024_2020     = "Illiterate voters",
  delta_education_turnout_gap_2024_2020  = "Education turnout gap (high - low)")
ggsave(file.path(FIG_DIR, "turnout_coefplot.pdf"),
       make_coefplot(turn_outcomes), width = 8, height = 4.2)
cat("  Saved turnout_coefplot.pdf\n")

cat("\nAll result figures complete.\n")
cat(sprintf("  Output directory: %s\n", FIG_DIR))
