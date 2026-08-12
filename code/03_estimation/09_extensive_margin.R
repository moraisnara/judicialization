# ============================================================================
# 09_extensive_margin.R
# Is the headline identification the EXTENSIVE margin (any 2020 adversarial
# litigation vs none) rather than the intensive shift-share composition?
#
# 20.6% of municipalities (1,146 / 5,560) have ZERO adversarial lawsuits in the
# 2020 base year, so the instrument piles up at exactly zero -- a mass point at
# the origin. This script decomposes the headline first stage AND the headline
# second stage into their extensive (zero-vs-positive) and intensive (slope among
# litigating munis) pieces, and asks whether the margin effect is really the crude
# zero-vs-positive contrast.
#
# Four diagnostics (main() dispatches each), all mirroring the headline machinery
# verbatim (see BASELINE_CONTROLS / ANCOVA_MAP / run_first_stage in 02_iv_main.R):
# margin LHS = margin_top1_top2_2024 with a free 2016 lag; FE = state; cluster = state.
#
#   [A] mass_point_robustness()      re-estimate FS + margin/blank IV on
#                                    full / positive-litig / nonzero-instrument samples
#   [B] first_stage_decomposition()  how much of Z, and of the FS, is the presence dummy
#   [C] presence_instrument_2sls()   headline (Delta ~ Z) vs presence-IV (Delta ~ D0);
#                                    equal coef => Bartik is a scaled presence dummy
#   [D] reduced_form_decomposition() does the margin reduced form survive dropping
#                                    zeros, and survive controlling for the presence dummy?
#
# Outputs:
#   output/tables/regressions/zero_exposure_robustness.csv      [A]
#   output/tables/regressions/extensive_margin_decomposition.csv [B]-[D]
# ============================================================================

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

ROOT   <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
DESIGN <- file.path(ROOT, "data/estimation/executive_margin_design.csv")
OUT_MP <- file.path(ROOT, "output/tables/regressions/zero_exposure_robustness.csv")
OUT_DC <- file.path(ROOT, "output/tables/regressions/extensive_margin_decomposition.csv")
OUT_TEX <- file.path(ROOT, "output/tables/tex/extensive_margin.tex")
OUT_MAC <- file.path(ROOT, "output/tables/tex/extensive_margin_macros.tex")

INSTR  <- "bartik_iv_2020_2024"
ENDOG  <- "delta_log1p_competition_lawsuits_2024_2020"
BASE20 <- "competition_lawsuits_2020"        # adversarial filing count in the base year
END24  <- "competition_lawsuits_2024"        # adversarial filing count in the end year (for PPML)
CTRL   <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
            "higher_educ_share_2010", "log1p_total_valid_votes_2020", "margin_2016")
# headline ANCOVA-2016 outcomes: LHS 2024 level + free 2016 lag
OUTCOMES <- list(
  margin = c(lhs = "margin_top1_top2_2024", lag = "margin_top1_top2_2016"),
  blank  = c(lhs = "blank_rate_2024",       lag = "blank_rate_2016")
)

# ---- helpers ---------------------------------------------------------------

grab <- function(fit, term) {
  ct <- fit$coeftable
  if (!term %in% rownames(ct)) return(c(coef = NA, se = NA, p = NA))
  pcol <- grep("^Pr", colnames(ct), value = TRUE)[1]   # "Pr(>|t|)" (feols) or "Pr(>|z|)" (fepois/fenegbin)
  c(coef = unname(ct[term, "Estimate"]), se = unname(ct[term, "Std. Error"]),
    p = unname(ct[term, pcol]))
}
Fstat <- function(fit, term) { g <- grab(fit, term); unname((g["coef"] / g["se"])^2) }

ctrl_rhs <- function() paste(CTRL, collapse = " + ")

