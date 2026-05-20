# Downloads the municipality crosswalk from Base dos Dados:
#   id_municipio      = IBGE municipality code
#   id_municipio_tse  = TSE municipality code
#
# Output: data/raw/bd_municipio_tse_ibge.csv

user_lib <- file.path(Sys.getenv("USERPROFILE"), "R", "win-library", "4.6")
if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))

suppressPackageStartupMessages({
  library(basedosdados)
})

args       <- commandArgs(trailingOnly = FALSE)
script_idx <- which(startsWith(args, "--file="))
if (length(script_idx) > 0) {
  script_path  <- sub("--file=", "", args[script_idx])
  project_root <- normalizePath(file.path(dirname(script_path), "..", ".."))
} else {
  project_root <- normalizePath(".")
}

out_path <- file.path(project_root, "data", "raw", "bd_municipio_tse_ibge.csv")
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

billing_id <- Sys.getenv("BASEDOSDADOS_BILLING_ID", unset = "")
if (billing_id == "") {
  stop("Set BASEDOSDADOS_BILLING_ID before running this script.")
}
set_billing_id(billing_id)

query <- "
SELECT
    dados.id_municipio AS id_municipio,
    dados.id_municipio_tse AS id_municipio_tse
FROM `basedosdados.br_bd_diretorios_brasil.municipio` AS dados
WHERE dados.id_municipio IS NOT NULL
  AND dados.id_municipio_tse IS NOT NULL
"

cat("Downloading municipality crosswalk from Base dos Dados...\n")
crosswalk <- read_sql(query, billing_project_id = get_billing_id())
crosswalk <- unique(crosswalk[, c("id_municipio", "id_municipio_tse")])

write.csv(crosswalk, out_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved:", out_path, "\n")
