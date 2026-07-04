# ============================================================================
# 12_treatment_definition.R
# Is the headline consolidation an artifact of the log1p treatment definition?
#
# The endogenous variable is Delta log(1 + adversarial lawsuits). log(1+x) is a
# choice: it compresses large counts and, because it has a floor at zero, it
# co-determines the extensive-margin behaviour documented in 09_extensive_margin.R.
# A referee will ask whether the sign/significance of the margin effect survives
# OTHER reasonable ways to measure the change in litigation intensity.
#
# We re-estimate the headline ANCOVA-2016 margin 2SLS under a grid of treatment
# definitions, holding the SAME Bartik instrument (bartik_iv_2020_2024), the same
# controls, state FE, and state clustering fixed. Definitions (all 2024 vs 2020):
#   log1p   Delta log(1+ell)                 (baseline / headline)
#   ihs     Delta asinh(ell)                 (zero-friendly, different curvature)
#   levels  Delta ell                        (raw count change, no compression)
#   rate    Delta (ell per 1,000 valid votes)(size-normalised)
#   binary  1[ell_2024>0] - 1[ell_2020>0]    (coarsest: onset of any litigation)
#
# THE KEY FACT the table makes visible: the REDUCED FORM (margin ~ Z) does NOT
# depend on the treatment definition at all -- it is one number. So the sign and
# significance of every 2SLS column are governed by that single fixed reduced form
# divided by a treatment-specific first stage; only the UNITS (and the first-stage
# F) change. We therefore report, per definition, the first-stage F, the 2SLS
# coef in native units, and the effect per 1 SD of that treatment so magnitudes are
# comparable. Conclusion mirrors 09: sign/significance robust, per-unit MAGNITUDE
# is definition-dependent (Chen-Roth 2023) -- so we lead with the reduced form.
#
# Outputs:
#   output/tables/regressions/treatment_definition.csv   (full grid, margin + blank)
#   output/tables/tex/treatment_definition.tex           (deck fragment, margin)
#   output/tables/tex/treatment_definition_macros.tex    (inline-prose macros)
# ============================================================================

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

ROOT   <- "c:/Users/naral/Desktop/Nara/Doutorado/Tese/judicialization"
DESIGN <- file.path(ROOT, "data/estimation/executive_margin_design.csv")
OUT_CSV <- file.path(ROOT, "output/tables/regressions/treatment_definition.csv")
OUT_TEX <- file.path(ROOT, "output/tables/tex/treatment_definition.tex")
OUT_MAC <- file.path(ROOT, "output/tables/tex/treatment_definition_macros.tex")

INSTR  <- "bartik_iv_2020_2024"
L20    <- "competition_lawsuits_2020"        # adversarial filing count, base year
L24    <- "competition_lawsuits_2024"        # adversarial filing count, end year
VOTES20 <- "log1p_total_valid_votes_2020"    # for the size-normalised rate (exp back out)
CTRL   <- c("log_pop_2010", "urban_share_2010", "log_income_pc_2010",
            "higher_educ_share_2010", "log1p_total_valid_votes_2020", "margin_2016")
OUTCOMES <- list(
  margin = c(lhs = "margin_top1_top2_2024", lag = "margin_top1_top2_2016"),
  blank  = c(lhs = "blank_rate_2024",       lag = "blank_rate_2016")
)

# ---- helpers ---------------------------------------------------------------
grab <- function(fit, term) {
  ct <- fit$coeftable
  if (!term %in% rownames(ct)) return(c(coef = NA, se = NA, p = NA))
  c(coef = unname(ct[term, "Estimate"]), se = unname(ct[term, "Std. Error"]),
    p = unname(ct[term, "Pr(>|t|)"]))
}
Fstat <- function(fit, term) { g <- grab(fit, term); unname((g["coef"] / g["se"])^2) }
ctrl_rhs <- function() paste(CTRL, collapse = " + ")
asinh0 <- function(x) log(x + sqrt(x^2 + 1))

