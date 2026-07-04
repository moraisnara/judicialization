# ============================================================================
# 13_reclassification_robustness.R
# Is the shift-share SHIFTER contaminated by TSE topic reclassification?
#
# The instrument's shifts are leave-own-state-out national growth rates of each
# ASSUNTO (subject) code. If TSE recoded a case type between 2020 and 2024 -- cases
# filed under subject A in 2020 landing under subject B in 2024 -- then A shows a
# spurious national DECLINE and B a spurious RISE, purely from the dictionary. A
# municipality's 2020 shares then load that artifact. Leave-own-state-out does NOT
# save us: it purges idiosyncratic STATE coding quirks, but a NATIONAL recode (every
# TRE adopts the new convention at once) survives the leave-out untouched.
#
# The exposure is concrete: the committed subject-level instrument is dominated by
# "Propaganda Politica" subjects whose national shocks are strongly NEGATIVE, and
# the propaganda decline is exactly the topic known to be part regime-substitution
# (takedowns replacing lawsuits) and part propaganda<->representacao recoding. So we
# stress-test whether the first stage and the margin reduced form survive making the
# shifter robust to reclassification.
#
# Three diagnostics:
#   [1] shift_audit()        which subject shifts drive Z; how concentrated in
#                            propaganda; sign and size of the propaganda national shock.
#   [2] family_invariance()  rebuild Z at the topic-FAMILY level. Reclassification that
#                            moves cases BETWEEN subjects WITHIN a family cancels exactly
#                            at the family level, so a stable family-Z first stage +
#                            margin RF means within-family recoding is not driving it.
#   [3] drop_propaganda()    rebuild Z EXCLUDING every propaganda subject's shift
#                            (the most recode-suspect topic); does the headline survive?
#
# All alternative instruments are rebuilt from the COMMITTED components file
# (municipality_bartik_components.csv) so they mirror the headline machinery exactly
# (baseline_share_2020 x leave-out log-growth), then merged to the design and run with
# the headline ANCOVA-2016 margin spec (state FE, state cluster, free 2016 lag).
#
# Outputs:
#   output/tables/regressions/reclassification_robustness.csv
#   output/tables/tex/reclassification_robustness.tex          (deck fragment)
#   output/tables/tex/reclassification_robustness_macros.tex   (inline-prose macros)
# ============================================================================

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

ROOT   <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
DESIGN <- file.path(ROOT, "data/estimation/executive_margin_design.csv")
COMPS  <- file.path(ROOT, "data/clean/municipality_bartik_components.csv")
OUT_CSV <- file.path(ROOT, "output/tables/regressions/reclassification_robustness.csv")
OUT_TEX <- file.path(ROOT, "output/tables/tex/reclassification_robustness.tex")
OUT_MAC <- file.path(ROOT, "output/tables/tex/reclassification_robustness_macros.tex")

INSTR  <- "bartik_iv_2020_2024"                 # committed subject-level instrument
CTRL   <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
            "higher_educ_share_2010", "log1p_total_valid_votes_2020", "margin_2016")
MARGIN <- c(lhs = "margin_top1_top2_2024", lag = "margin_top1_top2_2016")

grab <- function(fit, term) {
  ct <- fit$coeftable
  if (!term %in% rownames(ct)) return(c(coef = NA, se = NA, p = NA))
  c(coef = unname(ct[term, "Estimate"]), se = unname(ct[term, "Std. Error"]),
    p = unname(ct[term, "Pr(>|t|)"]))
}
Fstat <- function(fit, term) { g <- grab(fit, term); unname((g["coef"] / g["se"])^2) }
ctrl_rhs <- function() paste(CTRL, collapse = " + ")
is_prop <- function(x) grepl("PROPAGANDA", toupper(x), fixed = TRUE)

# ---- load design + committed components ------------------------------------
load_all <- function() {
  d <- fread(DESIGN, colClasses = list(character = c("state", "municipality_id_tse", "cluster_id")))
  setnames(d, "state", "SG_UF")
  req <- unique(c(INSTR, "cluster_id", "SG_UF", "municipality_id_tse", CTRL, unname(MARGIN)))
  d <- d[complete.cases(d[, ..req])]
  c <- fread(COMPS, colClasses = list(character = c("state", "municipality_id_tse", "main_subject_code")))
  list(design = d, comp = c)
}

