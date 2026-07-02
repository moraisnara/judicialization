# Extracts Census 2010 municipal-level covariates from person microdata (censobr).
#
# All variables computed with person weight V0010.
#
# Variables produced:
#   pop_2010                total weighted population
#   urban_share_2010        share of population in urban dwellings (V1006 == 1)
#   income_pc_2010          population-weighted mean household per capita income (V6527)
#   higher_educ_share_2010  share of 25+ population with complete higher education (V6400 == 4)
#
# Output: data/clean/censo2010_municipal_ibge.csv
#   Columns: code_muni (7-digit IBGE), abbrev_state, pop_2010,
#            urban_share_2010, income_pc_2010, higher_educ_share_2010

user_lib <- file.path(Sys.getenv("USERPROFILE"), "R", "win-library", "4.6")
if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))

suppressPackageStartupMessages({
  library(censobr)
  library(dplyr)
})

args       <- commandArgs(trailingOnly = FALSE)
script_idx <- which(startsWith(args, "--file="))
if (length(script_idx) > 0) {
  script_path  <- sub("--file=", "", args[script_idx])
  project_root <- normalizePath(file.path(dirname(script_path), "..", ".."))
} else {
  project_root <- normalizePath(".")
}
out_path <- file.path(project_root, "data", "clean", "censo2010_municipal_ibge.csv")
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

# ── Load person microdata (Arrow table — aggregated lazily) ──────────────────
cat("Loading Census 2010 person microdata via censobr...\n")
pop <- read_population(
  year         = 2010,
  columns      = c("code_muni", "abbrev_state", "V0010", "V1006", "V6036", "V6400", "V6527"),
  showProgress = FALSE,
  cache        = TRUE
)
# V0010 : person weight
# V1006 : dwelling situation  (1 = urban, 2 = rural)
# V6036 : age in years
# V6400 : highest completed education level (4 = Superior completo)
# V6527 : household per capita income (R$/month, assigned to all household members)

# ── Aggregate to municipality level ─────────────────────────────────────────
cat("Aggregating to municipality level...\n")
out <- pop %>%
  group_by(code_muni, abbrev_state) %>%
  summarise(
    pop_w      = sum(V0010, na.rm = TRUE),
    urban_w    = sum(if_else(V1006 == 1L,              V0010, 0.0), na.rm = TRUE),
    income_num = sum(if_else(!is.na(V6527), V6527 * V0010, 0.0),   na.rm = TRUE),
    income_den = sum(if_else(!is.na(V6527), V0010,          0.0),   na.rm = TRUE),
    pop25_w    = sum(if_else(V6036 >= 25L,             V0010, 0.0), na.rm = TRUE),
    edu_sup_w  = sum(if_else(V6036 >= 25L & V6400 == 4L, V0010, 0.0), na.rm = TRUE),
    .groups    = "drop"
  ) %>%
  collect() %>%
  mutate(
    pop_2010               = pop_w,
    urban_share_2010       = if_else(pop_w > 0, urban_w / pop_w, NA_real_),
    income_pc_2010         = if_else(income_den > 0, income_num / income_den, NA_real_),
    higher_educ_share_2010 = if_else(pop25_w > 0, edu_sup_w / pop25_w, NA_real_)
  ) %>%
  select(
    code_muni, abbrev_state, pop_2010, urban_share_2010, income_pc_2010, higher_educ_share_2010
  )

cat(sprintf("Municipalities in output: %d\n", nrow(out)))
cat(sprintf("Missing income_pc_2010:         %d\n", sum(is.na(out$income_pc_2010))))
cat(sprintf("Missing urban_share_2010:       %d\n", sum(is.na(out$urban_share_2010))))
cat(sprintf("Missing higher_educ_share_2010: %d\n", sum(is.na(out$higher_educ_share_2010))))

cat("\nSummary:\n")
print(summary(out[, c("pop_2010", "urban_share_2010",
                      "income_pc_2010", "higher_educ_share_2010")]))

write.csv(out, out_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved:", out_path, "\n")
