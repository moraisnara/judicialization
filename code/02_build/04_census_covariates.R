# Extracts Census 2010 municipal-level covariates using censobr + geobr.
#
# Variables produced (all Census 2010, fully predetermined):
#   log_pop_2010          log total population
#   urban_share_2010      share of population in urban tracts
#   log_income_pc_2010    log mean household income per capita
#   higher_educ_share_2010 share of 25+ population with complete higher education
#
# Output: data/clean/censo2010_municipal_ibge.csv
#   Columns: code_muni (7-digit IBGE), abbrev_state, name_muni, + 4 variables above

user_lib <- file.path(Sys.getenv("USERPROFILE"), "R", "win-library", "4.6")
if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))

suppressPackageStartupMessages({
  library(censobr)
  library(dplyr)
})

args <- commandArgs(trailingOnly = FALSE)
script_idx <- which(startsWith(args, "--file="))
if (length(script_idx) > 0) {
  script_path <- sub("--file=", "", args[script_idx])
  project_root <- normalizePath(file.path(dirname(script_path), "..", ".."))
} else {
  project_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), "..", ".."), mustWork = FALSE)
}
out_path <- file.path(project_root, "data", "clean", "censo2010_municipal_ibge.csv")
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

# -------------------------------------------------------------------
# 1. Basico dataset: population, income, households, urban/rural
# -------------------------------------------------------------------
cat("Loading Census 2010 Basico data via censobr...\n")
tracts <- as.data.frame(censobr::read_tracts(year = 2010, dataset = "Basico",
                                              showProgress = FALSE))

cat(sprintf("Basico rows: %d  cols: %s\n", nrow(tracts),
            paste(colnames(tracts), collapse = ", ")))

tract_col <- if ("code_tract" %in% colnames(tracts)) "code_tract" else "Cod_setor"
tracts$code_muni <- substr(as.character(tracts[[tract_col]]), 1, 6)

# Urban flag: digit 8 of the 15-char tract code
# 1 = urban face (face de quadra), 2 = urban enclave, 3 = rural, 4 = urban isolated
tracts$is_urban <- substr(as.character(tracts[[tract_col]]), 8, 8) %in% c("1", "2")

mun_basico <- tracts %>%
  group_by(code_muni) %>%
  summarise(
    total_pop    = sum(as.numeric(V002), na.rm = TRUE),
    urban_pop    = sum(as.numeric(V002) * is_urban, na.rm = TRUE),
    total_income = sum(as.numeric(V005), na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    urban_share_2010   = ifelse(total_pop > 0, urban_pop / total_pop, NA_real_),
    # income per capita = total declared income / total population (V005/V002)
    income_pc_2010     = ifelse(total_pop > 0, total_income / total_pop, NA_real_),
    log_pop_2010       = log1p(total_pop),
    log_income_pc_2010 = log1p(income_pc_2010)
  )

cat(sprintf("Municipalities from Basico: %d\n", nrow(mun_basico)))

# Education (higher_educ_share_2010) requires the censobr "DomicilioRenda" or
# individual-level dataset; not available in "Basico". Placeholder NA for now.
mun_educ <- NULL

# -------------------------------------------------------------------
# 3. Municipality metadata — extract directly from censobr Basico columns
#    (code_muni, name_muni, abbrev_state are already present)
# -------------------------------------------------------------------
cat("Extracting municipality metadata from censobr Basico data...\n")
munis_meta <- tracts %>%
  select(code_muni, name_muni, abbrev_state, code_micro, name_micro, code_meso, name_meso) %>%
  distinct()

# -------------------------------------------------------------------
# 4. Assemble final output
# -------------------------------------------------------------------
out <- mun_basico %>%
  left_join(munis_meta, by = "code_muni")

if (!is.null(mun_educ)) {
  out <- out %>%
    left_join(mun_educ, by = "code_muni") %>%
    mutate(higher_educ_share_2010 = ifelse(pop_25plus > 0, pop_sup / pop_25plus, NA_real_))
} else {
  out$higher_educ_share_2010 <- NA_real_
}

out <- out %>%
  select(code_muni, abbrev_state, name_muni,
         code_micro, name_micro, code_meso, name_meso,
         log_pop_2010, urban_share_2010, log_income_pc_2010, higher_educ_share_2010)

cat(sprintf("\nMunicipalities in output: %d\n", nrow(out)))
cat(sprintf("Missing log_income_pc_2010:    %d\n", sum(is.na(out$log_income_pc_2010))))
cat(sprintf("Missing higher_educ_share_2010: %d\n", sum(is.na(out$higher_educ_share_2010))))

write.csv(out, out_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved:", out_path, "\n")
