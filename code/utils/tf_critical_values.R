# ============================================================================
# tf_critical_values.R  —  shared tF weak-instrument critical values
# ----------------------------------------------------------------------------
# Authoritative Lee, McCrary, Moreira & Porter (2022, AER 112(10): 3260-90),
# "Valid t-ratio Inference for IV", tF adjusted critical values at the 5%
# two-sided level for a SINGLE instrument (just-identified).
#
# The table is indexed by sqrt(F): the grid runs sqrt(F) in [2.0, 10.3] in
# steps of 0.1 (84 points). The critical value reaches the usual 1.96 only at
# F ~ 104.7 (the paper's headline threshold) -- NOT at F = 23.1 as an earlier
# hand-typed copy in this repo wrongly assumed. Values transcribed from the
# ivDiag package (Yiqing Xu), which reproduces the paper's Table 3.
#
# Anchors (verifiable): sqrt(F)=2.5 (F=6.25) -> 4.92; F=10 -> 3.43;
#                       cv -> 1.96 as F -> ~106.
#
# Usage:  source(file.path(UTILS, "tf_critical_values.R"))  # UTILS = code/utils
#         cv <- get_tF_cv(first_stage_F)   # two-sided 5% cv replacing 1.96
# ============================================================================

# sqrt(F) grid, 84 points from 2.0 to 10.3
TF_SQRTF_GRID <- seq(2, 10.3, by = 0.1)

# 5% two-sided tF critical values (Lee et al. 2022, Table 3; via ivDiag)
TF_CV_05 <- c(
  18.66, 9.74, 7.37, 6.18, 5.43, 4.92, 4.54, 4.25, 4.01, 3.82, 3.65, 3.51,
   3.39, 3.29, 3.19, 3.11, 3.03, 2.97, 2.91, 2.85, 2.80, 2.75, 2.71, 2.67,
   2.63, 2.60, 2.57, 2.54, 2.51, 2.48, 2.46, 2.43, 2.41, 2.39, 2.37, 2.35,
   2.33, 2.32, 2.30, 2.29, 2.27, 2.26, 2.24, 2.23, 2.22, 2.21, 2.20, 2.19,
   2.17, 2.16, 2.16, 2.15, 2.14, 2.13, 2.12, 2.11, 2.10, 2.10, 2.09, 2.08,
   2.08, 2.07, 2.06, 2.06, 2.05, 2.04, 2.04, 2.03, 2.03, 2.02, 2.02, 2.01,
   2.01, 2.00, 2.00, 1.99, 1.99, 1.99, 1.98, 1.98, 1.97, 1.97, 1.97, 1.96
)
stopifnot(length(TF_SQRTF_GRID) == length(TF_CV_05))

# get_tF_cv(f): two-sided 5% tF critical value for observed first-stage F.
#   - Linear interpolation on the sqrt(F) grid (matches ivDiag / Lee et al.).
#   - rule = 2 clamps to the table ends: cv = 18.66 for a very weak first stage
#     (F <= 4, test essentially uninformative), cv = 1.96 once F >= ~106.
#   - NA / non-positive F -> NA (no valid-t claim is made).
get_tF_cv <- function(f) {
  if (length(f) != 1L) return(vapply(f, get_tF_cv, numeric(1)))
  if (is.na(f) || f <= 0) return(NA_real_)
  approx(TF_SQRTF_GRID, TF_CV_05, xout = sqrt(f), rule = 2)$y
}