load_data <- function() {
  df <- fread(DESIGN, colClasses = list(character = c("state", "municipality_id_tse", "cluster_id")))
  setnames(df, "state", "SG_UF")
  req <- unique(c(INSTR, ENDOG, "cluster_id", "SG_UF", BASE20, END24, CTRL,
                  unlist(lapply(OUTCOMES, unname))))
  full <- df[complete.cases(df[, ..req])]
  full[, D0 := as.integer(get(BASE20) > 0)]      # presence dummy: any 2020 adversarial litigation
  full[, l20log := log1p(get(BASE20))]           # baseline lag for the count-native ANCOVA
  full[]
}

# ============================================================================
# [A] Mass-point subsample robustness (re-estimate headline on 3 samples)
# ============================================================================
mass_point_robustness <- function(full) {
  fs_fml <- as.formula(sprintf("%s ~ %s + %s | SG_UF", ENDOG, INSTR, ctrl_rhs()))
  iv_fml <- function(o) as.formula(sprintf("%s ~ %s + %s | SG_UF | %s ~ %s",
                                           o["lhs"], ctrl_rhs(), o["lag"], ENDOG, INSTR))
  n0_base  <- sum(full[[BASE20]] == 0)
  n0_instr <- sum(full[[INSTR]] == 0)
  cat(sprintf("Full complete-case N = %d\n", nrow(full)))
  cat(sprintf("  baseline litigation == 0 : %d (%.1f%%)  <- the mass point\n",
              n0_base, 100 * n0_base / nrow(full)))
  cat(sprintf("  instrument == 0          : %d (%.1f%%)\n",
              n0_instr, 100 * n0_instr / nrow(full)))

  SAMPLES <- list(
    full           = function(d) d,
    positive_litig = function(d) d[get(BASE20) > 0],   # primary: drop the mass point
    nonzero_instr  = function(d) d[get(INSTR) != 0]    # secondary: drop exact-zero Z only
  )
  rows <- list()
  for (sname in names(SAMPLES)) {
    samp <- SAMPLES[[sname]](full)
    ncl  <- uniqueN(samp$cluster_id)
    fs   <- feols(fs_fml, data = samp, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    fsF  <- Fstat(fs, INSTR)
    for (oname in names(OUTCOMES)) {
      fit   <- feols(iv_fml(OUTCOMES[[oname]]), data = samp, cluster = ~cluster_id,
                     warn = FALSE, notes = FALSE)
      g     <- grab(fit, paste0("fit_", ENDOG))
      ymean <- mean(samp[[OUTCOMES[[oname]]["lhs"]]], na.rm = TRUE)
      rows[[length(rows) + 1]] <- data.table(
        sample = sname, outcome = oname, n = nrow(samp), n_clusters = ncl,
        first_stage_F = fsF, coef = unname(g["coef"]), se = unname(g["se"]),
        p = unname(g["p"]), dep_var_2024_mean = ymean)
    }
  }
  res <- rbindlist(rows)
  fwrite(res, OUT_MP)
  cat("\n==== [A] ZERO-EXPOSURE MASS-POINT ROBUSTNESS ====\n")
  print(res[, .(sample, outcome, n, first_stage_F = round(first_stage_F, 1),
                coef = round(coef, 4), se = round(se, 4), p = round(p, 4))])
  res
}

# ============================================================================
# [B] First-stage decomposition: how much is the presence dummy?
# ============================================================================
first_stage_decomposition <- function(full) {
  pos <- full[D0 == 1]
  # (1) share of instrument variance that is just the presence dummy (Z==0 iff D0==0)
  r2_z_on_d0 <- cor(full[[INSTR]], full$D0)^2
  # (2) extensive jump in the endogenous variable: Delta ~ D0 + controls | state
  ext <- feols(as.formula(sprintf("%s ~ D0 + %s | SG_UF", ENDOG, ctrl_rhs())),
               full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  g_ext <- grab(ext, "D0")
  # (3) intensive slope among litigating munis: Delta ~ Z + controls | state (positive only)
  ins <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF", ENDOG, INSTR, ctrl_rhs())),
               pos, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  g_ins <- grab(ins, INSTR)
  # (4) full first stage for reference
  fsf <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF", ENDOG, INSTR, ctrl_rhs())),
               full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
  g_fsf <- grab(fsf, INSTR)

  res <- data.table(
    block = "first_stage",
    quantity = c("cor(Z,D0)^2", "endog ~ D0 (extensive jump, full)",
                 "endog ~ Z (intensive slope, positive only)",
                 "endog ~ Z (full, headline FS)"),
    n = c(nrow(full), nrow(full), nrow(pos), nrow(full)),
    coef = c(NA, g_ext["coef"], g_ins["coef"], g_fsf["coef"]),
    se   = c(NA, g_ext["se"],   g_ins["se"],   g_fsf["se"]),
    p    = c(NA, g_ext["p"],    g_ins["p"],    g_fsf["p"]),
    F_or_R2 = c(r2_z_on_d0, Fstat(ext, "D0"), Fstat(ins, INSTR), Fstat(fsf, INSTR))
  )
  cat("\n==== [B] FIRST-STAGE DECOMPOSITION ====\n")
  cat(sprintf("Share of instrument variance that is the presence dummy: cor(Z,D0)^2 = %.3f\n",
              r2_z_on_d0))
  print(res[, .(quantity, n, coef = round(coef, 4), se = round(se, 4),
                p = round(p, 4), F_or_R2 = round(F_or_R2, 2))])
  res
}

# ============================================================================
# [C] Presence-instrument 2SLS vs headline (equal coef => Bartik ~ scaled D0)
#     DIAGNOSTIC ONLY: D0 is not defended as excludable; this shows the headline
#     coefficient IS the Wald zero-vs-positive contrast.
# ============================================================================
presence_instrument_2sls <- function(full) {
  rows <- list()
  for (oname in names(OUTCOMES)) {
    o <- OUTCOMES[[oname]]
    for (iv in c(bartik = INSTR, presence = "D0")) {
      ivname <- names(which(c(bartik = INSTR, presence = "D0") == iv))
      # first stage strength of this instrument
      fs <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF", ENDOG, iv, ctrl_rhs())),
                  full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
      # 2SLS
      fit <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF | %s ~ %s",
                                      o["lhs"], ctrl_rhs(), o["lag"], ENDOG, iv)),
                   full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
      g <- grab(fit, paste0("fit_", ENDOG))
      rows[[length(rows) + 1]] <- data.table(
        block = "presence_iv", outcome = oname, instrument = ivname,
        first_stage_F = Fstat(fs, iv),
        coef = unname(g["coef"]), se = unname(g["se"]), p = unname(g["p"]))
    }
  }
  res <- rbindlist(rows)
  cat("\n==== [C] PRESENCE-INSTRUMENT 2SLS vs HEADLINE ====\n")
  cat("(if 'presence' coef ~ 'bartik' coef, the Bartik is a scaled presence dummy)\n")
  print(res[, .(outcome, instrument, first_stage_F = round(first_stage_F, 1),
                coef = round(coef, 4), se = round(se, 4), p = round(p, 4))])
  res
}

