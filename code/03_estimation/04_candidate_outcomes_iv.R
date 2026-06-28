# 04_candidate_outcomes_iv.R
# -----------------------------------------------------------------------------
# Current-language estimation (SPECIFICATION.md + code/spec_config.json) for the
# CANDIDATE outcome side, organised by SUBSTANTIVE THEME.
#
# ALL OUTCOMES ARE VOTE SHARES (vote-weighted municipality shares / vote-share
# margins). We deliberately do NOT use the realised "elected" / binary-winner
# outcomes: a single binary winner per municipality is a high-variance object, so
# the mayoral elected-trait and winner-identity indicators are underpowered (wide
# CIs that no cluster choice tightens -- see the cluster-robustness diagnostic).
# The continuous vote-share margin answers the same substantive question with far
# more signal: "did a non-white / new / female candidate win?" is read off the
# corresponding vote share, and contest decisiveness is read off the winner /
# runner-up vote share and the top-two margin rather than a 0/1 majority flag.
# (The dropped elected-composition and winner-binary outcomes live in git history
# -- prior committed version of this script -- if a future power gain revives them.)
#
# Four themes, each comparing the two offices SOUGHT (mayor vs. council) side by
# side except where an office is structurally inapplicable:
#   T1. Descriptive representation  -- female / non-white / higher-ed VOTE share
#       (who draws votes), both offices.
#   T2. Renewal and incumbency      -- new-candidate / incumbent VOTE share, both
#       offices.
#   T3. Competition and fragmentation-- effective N and HHI of the VOTE
#       distribution. In a mayoral race each party fields one candidate, so
#       candidate- and party-level fragmentation coincide; the mayor panel shows
#       the two distinct measures (Eff. N, HHI) and the council panel shows all
#       four (candidate- and party-level).
#   T4. Contest closeness (executive)-- winner / runner-up VOTE share and the
#       top-two margin. Executive-only: "the winner" and the top-two gap have no
#       clean meaning in a multi-seat proportional council race.
#
# incumbent_reelected_share is excluded: its 2020 baseline is structurally ~0 (the
# 2020 re-election rate needs 2016 winners, not built), so its "delta" is just the
# 2024 level and breaks the first-difference design.
#
# Spec: baseline "option 1a" (spec_config.json) -- baseline universal controls +
# per-outcome lagged DV (the outcome's own 2020 level); state FE; CLUSTER BY STATE
# (cluster_id, 27 units) -- the leave-own-state-out shift is constant within a
# state, so the state is the level at which the shift-share variation lives
# (Adao-Kolesar-Morales); 2SLS, endogenous delta_log1p_competition_lawsuits,
# instrument bartik_iv; Lee et al. (2022) tF weak-IV critical values (K=1, 5%).
#
# Every table is etable()-generated (stars from signif.code, decimal-aligned via
# decimalize()), matching the voter-behaviour and first-stage tables.
#
# Outputs:
#   regressions/candidate_outcomes_iv.csv  (long: theme x office x outcome)
#   regressions/candidate_first_stage.csv  (per office, baseline relevance row)
#   tex/candidate_rep_voteshare.tex  tex/candidate_renewal.tex
#   tex/candidate_competition.tex    tex/candidate_contest.tex
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
EST_DIR <- file.path(ROOT, "data", "estimation")
REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
TEX_DIR <- file.path(ROOT, "output", "tables", "tex")
dir.create(REG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR, recursive = TRUE, showWarnings = FALSE)

