# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: hardcodes the 9 theme9 families and per-family bartik_iv_<family> cols.
# ===========================================================================
# 21_leave_one_family_out.R
# -----------------------------------------------------------------------------
# Leave-one-family-out robustness for the shift-share instrument.
#
# The headline Bartik IV (bartik_iv_2020_2024 = bartik_iv_theme9) is the sum of
# nine family-level components (bartik_iv_{prop_placement, prop_regulatory,
# prop_timing, disinformation, electoral_polls, abuse_power, campaign_finance,
# candidacy, criminal}). The Rotemberg decomposition shows the estimate is
# concentrated in a few families. The natural stress test is therefore:
#
#   Z_{-f} = Z_full - bartik_iv_f      (drop family f from the instrument)
#
# and re-estimate (a) the first-stage relevance and (b) the one significant
# second-stage result (null / non-valid votes, votes-cast denominator). If the
# first stage collapses or the result flips when a single family is removed, the
# instrument is effectively that family and the interpretation must narrow.
#
# Outputs:
#   output/tables/regressions/leave_one_out_first_stage.csv
#   output/tables/regressions/leave_one_out_voter_2sls.csv
#   output/tables/tex/leave_one_out_first_stage.tex
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

design <- as.data.frame(fread(
  file.path(EST_DIR, "executive_margin_design.csv"),
  colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))
))
admin <- fread(file.path(ROOT, "data", "clean", "electoral_admin_outcomes.csv"))

# headline voter outcome (votes-cast denominator), reconstructed exactly as in
# 03_voter_behavior_iv.R so the leave-out 2SLS is comparable.
admin[, null_share_cast    := null_votes  / total_votes]
admin[, invalid_share_cast := (blank_votes + null_votes) / total_votes]
w <- dcast(admin, municipality_id_tse ~ election_year,
           value.var = c("null_share_cast", "invalid_share_cast"))
# pad TSE integer codes to the canonical zero-filled 5-char key (see 03_voter_behavior_iv.R)
w[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
w[, delta_null_share_cast_2024_2020    := null_share_cast_2024    - null_share_cast_2020]
w[, delta_invalid_share_cast_2024_2020 := invalid_share_cast_2024 - invalid_share_cast_2020]
dt <- merge(design, w, by = "municipality_id_tse", all.x = TRUE)

INSTR <- spec_instrument()          # bartik_iv_2020_2024
ENDOG <- spec_endogenous()
CL    <- spec_cluster_col()
BASE  <- spec_baseline_controls()
FE    <- "state"
avail <- function(controls, data) controls[controls %in% names(data)]

FAMILIES <- c("prop_placement", "prop_regulatory", "prop_timing",
              "disinformation", "electoral_polls", "abuse_power",
              "campaign_finance", "candidacy", "criminal")
fam_cols <- paste0("bartik_iv_", FAMILIES)
stopifnot(all(fam_cols %in% names(dt)), INSTR %in% names(dt))

# tF critical values (Lee et al. 2022, K=1, 5%).
tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

ctr  <- avail(BASE, dt)
base_req <- unique(c(ENDOG, INSTR, fam_cols, CL, FE, ctr))
samp <- dt[complete.cases(dt[, base_req, drop = FALSE]), ]

# ---- helper: first stage + headline 2SLS for an arbitrary instrument column ----
first_stage <- function(data, zcol) {
  rhs <- paste(c(zcol, ctr), collapse = " + ")
  m   <- feols(as.formula(sprintf("%s ~ %s | %s", ENDOG, rhs, FE)),
               data = data, cluster = as.formula(paste0("~", CL)), warn = FALSE, notes = FALSE)
  row <- coeftable(m)[zcol, ]
  Fst <- unname(row["t value"])^2
  list(coef = unname(row["Estimate"]), se = unname(row["Std. Error"]),
       F = Fst, tF_cv = get_tF_cv(Fst), N = m$nobs)
}
iv_one <- function(data, zcol, dep, lagdv) {
  c2  <- avail(c(ctr, lagdv), data)
  req <- unique(c(dep, ENDOG, zcol, CL, FE, c2))
  d2  <- data[complete.cases(data[, req, drop = FALSE]), ]
  rhs <- paste(c2, collapse = " + ")
  m   <- feols(as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, FE, ENDOG, zcol)),
               data = d2, cluster = as.formula(paste0("~", CL)), warn = FALSE, notes = FALSE)
  row <- coeftable(m)[paste0("fit_", ENDOG), ]
  Fst <- tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
  list(coef = unname(row["Estimate"]), se = unname(row["Std. Error"]),
       p = unname(row["Pr(>|t|)"]), F = Fst, tF_cv = get_tF_cv(Fst),
       reject_tF = abs(unname(row["t value"])) > get_tF_cv(Fst), N = m$nobs)
}

