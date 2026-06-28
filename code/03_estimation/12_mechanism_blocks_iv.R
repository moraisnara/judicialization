# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: reads subst13 components off municipality_family_components.csv and
# block membership from the deleted 24_mechanism_grouping.py -> mechanism_grouping.csv.
# ===========================================================================
# 12_mechanism_blocks_iv.R  (Phase 2 — gate PASSED)
# -----------------------------------------------------------------------------
# Over-identified MULTI-TREATMENT 2SLS: separate the pooled judicialization null
# into its mechanism BLOCKS, estimated jointly so each block's effect is net of the
# others. Built because the escalation gate of the decomposition plan passed:
# 11_family_iv_channels.R showed >=2 opposite-signed channels EACH with an own
# first stage clearing tF (e.g. executive new-candidate vote share:
# electoral_polls +0.077*** F=123 and content_disinfo +0.046** F=480 rising vs
# abuse_political -0.060*** F=69 falling). The single pooled instrument forces one
# coefficient onto these opposing, well-identified channels; here we let them load
# on separate treatments.
#
# Block membership is taken VERBATIM from the ex-ante mechanism grouping
# (24_mechanism_grouping.py -> mechanism_grouping.csv) -- fixed before any block
# second stage was consulted. Two schemes:
#   SCHEME B3  three theory blocks: information_env / eligibility_conduct /
#              propaganda_mechanics  (-> voter signal-vs-noise / candidate
#              resource-drain / routine advertising).
#   SCHEME B2  sign blocks: rising vs falling leave-out shift -- the rawest test of
#              "opposite-signed shocks cancel in the pooled sum."
#
# For each scheme, each block gets ONE aggregated endogenous and ONE aggregated
# instrument, both rebuilt from municipality_family_components.csv (subst13):
#   endog_block  = log1p(sum_k in block L2024) - log1p(sum_k in block L2020)
#   iv_block     = z-score( sum_k in block  s_{m,k} * g_{k,-state} )   [standardized
#                  like the headline bartik_iv, so coefficients are per-SD exposure]
# The block models are JUST-IDENTIFIED (one IV per endogenous). An additional
# OVER-IDENTIFIED arm instruments the 3 block treatments with all 13 family IVs, so
# a Hansen J over-id test is available.
#
# Inference: state-clustered SE (27 UFs); per-endogenous first-stage / Sanderson-
# Windmeijer F via fitstat; Hansen J on the over-id arm. With only 27 clusters the
# cluster-robust SEs and the asymptotic weak-IV diagnostics should be read as
# provisional -- a wild-cluster-bootstrap / Anderson-Rubin pass is the remaining
# inference step (NOT implemented here; flagged, not faked).
#
# Outputs:
#   regressions/mechanism_blocks_iv.csv          (long: scheme x office x outcome x block)
#   regressions/mechanism_blocks_firststage.csv  (per-block first stage + Hansen J)
#   tex/mechanism_blocks_{b3,b2}_executive.tex   (etable, per headline outcome)
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
CLEAN   <- file.path(ROOT, "data", "clean")
REG_DIR <- file.path(ROOT, "output", "tables", "regressions")
TEX_DIR <- file.path(ROOT, "output", "tables", "tex")
DESC    <- file.path(ROOT, "output", "tables", "descriptives")

CL   <- spec_cluster_col()
BASE <- spec_baseline_controls()
FE   <- "state"
avail <- function(controls, data) controls[controls %in% names(data)]

tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

# =============================================================================
# Build block-aggregated endogenous + instrument columns from subst13 components.
# =============================================================================
comp <- fread(file.path(CLEAN, "municipality_family_components.csv"),
              colClasses = list(character = "id_municipio_tse"))
comp <- comp[rung == "subst13"]
comp[, mid := sprintf("%05d", as.integer(id_municipio_tse))]
grp  <- fread(file.path(DESC, "mechanism_grouping.csv"))
comp <- merge(comp, grp[, .(family, block, shift_sign)], by = "family", all.x = TRUE)
stopifnot(!any(is.na(comp$block)))

# aggregate family lawsuits + components to a partition column (block or sign)
agg_block <- function(part_col) {
  a <- comp[, .(L2020 = sum(L2020), L2024 = sum(L2024),
                bartik = sum(bartik_component)), by = c("mid", part_col)]
  a[, endog := log1p(L2024) - log1p(L2020)]
  iv <- dcast(a, mid ~ get(part_col), value.var = "bartik")
  en <- dcast(a, mid ~ get(part_col), value.var = "endog")
  parts <- setdiff(names(iv), "mid")
  setnames(iv, parts, paste0("iv_",    parts))
  setnames(en, parts, paste0("endog_", parts))
  # standardize each instrument (z-score) to the headline bartik_iv convention
  for (p in parts) {
    col <- paste0("iv_", p); v <- iv[[col]]
    iv[[col]] <- (v - mean(v, na.rm = TRUE)) / sd(v, na.rm = TRUE)
  }
  list(cols = merge(iv, en, by = "mid"), parts = parts)
}
B3 <- agg_block("block")       # information_env / eligibility_conduct / propaganda_mechanics
B2 <- agg_block("shift_sign")  # rising / falling

