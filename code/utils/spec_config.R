# Load the canonical estimation-design config (code/spec_config.json).
#
# Single source of truth for control lists, FE, clustering, and the per-outcome
# lagged-DV map. See SPECIFICATION.md. Source this from estimation scripts
# instead of hard-coding control lists:
#
#   source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))
#   ctrls <- c(spec_baseline_controls(), spec_lagged_dv(outcome))
#
# Note: in the R designs the FE column is renamed state -> SG_UF; spec_fe_col()
# returns the post-rename name for the baseline.

suppressPackageStartupMessages(library(jsonlite))

.spec_config_path <- function() {
  # Resolve relative to this file when sourced via source(); fall back to cwd.
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  here <- if (length(file_arg) > 0) dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
  candidates <- c(
    file.path(here, "..", "spec_config.json"),
    file.path(here, "spec_config.json"),
    "code/spec_config.json"
  )
  hit <- candidates[file.exists(candidates)]
  if (length(hit) == 0) stop("spec_config.json not found")
  normalizePath(hit[1])
}

SPEC_CONFIG <- jsonlite::fromJSON(.spec_config_path(), simplifyVector = TRUE)

spec_baseline_controls <- function() as.character(SPEC_CONFIG$baseline_controls)

spec_extended_controls <- function()
  c(spec_baseline_controls(), as.character(SPEC_CONFIG$extended_controls_extra))

# Returns the 2020-level lagged DV for a delta outcome, or NA if none defined.
spec_lagged_dv <- function(outcome) {
  val <- SPEC_CONFIG$lagged_dv[[outcome]]
  if (is.null(val)) NA_character_ else as.character(val)
}

# FE column. R designs rename state -> SG_UF, so map the baseline accordingly.
spec_fe_col <- function(which = "baseline") {
  raw <- SPEC_CONFIG$fe[[which]]
  if (identical(raw, "state")) "SG_UF" else raw
}

spec_cluster_col <- function() as.character(SPEC_CONFIG$cluster)
spec_instrument  <- function() as.character(SPEC_CONFIG$instrument)
spec_endogenous  <- function() as.character(SPEC_CONFIG$endogenous)