# ---- build leave-one-out instruments and run ----
fs_rows <- list(); iv_rows <- list()
VOTER <- list(
  null_share_cast    = c("delta_null_share_cast_2024_2020",    "null_share_cast_2020"),
  invalid_share_cast = c("delta_invalid_share_cast_2024_2020", "invalid_share_cast_2020")
)

add_rows <- function(tag, dropped, zcol) {
  fs <- first_stage(samp, zcol)
  fs_rows[[length(fs_rows) + 1]] <<- data.table(
    instrument = tag, dropped = dropped, fs_coef = fs$coef, fs_se = fs$se,
    F = fs$F, tF_cv = fs$tF_cv, N = fs$N)
  for (k in names(VOTER)) {
    iv <- iv_one(samp, zcol, VOTER[[k]][1], VOTER[[k]][2])
    iv_rows[[length(iv_rows) + 1]] <<- data.table(
      instrument = tag, dropped = dropped, outcome = k,
      coef = iv$coef, se = iv$se, p = iv$p, first_F = iv$F,
      tF_cv = iv$tF_cv, reject_tF = iv$reject_tF, N = iv$N)
  }
}

# full instrument (reference row)
add_rows("full", "(none)", INSTR)

# leave-one-out: Z_{-f} = Z_full - bartik_iv_f, created as a temp column
for (f in FAMILIES) {
  zname <- paste0("Z_minus_", f)
  samp[[zname]] <- samp[[INSTR]] - samp[[paste0("bartik_iv_", f)]]
  add_rows(zname, f, zname)
}

first_stage_dt <- rbindlist(fs_rows)
voter_dt       <- rbindlist(iv_rows)

fwrite(first_stage_dt, file.path(REG_DIR, "leave_one_out_first_stage.csv"))
fwrite(voter_dt,       file.path(REG_DIR, "leave_one_out_voter_2sls.csv"))

# ---- LaTeX: first-stage F when each family is dropped ----
f3 <- function(x) sprintf("%.3f", x); fF <- function(x) sprintf("%.1f", x)
fN <- function(x) formatC(as.integer(x), big.mark = ",", format = "d")
fs <- first_stage_dt
lab <- ifelse(fs$dropped == "(none)", "Full instrument", paste0("$-$ ", fs$dropped))
tex <- c(
  "% Auto-generated by code/04_analysis/21_leave_one_family_out.R -- do not edit.",
  "\\begin{tabular}{lrrrr}",
  "\\hline\\hline",
  " & \\multicolumn{1}{c}{First-stage} & \\multicolumn{1}{c}{} & \\multicolumn{1}{c}{First-stage} & \\multicolumn{1}{c}{} \\\\",
  " & \\multicolumn{1}{c}{coef.} & \\multicolumn{1}{c}{(SE)} & \\multicolumn{1}{c}{$F$} & \\multicolumn{1}{c}{$N$} \\\\",
  "\\hline",
  paste0(lab, " & ", sprintf("$%s$", f3(fs$fs_coef)), " & ",
         sprintf("$(%s)$", f3(fs$fs_se)), " & ", fF(fs$F), " & ", fN(fs$N), " \\\\"),
  "\\hline\\hline",
  "\\end{tabular}"
)
writeLines(tex, file.path(TEX_DIR, "leave_one_out_first_stage.tex"))

# ---- console ----
cat("\n==== LEAVE-ONE-FAMILY-OUT: FIRST STAGE ====\n")
print(first_stage_dt[, .(instrument, dropped, fs_coef = round(fs_coef,3),
                         F = round(F,1), tF_cv = round(tF_cv,2), N)])
cat("\n==== LEAVE-ONE-FAMILY-OUT: HEADLINE VOTER 2SLS (null / non-valid) ====\n")
print(voter_dt[, .(dropped, outcome, coef = round(coef,4), se = round(se,4),
                   p = round(p,4), first_F = round(first_F,1), reject_tF, N)])
cat("\nWrote:\n  ", file.path(REG_DIR, "leave_one_out_first_stage.csv"),
    "\n  ", file.path(REG_DIR, "leave_one_out_voter_2sls.csv"),
    "\n  ", file.path(TEX_DIR, "leave_one_out_first_stage.tex"), "\n")
