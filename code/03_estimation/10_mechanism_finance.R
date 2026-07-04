# Mechanism test: RESOURCE DRAIN / ATTRITION (campaign finance) -- fixest (R)
# -----------------------------------------------------------------------------
# The IV headline is CONSOLIDATION: exposure widens the mayoral top-two margin
# without changing the field or the winner. Entry-deterrence is rejected
# (compositional neutrality). The surviving candidate-side channel is resource
# drain: if litigation crowds out a CHALLENGER's campaign faster than the
# front-runner's, the front-runner pulls away -> the margin widens with the same
# field. Test = 2SLS of judicialization on the 2020->2024 change in campaign
# spending, cut by VOTE RANK (front-runner vs challenger) and by SEAT TYPE
# (open vs contested), same instrument/controls/FE/cluster as the headline.
#
# Outcomes (all pure first differences; SPCE has no clean 2016 baseline built):
#   delta_log1p_ch_total   challenger (rank 2) total contracted spend
#   delta_log1p_fr_total   front-runner (rank 1) total contracted spend
#   delta_ch_spend_share   challenger share of top-2 spend  <- sharpest signature
#   delta_log1p_muni_total whole-field mayoral spend (scale check)
#   delta_log1p_ch_mkt / delta_log1p_fr_mkt   marketing-only twins
#
# Prediction if the channel is live: challenger spend and challenger SHARE fall
# under exposure; front-runner spend does not; the drop concentrates in
# CONTESTED seats (an incumbent to out-resource), matching the blank-vote result.

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(fixest)
  library(data.table)
})

# ---- path detection (RStudio + Rscript) ----
if (exists("rstudioapi") && tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE)) {
  SCRIPT_DIR <- dirname(rstudioapi::getSourceEditorContext()$path)
} else {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  SCRIPT_DIR <- if (length(file_arg) > 0) {
    dirname(normalizePath(sub("^--file=", "", file_arg[1])))
  } else getwd()
}
PROJECT_ROOT   <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
ESTIMATION_DIR <- file.path(PROJECT_ROOT, "data", "estimation")
CLEAN_DIR      <- file.path(PROJECT_ROOT, "data", "clean")
ESTIMATES_DIR  <- file.path(PROJECT_ROOT, "output", "tables", "regressions")
TEX_DIR        <- file.path(PROJECT_ROOT, "output", "tables", "tex")
dir.create(ESTIMATES_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR,       recursive = TRUE, showWarnings = FALSE)