# ============================================================================
# [D] Reduced-form decomposition: is the margin RF the zero-vs-positive jump?
#   rf_full   Y_2024 ~ Z + controls + Y_2016 | state              (headline RF)
#   rf_pos    same, positive-litigation subsample                 (does it survive dropping zeros?)
#   rf_horse  Y_2024 ~ Z + D0 + controls + Y_2016 | state         (does Z survive controlling for D0?)
# ============================================================================
reduced_form_decomposition <- function(full) {
  pos <- full[D0 == 1]
  rows <- list()
  for (oname in names(OUTCOMES)) {
    o <- OUTCOMES[[oname]]
    # headline reduced form
    rf_full <- feols(as.formula(sprintf("%s ~ %s + %s + %s | SG_UF",
                                         o["lhs"], INSTR, ctrl_rhs(), o["lag"])),
                     full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    gZf <- grab(rf_full, INSTR)
    # reduced form among litigating munis only
    rf_pos <- feols(as.formula(sprintf("%s ~ %s + %s + %s | SG_UF",
                                        o["lhs"], INSTR, ctrl_rhs(), o["lag"])),
                    pos, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    gZp <- grab(rf_pos, INSTR)
    # horse race: Z vs presence dummy D0
    rf_horse <- feols(as.formula(sprintf("%s ~ %s + D0 + %s + %s | SG_UF",
                                          o["lhs"], INSTR, ctrl_rhs(), o["lag"])),
                      full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    gZh <- grab(rf_horse, INSTR)
    gDh <- grab(rf_horse, "D0")
    rows[[length(rows) + 1]] <- data.table(
      block = "reduced_form", outcome = oname,
      spec = c("rf_full: Z", "rf_positive: Z", "rf_horse: Z", "rf_horse: D0"),
      n    = c(nrow(full), nrow(pos), nrow(full), nrow(full)),
      coef = c(gZf["coef"], gZp["coef"], gZh["coef"], gDh["coef"]),
      se   = c(gZf["se"],   gZp["se"],   gZh["se"],   gDh["se"]),
      p    = c(gZf["p"],    gZp["p"],    gZh["p"],    gDh["p"]))
  }
  res <- rbindlist(rows)
  cat("\n==== [D] REDUCED-FORM DECOMPOSITION ====\n")
  cat("(rf_full = headline RF; rf_positive = drop zeros; rf_horse = Z net of presence dummy D0)\n")
  print(res[, .(outcome, spec, n, coef = round(coef, 4), se = round(se, 4), p = round(p, 4))])
  res
}

# ============================================================================
# [E] Count-native first stage (Poisson / Negative Binomial).
#   The log1p transform floors every silent muni at 0, so the strong headline
#   first stage (F=102) could in principle be an artifact of that floor rather
#   than a real response of the caseload to Z. A count model has no floor: its
#   conditional mean exp(beta*Z) is a PROPORTIONAL (intensive) response that
#   accommodates zeros natively. So PPML is the clean test of whether the
#   intensive margin is genuinely null or merely a log1p artifact.
#     E[ell_2024 | .] = exp( beta*Z + rho*log1p(ell_2020) + X'g + delta_UF )
#   Run full AND litigating-only; NegBin as an overdispersion robustness
#   (the 2024 count is heavily overdispersed, var >> mean). A null beta here
#   CONFIRMS the extensive-margin reading: relevance is onset (zero-vs-any),
#   not proportional growth among already-litigating municipalities.
# ============================================================================
count_native_first_stage <- function(full) {
  pos <- full[D0 == 1]
  disp <- var(full[[END24]]) / mean(full[[END24]])   # >1 => overdispersed
  fml_anc <- as.formula(sprintf("%s ~ %s + l20log + %s | SG_UF", END24, INSTR, ctrl_rhs()))
  fml_rel <- as.formula(sprintf("%s ~ %s + %s | SG_UF", END24, INSTR, ctrl_rhs()))
  fit1 <- function(fn, d, fml)
    fn(fml, data = d, cluster = ~cluster_id, warn = FALSE, notes = FALSE)

  specs <- list(
    list(key = "ppml_anc_full",  fn = fepois,   d = full, fml = fml_anc),
    list(key = "ppml_anc_litig", fn = fepois,   d = pos,  fml = fml_anc),
    list(key = "ppml_rel_full",  fn = fepois,   d = full, fml = fml_rel),
    list(key = "negbin_anc_full",  fn = fenegbin, d = full, fml = fml_anc),
    list(key = "negbin_anc_litig", fn = fenegbin, d = pos,  fml = fml_anc)
  )
  rows <- list()
  for (s in specs) {
    fit <- tryCatch(fit1(s$fn, s$d, s$fml), error = function(e) NULL)
    g <- if (is.null(fit)) c(coef = NA, se = NA, p = NA) else grab(fit, INSTR)
    dt <- data.table(                          # NB: avoid the reserved `key=` constructor arg
      block = "count_native", outcome = NA_character_, n = nrow(s$d),
      coef = unname(g["coef"]), se = unname(g["se"]), p = unname(g["p"]),
      aux = unname((g["coef"] / g["se"])^2))   # Wald chi-sq(1), comparable to F
    dt[, key := s$key]
    rows[[length(rows) + 1]] <- dt
  }
  res <- rbindlist(rows)
  disp_row <- data.table(block = "count_native", outcome = NA_character_, n = nrow(full),
                         coef = NA_real_, se = NA_real_, p = NA_real_, aux = disp)
  disp_row[, key := "dispersion_var_over_mean"]
  res <- rbind(res, disp_row)
  cat("\n==== [E] COUNT-NATIVE FIRST STAGE (PPML / NegBin) ====\n")
  cat(sprintf("2024-count overdispersion var/mean = %.1f (>>1)\n", disp))
  print(res[key != "dispersion_var_over_mean",
            .(key, n, coef = round(coef, 4), se = round(se, 4),
              p = round(p, 4), Wald = round(aux, 1))])
  res
}

# ============================================================================
# Deck outputs: house-style two-panel table + inline-prose macros.
# Panel A shows the relevance is EXTENSIVE (first stage collapses among
# litigating munis); Panel B shows the FINDING is not (the margin reduced form
# survives dropping the zero-litigation mass point AND a horse race vs the
# presence dummy). Nothing hard-coded downstream: prose numbers read from
# extensive_margin_macros.tex; the table from extensive_margin.tex.
# ============================================================================
star <- function(p) {
  if (is.na(p)) return("")
  if (p < .01) return("$^{***}$"); if (p < .05) return("$^{**}$")
  if (p < .10) return("$^{*}$"); ""
}
f3 <- function(x) sprintf("%.3f", x)

write_deck_outputs <- function(full, b, d, e) {
  bq <- function(q) b[quantity == q]
  fs_full <- bq("endog ~ Z (full, headline FS)")
  fs_int  <- bq("endog ~ Z (intensive slope, positive only)")
  fs_ext  <- bq("endog ~ D0 (extensive jump, full)")
  r2      <- b[quantity == "cor(Z,D0)^2", F_or_R2]
  n_full  <- fs_full$n; n_pos <- fs_int$n; n_zero <- n_full - n_pos

  dm <- d[outcome == "margin"]
  rf_full <- dm[spec == "rf_full: Z"]; rf_pos <- dm[spec == "rf_positive: Z"]
  rf_hz   <- dm[spec == "rf_horse: Z"]; rf_hd <- dm[spec == "rf_horse: D0"]

  coefse <- function(r, term = NULL) {
    cf <- r$coef; se <- r$se; p <- r$p
    list(c = sprintf("%s%s", f3(cf), star(p)), s = sprintf("\\textcolor{mygray}{(%s)}", f3(se)))
  }
  A_full <- coefse(fs_full); A_int <- coefse(fs_int); A_ext <- coefse(fs_ext)
  B_full <- coefse(rf_full); B_pos <- coefse(rf_pos); B_hz <- coefse(rf_hz); B_hd <- coefse(rf_hd)

  nf <- formatC(n_full, big.mark = ",", format = "d")
  np <- formatC(n_pos,  big.mark = ",", format = "d")

  tex <- c(
    "% Auto-generated by code/03_estimation/09_extensive_margin.R -- do not edit.",
    "\\begin{tabular}{lccc}",
    "\\toprule\\toprule",
    " & Coef. & (SE) & $F$ / $p$ \\\\",
    "\\midrule",
    sprintf("\\multicolumn{4}{l}{\\textit{Panel A. First stage:} $\\Delta\\log(1+\\ell_m)$} \\\\"),
    sprintf("Bartik $Z$ --- full ($N=%s$) & %s & %s & $F=%.0f$ \\\\", nf, A_full$c, A_full$s, fs_full$F_or_R2),
    sprintf("Bartik $Z$ --- litigating only ($N=%s$) & %s & %s & $F=%.1f$ \\\\", np, A_int$c, A_int$s, fs_int$F_or_R2),
    sprintf("Presence $\\mathbf{1}[\\ell_{2020}>0]$ --- full & %s & %s & $F=%.0f$ \\\\", A_ext$c, A_ext$s, fs_ext$F_or_R2),
    "\\midrule",
    "\\multicolumn{4}{l}{\\textit{Panel B. Reduced form: 2024 top-two margin}} \\\\",
    sprintf("Bartik $Z$ --- full & %s & %s & $p=%.3f$ \\\\", B_full$c, B_full$s, rf_full$p),
    "\\rowcolor{mylight}",
    sprintf("Bartik $Z$ --- litigating only & %s & %s & $p=%.3f$ \\\\", B_pos$c, B_pos$s, rf_pos$p),
    "\\rowcolor{mylight}",
    sprintf("Bartik $Z$ --- net of presence dummy & %s & %s & $p=%.3f$ \\\\", B_hz$c, B_hz$s, rf_hz$p),
    sprintf("Presence dummy --- net of $Z$ & %s & %s & $p=%.2f$ \\\\", B_hd$c, B_hd$s, rf_hd$p),
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  writeLines(tex, OUT_TEX)

  mac <- c(
    "% Auto-generated by code/03_estimation/09_extensive_margin.R -- do not edit.",
    sprintf("\\newcommand{\\ExtMassPointN}{%s}", formatC(n_zero, big.mark = ",", format = "d")),
    sprintf("\\newcommand{\\ExtMassPointPct}{%.1f}", 100 * n_zero / n_full),
    sprintf("\\newcommand{\\ExtFSfull}{%.0f}", fs_full$F_or_R2),
    sprintf("\\newcommand{\\ExtFSintensiveF}{%.1f}", fs_int$F_or_R2),
    sprintf("\\newcommand{\\ExtFSintensiveCoef}{%s}", f3(fs_int$coef)),
    sprintf("\\newcommand{\\ExtZonDzeroRtwo}{%.2f}", r2),
    sprintf("\\newcommand{\\ExtRFfullP}{%.3f}", rf_full$p),
    sprintf("\\newcommand{\\ExtRFpositiveP}{%.3f}", rf_pos$p),
    sprintf("\\newcommand{\\ExtRFhorseZP}{%.3f}", rf_hz$p),
    sprintf("\\newcommand{\\ExtRFhorseDzeroP}{%.2f}", rf_hd$p),
    # [E] count-native (Poisson / NegBin) confirmation that the intensive margin
    # is genuinely null -- not a log1p-floor artifact.
    sprintf("\\newcommand{\\ExtPPMLfullP}{%.2f}",  e[key == "ppml_anc_full",  p]),
    sprintf("\\newcommand{\\ExtPPMLlitigP}{%.2f}", e[key == "ppml_anc_litig", p]),
    sprintf("\\newcommand{\\ExtPPMLlitigCoef}{%s}", f3(e[key == "ppml_anc_litig", coef])),
    sprintf("\\newcommand{\\ExtNBfullP}{%.2f}",    e[key == "negbin_anc_full",  p]),
    sprintf("\\newcommand{\\ExtNBlitigP}{%.2f}",   e[key == "negbin_anc_litig", p]),
    sprintf("\\newcommand{\\ExtDisp}{%.0f}",       e[key == "dispersion_var_over_mean", aux])
  )
  writeLines(mac, OUT_MAC)
  cat(sprintf("\nWrote %s\n      %s\n", OUT_TEX, OUT_MAC))
}

# ============================================================================
main <- function() {
  full <- load_data()
  a <- mass_point_robustness(full)
  b <- first_stage_decomposition(full)
  c <- presence_instrument_2sls(full)
  d <- reduced_form_decomposition(full)
  e <- count_native_first_stage(full)
  write_deck_outputs(full, b, d, e)
  # decomposition CSV: stack [B]-[E] (common cols; [A] has its own file)
  dc <- rbindlist(list(
    b[, .(block, key = quantity, outcome = NA_character_, n, coef, se, p, aux = F_or_R2)],
    c[, .(block, key = instrument, outcome, n = NA_integer_, coef, se, p, aux = first_stage_F)],
    d[, .(block, key = spec, outcome, n, coef, se, p, aux = NA_real_)],
    e[, .(block, key, outcome, n, coef, se, p, aux)]
  ), fill = TRUE)
  fwrite(dc, OUT_DC)
  cat(sprintf("\nWrote %s\n      %s\n", OUT_MP, OUT_DC))
}

main()