# family IV columns (already on the designs) for the over-identified arm
FAM_IV <- paste0("bartik_iv_", grp$family)

read_design <- function(path) {
  d <- as.data.frame(fread(path, colClasses = list(
    character = c("state", "municipality_id_tse", "cluster_id"))))
  if ("code_meso" %in% names(d)) d$code_meso <- as.character(d$code_meso)
  d$municipality_id_tse <- sprintf("%05d", as.integer(d$municipality_id_tse))
  d
}
designs <- list(
  executive   = read_design(file.path(EST_DIR, "executive_margin_design.csv")),
  legislative = read_design(file.path(EST_DIR, "legislative_design.csv")))

# voter frame: executive design + spoilage + abstention (as 03_voter_behavior_iv.R)
admin <- fread(file.path(CLEAN, "electoral_admin_outcomes.csv"))
spoil <- fread(file.path(CLEAN, "office_ballot_spoilage.csv"),
               colClasses = list(character = "municipality_id_tse"))
spoil[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
ab <- dcast(admin, municipality_id_tse ~ election_year, value.var = "abstention_rate")
ab[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
setnames(ab, c("2020", "2024"), c("ab20", "ab24"))
ab[, delta_abstention_rate_2024_2020 := ab24 - ab20]
vdt <- merge(as.data.table(designs$executive), spoil, by = "municipality_id_tse", all.x = TRUE)
vdt <- merge(vdt, ab[, .(municipality_id_tse, delta_abstention_rate_2024_2020)],
             by = "municipality_id_tse", all.x = TRUE)
designs$voter <- as.data.frame(vdt)

# merge block columns onto every design (keyed by municipality)
for (o in names(designs)) {
  d <- as.data.table(designs[[o]])
  d <- merge(d, B3$cols, by.x = "municipality_id_tse", by.y = "mid", all.x = TRUE)
  d <- merge(d, B2$cols, by.x = "municipality_id_tse", by.y = "mid", all.x = TRUE)
  designs[[o]] <- as.data.frame(d)
}

# =============================================================================
# multi-treatment IV fit
#   endog cols: endog_<part>...   instr cols: instr (just-id) or FAM_IV (over-id)
# =============================================================================
fit_blocks <- function(office, dep, parts, just_id = TRUE) {
  data  <- designs[[office]]
  endog <- paste0("endog_", parts)
  instr <- if (just_id) paste0("iv_", parts) else FAM_IV
  if (!all(c(dep, endog, instr) %in% names(data))) return(NULL)
  lagdv <- spec_lagged_dv(dep)
  ctr   <- avail(c(BASE, if (!is.na(lagdv)) lagdv), data)
  req   <- unique(c(dep, endog, instr, CL, FE, ctr)); req <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  rhs   <- paste(ctr, collapse = " + ")
  fml   <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, FE,
                              paste(endog, collapse = " + "),
                              paste(instr, collapse = " + ")))
  m <- tryCatch(feols(fml, data = samp, cluster = as.formula(paste0("~", CL)),
                      warn = FALSE, notes = FALSE), error = function(e) NULL)
  if (is.null(m)) return(NULL)
  attr(m, "parts") <- parts; attr(m, "endog") <- endog
  attr(m, "office") <- office; attr(m, "dep") <- dep; attr(m, "just_id") <- just_id
  m
}

# per-endogenous first-stage F (Sanderson-Windmeijer when multi-endogenous; fixest
# returns one F per first-stage equation in $stat). Returns named vector.
sw_F <- function(m) {
  fs <- tryCatch(fitstat(m, "ivwald", simplify = FALSE), error = function(e) NULL)
  if (is.null(fs)) return(setNames(rep(NA_real_, length(attr(m, "endog"))), attr(m, "endog")))
  # fitstat ivwald returns a list per endogenous variable
  vals <- vapply(fs, function(x) tryCatch(x$stat, error = function(e) NA_real_), 0)
  vals
}
hansen_J <- function(m) tryCatch({
  s  <- fitstat(m, "sargan")
  sg <- if (!is.null(s$sargan)) s$sargan else s
  st <- tryCatch(sg$stat, error = function(e) NA_real_); if (is.null(st)) st <- NA_real_
  pv <- tryCatch(sg$p,    error = function(e) NA_real_); if (is.null(pv)) pv <- NA_real_
  list(stat = as.numeric(st), p = as.numeric(pv))
}, error = function(e) list(stat = NA_real_, p = NA_real_))

