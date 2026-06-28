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
  file.path(ESTIMATION, "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
# Rename to match FE and choropleth variable names used throughout the script
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
if ("municipality_id_tse" %in% names(df) && !"SG_UE" %in% names(df))
  names(df)[names(df) == "municipality_id_tse"] <- "SG_UE"
cat(sprintf("  N = %d municipalities\n", nrow(df)))

ENDOG <- "delta_log1p_act_lawsuits"
INSTR <- "bartik_iv_act"
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
  line    = c(1, 1),   # linear fit within the binscatter
  ci      = c(1, 1),   # CI around bins
  cb      = NULL,
  plotxrange = quantile(bs_df$x, c(0.01, 0.99))
)

# extract bin means
bin_df <- bs$data.plot$`Group Full Sample`$data.dots

# OLS slope (= first-stage coef in residualised space) — the regression line
fs_lm   <- lm(y ~ x, data = bs_df)
fs_coef <- coef(fs_lm)["x"]
fs_int  <- coef(fs_lm)["(Intercept)"]
fs_N    <- nrow(samp)

# annotation: slope + first-stage F (read from the IV estimation output,
# never hardcoded — the figure must track whatever the current build produces)
# Read the baseline first-stage F from the current (G8rh) voter-behaviour
# engine — the archived whole-grid CSV is superseded.
fs_csv <- file.path(REGRESSIONS, "voter_first_stage.csv")
fs_F_val <- tryCatch({
  fst <- as.data.frame(fread(fs_csv))
  fst$F[fst$spec == "baseline"][1]
}, error = function(e) NA_real_)
ann_lab <- sprintf("First stage: slope = %.2f\nF = %.1f,  N = %s",
                   fs_coef, fs_F_val, format(fs_N, big.mark = ","))
x_rng <- quantile(bs_df$x, c(0.01, 0.99))

p_bin <- ggplot() +
  geom_point(
    data = bin_df,
    aes(x = x, y = fit),
    color = COL_BLUE, size = 2.2, alpha = 0.85
  ) +
  geom_abline(
    intercept = fs_int, slope = fs_coef,
    color = COL_BLUE, linewidth = 1.0
  ) +
  geom_hline(yintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  geom_vline(xintercept = 0, color = "grey60", linetype = "dashed", linewidth = 0.4) +
  annotate("label", x = x_rng[1], y = Inf, hjust = 0, vjust = 1.2,
           label = ann_lab, size = 3.4, label.size = 0,
           fill = "white", color = COL_BLUE) +
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
