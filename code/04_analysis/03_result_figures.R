# 03_result_figures.R — causal-result figures for the deck
# ===========================================================================
# PURPOSE: figures that report the ESTIMATION RESULTS (the instrument's data
# universe is described in 02_descriptive_figures.R). Seven blocks:
#
#   [B] First stage, linear (AMV style)     -> firststage_linear.pdf
#   [C] Voter disengagement by seat type    -> voterbehavior_seat_coefplot.pdf
#   [D] Null-family coefficient plots       -> representation_coefplot.pdf
#                                              entrant_coefplot.pdf
#                                              turnout_coefplot.pdf
#   [E] Candidate-supply coefplot           -> candidate_supply_coefplot.pdf
#   [F] Legislative (council) coefplot      -> legislative_coefplot.pdf
#   [G] Seat-type heterogeneity coefplot    -> heterogeneity_seat_coefplot.pdf
#   [H] Gender incidence of consolidation   -> gender_consolidation_coefplot.pdf
#
# Figure convention (see CLAUDE.md): titles and footnotes live on the Beamer
# frame, NOT in the image. Colors come from code/utils/figure_style.R (PAL) and
# theme_report() blanks title/subtitle/caption. Do not re-add ad-hoc hex or plot
# titles here.
#
# Requires: fixest, ggplot2, dplyr, scales, data.table

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
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
# [A] FIRST-STAGE RESIDUALS — partial out the controls and the state FE from
#     both the endogenous variable and the instrument. Emits no figure of its
#     own; [B] bins these residuals into the linear first-stage plot.
# ============================================================================
cat("\n[A] Residualizing the first stage on controls + state FE...\n")

ctrl_formula <- paste(c(ctrls_avail, "SG_UF"), collapse = " + ")
resid_endog <- residuals(feols(as.formula(paste(ENDOG, "~", ctrl_formula)),
                               data = samp, warn = FALSE, notes = FALSE))
resid_instr <- residuals(feols(as.formula(paste(INSTR, "~", ctrl_formula)),
                               data = samp, warn = FALSE, notes = FALSE))
bs_df <- data.frame(x = resid_instr, y = resid_endog)


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
# [C] VOTER DISENGAGEMENT by seat type (mayoral ballot). Turnout is compulsory,
#     so withdrawal cannot show up as staying home -- it shows up inside the
#     ballot: blank / null votes that elect no one, and a falling valid share.
#     Three series per outcome -- the POOLED mayoral estimate plus the two seat
#     subsamples (open = term-limited, contested = incumbent eligible) -- so the
#     headline voter result and where it concentrates read off ONE exhibit.
#     Faceted by outcome with a FREE x: the valid-vote delta sits on a wider
#     scale than blank/null. Seat is on the y-axis, so color is free to encode
#     5%-significance as in the other coefplots (no legend needed); a faint rule
#     separates the pooled row from the two subsamples.
#     CONSOLIDATION outcomes are deliberately absent -- they carry their own
#     exhibits (executive_iv_competition.tex; heterogeneity_seat_coefplot.pdf in
#     [G] keeps both channels for the report deck). This block replaced the
#     orphaned voterbehavior_forest.pdf, which no deck consumed and which showed
#     compulsory turnout (a mechanical null) instead of the valid-vote share.
# ============================================================================
cat("\n[C] Voter disengagement by seat type...\n")

iv_raw <- as.data.frame(fread(file.path(REGRESSIONS, "executive_margin_iv_fixest.csv")))
spec_col <- if ("spec" %in% names(iv_raw)) "spec" else "sample"
iv_raw$spec_name <- iv_raw[[spec_col]]

DISENGAGE_OUTCOMES <- c(
  delta_blank_rate_2024_2020      = "Blank-vote rate",
  delta_null_rate_2024_2020       = "Null-vote rate",
  delta_valid_vote_rate_2024_2020 = "Valid-vote rate")
DISENGAGE_SPECS <- c(
  baseline       = "All mayoral races",
  open_seat      = "Open seat (term-limited)",
  contested_seat = "Contested (incumbent)")

dis_df <- iv_raw %>%
  filter(spec_name %in% names(DISENGAGE_SPECS),
         outcome   %in% names(DISENGAGE_OUTCOMES)) %>%
  mutate(
    trait   = factor(unname(DISENGAGE_OUTCOMES[outcome]),
                     levels = unname(DISENGAGE_OUTCOMES)),
    seat    = factor(unname(DISENGAGE_SPECS[spec_name]),
                     levels = rev(unname(DISENGAGE_SPECS))),
    sig     = p < 0.05,
    ci90_lo = coef - qnorm(0.95) * se,
    ci90_hi = coef + qnorm(0.95) * se,
    ci95_lo = ifelse(is.na(ci95_low_tF),  coef - 1.96 * se, ci95_low_tF),
    ci95_hi = ifelse(is.na(ci95_high_tF), coef + 1.96 * se, ci95_high_tF))