# ---- rebuild alternative instruments from the committed components ---------
# Each muni's committed Z = sum_s baseline_share_2020_s * shock_s.
#   family Z : collapse subjects to topic_family FIRST (shares summed; the leave-out
#              national counts summed within (state,family) then re-logged), so any
#              reclassification WITHIN a family cancels.
#   no-prop Z: drop propaganda subjects' contribution (keep original shares).
build_alt_instruments <- function(comp) {
  comp <- copy(comp)
  # (a) family-level instrument -------------------------------------------------
  # family leave-out national counts: dedup to (state, subject) then sum within family
  su <- unique(comp[, .(SG_UF = state, main_subject_code, topic_family,
                        leave_uf_out_2020, leave_uf_out_2024)])
  fam_lo <- su[, .(fam_leave_2020 = sum(leave_uf_out_2020, na.rm = TRUE),
                   fam_leave_2024 = sum(leave_uf_out_2024, na.rm = TRUE)),
               by = .(SG_UF, topic_family)]
  fam_lo[, fam_shock := log1p(fam_leave_2024) - log1p(fam_leave_2020)]
  # muni family share: sum baseline counts within family / muni total
  fam_ct <- comp[, .(fam_n = sum(n_lawsuits, na.rm = TRUE)),
                 by = .(SG_UF = state, municipality_id_tse, topic_family)]
  fam_ct[, muni_tot := sum(fam_n), by = .(SG_UF, municipality_id_tse)]
  fam_ct[, fam_share := fam_n / muni_tot]
  fam_ct <- merge(fam_ct, fam_lo, by = c("SG_UF", "topic_family"), all.x = TRUE)
  fam_ct[is.na(fam_shock), fam_shock := 0]
  z_fam <- fam_ct[, .(bartik_family = sum(fam_share * fam_shock, na.rm = TRUE)),
                  by = .(SG_UF, municipality_id_tse)]

  # (b) drop-propaganda instrument (keep original shares; zero propaganda's shift) --
  comp[, contrib := baseline_share_2020 * shock_log_growth_2020_2024]
  z_noprop <- comp[, .(bartik_noprop = sum(contrib[!is_prop(main_subject_name)], na.rm = TRUE)),
                   by = .(SG_UF = state, municipality_id_tse)]

  merge(z_fam, z_noprop, by = c("SG_UF", "municipality_id_tse"), all = TRUE)
}

# ============================================================================
# [1] which subject shifts drive the instrument, and how propaganda-concentrated
# ============================================================================
shift_audit <- function(comp) {
  comp <- copy(comp)
  comp[, contrib := baseline_share_2020 * shock_log_growth_2020_2024]
  by_subj <- comp[, .(tot_contrib = sum(contrib, na.rm = TRUE),
                      abs_contrib = abs(sum(contrib, na.rm = TRUE)),
                      mean_shock  = mean(shock_log_growth_2020_2024, na.rm = TRUE),
                      is_prop = any(is_prop(main_subject_name))),
                  by = .(main_subject_code, main_subject_name)]
  tot_abs <- sum(by_subj$abs_contrib)
  prop_abs <- sum(by_subj[is_prop == TRUE, abs_contrib])
  prop_share <- prop_abs / tot_abs
  # propaganda national leave-out totals (state-summed), and mean propaganda shock
  prop_lo <- unique(comp[is_prop(main_subject_name),
                         .(state, main_subject_code, leave_uf_out_2020, leave_uf_out_2024)])
  prop_shock_mean <- comp[is_prop(main_subject_name),
                          weighted.mean(shock_log_growth_2020_2024, baseline_share_2020, na.rm = TRUE)]
  cat("\n==== [1] SHIFT AUDIT ====\n")
  cat(sprintf("Propaganda share of |instrument contribution|: %.1f%%\n", 100 * prop_share))
  cat(sprintf("Share-weighted mean propaganda shock (log-growth): %.3f (negative = national decline)\n",
              prop_shock_mean))
  list(prop_share = prop_share, prop_shock_mean = prop_shock_mean,
       n_prop_subj = by_subj[is_prop == TRUE, .N], n_subj = nrow(by_subj))
}

# ============================================================================
# estimate a first stage + margin reduced form for a given instrument column
# ============================================================================
est_instrument <- function(dat, zcol) {
  fs <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF",
                                 "delta_log1p_competition_lawsuits_2024_2020", zcol, ctrl_rhs())),
              dat, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  rf <- feols(as.formula(sprintf("%s ~ %s + %s + %s | SG_UF",
                                 MARGIN["lhs"], zcol, ctrl_rhs(), MARGIN["lag"])),
              dat, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  gfs <- grab(fs, zcol); grf <- grab(rf, zcol)
  list(fs_coef = gfs["coef"], fs_se = gfs["se"], fs_F = Fstat(fs, zcol),
       rf_coef = grf["coef"], rf_se = grf["se"], rf_p = grf["p"])
}

