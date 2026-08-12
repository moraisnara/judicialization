# 02_descriptive_figures.R — descriptive figures for the deck
# ===========================================================================
# PURPOSE: figures that DESCRIBE the data universe and the instrument (not the
# causal results — those live in 03_result_figures.R). Four blocks:
#
#   [A] Litigation timing        -> litigation_timing_shape.pdf
#   [B] Data-universe map        -> sample_map.pdf
#   [C] Bartik IV histogram      -> instrument_histogram.pdf
#   [D] Bartik IV choropleth     -> instrument_map.pdf
#
# Figure convention (see CLAUDE.md): titles and footnotes live on the Beamer
# frame, NOT in the image. Colors come from code/utils/figure_style.R (PAL /
# PAL_CYCLE) and theme_report() blanks title/subtitle/caption. Do not re-add
# ad-hoc hex or plot titles here.
#
# Requires: data.table, ggplot2, dplyr, scales, fixest; geobr + sf for the maps.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(data.table)
  library(ggplot2)
  library(dplyr)
  library(scales)
  library(fixest)
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
CLEAN_DIR   <- file.path(ROOT, "data", "clean")
RAW_DIR     <- file.path(ROOT, "data", "raw")
DESC_DIR    <- file.path(ROOT, "output", "tables", "descriptives")
FIG_DIR     <- file.path(ROOT, "output", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

source(file.path(UTILS, "figure_style.R"))   # PAL, PAL_CYCLE, theme_report()


# ============================================================================
# [A] LITIGATION TIMING — adversarial filings by days-until-election
# ----------------------------------------------------------------------------
# Illustrates the "contencioso" face: adversarial litigation is not a background
# constant — it RAMPS UP toward election day and CONCENTRATES in a narrow window.
# Four views: (1) weekly count, (2) filings per 1,000 candidates, (3) adversarial
# share of ALL originário electoral filings (does the MIX tilt adversarial near
# the vote?), (4) WITHIN-CYCLE shape — each cycle's adversarial filings as a % of
# its own annual total by week (coverage-robust: no cross-year level comparison).
#
# SOURCE: the timing panel is produced by 01_descriptives.py from the SIG export
# (litigation_timing_panel.csv), applying the SAME text->code label bridge and the
# SAME adversarial DROP filter that build the instrument (02_shift_share_design.py).
# The bridge lives in Python (single source of truth); this script only plots.
# Unlike the estimation panel we KEEP post-election filings — ~3 in 10 adversarial
# filings land after election day, and that shift is part of the story.
#
# COVERAGE CAVEAT: SIG under-captures 2024 relative to 2020 (see memory
# sig_undercaptures_2024_coverage), so cross-year *levels* in panels (1)/(2) are
# not comparable — the 2024 curve sits artificially low. Read those for within-
# cycle SHAPE only; panels (3) share and (4) within-cycle shape are coverage-robust.
# ============================================================================
cat("[A] Litigation timing (SIG timing panel)...\n")

# window (days relative to election day) and bin size
WIN_LO <- -270L   # ~9 months before
WIN_HI <-   90L   # ~3 months after
BIN    <-    7L   # weekly bins

# dated, adversarial-tagged SIG panel (one row per election_year x days_rel):
# total_qt = all originário filings, adv_qt = adversarial subset. Emitted by
# 01_descriptives.py::litigation_composition(). Run that first if it is missing.
tim_path <- file.path(DESC_DIR, "litigation_timing_panel.csv")
if (!file.exists(tim_path)) {
  stop("Missing litigation_timing_panel.csv — run code/04_analysis/01_descriptives.py first.")
}
panel <- fread(tim_path)
panel <- panel[days_rel >= WIN_LO & days_rel <= WIN_HI]
panel[, year := factor(election_year)]

# candidate totals per cycle (denominator for the per-1,000 view)
cand <- as.data.frame(fread(
  file.path(CLEAN_DIR, "office_candidate_outcomes_panel.csv"),
  select = c("election_year", "total_candidates")
))
cand_tot <- tapply(cand$total_candidates, cand$election_year, sum, na.rm = TRUE)
cat(sprintf("  candidates: 2020 = %s, 2024 = %s\n",
            format(cand_tot["2020"], big.mark = ","),
            format(cand_tot["2024"], big.mark = ",")))

# weekly aggregation
panel[, week := (days_rel %/% BIN) * BIN]
agg <- panel[, .(total = sum(total_qt), adv = sum(adv_qt)), by = .(year, week)]
agg[, cand_tot := cand_tot[as.character(year)]]
agg[, per1000  := adv / (cand_tot / 1000)]
agg[, share    := adv / total]
# within-cycle shape: share of the CYCLE's windowed adversarial filings per week
# (each year integrates to 1 over the window) — coverage-robust timing shape.
agg[, adv_year_tot := sum(adv), by = year]
agg[, adv_frac     := adv / adv_year_tot]

# shared x scaffolding (election-day marker + breaks) so the three views align
timing_base <- function(p) {
  p +
    geom_vline(xintercept = 0, linetype = "dashed",
               color = "grey40", linewidth = 0.4) +
    annotate("text", x = 2, y = Inf, label = "election day",
             hjust = 0, vjust = 1.4, size = 2.7, color = "grey40") +
    scale_x_continuous(breaks = seq(WIN_LO, WIN_HI, by = 60)) +
    scale_color_manual(values = PAL_CYCLE) +
    scale_fill_manual(values  = PAL_CYCLE) +
    theme_report() +
    theme(legend.position = c(0.16, 0.85))
}

# (4) within-cycle shape — each year's adversarial filings as a % of its OWN
# windowed total (coverage-robust: no cross-year level comparison, only shape).
p_shape <- timing_base(
  ggplot(agg, aes(week, adv_frac, color = year, fill = year)) +
    geom_area(position = "identity", alpha = 0.10, color = NA) +
    geom_line(linewidth = 0.8)
) + scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
  labs(x = "Days relative to first-round election",
       y = "Share of the cycle's adversarial filings (weekly)")
ggsave(file.path(FIG_DIR, "litigation_timing_shape.pdf"), p_shape, width = 6.6, height = 4.0)
cat("  Saved litigation_timing_shape.pdf\n")


# ============================================================================
# [B] DATA-UNIVERSE MAP — municipalities per electoral zone
# ----------------------------------------------------------------------------
# Colors each electoral zone by how many municipalities it covers, showing that
# N_zones (~2,187) < N_municipalities (5,560): urban zones serve one muni, sparse
# interior zones cover many. This is the aggregation structure behind clustering.
# geobr/sf wrapped in tryCatch so a network failure does not break the pipeline.
# ============================================================================
cat("\n[B] Data-universe map...\n")

tryCatch({
  library(geobr)
  library(sf)

  # zone-municipality list
  lista <- as.data.frame(fread(
    file.path(RAW_DIR, "lista-zonas-municipios-10-07-24.csv"),
    sep = ";", fill = TRUE
  ))
  lista <- lista[, c("UF", "ZONA", "COD_LOCALIDADE")]
  lista$tse_id <- as.integer(lista$COD_LOCALIDADE)
  lista <- lista[lista$UF %in% c(
    "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
    "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
  ), ]

  zone_counts <- lista %>%
    group_by(UF, ZONA) %>%
    summarise(n_muni_in_zone = n_distinct(tse_id), .groups = "drop") %>%
    mutate(muni_bin = cut(
      n_muni_in_zone, breaks = c(0, 1, 2, 5, Inf),
      labels = c("1 municipality", "2 municipalities", "3–5 municipalities", "6 or more"),
      right = TRUE))

  # TSE ↔ IBGE crosswalk
  cw <- as.data.frame(fread(
    file.path(RAW_DIR, "bd_municipio_tse_ibge.csv"),
    colClasses = list(character = c("id_municipio", "id_municipio_tse"))
  ))
  cw$tse_id   <- as.integer(cw$id_municipio_tse)
  cw$ibge_chr <- cw$id_municipio

  zone_lookup <- lista %>%
    inner_join(cw[, c("tse_id", "ibge_chr")], by = "tse_id") %>%
    select(ibge_chr, UF, ZONA) %>%
    distinct()

  # municipality polygons -> dissolve to zone polygons
  muni_sf <- read_municipality(year = 2020, simplified = TRUE, showProgress = FALSE)
  muni_sf$ibge_chr <- formatC(as.integer(muni_sf$code_muni), width = 7, flag = "0")
  muni_sf <- muni_sf %>% left_join(zone_lookup, by = "ibge_chr")

  geom_col <- attr(muni_sf, "sf_column")
  zones_sf <- muni_sf %>%
    filter(!is.na(UF), !is.na(ZONA)) %>%
    group_by(UF, ZONA) %>%
    summarise(across(all_of(geom_col), st_union), .groups = "drop") %>%
    left_join(zone_counts, by = c("UF", "ZONA"))

  states_sf <- read_state(year = 2020, showProgress = FALSE)

  # sequential blue ramp anchored on the deck blue (PAL["blue"])
  bin_colors <- c(
    "1 municipality"     = unname(PAL["light"]),  # urban zone, single muni
    "2 municipalities"   = "#7FB0D4",
    "3–5 municipalities" = unname(PAL["blue"]),
    "6 or more"          = "#03294A"               # large rural zone
  )

  p_map <- ggplot() +
    geom_sf(data = zones_sf, aes(fill = muni_bin), color = NA, linewidth = 0) +
    scale_fill_manual(
      values = bin_colors, name = "Municipalities per zone", na.value = "grey70",
      guide = guide_legend(nrow = 2, title.position = "top", title.hjust = 0.5,
                           label.theme = element_text(size = 8.5))) +
    geom_sf(data = states_sf, fill = NA, color = "white", linewidth = 0.65) +
    coord_sf(expand = FALSE) +
    theme_void(base_size = 10) +
    theme(
      plot.title = element_blank(), plot.subtitle = element_blank(),
      plot.caption = element_blank(),           # title/footnote -> Beamer frame
      legend.position = "bottom",
      legend.title = element_text(face = "bold", size = 8),
      legend.text  = element_text(size = 8),
      legend.key.size = unit(0.4, "cm"),
      plot.margin = margin(2, 2, 2, 2),
      plot.background = element_rect(fill = "white", color = NA))

  ggsave(file.path(FIG_DIR, "sample_map.pdf"), p_map, width = 6.5, height = 5.5)
  cat("  Saved sample_map.pdf\n")
}, error = function(e) {
  cat("  Map failed:", conditionMessage(e), "\n  Skipping — geobr/sf issue.\n")
})


# ============================================================================
# [C]/[D] BARTIK IV — histogram + choropleth
# ----------------------------------------------------------------------------
# Both describe the instrument's within-state variation (residualised on state
# FE), which is what identifies the paper. Loaded from the executive design.
# ============================================================================
cat("\n[C]/[D] Bartik IV distribution...\n")

df <- as.data.frame(fread(
  file.path(ESTIMATION, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
if ("state" %in% names(df) && !"SG_UF" %in% names(df))
  names(df)[names(df) == "state"] <- "SG_UF"
if ("municipality_id_tse" %in% names(df) && !"SG_UE" %in% names(df))
  names(df)[names(df) == "municipality_id_tse"] <- "SG_UE"

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

# instrument residualised on state FE — the identifying within-state variation
z_resid <- residuals(
  feols(as.formula(paste(INSTR, "~ 1 | SG_UF")), data = samp,
        warn = FALSE, notes = FALSE)
)

# ── [C] histogram ─────────────────────────────────────────────────────────────
p_hist <- ggplot(data.frame(z = z_resid), aes(x = z)) +
  geom_histogram(binwidth = 0.05, fill = unname(PAL["blue"]),
                 color = "white", linewidth = 0.2) +
  geom_vline(xintercept = 0, color = unname(PAL["red"]),
             linetype = "dashed", linewidth = 0.7) +
  scale_x_continuous(labels = scales::label_number(accuracy = 0.1),
                     limits = quantile(z_resid, c(0.005, 0.995))) +
  scale_y_continuous(labels = scales::comma) +
  labs(x = "Bartik IV (residualised on state FE)", y = "Number of municipalities") +
  theme_report()
ggsave(file.path(FIG_DIR, "instrument_histogram.pdf"), p_hist, width = 6, height = 3.8)
cat("  Saved instrument_histogram.pdf\n")

# ── [D] choropleth ────────────────────────────────────────────────────────────
tryCatch({
  library(geobr)
  library(sf)

  muni_sf <- read_municipality(year = 2020, simplified = TRUE, showProgress = FALSE)
  crosswalk <- as.data.frame(fread(
    file.path(RAW_DIR, "bd_municipio_tse_ibge.csv"),
    colClasses = list(character = c("id_municipio", "id_municipio_tse"))
  ))
  crosswalk$id_municipio_tse <- sprintf("%05d", as.integer(crosswalk$id_municipio_tse))

  resid_df <- data.frame(SG_UE = samp$SG_UE, bartik_resid = z_resid)
  map_df <- resid_df %>%
    left_join(crosswalk %>% select(SG_UE = id_municipio_tse, code_muni = id_municipio),
              by = "SG_UE")
  merged <- muni_sf %>%
    mutate(code_muni = as.character(code_muni)) %>%
    left_join(map_df, by = "code_muni")

  breaks <- quantile(merged$bartik_resid, probs = seq(0, 1, 0.2), na.rm = TRUE)
  breaks[1] <- breaks[1] - 1e-9
  merged$iv_bin <- cut(
    merged$bartik_resid, breaks = breaks,
    labels = c("Bottom 20%", "20–40%", "40–60%", "60–80%", "Top 20%"),
    include.lowest = TRUE)

  state_sf <- read_state(year = 2020, simplified = TRUE, showProgress = FALSE)

  # diverging red -> blue, anchored on the deck red/blue (PAL)
  bin_palette <- c(
    "Bottom 20%" = unname(PAL["red"]),
    "20–40%"     = "#E0968C",
    "40–60%"     = "#F0EFEA",
    "60–80%"     = "#7FA6C8",
    "Top 20%"    = unname(PAL["blue"]))

  p_map <- ggplot() +
    geom_sf(data = merged, aes(fill = iv_bin), color = NA, linewidth = 0) +
    geom_sf(data = state_sf, fill = NA, color = "grey30", linewidth = 0.25) +
    scale_fill_manual(values = bin_palette, na.value = "grey88",
                      name = "Within-state\npercentile", na.translate = FALSE) +
    theme_void(base_size = 10) +
    theme(
      legend.position = "right",
      legend.title = element_text(size = 8, face = "bold"),
      legend.text  = element_text(size = 8),
      legend.key.height = unit(0.55, "cm"),
      legend.key.width  = unit(0.4, "cm"))

  ggsave(file.path(FIG_DIR, "instrument_map.pdf"), p_map, width = 8, height = 7)
  cat("  Saved instrument_map.pdf\n")
}, error = function(e) {
  cat("  Choropleth failed:", conditionMessage(e), "\n  Skipping — geobr/sf issue.\n")
})

cat("\nAll descriptive figures complete.\n")
cat(sprintf("  Output directory: %s\n", FIG_DIR))
