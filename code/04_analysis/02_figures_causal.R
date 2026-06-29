# Presentation figures for electoral judicialization
# Produces:
#   output/figures/binscatter_first_stage.pdf   — binscatter (Appendix-ready)
#   output/figures/forest_voter_behavior.pdf     — voter-behavior forest plot
#   output/figures/bartik_histogram.pdf          — IV histogram (Appendix E1)
#   output/figures/bartik_choropleth.pdf         — IV choropleth (Appendix E2)
#
# Requires: fixest, binsreg, geobr, sf, ggplot2, dplyr, tidyr, patchwork, scales

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(binsreg)
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(patchwork)
  library(scales)
  library(data.table)
})

# ── paths ────────────────────────────────────────────────────────────────────
args      <- commandArgs(trailingOnly = FALSE)
file_arg  <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else getwd()
ROOT         <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION   <- file.path(ROOT, "data", "estimation")
REGRESSIONS  <- file.path(ROOT, "output", "tables", "regressions")
FIG_DIR      <- file.path(ROOT, "output", "figures")
RAW_DIR      <- file.path(ROOT, "data", "raw")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

# ── shared palette ────────────────────────────────────────────────────────────
COL_BLUE <- "#1a5276"
COL_GRAY <- "#717d7e"
COL_RED  <- "#c0392b"

theme_clean <- function(...) {
  theme_minimal(base_size = 11) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major.y = element_line(color = "grey90"),
      panel.grid.major.x = element_blank(),
      axis.line.x = element_line(color = "grey40"),
      plot.title   = element_text(face = "bold", size = 11),
      plot.caption = element_text(color = "grey50", size = 7, hjust = 0),
      ...
    )
}