p_disengage <- ggplot(dis_df, aes(x = coef, y = seat)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
  geom_hline(yintercept = 2.5, color = "grey85", linewidth = 0.4) +
  geom_errorbarh(aes(xmin = ci95_lo, xmax = ci95_hi),
                 height = 0, color = COL_GRAY, linewidth = 0.6, alpha = 0.6) +
  geom_errorbarh(aes(xmin = ci90_lo, xmax = ci90_hi, color = sig),
                 height = 0, linewidth = 1.4) +
  geom_point(aes(color = sig), size = 3.0) +
  geom_text(aes(label = sprintf("%+.3f", coef)),
            vjust = -1.1, size = 2.8, color = "grey25") +
  scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE), guide = "none") +
  facet_wrap(~ trait, ncol = 3, scales = "free_x") +
  scale_x_continuous(expand = expansion(mult = 0.20),
                     labels = scales::label_number(accuracy = 0.005)) +
  labs(x = expression("2SLS effect of " * Delta * " log(1 + adversarial lawsuits)"),
       y = NULL) +
  theme_report() +
  theme(panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank(),
        strip.text = element_text(face = "bold"),
        axis.text.y = element_text(size = 9.5))
ggsave(file.path(FIG_DIR, "voterbehavior_seat_coefplot.pdf"),
       p_disengage, width = 9.5, height = 3.0)  # flat aspect: the deck frame is
                                                # height-bound, so a shorter
                                                # figure embeds WIDER
cat("  Saved voterbehavior_seat_coefplot.pdf (3 ballot outcomes x pooled/open/contested)\n")


# ============================================================================
# [D] COEFFICIENT PLOTS for the "nothing moves" families
#     One dot per outcome, 90% (thick) + 95% tF (thin) CI, zero line. Significant-
#     at-5% points highlighted; coefficient printed at the point. Titles are set
#     on the Beamer frame (theme_report blanks them), so make_coefplot no longer
#     bakes a title.
# ============================================================================
cat("\n[D] Coefficient plots (null families)...\n")

iv_base <- iv_raw[iv_raw$spec_name == "baseline", ]

