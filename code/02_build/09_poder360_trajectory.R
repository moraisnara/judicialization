suppressMessages({library(basedosdados); library(dplyr)})
set_billing_id("tentativa-333001")
tbl <- "basedosdados.br_poder360_pesquisas.microdados"

# (a) what response-type labels appear for prefeito polls?
cat("=== distinct nome_candidato for prefeito ===\n")
opt <- bdplyr(tbl) %>%
  filter(cargo == "prefeito") %>%
  distinct(nome_candidato) %>%
  bd_collect()
cat("total distinct labels:", nrow(opt), "\n")
hits <- opt$nome_candidato[grepl(
  "branco|nulo|sabe|indecis|nenhum|outro|respond|espon",
  opt$nome_candidato, ignore.case = TRUE)]
cat("non-candidate options found:\n"); print(hits)
cat("\nfull list:\n"); print(sort(unique(opt$nome_candidato)))

# (b) also check tipo_voto column
cat("\n=== distinct tipo_voto for prefeito ===\n")
tv <- bdplyr(tbl) %>%
  filter(cargo == "prefeito") %>%
  distinct(tipo_voto) %>%
  bd_collect()
print(tv)

# (c) poll trajectory per muni x year
cat("\n=== poll trajectory: polls & dates per muni per year ===\n")
traj <- bdplyr(tbl) %>%
  filter(cargo == "prefeito") %>%
  group_by(ano, sigla_uf, nome_municipio) %>%
  summarise(
    n_polls  = n_distinct(id_pesquisa),
    n_dates  = n_distinct(data),
    min_date = min(data, na.rm = TRUE),
    max_date = max(data, na.rm = TRUE),
    .groups  = "drop") %>%
  bd_collect()

cat("\nsummary by year:\n")
print(traj %>%
  group_by(ano) %>%
  summarise(
    munis      = n(),
    ge2_polls  = sum(n_polls >= 2),
    ge3_polls  = sum(n_polls >= 3),
    ge5_polls  = sum(n_polls >= 5),
    ge10_polls = sum(n_polls >= 10),
    max_polls  = max(n_polls)))

cat("\ntop 15 munis by n_polls in 2020:\n")
print(traj %>% filter(ano == 2020) %>%
  arrange(desc(n_polls)) %>%
  select(sigla_uf, nome_municipio, n_polls, n_dates, min_date, max_date) %>%
  head(15))

cat("\ntop 15 munis by n_polls in 2024:\n")
print(traj %>% filter(ano == 2024) %>%
  arrange(desc(n_polls)) %>%
  select(sigla_uf, nome_municipio, n_polls, n_dates, min_date, max_date) %>%
  head(15))

saveRDS(traj, file.path("data", "clean", "poder360_trajectory.rds"))
cat("\nSaved trajectory to data/clean/poder360_trajectory.rds\n")
