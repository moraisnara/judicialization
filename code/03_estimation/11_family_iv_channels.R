# ===========================================================================
# WARNING: PENDING ACT REPOINT — NOT in the live pipeline (see code/run_all.py).
# This script still targets the RETIRED substance-family design (old per-family
# bartik_iv_<family> columns / theme9 / subst13 / fine7 rungs). It will NOT run
# correctly against the current act-based design (instrument bartik_iv_act,
# treatment delta_log1p_act_lawsuits, cluster = state). Repoint before use.
# Reason stale: expects per-family bartik_iv_<family>/delta_log1p_<family> cols at
# the subst13 floor; comments reference the deleted 01c_family_ivs.py builder.
# ===========================================================================
# 11_family_iv_channels.R
# -----------------------------------------------------------------------------
# PER-CHANNEL just-identified IV decomposition of the pooled judicialization null.
#
# The headline 2SLS instruments a SINGLE municipality scalar
#   B_m = sum_k s_{m,k} * g_{k,-state}        (bartik_iv_2020_2024)
# that SUMS the Bartik components over all kept lawsuit families. Its second stage
# is a precise null. The pooled estimate is a Rotemberg-weighted average of the
# per-family LATEs; because the national leave-out shocks split by SIGN (some
# families rising 2020->2024, some falling), that average can net toward zero even
# when individual channels move outcomes. This script estimates each channel's OWN
# LATE so the cancellation is visible rather than hidden inside the sum.
#
# DESIGN CHOICE -- decompose at the subst13 FLOOR (13 families), not the theme9
# headline (9). The family content audit (23_family_content_audit.py) showed the
# theme9 families PRE-MERGE sub-families whose shocks oppose each other:
#   candidacy   = candidacy_challenge (-34%) + candidatura_ficticia (+69%)
#   abuse_power = abuse_economic (+2%)        + abuse_political (+33%)
#   content_disinfo bundles false_content (rising) + fraud_polls (rising) + reply (-)
# Decomposing at theme9 would average those opposite signs away inside a "channel"
# and defeat the purpose. The subst13 floor keeps them separate. (01c_family_ivs.py
# patched bartik_iv_<family> + delta_log1p_<family>_2024_2020 for BOTH rungs onto
# both designs; here we read the subst13 set off municipality_family_components.csv
# so the family list is never hard-coded.)
#
# One JUST-IDENTIFIED 2SLS per (family x outcome x office):
#   dep ~ baseline + lagged_dv | state | delta_log1p_<family> ~ bartik_iv_<family>
# state-clustered SE (27 UFs), Lee et al. (2022) tF weak-IV critical values (K=1).
# Every row carries first_F, tF_cv, reject_tF, and the tF-WIDENED CI
# (coef +- tF_cv*se) -- so channels whose own first stage is too weak to interpret
# (the rising channels: disinfo, polls, abuse, finance, ficticia) are FLAGGED and
# reported, never silently dropped. Machinery (fit/extract/tF) is reused verbatim
# from 04_candidate_outcomes_iv.R.
#
# Outputs:
#   regressions/family_iv_channels.csv   (long: office x family x outcome, full grid)
#   tex/family_iv_channels_executive.tex   tex/family_iv_channels_legislative.tex
#     (etable: per-family channel LATEs for the headline new-candidate vote share)
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
dir.create(REG_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(TEX_DIR, recursive = TRUE, showWarnings = FALSE)

read_design <- function(path) as.data.frame(fread(
  path, colClasses = list(character = c("state", "municipality_id_tse", "cluster_id"))))
designs <- list(
  executive   = read_design(file.path(EST_DIR, "executive_margin_design.csv")),
  legislative = read_design(file.path(EST_DIR, "legislative_design.csv")))
for (o in names(designs))
  if ("code_meso" %in% names(designs[[o]]))
    designs[[o]]$code_meso <- as.character(designs[[o]]$code_meso)

# ---- voter outcomes: replicate the spoilage + abstention merge from -----------
# 03_voter_behavior_iv.R so the per-channel decomposition can reach the voter side
# (turnout + office spoilage). Voter behaviour is municipality-level; it rides on
# the executive design frame, exactly as the headline voter script does.
admin <- fread(file.path(CLEAN, "electoral_admin_outcomes.csv"))
spoil <- fread(file.path(CLEAN, "office_ballot_spoilage.csv"),
               colClasses = list(character = "municipality_id_tse"))
spoil[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
ab <- dcast(admin, municipality_id_tse ~ election_year, value.var = "abstention_rate")
ab[, municipality_id_tse := sprintf("%05d", as.integer(municipality_id_tse))]
setnames(ab, c("2020", "2024"), c("abstention_rate_2020_adm", "abstention_rate_2024_adm"))
ab[, delta_abstention_rate_2024_2020 := abstention_rate_2024_adm - abstention_rate_2020_adm]
voter_dt <- merge(designs$executive, spoil, by = "municipality_id_tse", all.x = TRUE)
voter_dt <- merge(voter_dt, ab[, .(municipality_id_tse, delta_abstention_rate_2024_2020)],
                  by = "municipality_id_tse", all.x = TRUE)
designs$voter <- voter_dt   # voter outcomes fit on this augmented executive frame

# ---- subst13 family set (read from components, never hard-coded) -------------
comp <- fread(file.path(CLEAN, "municipality_family_components.csv"))
FAMILIES <- sort(unique(comp[rung == "subst13" & !is.na(family), family]))
slug_fam  <- function(s) gsub(" ", "_", tolower(s))
fam_iv    <- function(f) paste0("bartik_iv_", slug_fam(f))
fam_endog <- function(f) paste0("delta_log1p_", slug_fam(f), "_2024_2020")

# short labels for the tex header (families-as-columns)
FAM_LAB <- c(abuse_economic = "Ab.\\ econ", abuse_political = "Ab.\\ pol",
             campaign_finance = "Finance", candidacy_challenge = "Cand.\\ chal",
             candidatura_ficticia = "Cand.\\ fict", content_disinfo = "Disinfo",
             crime_other = "Crime oth", crime_speech = "Crime spch",
             crime_vote = "Crime vote", electoral_polls = "Polls",
             prop_placement = "Prop.\\ place", prop_regulatory = "Prop.\\ reg",
             prop_timing = "Prop.\\ time")

CL   <- spec_cluster_col()
BASE <- spec_baseline_controls()
FE   <- "state"
avail <- function(controls, data) controls[controls %in% names(data)]

# tF weak-instrument critical values (Lee, McCrary, Moreira & Porter 2022,
# Table 1, 5% two-sided, K=1) -- verbatim from 04_candidate_outcomes_iv.R.
tF_lookup <- data.frame(
  F_val = c(2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23.1,25,30,40),
  tF_cv = c(13.99,7.13,5.24,4.31,3.78,3.44,3.21,3.02,2.86,2.73,2.62,2.53,2.46,
            2.39,2.33,2.28,2.24,2.20,2.17,2.14,2.11,2.00,1.96,1.96,1.96))
get_tF_cv <- function(f) if (is.na(f) || f >= 23.1) 1.96 else
  if (f <= 2) 13.99 else approx(tF_lookup$F_val, tF_lookup$tF_cv, xout = f, rule = 2)$y

# ---- one just-identified channel IV: dep ~ ctr | state | endog ~ instr -------
# Returns the fitted feols model with the channel endogenous name stored so the
# SAME model object feeds both the CSV (extract) and etable (tables can't drift).
fit_channel <- function(office, dep, fam) {
  data  <- designs[[office]]
  endog <- fam_endog(fam); instr <- fam_iv(fam)
  if (!all(c(dep, endog, instr) %in% names(data))) return(NULL)
  lagdv <- spec_lagged_dv(dep)
  ctr   <- avail(c(BASE, if (!is.na(lagdv)) lagdv), data)
  req   <- unique(c(dep, endog, instr, CL, FE, ctr)); req <- req[req %in% names(data)]
  samp  <- data[complete.cases(data[, req, drop = FALSE]), ]
  rhs   <- paste(ctr, collapse = " + ")
  fml   <- as.formula(sprintf("%s ~ %s | %s | %s ~ %s", dep, rhs, FE, endog, instr))
  m <- tryCatch(
    feols(fml, data = samp, cluster = as.formula(paste0("~", CL)), warn = FALSE, notes = FALSE),
    error = function(e) NULL)
  if (is.null(m)) return(NULL)
  attr(m, "endog") <- endog; attr(m, "fam") <- fam
  attr(m, "office") <- office; attr(m, "dep") <- dep
  attr(m, "mean_delta") <- mean(samp[[dep]], na.rm = TRUE)
  m
}
extract_channel <- function(m) {
  endog <- attr(m, "endog"); iv <- paste0("fit_", endog)
  ct <- coeftable(m)
  if (!iv %in% rownames(ct)) return(NULL)
  row <- ct[iv, ]
  Fst <- tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_)
  cv  <- get_tF_cv(Fst); t <- unname(row["t value"]); se <- unname(row["Std. Error"])
  b   <- unname(row["Estimate"])
  list(coef = b, se = se, t = t, p = unname(row["Pr(>|t|)"]),
       first_F = Fst, tF_cv = cv, reject_tF = abs(t) > cv,
       ci_lo = b - cv * se, ci_hi = b + cv * se,
       mean_delta = attr(m, "mean_delta"), N = m$nobs)
}

# =============================================================================
# OUTCOME GRID  c(office_label, design_key, dep, label, group)
# design_key indexes designs[]; office_label is the reporting bucket.
# =============================================================================
J <- function(off, key, dep, lab, grp) list(off = off, key = key, dep = dep, lab = lab, grp = grp)
JOBS <- c(
  # --- executive candidate outcomes ---
  list(J("executive","executive","delta_female_vote_share_2024_2020","Female","T1 Representation"),
       J("executive","executive","delta_nonwhite_vote_share_2024_2020","Non-white","T1 Representation"),
       J("executive","executive","delta_higher_education_vote_share_2024_2020","Higher-ed","T1 Representation"),
       J("executive","executive","delta_new_candidate_vote_share_2024_2020","New cand.","T2 Renewal"),
       J("executive","executive","delta_incumbent_candidate_vote_share_2024_2020","Incumbent","T2 Renewal"),
       J("executive","executive","delta_effective_n_candidates_vote_2024_2020","Eff. N","T3 Competition"),
       J("executive","executive","delta_vote_hhi_candidate_2024_2020","HHI","T3 Competition"),
       J("executive","executive","delta_winner_vote_share_2024_2020","Winner VS","T4 Contest"),
       J("executive","executive","delta_runnerup_vote_share_2024_2020","Runner-up VS","T4 Contest"),
       J("executive","executive","delta_margin_top1_top2_2024_2020","Margin","T4 Contest"),
  # --- legislative candidate outcomes ---
       J("legislative","legislative","delta_female_vote_share_2024_2020","Female","T1 Representation"),
       J("legislative","legislative","delta_nonwhite_vote_share_2024_2020","Non-white","T1 Representation"),
       J("legislative","legislative","delta_higher_education_vote_share_2024_2020","Higher-ed","T1 Representation"),
       J("legislative","legislative","delta_new_candidate_vote_share_2024_2020","New cand.","T2 Renewal"),
       J("legislative","legislative","delta_incumbent_candidate_vote_share_2024_2020","Incumbent","T2 Renewal"),
       J("legislative","legislative","delta_effective_n_candidates_vote_2024_2020","Eff. N cand","T3 Competition"),
       J("legislative","legislative","delta_vote_hhi_candidate_2024_2020","HHI cand","T3 Competition"),
       J("legislative","legislative","delta_effective_n_parties_vote_2024_2020","Eff. N party","T3 Competition"),
       J("legislative","legislative","delta_vote_hhi_party_2024_2020","HHI party","T3 Competition"),
  # --- voter behaviour (municipality-level, on the executive frame) ---
       J("voter","voter","delta_turnout_rate_2024_2020","Turnout","V Participation"),
       J("voter","voter","delta_prefeito_null_share_cast_2024_2020","Mayor null","V Spoilage"),
       J("voter","voter","delta_prefeito_blank_share_cast_2024_2020","Mayor blank","V Spoilage"),
       J("voter","voter","delta_vereador_null_share_cast_2024_2020","Council null","V Spoilage"),
       J("voter","voter","delta_vereador_blank_share_cast_2024_2020","Council blank","V Spoilage")))

# =============================================================================
# FULL GRID -> long CSV (office x family x outcome)
# =============================================================================
rows <- list()
for (job in JOBS) for (fam in FAMILIES) {
  m <- fit_channel(job$key, job$dep, fam)
  if (is.null(m)) next
  r <- extract_channel(m)
  if (is.null(r)) next
  rows[[length(rows) + 1]] <- data.table(
    office = job$off, group = job$grp, outcome = job$lab, dep = job$dep,
    family = fam, coef = r$coef, se = r$se, t = r$t, p = r$p,
    first_F = r$first_F, tF_cv = r$tF_cv, reject_tF = r$reject_tF,
    ci_lo = r$ci_lo, ci_hi = r$ci_hi, mean_delta = r$mean_delta, N = r$N)
}
res <- rbindlist(rows)
fwrite(res, file.path(REG_DIR, "family_iv_channels.csv"))

# =============================================================================
# LaTeX -- per office, the headline NEW-CANDIDATE vote share decomposed across the
# 13 channels (one etable, families as columns). The full grid lives in the CSV
# and feeds the channel-vector figure (25_channel_vector_figure.R); this table is
# the readable "why does competition net to zero" snapshot. etable-generated
# (stars from signif.code), decimal-aligned via decimalize() -- the table rule.
# =============================================================================
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
      if (c0 == "") "" else if (grepl("[0-9]\\.[0-9]", c0))
        paste0(" ", gsub("$", "", c0, fixed = TRUE), " ") else wrapc(c0)
    }, "", USE.NAMES = FALSE)
    paste0(paste(c(cells[1], dat), collapse = "&"), term)
  }, "", USE.NAMES = FALSE)
}
gen_comment <- "% Auto-generated by code/03_estimation/11_family_iv_channels.R via fixest::etable() -- do not edit."