extract_blocks <- function(m) {
  endog <- attr(m, "endog"); ct <- coeftable(m)
  Fs <- sw_F(m)
  rows <- lapply(endog, function(e) {
    rn <- paste0("fit_", e)
    if (!rn %in% rownames(ct)) return(NULL)
    r <- ct[rn, ]
    f <- if (!is.null(names(Fs))) {
      hit <- Fs[grepl(e, names(Fs), fixed = TRUE)]; if (length(hit)) hit[1] else NA_real_
    } else NA_real_
    cv <- get_tF_cv(f); b <- unname(r["Estimate"]); se <- unname(r["Std. Error"])
    t  <- unname(r["t value"])
    data.table(block = sub("^endog_", "", e), coef = b, se = se, t = t,
               p = unname(r["Pr(>|t|)"]), first_F = unname(f), tF_cv = cv,
               reject_tF = abs(t) > cv, ci_lo = b - cv * se, ci_hi = b + cv * se)
  })
  rbindlist(Filter(Negate(is.null), rows))
}

# =============================================================================
# OUTCOME GRID (subset of the headline outcomes — the ones the decomposition flags)
# =============================================================================
J <- function(off, dep, lab, grp) list(off = off, dep = dep, lab = lab, grp = grp)
JOBS <- list(
  J("executive","delta_female_vote_share_2024_2020","Female","T1"),
  J("executive","delta_nonwhite_vote_share_2024_2020","Non-white","T1"),
  J("executive","delta_new_candidate_vote_share_2024_2020","New cand.","T2"),
  J("executive","delta_incumbent_candidate_vote_share_2024_2020","Incumbent","T2"),
  J("executive","delta_effective_n_candidates_vote_2024_2020","Eff. N","T3"),
  J("executive","delta_vote_hhi_candidate_2024_2020","HHI","T3"),
  J("executive","delta_winner_vote_share_2024_2020","Winner VS","T4"),
  J("executive","delta_margin_top1_top2_2024_2020","Margin","T4"),
  J("legislative","delta_female_vote_share_2024_2020","Female","T1"),
  J("legislative","delta_new_candidate_vote_share_2024_2020","New cand.","T2"),
  J("legislative","delta_effective_n_parties_vote_2024_2020","Eff. N party","T3"),
  J("voter","delta_turnout_rate_2024_2020","Turnout","V"),
  J("voter","delta_prefeito_null_share_cast_2024_2020","Mayor null","V"),
  J("voter","delta_vereador_null_share_cast_2024_2020","Council null","V"))

SCHEMES <- list(
  b3 = list(parts = B3$parts, label = "3 theory blocks"),
  b2 = list(parts = B2$parts, label = "rising vs falling"))

res <- list(); fs_rows <- list()
for (sk in names(SCHEMES)) {
  parts <- SCHEMES[[sk]]$parts
  for (job in JOBS) {
    # just-identified block model
    m <- fit_blocks(job$off, job$dep, parts, just_id = TRUE)
    if (!is.null(m)) {
      e <- extract_blocks(m)
      if (nrow(e)) res[[length(res) + 1]] <- cbind(
        data.table(scheme = sk, arm = "just_id", office = job$off,
                   outcome = job$lab, group = job$grp, N = m$nobs), e)
    }
    # over-identified arm only for the 3-block scheme (13 family IVs -> 3 endog)
    if (sk == "b3") {
      mo <- fit_blocks(job$off, job$dep, parts, just_id = FALSE)
      if (!is.null(mo)) {
        e <- extract_blocks(mo); hj <- hansen_J(mo)
        if (nrow(e)) res[[length(res) + 1]] <- cbind(
          data.table(scheme = sk, arm = "overid", office = job$off,
                     outcome = job$lab, group = job$grp, N = mo$nobs), e)
        fs_rows[[length(fs_rows) + 1]] <- data.table(
          scheme = sk, office = job$off, outcome = job$lab,
          hansen_J = hj$stat, hansen_p = hj$p, N = mo$nobs)
      }
    }
  }
}
res <- rbindlist(res, fill = TRUE)
fwrite(res, file.path(REG_DIR, "mechanism_blocks_iv.csv"))
fs <- rbindlist(fs_rows, fill = TRUE)
fwrite(fs, file.path(REG_DIR, "mechanism_blocks_firststage.csv"))

# =============================================================================
# CONSOLE
# =============================================================================
cat("\n==== SCHEME B3 (3 theory blocks), just-identified, by outcome ====\n")
print(res[scheme == "b3" & arm == "just_id",
      .(office, outcome, block, coef = round(coef,4), p = round(p,4),
        first_F = round(first_F,1), reject_tF)], nrow = 200)
cat("\n==== SCHEME B2 (rising vs falling), just-identified ====\n")
print(res[scheme == "b2" & arm == "just_id",
      .(office, outcome, block, coef = round(coef,4), p = round(p,4),
        first_F = round(first_F,1), reject_tF)], nrow = 200)
cat("\n==== Over-identified arm (13 family IVs -> 3 blocks): Hansen J ====\n")
print(fs[, .(office, outcome, hansen_J = round(hansen_J,2), hansen_p = round(hansen_p,3))], nrow = 200)

cat("\nWrote:\n  ", file.path(REG_DIR, "mechanism_blocks_iv.csv"),
    "\n  ", file.path(REG_DIR, "mechanism_blocks_firststage.csv"), "\n")
cat("NOTE: 27 state clusters -> SEs + weak-IV F asymptotic; AR / wild-cluster-bootstrap pass still pending.\n")
