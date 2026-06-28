# Maps of Atlas da Noticias news presence across Brazilian municipalities
# Output: output/figures/atlas_*.pdf
# Titles, subtitles, footnotes go in LaTeX — not here

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(ggplot2)
  library(dplyr)
  library(sf)
  library(geobr)
})

# ---- path detection ----
if (exists("rstudioapi") && tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE)) {
  SCRIPT_DIR <- dirname(rstudioapi::getSourceEditorContext()$path)
} else {
  args     <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0)
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  else getwd()
}
PROJECT_ROOT <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
FIG_DIR      <- file.path(PROJECT_ROOT, "output", "figures")
dir.create(FIG_DIR, recursive = TRUE, showWarnings = FALSE)

# ---- load data ----
atlas <- read.csv(file.path(PROJECT_ROOT, "data", "clean", "atlas_noticias.csv"),
                  encoding = "UTF-8", stringsAsFactors = FALSE)
atlas$cod_ibge7 <- formatC(as.integer(atlas$cod_ibge7), width = 7, flag = "0")

# ---- shapefiles ----
cat("Loading shapefiles...\n")
muni_sf  <- read_municipality(year = 2020, simplified = TRUE,  showProgress = FALSE)
state_sf <- read_state(       year = 2020, simplified = TRUE,  showProgress = FALSE)
muni_sf$codmun7 <- formatC(as.integer(muni_sf$code_muni), width = 7, flag = "0")

map_data <- left_join(muni_sf, atlas, by = c("codmun7" = "cod_ibge7"))
cat(sprintf("Matched: %d / %d\n\n", sum(!is.na(map_data$outlets_total_atlas)), nrow(muni_sf)))

# ---- shared theme ----
theme_map <- theme_void(base_size = 10) +
  theme(
    legend.position   = "right",
    legend.title      = element_text(size = 8, face = "bold"),
    legend.text       = element_text(size = 8),
    legend.key.height = unit(0.55, "cm"),
    legend.key.width  = unit(0.4,  "cm")
  )

state_layer <- geom_sf(data = state_sf, fill = NA, color = "grey30", linewidth = 0.2)

save_pdf <- function(p, filename, width = 9, height = 7) {
  path <- file.path(FIG_DIR, filename)
  ggsave(path, p, width = width, height = height)
  cat("Saved ->", path, "\n")
}

# ---- Map 1: desert classification ----
map_data <- map_data %>%
  mutate(desert_label = factor(
    desert_class,
    levels = c("news_desert", "almost_desert", "has_coverage"),
    labels = c("News desert (0)", "Almost desert (1-2)", "Has coverage (3+)")
  ))

p1 <- ggplot() +
  geom_sf(data = map_data, aes(fill = desert_label), color = NA, linewidth = 0) +
  state_layer +
  scale_fill_manual(
    values = c("News desert (0)"     = "#c0392b",
               "Almost desert (1-2)" = "#f5c96a",
               "Has coverage (3+)"   = "#2980b9"),
    na.value = "grey88",
    name = "Classification",
    na.translate = FALSE
  ) +
  theme_map

save_pdf(p1, "atlas_desert_classification.pdf")

# ---- Map 2: total outlets (log1p continuous) ----
p2 <- ggplot() +
  geom_sf(data = map_data, aes(fill = outlets_total_atlas), color = NA, linewidth = 0) +
  state_layer +
  scale_fill_viridis_c(
    option = "plasma", trans = "log1p", na.value = "grey88",
    name = "Total\noutlets",
    breaks = c(0, 1, 3, 10, 30, 100),
    labels = c("0", "1", "3", "10", "30", "100+")
  ) +
  theme_map

save_pdf(p2, "atlas_n_outlets.pdf")

# ---- Map 3: outlets per 100k (log1p continuous) ----
p3 <- ggplot() +
  geom_sf(data = map_data, aes(fill = outlets_per_100k), color = NA, linewidth = 0) +
  state_layer +
  scale_fill_viridis_c(
    option = "magma", trans = "log1p", na.value = "grey88",
    name = "Outlets per\n100k pop."
  ) +
  theme_map

save_pdf(p3, "atlas_outlets_per_100k.pdf")

# ---- Maps 4-7: by outlet type (continuous log scale) ----
type_vars <- c(n_online = "Online", n_impresso = "Print", n_radio = "Radio", n_tv = "TV")

for (col in names(type_vars)) {
  lbl <- type_vars[col]
  p <- ggplot() +
    geom_sf(data = map_data, aes(fill = .data[[col]]), color = NA, linewidth = 0) +
    state_layer +
    scale_fill_viridis_c(
      option   = "plasma",
      trans    = "log1p",
      na.value = "grey88",
      name     = paste(lbl, "\noutlets (log)")
    ) +
    theme_map
  save_pdf(p, paste0("atlas_outlets_", sub("n_", "", col), ".pdf"))
}

cat("\nDone.\n")