# ── load design ───────────────────────────────────────────────────────────────
cat("Loading design...\n")
df <- as.data.frame(fread(
  file.path(ESTIMATION, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
# Rename to match FE and choropleth variable names used throughout the script
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
if ("municipality_id_tse" %in% names(df) && !"SG_UE" %in% names(df))
  names(df)[names(df) == "municipality_id_tse"] <- "SG_UE"
cat(sprintf("  N = %d municipalities\n", nrow(df)))

ENDOG <- "delta_log1p_competition_lawsuits_2024_2020"
INSTR <- "bartik_iv_2020_2024"
CTRLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010",
  "margin_2016",
  "log1p_total_valid_votes_2020", "margin_top1_top2_2020",
  "log1p_total_candidates_2020"
)
ctrls_avail <- intersect(CTRLS, names(df))

# complete-case sample for baseline spec
req   <- unique(c(ENDOG, INSTR, "cluster_id", "SG_UF", ctrls_avail))
samp  <- df[complete.cases(df[, req]), ]
cat(sprintf("  Baseline sample: N = %d\n", nrow(samp)))


# ============================================================
# 1. BINSCATTER — first stage
# ============================================================
cat("\n[1] Binscatter (first stage)...\n")

# Residualise both variables on controls + state FE
ctrl_formula <- paste(c(ctrls_avail, "SG_UF"), collapse = " + ")

resid_endog <- residuals(
  feols(as.formula(paste(ENDOG, "~", ctrl_formula)), data = samp,
        warn = FALSE, notes = FALSE)
)
resid_instr <- residuals(
  feols(as.formula(paste(INSTR, "~", ctrl_formula)), data = samp,
        warn = FALSE, notes = FALSE)
)

bs_df <- data.frame(x = resid_instr, y = resid_endog)

# binsreg automatically computes the binscatter + pointwise CI
set.seed(42)
bs <- binsreg(
  y = bs_df$y, x = bs_df$x,
  nbins = 30,
  line    = c(3, 3),   # cubic polynomial line
  ci      = c(3, 3),   # CI around bins
  cb      = NULL,
  plotxrange = quantile(bs_df$x, c(0.01, 0.99))
)

# extract bin means
bin_df <- bs$data.plot$`Group Full Sample`$data.dots
line_df <- bs$data.plot$`Group Full Sample`$data.line

# OLS slope (= first-stage coef in residualised space)
fs_coef <- coef(lm(y ~ x, data = bs_df))["x"]
fs_N    <- nrow(samp)

p_bin <- ggplot() +
  geom_ribbon(
    data = bs$data.plot$`Group Full Sample`$data.ci,
    aes(x = x, ymin = ci.l, ymax = ci.r),
    fill = COL_BLUE, alpha = 0.15
  ) +
  geom_line(
    data = line_df,
    aes(x = x, y = fit),
    color = COL_BLUE, linewidth = 0.9
  ) +
  geom_point(
    data = bin_df,
    aes(x = x, y = fit),
    color = COL_BLUE, size = 2.2
  ) +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  labs(
    x = "Bartik IV (residualised on 7 controls + state FE)",
    y = expression(Delta*log(1 + lawsuits) ~ " (residualised)")
  ) +
  theme_clean()

ggsave(
  file.path(FIG_DIR, "binscatter_first_stage.pdf"),
  p_bin, width = 7, height = 4.5
)
cat("  Saved binscatter_first_stage.pdf\n")


# ============================================================
# 1b. LINEAR FIRST STAGE (Ash–Morelli–Vannoni style)
#     Residualised binscatter with a STRAIGHT OLS fit and the
#     cluster-robust slope + first-stage F annotated. This is the
#     headline first-stage figure (frame 16); the cubic binscatter
#     above is the appendix diagnostic.
# ============================================================
cat("\n[1b] Linear first stage (AMV style)...\n")

# Cluster-robust first stage (FWL: the partialled-out slope equals the
# residual-space OLS slope, so the annotated beta matches the drawn line).
fs_fit <- feols(
  as.formula(paste(ENDOG, "~", INSTR, "+",
                   paste(ctrls_avail, collapse = " + "), "| SG_UF")),
  data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE
)
fs_beta <- as.numeric(coef(fs_fit)[INSTR])
fs_se   <- as.numeric(se(fs_fit)[INSTR])
fs_F    <- (fs_beta / fs_se)^2

# Equal-count bins on the residualised instrument (25 bins, AMV uses ~20).
nb <- 25
bs_df$xbin <- cut(bs_df$x,
                  breaks = quantile(bs_df$x, probs = seq(0, 1, length.out = nb + 1),
                                    na.rm = TRUE),
                  include.lowest = TRUE)
binned <- aggregate(cbind(x, y) ~ xbin, data = bs_df, FUN = mean)

xr <- quantile(bs_df$x, c(0.01, 0.99))
line_lin <- data.frame(x = xr, y = fs_beta * xr)   # intercept ~0 in residual space

annot <- sprintf("hat(beta) == '%.3f'~'('*%.3f*')'", fs_beta, fs_se)
annot_F <- sprintf("First-stage~italic(F) == '%.1f'", fs_F)

p_lin <- ggplot() +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_point(data = binned, aes(x = x, y = y),
             color = COL_BLUE, size = 2.4, alpha = 0.9) +
  geom_line(data = line_lin, aes(x = x, y = y),
            color = COL_RED, linewidth = 1.0) +
  annotate("text", x = xr[1], y = max(binned$y),
           label = annot,   parse = TRUE, hjust = 0, vjust = 1, size = 3.6) +
  annotate("text", x = xr[1], y = max(binned$y) * 0.82,
           label = annot_F, parse = TRUE, hjust = 0, vjust = 1, size = 3.6) +
  coord_cartesian(xlim = xr) +
  labs(
    x = "Predicted exposure (Bartik IV, residualised on controls + state FE)",
    y = expression(Delta*log(1 + lawsuits) ~ "(residualised)")
  ) +
  theme_clean()

ggsave(
  file.path(FIG_DIR, "first_stage_linear.pdf"),
  p_lin, width = 7, height = 4.5
)
cat(sprintf("  Saved first_stage_linear.pdf  (beta=%.3f, se=%.3f, F=%.1f)\n",
            fs_beta, fs_se, fs_F))


# ============================================================
# 2. VOTER BEHAVIOR FOREST PLOT
# ============================================================
cat("\n[2] Voter behavior forest plot...\n")

iv_file <- file.path(REGRESSIONS, "executive_margin_iv_fixest.csv")

iv_raw <- as.data.frame(fread(iv_file))

spec_col <- if ("spec" %in% names(iv_raw)) "spec" else "sample"
iv_raw$spec_name <- iv_raw[[spec_col]]

vb_outcomes <- c(
  "delta_turnout_rate_2024_2020",
  "delta_null_rate_2024_2020",
  "delta_blank_rate_2024_2020"
)

# Non-subgroup specs only for the forest plot
spec_labels <- c(
  baseline          = "Baseline",
  single_zone       = "Single-zone municipalities",
  extended_controls = "Extended controls",
  broader_treatment = "Broader treatment measure"
)

outcome_labels <- c(
  delta_turnout_rate_2024_2020 = "Turnout rate",
  delta_null_rate_2024_2020    = "Null vote rate",
  delta_blank_rate_2024_2020   = "Blank vote rate"
)

vb_df <- iv_raw %>%
  filter(
    spec_name %in% names(spec_labels),
    outcome   %in% vb_outcomes
  ) %>%
  mutate(
    spec_label    = factor(spec_labels[spec_name],
                           levels = rev(unname(spec_labels))),
    outcome_label = factor(outcome_labels[outcome],
                           levels = unname(outcome_labels)),
    ci90_lo = coef - qnorm(0.95) * se,
    ci90_hi = coef + qnorm(0.95) * se,
    ci95_lo = coef - 1.96 * se,
    ci95_hi = coef + 1.96 * se
  )

p_forest <- ggplot(vb_df, aes(x = coef, y = spec_label)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey50", linewidth = 0.5) +
  geom_linerange(
    aes(xmin = ci95_lo, xmax = ci95_hi),
    color = COL_BLUE, linewidth = 0.6, alpha = 0.5
  ) +
  geom_linerange(
    aes(xmin = ci90_lo, xmax = ci90_hi),
    color = COL_BLUE, linewidth = 1.2
  ) +
  geom_point(
    aes(color = (p < 0.10)),
    size = 2.5
  ) +
  scale_color_manual(
    values = c(`TRUE` = COL_RED, `FALSE` = COL_BLUE),
    labels = c(`TRUE` = "p < 0.10", `FALSE` = "p ≥ 0.10"),
    name   = NULL
  ) +
  facet_wrap(~ outcome_label, ncol = 3) +
  scale_x_continuous(labels = scales::label_number(accuracy = 0.01)) +
  labs(
    x = "IV coefficient (2SLS)",
    y = NULL
  ) +
  theme_clean() +
  theme(
    legend.position  = "bottom",
    strip.text       = element_text(face = "bold"),
    panel.grid.major.x = element_line(color = "grey90"),
    panel.grid.major.y = element_blank()
  )

ggsave(
  file.path(FIG_DIR, "forest_voter_behavior.pdf"),
  p_forest, width = 9, height = 4.5
)
cat("  Saved forest_voter_behavior.pdf\n")


# ============================================================
# 2b. COEFFICIENT PLOTS for the "nothing moves" families
#     One dot per outcome, 90% (thick) + 95% tF (thin) CI, zero line.
#     Significant-at-5% points highlighted; coefficient printed at the
#     point so the reader reads the magnitude, not just the position.
#     Replaces the wide null tables on the primary slides (full tables
#     move to the appendix).
# ============================================================
cat("\n[2b] Coefficient plots (null families)...\n")

# baseline-spec rows, keyed by outcome
iv_base <- iv_raw[iv_raw$spec_name == "baseline", ]

make_coefplot <- function(outcomes, title, file, xexpand = 0.012) {
  d <- iv_base[match(names(outcomes), iv_base$outcome), ]
  d <- d[!is.na(d$outcome), ]
  d$lab <- factor(unname(outcomes[d$outcome]), levels = rev(unname(outcomes)))
  d$sig <- d$p < 0.05
  d$ci90_lo <- d$coef - qnorm(0.95) * d$se
  d$ci90_hi <- d$coef + qnorm(0.95) * d$se
  # tF-corrected 95% CI if present, else normal
  lo <- if ("ci95_low_tF"  %in% names(d)) d$ci95_low_tF  else d$coef - 1.96 * d$se
  hi <- if ("ci95_high_tF" %in% names(d)) d$ci95_high_tF else d$coef + 1.96 * d$se
  d$ci95_lo <- lo; d$ci95_hi <- hi
  xr <- range(c(d$ci95_lo, d$ci95_hi, 0))
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
         y = NULL, title = title) +
    theme_clean() +
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
  delta_winner_is_new_vs_2020_2024_2020          = "Winner is new entrant (Pr.)"
)
p_rep <- make_coefplot(rep_outcomes,
  "Descriptive representation — vote share by candidate position",
  "coefplot_representation.pdf")
ggsave(file.path(FIG_DIR, "coefplot_representation.pdf"), p_rep, width = 8, height = 4.2)
cat("  Saved coefplot_representation.pdf\n")

# T2 — renewal / entrant typology (vote share)
ent_outcomes <- c(
  delta_share_first_time_candidates_2024_2020 = "First-time entrants",
  delta_share_serial_challenger_2024_2020     = "Serial challengers",
  delta_share_cross_cycle_returner_2024_2020  = "Cross-cycle returners"
)
p_ent <- make_coefplot(ent_outcomes,
  "Renewal — vote share by entrant type",
  "coefplot_entrant.pdf")
ggsave(file.path(FIG_DIR, "coefplot_entrant.pdf"), p_ent, width = 8, height = 3.0)
cat("  Saved coefplot_entrant.pdf\n")

# Turnout by voter profile (compulsory vs facultative + education)
turn_outcomes <- c(
  delta_compulsory_turnout_2024_2020     = "Compulsory electorate",
  delta_facultative_turnout_2024_2020    = "Facultative electorate (16-17, 70+)",
  delta_low_ed_turnout_2024_2020         = "Low-education voters",
  delta_high_ed_turnout_2024_2020        = "High-education voters",
  delta_analfabeto_turnout_2024_2020     = "Illiterate voters",
  delta_education_turnout_gap_2024_2020  = "Education turnout gap (high - low)"
)
p_turn <- make_coefplot(turn_outcomes,
  "Turnout response by voter profile",
  "coefplot_turnout_profile.pdf")
ggsave(file.path(FIG_DIR, "coefplot_turnout_profile.pdf"), p_turn, width = 8, height = 4.2)
cat("  Saved coefplot_turnout_profile.pdf\n")


# ============================================================
# 3. APPENDIX E1 — Bartik Z histogram
# ============================================================
cat("\n[3] Bartik histogram (Appendix E1)...\n")

# residualise on state FE only (as in the presentation note)
z_resid <- residuals(
  feols(as.formula(paste(INSTR, "~ 1 | SG_UF")), data = samp,
        warn = FALSE, notes = FALSE)
)

hist_df <- data.frame(z = z_resid)

p_hist <- ggplot(hist_df, aes(x = z)) +
  geom_histogram(
    binwidth = 0.05, fill = COL_BLUE, color = "white", linewidth = 0.2
  ) +
  geom_vline(xintercept = 0, color = COL_RED, linetype = "dashed", linewidth = 0.7) +
  scale_x_continuous(
    labels = scales::label_number(accuracy = 0.1),
    limits = quantile(z_resid, c(0.005, 0.995))
  ) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    x = "Bartik IV (residualised on state FE)",
    y = "Number of municipalities"
  ) +
  theme_clean()

ggsave(
  file.path(FIG_DIR, "bartik_histogram.pdf"),
  p_hist, width = 6, height = 3.8
)
cat("  Saved bartik_histogram.pdf\n")


# ============================================================
# 4. APPENDIX E2 — Bartik Z choropleth
# ============================================================
cat("\n[4] Bartik choropleth (Appendix E2)...\n")

tryCatch({
  library(geobr)
  library(sf)

  cat("  Downloading municipality shapefile (geobr)...\n")
  muni_sf <- read_municipality(year = 2020, simplified = TRUE, showProgress = FALSE)
  crosswalk <- as.data.frame(fread(
    file.path(RAW_DIR, "bd_municipio_tse_ibge.csv"),
    colClasses = list(character = c("id_municipio", "id_municipio_tse"))
  ))
  crosswalk$id_municipio_tse <- sprintf("%05d", as.integer(crosswalk$id_municipio_tse))

  # Residualise on state FE: within-state variation is what identifies the paper
  resid_iv <- residuals(
    feols(as.formula(paste(INSTR, "~ 1 | SG_UF")), data = samp,
          warn = FALSE, notes = FALSE)
  )
  resid_df <- data.frame(SG_UE = samp$SG_UE, bartik_resid = resid_iv)

  map_df <- resid_df %>%
    left_join(crosswalk %>% select(SG_UE = id_municipio_tse, code_muni = id_municipio),
              by = "SG_UE")

  merged <- muni_sf %>%
    mutate(code_muni = as.character(code_muni)) %>%
    left_join(map_df, by = "code_muni")

  # Quintile bins on the residual (5 groups, equal-count)
  breaks <- quantile(merged$bartik_resid, probs = seq(0, 1, 0.2), na.rm = TRUE)
  breaks[1] <- breaks[1] - 1e-9   # open left boundary
  merged$iv_bin <- cut(
    merged$bartik_resid,
    breaks = breaks,
    labels = c("Bottom 20%", "20–40%", "40–60%", "60–80%", "Top 20%"),
    include.lowest = TRUE
  )

  # State boundaries for overlay
  state_sf <- read_state(year = 2020, simplified = TRUE, showProgress = FALSE)

  bin_palette <- c(
    "Bottom 20%" = "#c0392b",
    "20–40%"     = "#e8a090",
    "40–60%"     = "#f5f0eb",
    "60–80%"     = "#8aaecf",
    "Top 20%"    = COL_BLUE
  )

  p_map <- ggplot() +
    geom_sf(data = merged, aes(fill = iv_bin), color = NA, linewidth = 0) +
    geom_sf(data = state_sf, fill = NA, color = "grey30", linewidth = 0.25) +
    scale_fill_manual(
      values   = bin_palette,
      na.value = "grey88",
      name     = "Within-state\npercentile",
      na.translate = FALSE
    ) +
    theme_void(base_size = 10) +
    theme(
      legend.position      = "right",
      legend.title         = element_text(size = 8, face = "bold"),
      legend.text          = element_text(size = 8),
      legend.key.height    = unit(0.55, "cm"),
      legend.key.width     = unit(0.4, "cm")
    )

  ggsave(
    file.path(FIG_DIR, "bartik_choropleth.pdf"),
    p_map, width = 8, height = 7
  )
  cat("  Saved bartik_choropleth.pdf\n")

}, error = function(e) {
  cat("  Choropleth failed:", conditionMessage(e), "\n")
  cat("  Skipping — geobr/sf issue.\n")
})


cat("\nAll figures complete.\n")
cat(sprintf("  Output directory: %s\n", FIG_DIR))