write_channel_etable <- function(office_label, design_key, dep, file) {
  models <- lapply(FAMILIES, function(f) fit_channel(design_key, dep, f))
  keep   <- !vapply(models, is.null, logical(1))
  models <- models[keep]; fams <- FAMILIES[keep]
  # all channels share ONE displayed coefficient row: map every fit_<endog> name to
  # the same dict label so etable collapses them into a single "Channel LATE" line.
  dict <- setNames(rep("$\\hat\\beta_{\\text{channel}}$", length(models)),
                   vapply(models, function(m) paste0("fit_", attr(m, "endog")), ""))
  Fv  <- vapply(models, function(m)
           tryCatch(fitstat(m, "ivwald1")[[1]]$stat, error = function(e) NA_real_), 0)
  tFv <- vapply(Fv, get_tF_cv, 0)
  et <- etable(
    models, tex = TRUE, keep = "%fit_", depvar = FALSE,
    headers = unname(FAM_LAB[fams]), dict = dict,
    fitstat = ~ n, digits = "r3", digits.stats = "r3",
    extralines = list("First-stage $F$"            = sprintf("%.1f", Fv),
                      "$tF_{\\mathrm{cv}}$ (5\\%)" = sprintf("%.2f", tFv)),
    signif.code = c("***" = 0.01, "**" = 0.05, "*" = 0.10),
    style.tex = style.tex("base"))
  a <- grep("\\\\begin\\{tabular\\}", et)[1]
  b <- grep("\\\\end\\{tabular\\}",   et)[1]
  writeLines(c(gen_comment, decimalize(et[a:b], length(models))), file)
  invisible(length(models))
}

