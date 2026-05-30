# Map: municipalities per electoral zone
# Produces: output/figures/map_data_universe.pdf
#
# Colors each electoral zone by how many municipalities it covers, showing
# that N_zones (2,187) < N_municipalities (5,560). Zones covering 1 muni
# (urban centres) vs. zones covering many munis (sparse interior) reveal
# the aggregation structure underlying the clustering design.
#
# Sources:
#   data/raw/lista-zonas-municipios-10-07-24.csv  — TSE zone→municipality list
#   data/raw/bd_municipio_tse_ibge.csv            — TSE ↔ IBGE crosswalk
#   data/estimation/executive_margin_design.csv   — sample size (for subtitle)
#   geobr::read_municipality(2020)                — municipality polygons
#   geobr::read_state(2020)                       — state borders

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(geobr)
  library(sf)
  library(ggplot2)
  library(dplyr)
  library(data.table)
})

# ── paths ─────────────────────────────────────────────────────────────────────
args       <- commandArgs(trailingOnly = FALSE)
file_arg   <- grep("^--file=", args, value = TRUE)
SCRIPT_DIR <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
} else getwd()
ROOT       <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION <- file.path(ROOT, "data", "estimation")
RAW_DIR    <- file.path(ROOT, "data", "raw")
FIG_DIR    <- file.path(ROOT, "output", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

# ── zone-municipality list ────────────────────────────────────────────────────
cat("Loading zone-municipality list...\n")
lista <- as.data.frame(fread(
  file.path(RAW_DIR, "lista-zonas-municipios-10-07-24.csv"),
  sep = ";", fill = TRUE
))
lista <- lista[, c("UF", "ZONA", "COD_LOCALIDADE")]
lista$tse_id <- as.integer(lista$COD_LOCALIDADE)

# drop non-geographic UF codes (ZZ = overseas / undefined)
lista <- lista[lista$UF %in% c(
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
  "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
), ]

# municipalities per zone
zone_counts <- lista %>%
  group_by(UF, ZONA) %>%
  summarise(n_muni_in_zone = n_distinct(tse_id), .groups = "drop") %>%
  mutate(
    muni_bin = cut(
      n_muni_in_zone,
      breaks = c(0, 1, 2, 5, Inf),
      labels = c("1 municipality", "2 municipalities", "3–5 municipalities", "6 or more"),
      right  = TRUE
    )
  )
cat("Municipalities per zone:\n")
print(table(zone_counts$muni_bin))

# ── TSE ↔ IBGE crosswalk ──────────────────────────────────────────────────────
cat("\nLoading TSE-IBGE crosswalk...\n")
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

# ── sample totals (for subtitle) ──────────────────────────────────────────────
design <- as.data.frame(fread(
  file.path(ESTIMATION, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse")),
  select = c("state", "municipality_id_tse", "principal_zone")
))
n_muni  <- n_distinct(design$municipality_id_tse)
n_zones <- n_distinct(paste(design$state, design$principal_zone))

# ── geobr: municipality polygons ──────────────────────────────────────────────
cat("Downloading municipality polygons (geobr)...\n")
muni_sf <- read_municipality(year = 2020, simplified = TRUE, showProgress = FALSE)
muni_sf$ibge_chr <- formatC(as.integer(muni_sf$code_muni), width = 7, flag = "0")

muni_sf <- muni_sf %>%
  left_join(zone_lookup, by = "ibge_chr")

# ── dissolve municipalities → zone polygons ───────────────────────────────────
cat("Dissolving to zone polygons...\n")
geom_col <- attr(muni_sf, "sf_column")

zones_sf <- muni_sf %>%
  filter(!is.na(UF), !is.na(ZONA)) %>%
  group_by(UF, ZONA) %>%
  summarise(across(all_of(geom_col), st_union), .groups = "drop") %>%
  left_join(zone_counts, by = c("UF", "ZONA"))

cat(sprintf("  %d zone polygons\n", nrow(zones_sf)))

# ── geobr: state borders ──────────────────────────────────────────────────────
cat("Downloading state borders (geobr)...\n")
states_sf <- read_state(year = 2020, showProgress = FALSE)

# ── colour palette ────────────────────────────────────────────────────────────
# Light (1 muni = urban zone) → dark (many munis = large rural zone)
bin_colors <- c(
  "1 municipality"   = "#d0e4f7",   # very light blue
  "2 municipalities" = "#5b9bd5",   # medium blue
  "3–5 municipalities" = "#1a5276", # dark navy
  "6 or more"        = "#0d1b2a"    # near-black
)

# ── plot ──────────────────────────────────────────────────────────────────────
cat("Rendering map...\n")

p <- ggplot() +
  geom_sf(
    data      = zones_sf,
    aes(fill  = muni_bin),
    color     = NA,
    linewidth = 0
  ) +
  scale_fill_manual(
    values   = bin_colors,
    name     = "Municipalities per zone",
    na.value = "grey70",
    guide    = guide_legend(
      nrow           = 2,
      title.position = "top",
      title.hjust    = 0.5,
      label.theme    = element_text(size = 8.5)
    )
  ) +
  geom_sf(
    data      = states_sf,
    fill      = NA,
    color     = "white",
    linewidth = 0.65
  ) +
  labs(
    title    = "Electoral Zones vs. Municipalities",
    subtitle = sprintf(
      "%d municipalities  ->  %d electoral zones   (avg %.1f municipalities per zone)",
      n_muni, n_zones, n_muni / n_zones
    ),
    caption = paste(
      "Each polygon is one electoral zone (zona eleitoral).",
      "Color = number of municipalities sharing that zone.",
      "Light = urban zones serving a single municipality; dark = large zones covering many municipalities.",
      "White borders = state (UF). Source: TSE 2020–2024; geobr; IBGE."
    )
  ) +
  coord_sf(expand = FALSE) +
  theme_void(base_size = 10) +
  theme(
    plot.title    = element_blank(),   # title lives in the beamer frame
    plot.subtitle = element_blank(),
    plot.caption  = element_blank(),
    legend.position  = "bottom",
    legend.title     = element_text(face = "bold", size = 8),
    legend.text      = element_text(size = 8),
    legend.key.size  = unit(0.4, "cm"),
    plot.margin      = margin(2, 2, 2, 2),
    plot.background  = element_rect(fill = "white", color = NA)
  )

out_path <- file.path(FIG_DIR, "map_data_universe.pdf")
ggsave(out_path, p, width = 6.5, height = 5.5)
cat(sprintf("  Saved: %s\n", out_path))
cat("\nDone.\n")