make_coefplot <- function(outcomes, xexpand = 0.012, src = iv_base) {
  d <- src[match(names(outcomes), src$outcome), ]
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


# ============================================================================
# [E] CANDIDATE-SUPPLY coefplot (Engine 1: "who runs" is a null, both offices)
#     Mayoral + council field size and composition on one comparable axis; the
#     legislative rows are pulled from the council IV file and suffixed _LEG so
#     the shared delta_female_share key does not collide. Spending ("how they
#     campaign") is a different (log-point) scale, so it stays a table (app:spending),
#     not a dot here.
# ============================================================================
cat("\n[E] Candidate-supply coefplot (symmetric both-office demographic panel)...\n")

leg_raw <- as.data.frame(fread(file.path(REGRESSIONS, "legislative_iv_fixest.csv")))
leg_base <- leg_raw[leg_raw$spec == "baseline", ]

# The full "who runs" face on one comparable axis, both offices. Field size is a
# log1p count delta; the five demographics are candidate-pool shares (0-1). All
# sit on the same small scale. Mean candidate age is on a YEARS scale (mayoral
# +0.86 yr p=.22; council -0.32 yr p=.02) -- off this axis, so it is reported in
# the frame text, not plotted here. Faceted by office so the symmetric null reads
# at a glance.
SUPPLY_LEVELS <- c("Field size (count)", "Female share", "Non-white share",
                   "Higher-ed share", "New-candidate share", "Incumbent share")
may_map <- c(
  delta_log1p_n_candidates_with_votes_2024_2020 = "Field size (count)",
  delta_female_share_2024_2020                  = "Female share",
  delta_nonwhite_share_2024_2020                = "Non-white share",
  delta_higher_education_share_2024_2020        = "Higher-ed share",
  delta_new_candidate_share_2024_2020           = "New-candidate share",
  delta_incumbent_candidate_share_2024_2020     = "Incumbent share")
cou_map <- c(
  delta_log1p_total_candidates_2024_2020        = "Field size (count)",
  delta_female_share_2024_2020                  = "Female share",
  delta_nonwhite_share_2024_2020                = "Non-white share",
  delta_higher_education_share_2024_2020        = "Higher-ed share",
  delta_new_candidate_share_2024_2020           = "New-candidate share",
  delta_incumbent_candidate_share_2024_2020     = "Incumbent share")

build_supply <- function(src, map, office) {
  if ("estimator" %in% names(src)) src <- src[src$estimator == "2sls" |
                                              is.na(src$estimator), ]
  d <- src[match(names(map), src$outcome), ]
  d <- d[!is.na(d$outcome), , drop = FALSE]
  d$trait   <- unname(map[d$outcome])
  d$office  <- office
  d$ci90_lo <- d$coef - qnorm(0.95) * d$se
  d$ci90_hi <- d$coef + qnorm(0.95) * d$se
  d$ci95_lo <- if ("ci95_low_tF"  %in% names(d)) d$ci95_low_tF  else d$coef - 1.96 * d$se
  d$ci95_hi <- if ("ci95_high_tF" %in% names(d)) d$ci95_high_tF else d$coef + 1.96 * d$se
  d$sig     <- d$p < 0.05
  d[, c("trait", "office", "coef", "se", "p", "sig",
        "ci90_lo", "ci90_hi", "ci95_lo", "ci95_hi")]
}
sup <- dplyr::bind_rows(
  build_supply(iv_base,  may_map, "Mayoral (prefeito)"),
  build_supply(leg_base, cou_map, "Council (vereador)"))
sup$trait  <- factor(sup$trait, levels = rev(SUPPLY_LEVELS))
sup$office <- factor(sup$office,
                     levels = c("Mayoral (prefeito)", "Council (vereador)"))

p_supply <- ggplot(sup, aes(x = coef, y = trait)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
  geom_errorbarh(aes(xmin = ci95_lo, xmax = ci95_hi),
                 height = 0, color = COL_GRAY, linewidth = 0.6, alpha = 0.6) +
  geom_errorbarh(aes(xmin = ci90_lo, xmax = ci90_hi, color = sig),
                 height = 0, linewidth = 1.4) +
  geom_point(aes(color = sig), size = 3.0) +
  geom_text(aes(label = sprintf("%+.3f", coef)),
            vjust = -1.0, size = 2.8, color = "grey25") +
  scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE), guide = "none") +
  facet_wrap(~ office) +
  scale_x_continuous(expand = expansion(mult = 0.16),
                     labels = scales::label_number(accuracy = 0.01)) +
  labs(x = expression("2SLS effect of " * Delta * " log(1 + adversarial lawsuits)"),
       y = NULL) +
  theme_report() +
  theme(panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank(),
        strip.text = element_text(face = "bold"),
        axis.text.y = element_text(size = 9.5))
ggsave(file.path(FIG_DIR, "candidate_supply_coefplot.pdf"),
       p_supply, width = 9, height = 3.8)
cat("  Saved candidate_supply_coefplot.pdf (both offices, 6 traits each)\n")


# ============================================================================
# [F] LEGISLATIVE coefplot (the council placebo office, one exhibit for all
#     of candidate-pool + elected composition). Share outcomes only (common
#     0-1 scale). Elected female share is the lone point whose tF CI excludes
#     zero -- shown honestly, flagged as not surviving multiple testing.
# ============================================================================
cat("\n[F] Legislative (council) coefplot...\n")

leg_outcomes <- c(
  delta_female_share_2024_2020              = "Field: female share",
  delta_nonwhite_share_2024_2020            = "Field: non-white share",
  delta_higher_education_share_2024_2020    = "Field: higher-ed share",
  delta_new_candidate_share_2024_2020       = "Field: new-candidate share",
  delta_incumbent_candidate_share_2024_2020 = "Field: incumbent share",
  delta_elected_female_share_2024_2020      = "Elected: female share",
  delta_elected_nonwhite_share_2024_2020    = "Elected: non-white share",
  delta_elected_higher_ed_share_2024_2020   = "Elected: higher-ed share",
  delta_incumbent_reelected_share_2024_2020 = "Elected: incumbent re-elected")
ggsave(file.path(FIG_DIR, "legislative_coefplot.pdf"),
       make_coefplot(leg_outcomes, src = leg_base), width = 8, height = 4.6)
cat("  Saved legislative_coefplot.pdf\n")


