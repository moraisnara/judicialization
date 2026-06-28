# Build municipal-level Atlas da Noticias variables
# Input:  data/raw/atlas_noticias/atlas_noticias_municipalities.csv
#         data/raw/atlas_noticias/atlas_noticias_organizations.csv
# Output: data/clean/atlas_noticias.csv

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(dplyr)
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
RAW_DIR   <- file.path(PROJECT_ROOT, "data", "raw",   "atlas_noticias")
CLEAN_DIR <- file.path(PROJECT_ROOT, "data", "clean")

# ---- load raw data ----
muni <- read.csv(file.path(RAW_DIR, "atlas_noticias_municipalities.csv"),
                 encoding = "UTF-8", stringsAsFactors = FALSE)
orgs <- read.csv(file.path(RAW_DIR, "atlas_noticias_organizations.csv"),
                 encoding = "UTF-8", stringsAsFactors = FALSE)

cat("Municipalities:", nrow(muni), "rows\n")
cat("Organizations: ", nrow(orgs), "rows\n")
cat("Outlet types (segmento):", paste(sort(unique(orgs$segmento)), collapse = ", "), "\n\n")

# ---- standardise IBGE codes ----
# municipalities: codmun is 7-digit (with check digit)
muni$cod_ibge7 <- formatC(as.integer(muni$codmun), width = 7, flag = "0")
muni$cod_ibge  <- substr(muni$cod_ibge7, 1, 6)   # 6-digit for merge with TSE crosswalk

# organizations: codmun may also be 7-digit
orgs$cod_ibge7 <- formatC(as.integer(orgs$codmun), width = 7, flag = "0")

# ---- count outlets by type per municipality ----
# Map raw segmento values to clean categories
type_map <- c(
  "impresso"      = "impresso",
  "digital"       = "online",
  "online"        = "online",
  "radio"         = "radio",
  "televisao"     = "tv",
  "televisão"     = "tv",
  "agencia"       = "agencia",
  "agência"       = "agencia",
  "multiplas"     = "multiplas",
  "múltiplas"     = "multiplas"
)

orgs <- orgs %>%
  mutate(tipo = tolower(trimws(segmento)),
         tipo = ifelse(tipo %in% names(type_map), type_map[tipo], "outro"))

cat("Type distribution:\n")
print(sort(table(orgs$tipo), decreasing = TRUE))
cat("\n")

type_counts <- orgs %>%
  group_by(cod_ibge7, tipo) %>%
  summarise(n = n(), .groups = "drop") %>%
  tidyr::pivot_wider(names_from = tipo, values_from = n,
                     values_fill = 0, names_prefix = "n_")

# Total from orgs (may differ slightly from qtd_veiculos in muni due to ativo filter)
type_counts <- type_counts %>%
  mutate(n_outlets_total = rowSums(across(starts_with("n_"))))

# ---- merge with municipal summary ----
atlas <- muni %>%
  left_join(type_counts, by = "cod_ibge7") %>%
  mutate(across(starts_with("n_"), ~replace(., is.na(.), 0)))

# Use qtd_veiculos from get_municipalities() as authoritative total
atlas <- atlas %>%
  rename(outlets_total_atlas = qtd_veiculos,
         outlets_per_100k    = veiculos_por_100k_hab,
         populacao_ref       = populacao)

# Per-100k by type
pop100k <- atlas$populacao_ref / 100000
pop100k[pop100k == 0] <- NA
type_n_cols <- grep("^n_", names(atlas), value = TRUE)
for (col in type_n_cols) {
  atlas[[paste0(col, "_per_100k")]] <- atlas[[col]] / pop100k
}

# ---- desert classification ----
atlas <- atlas %>%
  mutate(
    news_desert   = as.integer(outlets_total_atlas == 0),
    almost_desert = as.integer(outlets_total_atlas >= 1 & outlets_total_atlas <= 2),
    has_coverage  = as.integer(outlets_total_atlas >= 3),
    desert_class  = case_when(
      outlets_total_atlas == 0              ~ "news_desert",
      outlets_total_atlas <= 2              ~ "almost_desert",
      TRUE                                  ~ "has_coverage"
    )
  )

# ---- summary ----
cat("=== Desert classification ===\n")
print(table(atlas$desert_class))
cat("\n")
cat("Municipalities with outlet-type data from orgs:", sum(atlas$n_outlets_total > 0), "\n\n")

# ---- select and save ----
out_cols <- c(
  "municipio", "uf", "regiao", "cod_ibge7", "cod_ibge",
  "populacao_ref", "ano_populacao",
  "outlets_total_atlas", "outlets_per_100k",
  "IDHM", "IDHM_R", "IDHM_E",
  "news_desert", "almost_desert", "has_coverage", "desert_class",
  grep("^n_", names(atlas), value = TRUE)
)
out_cols <- intersect(out_cols, names(atlas))

out <- atlas[, out_cols]

out_path <- file.path(CLEAN_DIR, "atlas_noticias.csv")
write.csv(out, out_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved ->", out_path, "\n")
cat("Rows:", nrow(out), "| Columns:", ncol(out), "\n")
cat("Columns:", paste(names(out), collapse = ", "), "\n")