write_channel_etable("executive", "executive",
  "delta_new_candidate_vote_share_2024_2020",
  file.path(TEX_DIR, "family_iv_channels_executive.tex"))
write_channel_etable("legislative", "legislative",
  "delta_new_candidate_vote_share_2024_2020",
  file.path(TEX_DIR, "family_iv_channels_legislative.tex"))

# =============================================================================
# CONSOLE -- per outcome, the channel LATEs sorted, flagging weak first stages.
# =============================================================================
cat(sprintf("\nSubst13 floor: %d families x %d outcomes x offices -> %d channel IVs\n",
            length(FAMILIES), length(JOBS), nrow(res)))
cat("Families:", paste(FAMILIES, collapse = ", "), "\n")

cat("\n==== Channels with an interpretable own first stage (reject_tF == TRUE) ====\n")
strong <- res[reject_tF == TRUE]
if (nrow(strong)) {
  print(strong[order(office, outcome, -abs(coef)),
        .(office, outcome, family, coef = round(coef,4), p = round(p,4),
          first_F = round(first_F,1), N)], nrow = 200)
} else {
  cat("  (none -- every channel's own first stage is too weak to interpret)\n")
}

cat("\n==== First-stage strength by family (max across outcomes) ====\n")
print(res[, .(max_F = round(max(first_F, na.rm = TRUE),1),
              ever_reject = any(reject_tF)), by = family][order(-max_F)])

cat("\nWrote:\n  ", file.path(REG_DIR, "family_iv_channels.csv"),
    "\n  ", file.path(TEX_DIR, "family_iv_channels_{executive,legislative}.tex"), "\n")