# ============================================================================
# [G] CONTESTED x OPEN-SEAT heterogeneity coefplot (mayoral). Two seat series
#     (open = term-limited, no incumbent; contested = incumbent eligible) across
#     two channels: consolidation (margin / winner share / majority) and voter
#     disengagement (blank / null / valid). x is FREE per channel -- the winner-
#     majority (>50%) delta is on a much wider scale than the vote-share deltas.
#     Color encodes SEAT TYPE here (not 5%-significance as elsewhere): this is a
#     two-series exhibit, so it carries a legend. The banded numbers live in the
#     appendix (executive_iv_heterogeneity_seat.tex).
# ============================================================================
cat("\n[G] Contested x open-seat heterogeneity coefplot...\n")

het_map <- c(
  delta_margin_top1_top2_2024_2020  = "Winner's top-two margin",
  delta_winner_vote_share_2024_2020 = "Winner vote share",
  delta_winner_majority_2024_2020   = "Winner majority (>50%)",
  delta_blank_rate_2024_2020        = "Blank-vote rate",
  delta_null_rate_2024_2020         = "Null-vote rate",
  delta_valid_vote_rate_2024_2020   = "Valid-vote rate")
het_channel <- c(
  delta_margin_top1_top2_2024_2020  = "Consolidation",
  delta_winner_vote_share_2024_2020 = "Consolidation",
  delta_winner_majority_2024_2020   = "Consolidation",
  delta_blank_rate_2024_2020        = "Voter disengagement",
  delta_null_rate_2024_2020         = "Voter disengagement",
  delta_valid_vote_rate_2024_2020   = "Voter disengagement")

build_het <- function(spec, seat_label) {
  d <- iv_raw[iv_raw$spec_name == spec & iv_raw$outcome %in% names(het_map), ]
  d <- d[match(names(het_map), d$outcome), ]
  d <- d[!is.na(d$outcome), , drop = FALSE]
  d$trait   <- unname(het_map[d$outcome])
  d$channel <- unname(het_channel[d$outcome])
  d$seat    <- seat_label
  d$ci90_lo <- d$coef - qnorm(0.95) * d$se
  d$ci90_hi <- d$coef + qnorm(0.95) * d$se
  d$ci95_lo <- if ("ci95_low_tF"  %in% names(d)) d$ci95_low_tF  else d$coef - 1.96 * d$se
  d$ci95_hi <- if ("ci95_high_tF" %in% names(d)) d$ci95_high_tF else d$coef + 1.96 * d$se
  d[, c("trait", "channel", "seat", "coef", "se", "p",
        "ci90_lo", "ci90_hi", "ci95_lo", "ci95_hi")]
}
het <- dplyr::bind_rows(
  build_het("open_seat",      "Open seat (term-limited)"),
  build_het("contested_seat", "Contested (incumbent)"))
het$trait   <- factor(het$trait, levels = rev(unname(het_map)))
het$channel <- factor(het$channel, levels = c("Consolidation", "Voter disengagement"))
het$seat    <- factor(het$seat,
                      levels = c("Contested (incumbent)", "Open seat (term-limited)"))