load_data <- function() {
  df <- fread(DESIGN, colClasses = list(character = c("state", "municipality_id_tse", "cluster_id")))
  setnames(df, "state", "SG_UF")
  req <- unique(c(INSTR, L20, L24, VOTES20, CTRL, "cluster_id", "SG_UF",
                  unlist(lapply(OUTCOMES, unname))))
  full <- df[complete.cases(df[, ..req])]
  # build the treatment definitions (all are 2024-vs-2020 changes)
  full[, td_log1p := log1p(get(L24)) - log1p(get(L20))]
  full[, td_ihs   := asinh0(get(L24)) - asinh0(get(L20))]
  full[, td_levels := get(L24) - get(L20)]
  votes20 <- expm1(full[[VOTES20]])                     # back out valid-vote level
  full[, tot_votes_2020 := votes20]
  full[, td_rate  := 1000 * (get(L24) - get(L20)) / pmax(votes20, 1)]
  full[, td_binary := as.integer(get(L24) > 0) - as.integer(get(L20) > 0)]
  full[]
}

TDEFS <- c(log1p = "td_log1p", ihs = "td_ihs", levels = "td_levels",
           rate = "td_rate", binary = "td_binary")
TDEF_LABEL <- c(
  log1p  = "$\\Delta\\log(1+\\ell)$ \\;\\scriptsize(baseline)",
  ihs    = "$\\Delta\\,\\mathrm{asinh}(\\ell)$",
  levels = "$\\Delta\\ell$ \\;\\scriptsize(raw count)",
  rate   = "$\\Delta\\ell$ per 1{,}000 votes",
  binary = "$\\mathbf{1}[\\ell_{24}{>}0]-\\mathbf{1}[\\ell_{20}{>}0]$"
)

