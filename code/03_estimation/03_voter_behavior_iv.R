# 03_voter_behavior_iv.R
# -----------------------------------------------------------------------------
# MAIN voter-behaviour estimation (self-contained; full municipal sample).
#
# The headline table is OFFICE-AWARE. Blank/null votes are cast on a SEPARATE
# ballot for mayor and for council, so spoilage is a per-office outcome (just like
# the candidate-composition outcomes, which are reported for both the executive
# and the legislative race). The headline panel therefore splits Null / Blank /
# Non-valid by office (Mayor, Council).
#
# Turnout is NOT office-specific (a voter attends once: a single comparecimento),
# so turnout and abstention (= 1 - turnout) are reported once, municipality-wide,
# in a companion block. A roll-off placebo (Council - Mayor) is reported as a
# specification check, not a headline outcome.
#
# Baseline "option 1a" spec (spec_config.json): baseline universal controls +
# per-outcome lagged DV (the outcome's own 2020 level); state FE; CLUSTER BY STATE
# (cluster_id, 27 units) -- the leave-own-state-out shift is constant within a
# state, so clustering at the state level is the appropriate level for the
# shift-share variation; 2SLS, endogenous delta_log1p_competition_lawsuits,
# instrument bartik_iv; Lee et al. (2022) tF weak-IV critical values (K=1, 5%).
#
# The lawsuit data is municipality-resolved (SIG source), so estimation is on the
# full municipal sample. (The former single-zone heterogeneity split, a workaround
# from the zona-level era, has been retired.)
#
# Outputs:
#   regressions/voter_office_spoilage_iv.csv   tex/voter_office_spoilage.tex   (MAIN)
#   regressions/voter_turnout_iv.csv           tex/voter_turnout.tex
#   regressions/voter_rolloff_placebo_iv.csv   tex/voter_rolloff_placebo.tex   (placebo)
#   regressions/voter_first_stage.csv          tex/voter_first_stage.tex
# -----------------------------------------------------------------------------

suppressPackageStartupMessages({
  user_lib <- "C:/Users/naral/R/win-library/4.6"
  if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))
  library(data.table)
  library(fixest)
})

SCRIPT_DIR <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  dirname(normalizePath(sub("^--file=", "", grep("^--file=", args, value = TRUE)[1])))
}, error = function(e) getwd())

source(file.path(SCRIPT_DIR, "..", "utils", "spec_config.R"))

ROOT    <- normalizePath(file.path(SCRIPT_DIR, "..", ".."))
REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
TEX_DIR <- file.path(ROOT, "output", "tables", "tex")
dir.create(REG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR, recursive = TRUE, showWarnings = FALSE)

