################################################
## Download Poder360 prefeito municipality-year coverage
## Queries basedosdados.br_poder360_pesquisas.microdados via BigQuery.
## Saves:
##   data/raw/poder360_sample.rds           (50-row schema sample)
##   data/clean/poder360_prefeito_muni_year.csv
## Author: Nara Morais
################################################

suppressMessages({
  library(basedosdados)
  library(dplyr)
})

set_billing_id("tentativa-333001")

tbl <- "basedosdados.br_poder360_pesquisas.microdados"

# Schema sample — kept for reference.
samp <- bdplyr(tbl) %>% head(50) %>% bd_collect()
saveRDS(samp, file.path("data", "raw", "poder360_sample.rds"))
cat("Saved schema sample to data/raw/poder360_sample.rds\n")

# Distinct prefeito municipalities by year — used by coverage map + balance test.
# No IBGE code in this table; name-matching is done downstream.
muni_year <- bdplyr(tbl) %>%
  filter(cargo == "prefeito") %>%
  group_by(ano, sigla_uf, nome_municipio) %>%
  summarise(n_polls = n_distinct(id_pesquisa), .groups = "drop") %>%
  bd_collect()

write.csv(muni_year,
          file.path("data", "clean", "poder360_prefeito_muni_year.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
cat(sprintf("Saved %d prefeito muni-year rows to data/clean/poder360_prefeito_muni_year.csv\n",
            nrow(muni_year)))