# ============================================================
# 1. LOAD + MERGE
# ============================================================
df <- as.data.frame(fread(
  file.path(ESTIMATION_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
fin <- as.data.frame(fread(
  file.path(CLEAN_DIR, "candidate_finance_panel.csv"),
  colClasses = list(character = "municipality_id_tse")
))
n_design <- nrow(df)
df <- merge(df, fin, by = "municipality_id_tse", all.x = TRUE)
matched <- sum(df$municipality_id_tse %in% fin$municipality_id_tse)
cat(sprintf("Design %d munis; finance panel %d munis; matched %d (%.1f%%)\n",
            n_design, nrow(fin), matched, 100 * matched / n_design))

names(df)[names(df) == "state"]      <- "SG_UF"

INSTRUMENT <- "bartik_iv_2020_2024"
ENDOGENOUS <- "delta_log1p_competition_lawsuits_2024_2020"
BASELINE_CONTROLS <- c(
  "log_pop_2010", "urban_share_2010", "log_income_pc_2010", "higher_educ_share_2010",
  "log1p_total_valid_votes_2020", "margin_2016"
)

OUTCOMES <- c(
  delta_log1p_ch_total   = "$\\Delta$ Log challenger spend",
  delta_log1p_fr_total   = "$\\Delta$ Log front-runner spend",
  delta_ch_spend_share   = "$\\Delta$ Challenger spend share",
  delta_log1p_muni_total = "$\\Delta$ Log field spend",
  delta_log1p_ch_mkt     = "$\\Delta$ Log challenger marketing",
  delta_log1p_fr_mkt     = "$\\Delta$ Log front-runner marketing"
)

# ============================================================
# 2. HELPERS  (self-contained; mirrors 02_iv_main.R house style)
# ============================================================
avail <- function(controls, data) controls[controls %in% names(data)]
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

SEATS <- list(
  full      = function(d) d,
  open      = function(d) d[!is.na(d$open_seat_2024) & d$open_seat_2024 == 1L, ],
  contested = function(d) d[!is.na(d$open_seat_2024) & d$open_seat_2024 == 0L, ]
)

# 2SLS in pure first-difference form: y ~ controls | SG_UF | endog ~ instrument.
fit_iv <- function(data, y) {
  ctrls <- avail(BASELINE_CONTROLS, data)
  req   <- unique(c(y, INSTRUMENT, ENDOGENOUS, "SG_UF", "cluster_id", ctrls))
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  if (nrow(samp) < 50) return(NULL)
  rhs   <- if (length(ctrls) > 0) paste(ctrls, collapse = " + ") else "1"
  fml   <- as.formula(sprintf("%s ~ %s | SG_UF | %s ~ %s", y, rhs, ENDOGENOUS, INSTRUMENT))
  fit   <- feols(fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  attr(fit, "mean_delta") <- mean(samp[[y]], na.rm = TRUE)
  attr(fit, "n_clusters") <- length(unique(samp$cluster_id))
  fit
}

iv_name <- paste0("fit_", ENDOGENOUS)
grab <- function(fit, f) if (is.null(fit)) NA_real_ else unname(f(fit)[iv_name])

# ============================================================
# 3. ESTIMATE (outcomes x seat subsamples)
# ============================================================
fits <- list()   # fits[[seat]][[outcome]]
rows <- list()
for (seat in names(SEATS)) {
  dsub <- SEATS[[seat]](df)
  fits[[seat]] <- list()
  for (y in names(OUTCOMES)) {
    fit <- fit_iv(dsub, y)
    fits[[seat]][[y]] <- fit
    if (is.null(fit)) next
    fs_F <- tryCatch(fitstat(fit, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
    rows[[length(rows) + 1]] <- data.frame(
      seat = seat, outcome = y,
      coef = grab(fit, coef), se = grab(fit, se),
      t = grab(fit, tstat), p = grab(fit, pvalue),
      mean_delta = attr(fit, "mean_delta"),
      first_stage_F = fs_F, nobs = nobs(fit),
      n_clusters = attr(fit, "n_clusters"),
      stringsAsFactors = FALSE
    )
  }
}
res <- do.call(rbind, rows)
res_path <- file.path(ESTIMATES_DIR, "mechanism_finance_fixest.csv")
write.csv(res, res_path, row.names = FALSE)
cat("  Wrote:", res_path, "\n")
print(res[res$seat == "full", c("outcome", "coef", "se", "p", "mean_delta", "nobs")], row.names = FALSE)

# ============================================================
# 4. HOUSE-STYLE TABLES (hand-built, mylight band on coef row)
# ============================================================
star <- function(p) {
  if (is.na(p)) return("")
  if (p < .01) "$^{***}$" else if (p < .05) "$^{**}$" else if (p < .10) "$^{*}$" else ""
}
coef_cell <- function(fit) if (is.null(fit)) "---" else sprintf("%.3f%s", grab(fit, coef), star(grab(fit, pvalue)))
se_cell   <- function(fit) if (is.null(fit)) "" else sprintf("\\textcolor{mygray}{(%.3f)}", grab(fit, se))
mean_cell <- function(fit) if (is.null(fit)) "" else sprintf("%.3f", attr(fit, "mean_delta"))
n_cell    <- function(fit) if (is.null(fit)) "" else formatC(nobs(fit), format = "d", big.mark = ",")
hrow <- function(label, cells) paste0(label, " & ", paste(cells, collapse = " & "), " \\\\")

write_tex <- function(path, lines) {
  writeLines(c("% Auto-generated by code/03_estimation/10_mechanism_finance.R",
               "% Do not edit manually -- rerun the generating script to update", "", lines),
             con = path)
  cat("  Wrote:", path, "\n")
}

# ---- Seat split (transposed): rows = subsamples, cols = challenger/front-runner/share
#          Bands the Contested row -- the seat where an incumbent can be out-resourced.
#          N embedded in each subsample label (N differs by row). ----
{
  outs <- c("delta_log1p_ch_total", "delta_log1p_fr_total", "delta_ch_spend_share")
  seat_lab <- c(full = "All seats", open = "Open seat", contested = "Contested")
  hdr  <- sprintf("\\textbf{%s}", OUTCOMES[outs])
  lines <- c(
    sprintf("\\begin{tabular}{l*{%d}{c}}", length(outs)),
    "\\toprule\\toprule",
    hrow("Subsample ($N$)", hdr),
    "\\midrule"
  )
  for (seat in c("full", "open", "contested")) {
    mods <- lapply(outs, function(y) fits[[seat]][[y]])
    n_lab <- n_cell(fits[[seat]][["delta_log1p_ch_total"]])
    row_lab <- sprintf("\\textbf{%s} (%s)", seat_lab[seat], n_lab)
    lines <- c(lines,
      if (seat == "contested") "\\rowcolor{mylight}" else NULL,
      hrow(row_lab, vapply(mods, coef_cell, "")),
      if (seat == "contested") "\\rowcolor{mylight}" else NULL,
      hrow("", vapply(mods, se_cell, "")))
  }
  lines <- c(lines, "\\bottomrule\\bottomrule", "\\end{tabular}")
  write_tex(file.path(TEX_DIR, "mechanism_finance_seat.tex"), lines)
}

cat("\nDone: campaign-finance resource-drain mechanism.\n")
