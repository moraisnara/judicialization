# Download Atlas da Noticias municipal-level news presence data
# Uses newsatlasbr R package (voltdatalab/newsatlasbr)
# Credentials loaded from .env — never hardcoded

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
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
RAW_DIR      <- file.path(PROJECT_ROOT, "data", "raw", "atlas_noticias")
dir.create(RAW_DIR, recursive = TRUE, showWarnings = FALSE)

# ---- load credentials from .env ----
env_file <- file.path(PROJECT_ROOT, ".env")
if (!file.exists(env_file)) stop(".env file not found at: ", env_file)
readRenviron(env_file)

email    <- Sys.getenv("ATLAS_NOTICIAS_EMAIL")
password <- Sys.getenv("ATLAS_NOTICIAS_PASSWORD")
if (nchar(email) == 0 || nchar(password) == 0 ||
    password == "CHANGE_THIS_TO_YOUR_NEW_PASSWORD") {
  stop("Credentials not set in .env — fill in ATLAS_NOTICIAS_EMAIL and ATLAS_NOTICIAS_PASSWORD")
}
cat("Credentials loaded for:", email, "\n")

# ---- install newsatlasbr if needed ----
if (!requireNamespace("newsatlasbr", quietly = TRUE)) {
  if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes")
  remotes::install_github("voltdatalab/newsatlasbr", quiet = TRUE)
}
library(newsatlasbr)

# ---- authenticate ----
cat("Authenticating...\n")
atlas_signin(email = email, password = password)
cat("Authentication successful.\n\n")

# ---- download municipal-level summary data ----
cat("Downloading municipal news presence data...\n")
municipalities <- get_municipalities()
cat(sprintf("  Rows: %d | Columns: %d\n", nrow(municipalities), ncol(municipalities)))
cat("  Columns:", paste(names(municipalities), collapse = ", "), "\n\n")

out_path <- file.path(RAW_DIR, "atlas_noticias_municipalities.csv")
write.csv(municipalities, out_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved ->", out_path, "\n")

# ---- download organization-level data for all states ----
# organizations_state() does not accept "all" — must loop over UFs
STATES <- c("AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
            "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO")

cat("\nDownloading organization-level data by state (27 UFs)...\n")
orgs_list <- vector("list", length(STATES))
names(orgs_list) <- STATES

for (uf in STATES) {
  cat(sprintf("  %s ... ", uf))
  orgs_list[[uf]] <- tryCatch(
    organizations_state(uf = uf),
    error = function(e) {
      cat("FAILED:", conditionMessage(e), "\n")
      NULL
    }
  )
  n <- if (!is.null(orgs_list[[uf]])) nrow(orgs_list[[uf]]) else 0
  cat(sprintf("%d orgs\n", n))
}

orgs <- do.call(rbind, orgs_list[!sapply(orgs_list, is.null)])
rownames(orgs) <- NULL

# Drop nested list columns that write.csv cannot serialize
scalar_cols <- names(orgs)[!sapply(orgs, is.list)]
orgs <- orgs[, scalar_cols]

cat(sprintf("\nTotal organizations: %d rows x %d cols\n", nrow(orgs), ncol(orgs)))
cat("Columns:", paste(names(orgs), collapse = ", "), "\n")

orgs_path <- file.path(RAW_DIR, "atlas_noticias_organizations.csv")
write.csv(orgs, orgs_path, row.names = FALSE, fileEncoding = "UTF-8")
cat("Saved ->", orgs_path, "\n")

cat("\nDone.\n")