# ---- deck outputs ----------------------------------------------------------
star <- function(p) {
  if (is.na(p)) return("")
  if (p < .01) return("$^{***}$"); if (p < .05) return("$^{**}$")
  if (p < .10) return("$^{*}$"); ""
}
f3 <- function(x) sprintf("%.3f", x)

write_deck <- function(rows, audit) {
  # rows: named list of est_instrument() results, keyed subject/family/noprop
  lab <- c(subject = "Subject-level \\;\\scriptsize(committed)",
           family  = "Topic-family \\;\\scriptsize(within-family recode immune)",
           noprop  = "Drop propaganda shift")
  body <- c()
  for (k in c("subject", "family", "noprop")) {
    r <- rows[[k]]
    band <- if (k == "subject") "\\rowcolor{mylight}\n" else ""
    body <- c(body, sprintf("%s%s & $%.0f$ & %s%s & \\textcolor{mygray}{(%s)} & $%.3f$ \\\\",
                            band, lab[[k]], r$fs_F, f3(r$rf_coef), star(r$rf_p),
                            f3(r$rf_se), r$rf_p))
  }
  tex <- c(
    "% Auto-generated by code/03_estimation/13_reclassification_robustness.R -- do not edit.",
    "\\begin{tabular}{lcccc}",
    "\\toprule\\toprule",
    " & First stage & \\multicolumn{3}{c}{Reduced form: 2024 margin} \\\\",
    "\\cmidrule(lr){2-2}\\cmidrule(lr){3-5}",
    "Instrument built at & $F$ & Coef. & (SE) & $p$ \\\\",
    "\\midrule",
    body,
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  writeLines(tex, OUT_TEX)

  s <- rows$subject; f <- rows$family; n <- rows$noprop
  mac <- c(
    "% Auto-generated by code/03_estimation/13_reclassification_robustness.R -- do not edit.",
    sprintf("\\newcommand{\\RecPropShare}{%.0f}", 100 * audit$prop_share),
    sprintf("\\newcommand{\\RecPropShock}{%.2f}", audit$prop_shock_mean),
    sprintf("\\newcommand{\\RecNsubj}{%d}", audit$n_subj),
    sprintf("\\newcommand{\\RecSubjF}{%.0f}", s$fs_F),
    sprintf("\\newcommand{\\RecSubjRFp}{%.3f}", s$rf_p),
    sprintf("\\newcommand{\\RecFamF}{%.0f}", f$fs_F),
    sprintf("\\newcommand{\\RecFamRFcoef}{%s}", f3(f$rf_coef)),
    sprintf("\\newcommand{\\RecFamRFp}{%.3f}", f$rf_p),
    sprintf("\\newcommand{\\RecNoPropF}{%.0f}", n$fs_F),
    sprintf("\\newcommand{\\RecNoPropRFcoef}{%s}", f3(n$rf_coef)),
    sprintf("\\newcommand{\\RecNoPropRFp}{%.3f}", n$rf_p)
  )
  writeLines(mac, OUT_MAC)
  cat(sprintf("\nWrote %s\n      %s\n", OUT_TEX, OUT_MAC))
}

main <- function() {
  dc <- load_all()
  design <- dc$design; comp <- dc$comp
  audit <- shift_audit(comp)

  alt <- build_alt_instruments(comp)
  dat <- merge(design, alt[, .(municipality_id_tse, bartik_family, bartik_noprop)],
               by = "municipality_id_tse", all.x = TRUE)
  dat[is.na(bartik_family), bartik_family := 0]     # zero-litigation munis absent from components
  dat[is.na(bartik_noprop), bartik_noprop := 0]

  rows <- list(
    subject = est_instrument(dat, INSTR),
    family  = est_instrument(dat, "bartik_family"),
    noprop  = est_instrument(dat, "bartik_noprop")
  )
  res <- rbindlist(lapply(names(rows), function(k) {
    r <- rows[[k]]
    data.table(instrument = k, fs_F = r$fs_F, fs_coef = r$fs_coef, fs_se = r$fs_se,
               rf_coef = r$rf_coef, rf_se = r$rf_se, rf_p = r$rf_p)
  }))
  fwrite(res, OUT_CSV)
  cat("\n==== [2]-[3] RECLASSIFICATION-ROBUST INSTRUMENTS (margin) ====\n")
  print(res[, .(instrument, fs_F = round(fs_F, 1), rf_coef = round(rf_coef, 4),
                rf_p = round(rf_p, 4))])
  write_deck(rows, audit)
  cat(sprintf("Wrote %s\n", OUT_CSV))
}

main()