# ---- load + merge ------------------------------------------------------------
design <- as.data.frame(fread(
  file.path(ROOT, "data", "estimation", "act_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
for (rc in c("code_meso")) if (rc %in% names(design)) design[[rc]] <- as.character(design[[rc]])

admin <- fread(file.path(ROOT, "data", "clean", "electoral_admin_outcomes.csv"))
spoil <- fread(file.path(ROOT, "data", "clean", "office_ballot_spoilage.csv"),
               colClasses = list(character = "municipality_id_tse"))
spoil[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]

# Abstention rate = abstentions / registered = 1 - turnout (exactly). We report
# it alongside turnout so the "share who did not vote" margin can be read off
# directly. Because abstention = 1 - turnout, its IV coefficient is the EXACT
# negative of turnout's (identical SE and p) -- shown for interpretability, not as
# independent evidence. Reconstructed from admin to obtain the 2020->2024 delta;
# the design already carries the 2020 level (abstention_rate_2020) as lagged DV.
ab <- dcast(admin, municipality_id_tse ~ election_year, value.var = "abstention_rate")
# pad bare-integer TSE codes to the canonical 5-char key ("01007") so the 519
# leading-zero municipalities are not silently dropped by the merge.
ab[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
setnames(ab, c("2020", "2024"), c("abstention_rate_2020_adm", "abstention_rate_2024_adm"))
ab[, delta_abstention_rate_2024_2020 := abstention_rate_2024_adm - abstention_rate_2020_adm]

dt <- merge(design, spoil, by = "municipality_id_tse", all.x = TRUE)
dt <- merge(dt, ab[, .(municipality_id_tse, delta_abstention_rate_2024_2020)],
            by = "municipality_id_tse", all.x = TRUE)

# ---- spec pieces -------------------------------------------------------------
INSTR <- spec_instrument()
ENDOG <- spec_endogenous()
CL    <- spec_cluster_col()
BASE  <- spec_baseline_controls()
EXT   <- spec_extended_controls()
avail <- function(controls, data) controls[controls %in% names(data)]

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

SAMP <- dt

# ---- generic 2SLS for one outcome -------------------------------------------
# fit_iv() returns the fitted feols IV model (the outcome's 2020 mean and mean
# delta attached as attributes). extract_iv() pulls the headline numbers for the
# CSVs. The SAME fitted models are handed to etable() for the LaTeX tables, so the
# tables and the CSVs can never drift, and every table is etable-generated (stars
# from signif.code, decimal-aligned via decimalize()) -- the first-stage rule.
fit_iv <- function(dep, lagdv, ctr0 = BASE, fe = "state") {
  ctr  <- avail(c(ctr0, lagdv), SAMP)
  req  <- unique(c(dep, ENDOG, INSTR, CL, fe, ctr))
  samp <- SAMP[complete.cases(SAMP[, req, drop = FALSE]), ]
  rhs  <- paste(ctr, collapse = " + ")
  fml  <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, fe, ENDOG, INSTR))
  m    <- feols(fml, data = samp, cluster = as.formula(paste0("~", CL)),
                warn = FALSE, notes = FALSE)
  attr(m, "mean_2020")  <- mean(samp[[lagdv]], na.rm = TRUE)
  attr(m, "mean_delta") <- mean(samp[[dep]], na.rm = TRUE)
  m
}
extract_iv <- function(m) {
  ct  <- coeftable(m); iv <- paste0("fit_", ENDOG); row <- ct[iv, ]
  Fst <- tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
  list(coef = unname(row["Estimate"]), se = unname(row["Std. Error"]),
       t = unname(row["t value"]), p = unname(row["Pr(>|t|)"]),
       first_F = Fst, tF_cv = get_tF_cv(Fst),
       reject_tF = abs(unname(row["t value"])) > get_tF_cv(Fst),
       mean_2020 = attr(m, "mean_2020"), mean_delta = attr(m, "mean_delta"),
       N = m$nobs)
}

# =============================================================================
# 1. OFFICE-AWARE SPOILAGE (MAIN) — panels Mayor / Council
# =============================================================================
OFFICE <- list(
  prefeito_null    = c("delta_prefeito_null_share_cast_2024_2020",    "prefeito_null_share_cast_2020",    "Mayor",    "Null"),
  prefeito_blank   = c("delta_prefeito_blank_share_cast_2024_2020",   "prefeito_blank_share_cast_2020",   "Mayor",    "Blank"),
  prefeito_invalid = c("delta_prefeito_invalid_share_cast_2024_2020", "prefeito_invalid_share_cast_2020", "Mayor",    "Non-valid"),
  vereador_null    = c("delta_vereador_null_share_cast_2024_2020",    "vereador_null_share_cast_2020",    "Council",  "Null"),
  vereador_blank   = c("delta_vereador_blank_share_cast_2024_2020",   "vereador_blank_share_cast_2020",   "Council",  "Blank"),
  vereador_invalid = c("delta_vereador_invalid_share_cast_2024_2020", "vereador_invalid_share_cast_2020", "Council",  "Non-valid"))

office_models <- lapply(OFFICE, function(o) fit_iv(o[1], o[2]))
office_res <- rbindlist(Map(function(k, o, m) {
  r <- extract_iv(m)
  data.table(okey = k, panel = o[3], measure = o[4],
             coef = r$coef, se = r$se, t = r$t, p = r$p,
             first_F = r$first_F, tF_cv = r$tF_cv, reject_tF = r$reject_tF,
             mean_2020 = r$mean_2020, mean_delta = r$mean_delta, N = r$N)
}, names(OFFICE), OFFICE, office_models))
fwrite(office_res, file.path(REG_DIR, "voter_office_spoilage_iv.csv"))

# =============================================================================
# 2. OVERALL turnout + abstention (municipality-wide, office-invariant)
# =============================================================================
# Abstention = 1 - turnout exactly, so its IV coefficient is the exact negative of
# turnout's (same SE, same p). Reported alongside turnout purely to read off the
# "did not vote" margin's sign and magnitude directly.
OVERALL <- list(
  turnout_rate    = c("delta_turnout_rate_2024_2020",       "turnout_rate_2020",    "Turnout (registered)"),
  abstention_rate = c("delta_abstention_rate_2024_2020",    "abstention_rate_2020", "Abstention (1 - turnout)"))
overall_models <- lapply(OVERALL, function(o) fit_iv(o[1], o[2]))
overall_res <- rbindlist(Map(function(k, o, m) {
  r <- extract_iv(m)
  data.table(outcome = k, label = o[3],
             coef = r$coef, se = r$se, t = r$t, p = r$p,
             first_F = r$first_F, tF_cv = r$tF_cv, reject_tF = r$reject_tF,
             mean_2020 = r$mean_2020, mean_delta = r$mean_delta, N = r$N)
}, names(OVERALL), OVERALL, overall_models))
fwrite(overall_res, file.path(REG_DIR, "voter_turnout_iv.csv"))

# =============================================================================
# 2b. ROLLOFF PLACEBO — office-differenced spoilage (Council minus Mayor)
# =============================================================================
# Rolloff differences the two ballots filled in by the SAME voters in one sitting,
# netting out everything common to the voter and the municipality (disaffection,
# education, machine familiarity, a bad turnout day). Our treatment is
# municipality-wide, so a genuine common participation shock should DIFFERENCE OUT
# here: a coefficient near zero supports the headline as a real municipality-level
# effect rather than a one-ballot artifact, while a significant rolloff effect
# would flag office-idiosyncratic contamination. This is a placebo / specification
# check, NOT a headline outcome.
ROLLOFF <- list(
  rolloff_null    = c("delta_rolloff_null_share_cast_2024_2020",    "rolloff_null_share_cast_2020",    "Null"),
  rolloff_blank   = c("delta_rolloff_blank_share_cast_2024_2020",   "rolloff_blank_share_cast_2020",   "Blank"),
  rolloff_invalid = c("delta_rolloff_invalid_share_cast_2024_2020", "rolloff_invalid_share_cast_2020", "Non-valid"))
rolloff_models <- lapply(ROLLOFF, function(o) fit_iv(o[1], o[2]))
rolloff_res <- rbindlist(Map(function(k, o, m) {
  r <- extract_iv(m)
  data.table(okey = k, measure = o[3],
             coef = r$coef, se = r$se, t = r$t, p = r$p,
             first_F = r$first_F, tF_cv = r$tF_cv, reject_tF = r$reject_tF,
             mean_2020 = r$mean_2020, mean_delta = r$mean_delta, N = r$N)
}, names(ROLLOFF), ROLLOFF, rolloff_models))
fwrite(rolloff_res, file.path(REG_DIR, "voter_rolloff_placebo_iv.csv"))

# Consolidated long file consumed by downstream summaries (23_mde_power.R,
# slides). One row per voter outcome; the office-specific spoilage uses the
# MAYORAL race (the litigated executive contest) under its historical names so
# existing consumers keep working. spec="baseline" mirrors the old schema.
mayor_map <- c(null_share_cast = "Null", blank_share_cast = "Blank",
               invalid_share_cast = "Non-valid")
consol <- rbindlist(list(
  office_res[panel == "Mayor"][match(mayor_map, measure)][, .(
    spec = "baseline", outcome = names(mayor_map),
    coef, se, t, p, first_F, tF_cv, reject_tF, mean_2020, mean_delta, N)],
  overall_res[, .(spec = "baseline", outcome,
    coef, se, t, p, first_F, tF_cv, reject_tF, mean_2020, mean_delta, N)]
))
fwrite(consol, file.path(REG_DIR, "voter_behavior_iv.csv"))

# =============================================================================
# 3. FIRST STAGE -- agreed robustness EQUATIONS only
# =============================================================================
# The first-stage robustness battery is a set of alternative estimating
# EQUATIONS: (i) baseline controls + state FE, (ii) extended controls,
# (iii) mesoregion fixed effects.
fs_specs <-
  list(list("baseline",          "Baseline",          BASE, "state"),
       list("extended_controls", "Extended controls", EXT,  "state"),
       list("region_fe",         "Mesoregion FE",     BASE, "code_meso"))
fit_fs <- function(sp) {
  ctr <- avail(sp[[3]], SAMP); fe <- sp[[4]]
  req  <- unique(c(ENDOG, INSTR, CL, fe, ctr))
  samp <- SAMP[complete.cases(SAMP[, req, drop = FALSE]), ]
  rhs  <- paste(c(INSTR, ctr), collapse = " + ")
  m <- feols(as.formula(sprintf("%s ~ %s | %s", ENDOG, rhs, fe)),
             data = samp, cluster = as.formula(paste0("~", CL)),
             warn = FALSE, notes = FALSE)
  attr(m, "n_clusters") <- length(unique(samp[[CL]])); m
}
fs_models <- lapply(fs_specs, fit_fs)
first_stage <- rbindlist(Map(function(sp, m) {
  row <- coeftable(m)[INSTR, ]; Fstat <- unname(row["t value"])^2
  data.table(spec = sp[[1]], label = sp[[2]], coef = unname(row["Estimate"]),
             se = unname(row["Std. Error"]), p = unname(row["Pr(>|t|)"]),
             F = Fstat, tF_cv = get_tF_cv(Fstat),
             N = m$nobs, n_clusters = attr(m, "n_clusters"))
}, fs_specs, fs_models))
fwrite(first_stage, file.path(REG_DIR, "voter_first_stage.csv"))

# =============================================================================
# 4. LaTeX TABLES — every table via fixest::etable() (the first-stage rule)
# =============================================================================
# All regression tables are etable-generated: the coefficient, SE, and stars come
# from etable's own formatting (signif.code), none hand-typeset; the coefficient
# sits above its SE (stacked, conventional layout). fixest 0.14 only emits centered
# text columns, so decimalize() rewrites the numeric columns to dcolumn D-columns
# -- every value carrying a decimal point (coef, SE, means, F, tF) is aligned on
# the decimal, matching the F / tF rows. Integer/text cells (N, headers) are
# centered via \multicolumn. Requires \usepackage{dcolumn} in the slide preamble.
decimalize <- function(tab, nC) {
  dspec <- paste(rep("D{.}{.}{-1}", nC), collapse = " ")
  wrapc <- function(x) sprintf("\\multicolumn{1}{c}{%s}", x)
  out <- vapply(tab, function(ln) {
    if (grepl("\\\\begin\\{tabular\\}", ln))
      return(sprintf("\\begin{tabular}{l %s}", dspec))
    if (!grepl("&", ln) || grepl("\\\\multicolumn\\{[0-9]", ln)) return(ln)
    m    <- regexpr("\\\\\\\\[[:space:]]*$", ln)
    term <- if (m > 0) regmatches(ln, m) else ""
    body <- sub("\\\\\\\\[[:space:]]*$", "", ln)
    cells <- strsplit(body, "&", fixed = TRUE)[[1]]
    if (length(cells) < 2) return(ln)
    dat <- vapply(trimws(cells[-1]), function(c0) {
      if (c0 == "") ""
      else if (grepl("[0-9]\\.[0-9]", c0)) paste0(" ", gsub("$", "", c0, fixed = TRUE), " ")
      else wrapc(c0)
    }, "", USE.NAMES = FALSE)
    paste0(paste(c(cells[1], dat), collapse = "&"), term)
  }, "", USE.NAMES = FALSE)
  out
}

gen_comment <- "% Auto-generated by code/03_estimation/03_voter_behavior_iv.R via fixest::etable() -- do not edit."

# Second-stage IV table: the instrumented (endogenous) coefficient with its
# first-stage F and tF critical value, plus the outcome's 2020 mean and mean change
# as extra lines. `headers` is passed straight to etable -- a character vector
# (one title per column) or a list (grouped/spanning header rows).
write_iv_etable <- function(models, headers, file) {
  fitn <- paste0("fit_", ENDOG)
  Fv   <- vapply(models, function(m)
            tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_), 0)
  tFv  <- vapply(Fv, get_tF_cv, 0)
  m20  <- vapply(models, function(m) attr(m, "mean_2020"),  0)
  mdl  <- vapply(models, function(m) attr(m, "mean_delta"), 0)
  et <- etable(
    models, tex = TRUE,
    keep_raw = fitn, depvar = FALSE, headers = headers,
    dict = setNames("$\\Delta\\log(1+\\text{lawsuits})$", fitn),
    fitstat = ~ n, digits = "r3", digits.stats = "r3",
    extralines = list("Mean (2020)"              = sprintf("%.3f", m20),
                      "Mean $\\Delta$ 2020--24"   = sprintf("%.3f", mdl),
                      "First-stage $F$"           = sprintf("%.1f", Fv),
                      "$tF_{\\mathrm{cv}}$ (5\\%)" = sprintf("%.2f", tFv)),
    signif.code = c("***" = 0.01, "**" = 0.05, "*" = 0.10),
    style.tex = style.tex("base"))
  a <- grep("\\\\begin\\{tabular\\}", et)[1]
  b <- grep("\\\\end\\{tabular\\}",   et)[1]
  writeLines(c(gen_comment, decimalize(et[a:b], length(models))), file)
}

# MAIN: office spoilage, (Mayor | Council) x (Null, Blank, Non-valid)
write_iv_etable(
  office_models,
  headers = list(" "  = list("Mayor" = 3, "Council" = 3),
                 "  " = c("Null","Blank","Non-valid","Null","Blank","Non-valid")),
  file = file.path(TEX_DIR, "voter_office_spoilage.tex"))

# Overall turnout / abstention (municipality-wide)
write_iv_etable(
  overall_models,
  headers = c("Turnout", "Abstention"),
  file = file.path(TEX_DIR, "voter_turnout.tex"))

# Rolloff placebo (Council - Mayor, office-differenced)
write_iv_etable(
  rolloff_models,
  headers = c("Null", "Blank", "Non-valid"),
  file = file.path(TEX_DIR, "voter_rolloff_placebo.tex"))

# First stage: instrument -> endogenous, across the robustness equations
Fvals  <- vapply(fs_models, function(m) unname(coeftable(m)[INSTR, "t value"])^2, 0)
tFvals <- vapply(Fvals, get_tF_cv, 0)
labs   <- vapply(fs_specs, `[[`, "", 2)
et <- etable(
  fs_models, tex = TRUE,
  keep_raw = INSTR, depvar = FALSE, headers = labs,
  dict = c(setNames("Bartik IV", INSTR), state = "State", code_meso = "Mesoregion"),
  fitstat = ~ n, digits = 3,
  extralines = list("First-stage $F$"           = sprintf("%.1f", Fvals),
                    "$tF_{\\mathrm{cv}}$ (5\\%)" = sprintf("%.2f", tFvals)),
  signif.code = c("***" = 0.01, "**" = 0.05, "*" = 0.10),
  style.tex = style.tex("base"))
a <- grep("\\\\begin\\{tabular\\}", et)[1]
b <- grep("\\\\end\\{tabular\\}",   et)[1]
writeLines(c(gen_comment, decimalize(et[a:b], length(fs_models))),
           file.path(TEX_DIR, "voter_first_stage.tex"))

# =============================================================================
# 5. CONSOLE
# =============================================================================
cat("\n==== VOTER BEHAVIOUR 2SLS -- full municipal sample ====\n")
cat("Office spoilage (votes-cast denominator); panels Mayor / Council\n")
print(office_res[, .(panel, measure, coef = round(coef,4), se = round(se,4),
                     p = round(p,4), first_F = round(first_F,1),
                     tF_cv = round(tF_cv,2), reject_tF, mean_2020 = round(mean_2020,4), N)])
cat("\n-- overall turnout / effective participation (municipality-wide) --\n")
print(overall_res[, .(label, coef = round(coef,4), se = round(se,4),
                      p = round(p,4), first_F = round(first_F,1),
                      tF_cv = round(tF_cv,2), reject_tF, mean_2020 = round(mean_2020,4), N)])
cat("\n-- rolloff PLACEBO (Council - Mayor; expect ~0 if effect is a common shock) --\n")
print(rolloff_res[, .(measure, coef = round(coef,4), se = round(se,4),
                      p = round(p,4), first_F = round(first_F,1),
                      tF_cv = round(tF_cv,2), reject_tF, mean_2020 = round(mean_2020,4), N)])
cat("\n-- first stage --\n")
print(first_stage[, .(spec, coef = round(coef,3), se = round(se,3),
                      F = round(F,1), tF_cv = round(tF_cv,2), N)])

cat("\nWrote:\n",
    "  output/tables/regressions/voter_office_spoilage_iv.csv  + tex/voter_office_spoilage.tex\n",
    "  output/tables/regressions/voter_turnout_iv.csv          + tex/voter_turnout.tex\n",
    "  output/tables/regressions/voter_rolloff_placebo_iv.csv  + tex/voter_rolloff_placebo.tex\n",
    "  output/tables/regressions/voter_first_stage.csv         + tex/voter_first_stage.tex\n")