read_design <- function(path) as.data.frame(fread(
  path, colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
designs <- list(
  executive   = read_design(file.path(EST_DIR, "act_design.csv")),
  legislative = read_design(file.path(EST_DIR, "legislative_design.csv"))
)
for (o in names(designs))
  if ("code_meso" %in% names(designs[[o]]))
    designs[[o]]$code_meso <- as.character(designs[[o]]$code_meso)

# --- spec pieces from config --------------------------------------------------
INSTR <- spec_instrument()        # bartik_iv_2020_2024 (standardized)
ENDOG <- spec_endogenous()        # delta_log1p_competition_lawsuits_2024_2020
CL    <- spec_cluster_col()       # cluster_id == STATE (27 UFs)
BASE  <- spec_baseline_controls() # option-1a universal controls
FE    <- "state"                  # baseline FE (UF); both designs use 'state'

avail <- function(controls, data) controls[controls %in% names(data)]

# tF weak-instrument critical values (Lee, McCrary, Moreira & Porter 2022,
# Table 1, 5% two-sided, K=1). Linear-interpolated; >=23.1 -> 1.96.
tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

# ---- generic 2SLS for one outcome in one office -----------------------------
# fit_one() returns the fitted feols IV model with the outcome's 2020 mean and mean
# delta attached as attributes. The SAME fitted models feed both the CSVs and
# etable(), so the tables and CSVs can never drift.
fit_one <- function(office, dep, ctr0 = BASE, fe = FE) {
  data  <- designs[[office]]
  lagdv <- spec_lagged_dv(dep)
  ctr   <- avail(c(ctr0, if (!is.na(lagdv)) lagdv), data)
  req   <- unique(c(dep, ENDOG, INSTR, CL, fe, ctr)); req <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  rhs   <- paste(ctr, collapse = " + ")
  fml   <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, fe, ENDOG, INSTR))
  m     <- feols(fml, data = samp, cluster = as.formula(paste0("~", CL)),
                 warn = FALSE, notes = FALSE)
  attr(m, "mean_2020")  <- if (!is.na(lagdv) && lagdv %in% names(samp))
                             mean(samp[[lagdv]], na.rm = TRUE) else NA_real_
  attr(m, "mean_delta") <- mean(samp[[dep]], na.rm = TRUE)
  attr(m, "office") <- office; attr(m, "dep") <- dep
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

# Build a both-office model list: executive outcomes first, then legislative, so a
# Mayor(n) | Council(n) spanning header lines up.
both_office_models <- function(outcomes)
  c(lapply(outcomes, function(o) fit_one("executive",   o[1])),
    lapply(outcomes, function(o) fit_one("legislative", o[1])))
# NB: span counts MUST be doubles -- fixest etable mis-parses an integer span
# (length() returns 3L) into a broken \multicolumn, so coerce with as.numeric().
office_header <- function(n_mayor, n_council, labs)
  list(" "  = list("Mayor" = as.numeric(n_mayor), "Council" = as.numeric(n_council)),
       "  " = labs)

# =============================================================================
# THEME outcome definitions  c(delta column, short label) -- all VOTE shares
# =============================================================================
REP_VOTE <- list(
  c("delta_female_vote_share_2024_2020",           "Female"),
  c("delta_nonwhite_vote_share_2024_2020",         "Non-white"),
  c("delta_higher_education_vote_share_2024_2020", "Higher-ed"))
RENEWAL <- list(
  c("delta_new_candidate_vote_share_2024_2020",       "New cand."),
  c("delta_incumbent_candidate_vote_share_2024_2020", "Incumbent"))
# Competition: mayor candidate-level == party-level (one candidate per party), so
# the mayor panel shows only the two distinct measures; council shows all four.
COMP_MAYOR <- list(
  c("delta_effective_n_candidates_vote_2024_2020", "Eff.\\ N"),
  c("delta_vote_hhi_candidate_2024_2020",          "HHI"))
COMP_COUNCIL <- list(
  c("delta_effective_n_candidates_vote_2024_2020", "Eff.\\ N cand."),
  c("delta_vote_hhi_candidate_2024_2020",          "HHI cand."),
  c("delta_effective_n_parties_vote_2024_2020",    "Eff.\\ N party"),
  c("delta_vote_hhi_party_2024_2020",              "HHI party"))
CONTEST <- list(   # executive only, continuous closeness margins
  c("delta_winner_vote_share_2024_2020",   "Winner VS"),
  c("delta_runnerup_vote_share_2024_2020", "Runner-up VS"),
  c("delta_margin_top1_top2_2024_2020",    "Margin"))

# Fit every theme's models -----------------------------------------------------
rep_models     <- both_office_models(REP_VOTE)
renewal_models <- both_office_models(RENEWAL)
competition_models <- c(
  lapply(COMP_MAYOR,   function(o) fit_one("executive",   o[1])),
  lapply(COMP_COUNCIL, function(o) fit_one("legislative", o[1])))
contest_models <- lapply(CONTEST, function(o) fit_one("executive", o[1]))

# =============================================================================
# Long results CSV (theme x office x outcome) -- driven by model attributes
# =============================================================================
collect <- function(models, theme, labels) {
  rbindlist(Map(function(m, lab) {
    r <- extract_iv(m)
    data.table(theme = theme, office = attr(m, "office"), outcome = lab,
               coef = r$coef, se = r$se, t = r$t, p = r$p,
               first_F = r$first_F, tF_cv = r$tF_cv, reject_tF = r$reject_tF,
               mean_2020 = r$mean_2020, mean_delta = r$mean_delta, N = r$N)
  }, models, labels))
}
labs2 <- function(outcomes) vapply(outcomes, `[`, "", 2)
res <- rbindlist(list(
  collect(rep_models,         "T1 Representation", rep(labs2(REP_VOTE), 2)),
  collect(renewal_models,     "T2 Renewal",        rep(labs2(RENEWAL), 2)),
  collect(competition_models, "T3 Competition",    c(labs2(COMP_MAYOR), labs2(COMP_COUNCIL))),
  collect(contest_models,     "T4 Contest",        labs2(CONTEST))
))
fwrite(res, file.path(REG_DIR, "candidate_outcomes_iv.csv"))

# =============================================================================
# Per-office baseline first stage (single relevance row per office)
# =============================================================================
fs_rows <- list()
for (office in c("executive", "legislative")) {
  data <- designs[[office]]
  ctr  <- avail(BASE, data)
  req  <- unique(c(ENDOG, INSTR, CL, FE, ctr))
  samp <- data[complete.cases(data[, req, drop = FALSE]), ]
  rhs  <- paste(c(INSTR, ctr), collapse = " + ")
  m    <- feols(as.formula(sprintf("%s ~ %s | %s", ENDOG, rhs, FE)),
                data = samp, cluster = as.formula(paste0("~", CL)),
                warn = FALSE, notes = FALSE)
  row  <- coeftable(m)[INSTR, ]; Fstat <- unname(row["t value"])^2
  fs_rows[[length(fs_rows) + 1]] <- data.table(
    office = office, coef = unname(row["Estimate"]), se = unname(row["Std. Error"]),
    F = Fstat, tF_cv = get_tF_cv(Fstat),
    N = m$nobs, n_clusters = length(unique(samp[[CL]])))
}
first_stage <- rbindlist(fs_rows)
fwrite(first_stage, file.path(REG_DIR, "candidate_first_stage.csv"))

# =============================================================================
# LaTeX TABLES -- every table via fixest::etable() (the first-stage rule)
# =============================================================================
# Identical machinery to 03_voter_behavior_iv.R: stars from signif.code, coef
# stacked above SE, and decimalize() rewrites numeric columns to dcolumn
# D-columns so every decimal value aligns on the point. Requires \usepackage
# {dcolumn} in the slide preamble.
decimalize <- function(tab, nC) {
  dspec <- paste(rep("D{.}{.}{-1}", nC), collapse = " ")
  wrapc <- function(x) sprintf("\\multicolumn{1}{c}{%s}", x)
  vapply(tab, function(ln) {
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
}

gen_comment <- "% Auto-generated by code/03_estimation/04_candidate_outcomes_iv.R via fixest::etable() -- do not edit."

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
    extralines = list("Mean (2020)"               = sprintf("%.3f", m20),
                      "Mean $\\Delta$ 2020--24"    = sprintf("%.3f", mdl),
                      "First-stage $F$"            = sprintf("%.1f", Fv),
                      "$tF_{\\mathrm{cv}}$ (5\\%)" = sprintf("%.2f", tFv)),
    signif.code = c("***" = 0.01, "**" = 0.05, "*" = 0.10),
    style.tex = style.tex("base"))
  a <- grep("\\\\begin\\{tabular\\}", et)[1]
  b <- grep("\\\\end\\{tabular\\}",   et)[1]
  writeLines(c(gen_comment, decimalize(et[a:b], length(models))), file)
}

# T1 representation -- vote share (Mayor 3 | Council 3)
write_iv_etable(rep_models, office_header(3, 3, rep(labs2(REP_VOTE), 2)),
                file.path(TEX_DIR, "candidate_rep_voteshare.tex"))
# T2 renewal -- vote share (Mayor 2 | Council 2)
write_iv_etable(renewal_models, office_header(2, 2, rep(labs2(RENEWAL), 2)),
                file.path(TEX_DIR, "candidate_renewal.tex"))
# T3 competition / fragmentation -- vote share (Mayor 2 | Council 4)
write_iv_etable(competition_models,
                office_header(2, 4, c(labs2(COMP_MAYOR), labs2(COMP_COUNCIL))),
                file.path(TEX_DIR, "candidate_competition.tex"))
# T4 contest closeness -- executive only, continuous margins
write_iv_etable(contest_models, labs2(CONTEST),
                file.path(TEX_DIR, "candidate_contest.tex"))

# =============================================================================
# CONSOLE SUMMARY
# =============================================================================
cat("\n==== FIRST STAGE per office (endogenous ~ Bartik IV | state FE), state-clustered ====\n")
print(first_stage[, .(office, coef = round(coef,3), se = round(se,3),
                      F = round(F,1), tF_cv = round(tF_cv,2), N, n_clusters)])

for (th in unique(res$theme)) {
  cat(sprintf("\n==== %s ====\n", th))
  print(res[theme == th, .(office, outcome, coef = round(coef,4), se = round(se,4),
                           p = round(p,4), first_F = round(first_F,1),
                           tF_cv = round(tF_cv,2), reject_tF, N)])
}

cat("\nWrote:\n  ", file.path(REG_DIR, "candidate_outcomes_iv.csv"),
    "\n  ", file.path(REG_DIR, "candidate_first_stage.csv"),
    "\n  ", file.path(TEX_DIR, "candidate_{rep_voteshare,renewal,competition,contest}.tex"), "\n")