het_pos <- position_dodge(width = 0.55)
p_het <- ggplot(het, aes(x = coef, y = trait, color = seat, group = seat)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
  geom_errorbarh(aes(xmin = ci95_lo, xmax = ci95_hi),
                 height = 0, linewidth = 0.6, alpha = 0.45, position = het_pos) +
  geom_errorbarh(aes(xmin = ci90_lo, xmax = ci90_hi),
                 height = 0, linewidth = 1.4, position = het_pos) +
  geom_point(size = 3.0, position = het_pos) +
  scale_color_manual(values = c("Contested (incumbent)"    = COL_BLUE,
                                "Open seat (term-limited)"  = COL_RED),
                     name = NULL) +
  facet_wrap(~ channel, scales = "free") +
  scale_x_continuous(expand = expansion(mult = 0.18),
                     labels = scales::label_number(accuracy = 0.01)) +
  labs(x = expression("2SLS effect of " * Delta * " log(1 + adversarial lawsuits)"),
       y = NULL) +
  theme_report() +
  theme(panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank(),
        strip.text = element_text(face = "bold"),
        axis.text.y = element_text(size = 9.5),
        legend.position = "bottom")
ggsave(file.path(FIG_DIR, "heterogeneity_seat_coefplot.pdf"),
       p_het, width = 9.5, height = 3.7)
cat("  Saved heterogeneity_seat_coefplot.pdf (2 seat series x 2 channels)\n")


# ============================================================================
# [H] GENDER INCIDENCE of the consolidation (mayoral). Layer 3 says vote moves
#     from the runner-up slot to the winner slot; this asks whose share moves.
#     Left panel = the unconditional decomposition (female + male sum EXACTLY to
#     the layer-3 totals, same N). Right panel = the female-minus-male gap in
#     each slot, estimated as its own outcome -- that p-value, not the contrast
#     between a starred and an unstarred component, is the differential test.
#     Color encodes 5%-significance (the script's dominant convention, blocks
#     C/D/E), NOT gender: the point of the exhibit is which component moves, and
#     a gender-keyed red/blue legend would collide with the deck's red=barrier /
#     green=leveller semantics. Gender is carried by the row labels instead.
# ============================================================================
cat("\n[H] Gender incidence of the consolidation...\n")

FAC_COMP <- "Vote-share component"
FAC_GAP  <- "Gender gap (female - male)"
gen_map <- rbind(
  data.frame(outcome = "delta_female_winner_vote_share_2024_2020",
             panel = FAC_COMP, row = "Female winner"),
  data.frame(outcome = "delta_male_winner_vote_share_2024_2020",
             panel = FAC_COMP, row = "Male winner"),
  data.frame(outcome = "delta_female_runnerup_vote_share_2024_2020",
             panel = FAC_COMP, row = "Female runner-up"),
  data.frame(outcome = "delta_male_runnerup_vote_share_2024_2020",
             panel = FAC_COMP, row = "Male runner-up"),
  data.frame(outcome = "delta_female_male_winner_gap_2024_2020",
             panel = FAC_GAP,  row = "Winner's slot"),
  data.frame(outcome = "delta_female_male_runnerup_gap_2024_2020",
             panel = FAC_GAP,  row = "Runner-up's slot"))

gen_df <- iv_raw %>%
  filter(spec_name == "baseline", outcome %in% gen_map$outcome) %>%
  left_join(gen_map, by = "outcome") %>%
  mutate(
    row     = factor(row, levels = rev(gen_map$row)),
    panel   = factor(panel, levels = c(FAC_COMP, FAC_GAP)),
    sig     = p < 0.05,
    ci90_lo = coef - qnorm(0.95) * se,
    ci90_hi = coef + qnorm(0.95) * se,
    ci95_lo = ifelse(is.na(ci95_low_tF),  coef - 1.96 * se, ci95_low_tF),
    ci95_hi = ifelse(is.na(ci95_high_tF), coef + 1.96 * se, ci95_high_tF))

missing_gen <- setdiff(gen_map$outcome, gen_df$outcome)
if (length(missing_gen))
  cat("  WARNING: outcome(s) absent from the results file:",
      paste(missing_gen, collapse = ", "), "\n")

p_gender <- ggplot(gen_df, aes(x = coef, y = row)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey45", linewidth = 0.5) +
  geom_errorbarh(aes(xmin = ci95_lo, xmax = ci95_hi),
                 height = 0, color = COL_GRAY, linewidth = 0.6, alpha = 0.6) +
  geom_errorbarh(aes(xmin = ci90_lo, xmax = ci90_hi, color = sig),
                 height = 0, linewidth = 1.4) +
  geom_point(aes(color = sig), size = 3.0) +
  geom_text(aes(label = sprintf("%+.3f", coef)),
            vjust = -1.1, size = 2.8, color = "grey25") +
  scale_color_manual(values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE), guide = "none") +
  facet_wrap(~ panel, scales = "free") +
  scale_x_continuous(expand = expansion(mult = 0.22),
                     labels = scales::label_number(accuracy = 0.01)) +
  labs(x = expression("2SLS effect of " * Delta * " log(1 + adversarial lawsuits)"),
       y = NULL) +
  theme_report() +
  theme(panel.grid.major.x = element_line(color = "grey90"),
        panel.grid.major.y = element_blank(),
        strip.text = element_text(face = "bold"),
        axis.text.y = element_text(size = 9.5))
# Flat aspect: the deck frame is height-bound, so a shorter figure embeds WIDER.
# Flatter than the other coefplots (aspect 3.6 vs 3.2) because this frame carries
# more prose above the exhibit, tightening the height cap further.
ggsave(file.path(FIG_DIR, "gender_consolidation_coefplot.pdf"),
       p_gender, width = 10.0, height = 2.8)
cat("  Saved gender_consolidation_coefplot.pdf (4 components + 2 slot gaps)\n")

cat("\nAll result figures complete.\n")
cat(sprintf("  Output directory: %s\n", FIG_DIR))