# ---- estimation ------------------------------------------------------------
estimate_grid <- function(full) {
  rows <- list()
  for (oname in names(OUTCOMES)) {
    o <- OUTCOMES[[oname]]
    # the reduced form is INVARIANT to the treatment definition -- compute once
    rf <- feols(as.formula(sprintf("%s ~ %s + %s + %s | SG_UF",
                                    o["lhs"], INSTR, ctrl_rhs(), o["lag"])),
                full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
    grf <- grab(rf, INSTR)
    for (tname in names(TDEFS)) {
      td <- TDEFS[[tname]]
      sd_t <- sd(full[[td]], na.rm = TRUE)
      # first stage: this treatment definition on Z
      fs <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF", td, INSTR, ctrl_rhs())),
                  full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
      gfs <- grab(fs, INSTR)
      # 2SLS: ANCOVA-2016 margin on the instrumented treatment
      iv <- feols(as.formula(sprintf("%s ~ %s + %s | SG_UF | %s ~ %s",
                                      o["lhs"], ctrl_rhs(), o["lag"], td, INSTR)),
                  full, cluster = ~cluster_id, warn = FALSE, notes = FALSE)
      giv <- grab(iv, paste0("fit_", td))
      rows[[length(rows) + 1]] <- data.table(
        outcome = oname, tdef = tname, n = nrow(full),
        sd_treat = sd_t,
        fs_coef = unname(gfs["coef"]), fs_se = unname(gfs["se"]), fs_F = Fstat(fs, INSTR),
        iv_coef = unname(giv["coef"]), iv_se = unname(giv["se"]), iv_p = unname(giv["p"]),
        iv_per_sd = unname(giv["coef"]) * sd_t,
        rf_coef = unname(grf["coef"]), rf_se = unname(grf["se"]), rf_p = unname(grf["p"]))
    }
  }
  rbindlist(rows)
}

# ---- deck outputs ----------------------------------------------------------
star <- function(p) {
  if (is.na(p)) return("")
  if (p < .01) return("$^{***}$"); if (p < .05) return("$^{**}$")
  if (p < .10) return("$^{*}$"); ""
}
f3 <- function(x) sprintf("%.3f", x)
gray <- function(x) sprintf("\\textcolor{mygray}{(%s)}", f3(x))

write_deck <- function(grid) {
  m <- grid[outcome == "margin"]
  setkey(m, tdef)
  ord <- names(TDEFS)
  rf_p <- m[tdef == "log1p", rf_p]; rf_c <- m[tdef == "log1p", rf_coef]
  rf_se <- m[tdef == "log1p", rf_se]

  body <- c()
  for (tn in ord) {
    r <- m[tdef == tn]
    band <- if (tn == "log1p") "\\rowcolor{mylight}\n" else ""
    body <- c(body, sprintf(
      "%s%s & %s & $%.1f$ & %s%s & %s & $%.3f$ \\\\",
      band, TDEF_LABEL[[tn]],
      f3(r$fs_coef), r$fs_F,
      f3(r$iv_coef), star(r$iv_p), f3(r$iv_per_sd), r$iv_p))
    # SE line under the 2SLS coef (house style), gray
    body <- c(body, sprintf(
      "%s & \\textcolor{mygray}{(%s)} & & \\textcolor{mygray}{(%s)} & & \\\\",
      if (tn == "log1p") "\\rowcolor{mylight}" else "",
      f3(r$fs_se), f3(r$iv_se)))
  }

  tex <- c(
    "% Auto-generated by code/03_estimation/12_treatment_definition.R -- do not edit.",
    "\\begin{tabular}{lccccc}",
    "\\toprule\\toprule",
    " & \\multicolumn{2}{c}{First stage} & \\multicolumn{3}{c}{2SLS: 2024 top-two margin} \\\\",
    "\\cmidrule(lr){2-3}\\cmidrule(lr){4-6}",
    "Treatment definition & Coef. & $F$ & Coef. & /\\,SD & $p$ \\\\",
    "\\midrule",
    body,
    "\\bottomrule\\bottomrule",
    "\\end{tabular}"
  )
  writeLines(tex, OUT_TEX)

  # macros: reduced form (invariant) + range of per-SD 2SLS effects + F range
  per_sd <- m$iv_per_sd; ps <- m$iv_p
  mac <- c(
    "% Auto-generated by code/03_estimation/12_treatment_definition.R -- do not edit.",
    sprintf("\\newcommand{\\TdefRFcoef}{%s}", f3(rf_c)),
    sprintf("\\newcommand{\\TdefRFse}{%s}", f3(rf_se)),
    sprintf("\\newcommand{\\TdefRFp}{%.3f}", rf_p),
    sprintf("\\newcommand{\\TdefNdefs}{%d}", length(ord)),
    sprintf("\\newcommand{\\TdefPerSDlo}{%s}", f3(min(per_sd))),
    sprintf("\\newcommand{\\TdefPerSDhi}{%s}", f3(max(per_sd))),
    sprintf("\\newcommand{\\TdefPmax}{%.3f}", max(ps)),
    sprintf("\\newcommand{\\TdefFlo}{%.1f}", min(m$fs_F)),
    sprintf("\\newcommand{\\TdefFhi}{%.0f}", max(m$fs_F))
  )
  writeLines(mac, OUT_MAC)
  cat(sprintf("Wrote %s\n      %s\n", OUT_TEX, OUT_MAC))
}

main <- function() {
  full <- load_data()
  grid <- estimate_grid(full)
  fwrite(grid, OUT_CSV)
  cat("\n==== TREATMENT-DEFINITION ROBUSTNESS (margin) ====\n")
  print(grid[outcome == "margin", .(tdef, fs_F = round(fs_F, 1),
             iv_coef = round(iv_coef, 4), iv_p = round(iv_p, 4),
             per_sd = round(iv_per_sd, 4))])
  cat(sprintf("\nReduced form (invariant across definitions): margin ~ Z coef=%.4f p=%.4f\n",
              grid[outcome == "margin" & tdef == "log1p", rf_coef],
              grid[outcome == "margin" & tdef == "log1p", rf_p]))
  write_deck(grid)
  cat(sprintf("Wrote %s\n", OUT_CSV))
}

main()
