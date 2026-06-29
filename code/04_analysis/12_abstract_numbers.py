#!/usr/bin/env python3
"""
12_abstract_numbers.py
Reads all regression CSVs and descriptive tables; generates:
  output/tables/tex/abstract_macros.tex  — \\newcommand definitions for every number
  output/tables/tex/abstract_table.tex   — formatted 4-panel results table
Both files are \\input{}'d by output/presentation/extended_abstract.tex.
No numbers are hardcoded in the abstract itself.
"""

import os
import math
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT  = os.path.join(os.path.dirname(__file__), '..', '..')
REG   = os.path.join(ROOT, 'output', 'tables', 'regressions')
DESC  = os.path.join(ROOT, 'output', 'tables', 'descriptives')
TEX   = os.path.join(ROOT, 'output', 'tables', 'tex')
os.makedirs(TEX, exist_ok=True)

# ── Formatting helpers ─────────────────────────────────────────────────────────
def coef(x):
    """Signed coefficient, 3 dp."""
    return f'+{x:.3f}' if x >= 0 else f'{x:.3f}'

def se_par(x):
    """SE in parentheses, 3 dp."""
    return f'({x:.3f})'

def pval(x):
    """p-value, 3 dp (or <0.001)."""
    if x < 0.001:
        return r'$<$0.001'
    return f'{x:.3f}'

def f1(x):
    """1 decimal place float."""
    return f'{x:.1f}'

def f2(x):
    """2 decimal place float."""
    return f'{x:.2f}'

def pct1(x):
    """1 dp percentage, no % sign (append \\% in macro)."""
    return f'{x:.1f}'

def big(x):
    """Integer with thousand separators."""
    return f'{int(round(x)):,}'

def millions(x):
    """Round to 2 dp millions string, e.g. 1.23."""
    return f'{x / 1e6:.2f}'

def tick_cross(flag):
    """LaTeX tick or cross."""
    try:
        val = int(float(flag))
    except (ValueError, TypeError):
        val = 1 if str(flag).strip().lower() in ('true', '1', 'yes') else 0
    return r'\tick' if val else r'\cross'

# ── Load data ─────────────────────────────────────────────────────────────────
ovl  = pd.read_csv(os.path.join(DESC, 'overview_lawsuits.csv'))
ovv  = pd.read_csv(os.path.join(DESC, 'overview_voters.csv'))
ovc  = pd.read_csv(os.path.join(DESC, 'overview_candidates.csv'))
iv   = pd.read_csv(os.path.join(REG,  'executive_margin_iv_fixest.csv'))
fs   = pd.read_csv(os.path.join(REG,  'executive_margin_first_stage_fixest.csv'))
leg  = pd.read_csv(os.path.join(REG,  'legislative_iv_fixest.csv'))
er   = pd.read_csv(os.path.join(REG,  'exposure_robust_se.csv'))

# Estimation panels (for dependent-variable means over the estimation sample)
EST       = os.path.join(ROOT, 'data', 'estimation')
panel_ex  = pd.read_csv(os.path.join(EST, 'executive_margin_design.csv'))
panel_leg = pd.read_csv(os.path.join(EST, 'legislative_design.csv'))
TREAT = 'delta_log1p_competition_lawsuits_2024_2020'
INSTR = 'bartik_iv_2020_2024'

def dvmean(panel, outcome, extra=None):
    """Mean of the dependent variable over the estimation sample (non-missing
    treatment, instrument, and outcome). `extra` is an optional boolean mask
    (e.g. open-seat subsample) aligned to `panel`."""
    m = panel[TREAT].notna() & panel[INSTR].notna() & panel[outcome].notna()
    if extra is not None:
        m = m & extra
    return panel.loc[m, outcome].mean()

# Headline = ANCOVA on the 2016 pre-window baseline (Y_2024 ~ D + Y_2016 + X),
# so the dependent variable the coefficient acts on is the 2024 LEVEL, not the
# 2024-2020 change. Map each delta outcome to its 2024 level column so the
# reported dep-var mean matches the R tables (which report the 2024-level mean).
# Outcomes with no 2016 analog (extensive shares, entrant typology) keep the
# first-difference LHS and fall through to the delta mean.
ANCOVA_LEVEL = {
    'delta_margin_top1_top2_2024_2020':              'margin_top1_top2_2024',
    'delta_winner_vote_share_2024_2020':             'winner_vote_share_2024',
    'delta_runnerup_vote_share_2024_2020':           'runnerup_vote_share_2024',
    'delta_winner_majority_2024_2020':               'winner_majority_2024',
    'delta_log1p_n_candidates_with_votes_2024_2020': 'log1p_n_candidates_with_votes_2024',
    'delta_female_vote_share_2024_2020':             'female_vote_share_2024',
    'delta_nonwhite_vote_share_2024_2020':           'nonwhite_vote_share_2024',
    'delta_winner_is_female_2024_2020':              'winner_is_female_2024',
    'delta_blank_rate_2024_2020':                    'blank_rate_2024',
    'delta_null_rate_2024_2020':                     'null_rate_2024',
    'delta_turnout_rate_2024_2020':                  'turnout_rate_2024',
    'delta_valid_vote_rate_2024_2020':               'valid_vote_rate_2024',
    'delta_blank_rate_vereador_2024_2020':           'blank_rate_vereador_2024',
    'delta_null_rate_vereador_2024_2020':            'null_rate_vereador_2024',
    'delta_valid_vote_rate_vereador_2024_2020':      'valid_vote_rate_vereador_2024',
}

def repmean(panel, outcome, extra=None):
    """Dep-var mean to REPORT under the headline spec: the 2024-level mean for
    ANCOVA outcomes (matching the R tables), the delta mean otherwise."""
    lvl = ANCOVA_LEVEL.get(outcome)
    if lvl is not None and lvl in panel.columns:
        m = panel[TREAT].notna() & panel[INSTR].notna() & panel[lvl].notna()
        if extra is not None:
            m = m & extra
        return panel.loc[m, lvl].mean()
    return dvmean(panel, outcome, extra=extra)

# ── Helper: pull one row from IV results ──────────────────────────────────────
def get_iv(spec, outcome, variant='adversarial'):
    row = iv.loc[(iv['spec'] == spec) & (iv['outcome'] == outcome) &
                 (iv['variant'] == variant)]
    assert len(row) == 1, f'Expected 1 row for {spec}/{outcome}, got {len(row)}'
    return row.iloc[0]

def get_fs(spec, variant='adversarial'):
    row = fs.loc[(fs['spec'] == spec) & (fs['variant'] == variant)]
    assert len(row) == 1, f'Expected 1 fs row for {spec}, got {len(row)}'
    return row.iloc[0]

def get_leg(spec, outcome):
    row = leg.loc[(leg['spec'] == spec) & (leg['outcome'] == outcome)]
    assert len(row) == 1, f'Expected 1 leg row for {spec}/{outcome}, got {len(row)}'
    return row.iloc[0]

def get_er(outcome, spec='baseline', variant='adversarial'):
    row = er.loc[(er['outcome'] == outcome) & (er['spec'] == spec) &
                 (er['variant'] == variant)]
    assert len(row) == 1, f'Expected 1 er row for {outcome}, got {len(row)}'
    return row.iloc[0]

# ── Extract values ─────────────────────────────────────────────────────────────

# Descriptive — lawsuits
l20 = ovl.loc[ovl['election_year'] == 2020].iloc[0]
l24 = ovl.loc[ovl['election_year'] == 2024].iloc[0]

# Descriptive — voters
v20 = ovv.loc[ovv['election_year'] == 2020].iloc[0]
v24 = ovv.loc[ovv['election_year'] == 2024].iloc[0]

# Descriptive — candidates (executive only)
ce20 = ovc.loc[(ovc['election_year'] == 2020) & (ovc['office_group'] == 'executive')].iloc[0]
ce24 = ovc.loc[(ovc['election_year'] == 2024) & (ovc['office_group'] == 'executive')].iloc[0]
cl20 = ovc.loc[(ovc['election_year'] == 2020) & (ovc['office_group'] == 'legislative')].iloc[0]
cl24 = ovc.loc[(ovc['election_year'] == 2024) & (ovc['office_group'] == 'legislative')].iloc[0]

# First stage — baseline
fs_base = get_fs('baseline')

# First stage — subgroups
fs_open = get_fs('open_seat')
fs_cont = get_fs('contested_seat')

# IV — voter behavior
r_blank   = get_iv('baseline', 'delta_blank_rate_2024_2020')
r_turnout = get_iv('baseline', 'delta_turnout_rate_2024_2020')
r_null    = get_iv('baseline', 'delta_null_rate_2024_2020')
r_valid   = get_iv('baseline', 'delta_valid_vote_rate_2024_2020')
# council (vereador) ballot composition — same spec, other ballot
r_blank_v = get_iv('baseline', 'delta_blank_rate_vereador_2024_2020')
r_null_v  = get_iv('baseline', 'delta_null_rate_vereador_2024_2020')
r_valid_v = get_iv('baseline', 'delta_valid_vote_rate_vereador_2024_2020')

# IV — competition
r_cand    = get_iv('baseline', 'delta_log1p_n_candidates_with_votes_2024_2020')
r_margin  = get_iv('baseline', 'delta_margin_top1_top2_2024_2020')
r_ruup    = get_iv('baseline', 'delta_runnerup_vote_share_2024_2020')
r_wmaj    = get_iv('baseline', 'delta_winner_majority_2024_2020')
r_wshare  = get_iv('baseline', 'delta_winner_vote_share_2024_2020')

# IV — open seat heterogeneity (blank rate)
r_blank_open = get_iv('open_seat',     'delta_blank_rate_2024_2020')
r_blank_cont = get_iv('contested_seat','delta_blank_rate_2024_2020')

# IV — composition: female
r_female_vs   = get_iv('baseline', 'delta_female_vote_share_2024_2020')
r_female_win  = get_iv('baseline', 'delta_winner_is_female_2024_2020')
r_female_cand = get_iv('baseline', 'delta_female_share_2024_2020')

# Legislative
r_leg_cand = get_leg('baseline', 'delta_log1p_total_candidates_2024_2020')

# Exposure-robust
er_blank = get_er('delta_blank_rate_2024_2020')
t_bhj    = er_blank['tau_2sls'] / er_blank['se_bhj']
ratio_bhj = er_blank['se_bhj'] / er_blank['se_conventional']

# ── Build macro dict ───────────────────────────────────────────────────────────
M = {}

# --- Scale ---
M['AdvLawsuitsTwenty']       = millions(l20['adversarial_lawsuits'])
M['AdvLawsuitsFortyFour']    = millions(l24['adversarial_lawsuits'])
M['TotalLawsuitsTwenty']     = millions(l20['total_lawsuits'])
M['NMunisExposedTwenty']     = big(l20['n_munis_adversarial'])
M['ShareMunisExposedTwenty'] = pct1(l20['share_munis_exposed_pct'])
M['AdvPerCandidateTwenty']   = f1(l20['adv_lawsuits_per_candidate'])
M['AdvPerCandidateFortyFour']= f1(l24['adv_lawsuits_per_candidate'])
M['VotersPerAdvTwenty']      = big(l20['registered_voters_per_adv'])
M['VotersPerAdvFortyFour']   = big(l24['registered_voters_per_adv'])

M['RegisteredVotersTwenty']  = millions(v20['registered_voters'])
M['RegisteredVotersFortyFour']= millions(v24['registered_voters'])
M['TurnoutRateTwenty']       = pct1(v20['turnout_rate_pct'])
M['TurnoutRateFortyFour']    = pct1(v24['turnout_rate_pct'])
M['BlankRateTwenty']         = pct1(v20['blank_rate_pct'])
M['BlankRateFortyFour']      = pct1(v24['blank_rate_pct'])
M['BlankVotesTwenty']        = millions(v20['blank_votes'])

M['ExecCandsTwenty']         = big(ce20['total_candidates'])
M['ExecCandsFortyFour']      = big(ce24['total_candidates'])
M['LegCandsTwenty']          = big(cl20['total_candidates'])
M['LegCandsFortyFour']       = big(cl24['total_candidates'])
M['FemaleShareExecTwenty']   = pct1(ce20['female_share_pct'])
M['FemaleShareExecFortyFour']= pct1(ce24['female_share_pct'])

# --- First stage ---
M['NMunis']      = big(int(fs_base['nobs']))
M['NZones']      = big(int(fs_base['n_clusters']))
M['FSCoef']      = f'{fs_base["coef"]:.3f}'
M['FSSE']        = f'{fs_base["se"]:.3f}'
M['FSF']         = f1(fs_base['first_stage_F'])
M['tFcv']        = f'{fs_base["tF_cv"]:.2f}'
M['OpenSeatF']   = f1(fs_open['first_stage_F'])
M['OpenSeattFcv']= f'{fs_open["tF_cv"]:.2f}'
M['ContF']       = f1(fs_cont['first_stage_F'])
M['OpenN']       = big(int(fs_open['nobs']))
M['ContN']       = big(int(fs_cont['nobs']))
M['OpenShare']   = pct1(100 * int(fs_open['nobs']) / int(fs_base['nobs']))

# --- Voter behavior (baseline) ---
M['BlankCoef']   = coef(r_blank['coef'])
M['BlankSE']     = se_par(r_blank['se'])
M['BlankP']      = pval(r_blank['p'])
M['BlankTF']     = tick_cross(r_blank['reject_tF_5pct'])
M['BlankT']      = f2(abs(r_blank['t']))

M['TurnoutCoef'] = coef(r_turnout['coef'])
M['TurnoutSE']   = se_par(r_turnout['se'])
M['TurnoutP']    = pval(r_turnout['p'])
M['TurnoutTF']   = tick_cross(r_turnout['reject_tF_5pct'])

M['NullCoef']    = coef(r_null['coef'])
M['NullSE']      = se_par(r_null['se'])
M['NullP']       = pval(r_null['p'])
M['NullTF']      = tick_cross(r_null['reject_tF_5pct'])

M['ValidCoef']   = coef(r_valid['coef'])
M['ValidSE']     = se_par(r_valid['se'])
M['ValidP']      = pval(r_valid['p'])

# council ballot
M['BlankVerCoef'] = coef(r_blank_v['coef']); M['BlankVerSE'] = se_par(r_blank_v['se']); M['BlankVerP'] = pval(r_blank_v['p'])
M['NullVerCoef']  = coef(r_null_v['coef']);  M['NullVerSE']  = se_par(r_null_v['se']);  M['NullVerP']  = pval(r_null_v['p'])
M['ValidVerCoef'] = coef(r_valid_v['coef']); M['ValidVerSE'] = se_par(r_valid_v['se']); M['ValidVerP'] = pval(r_valid_v['p'])

# --- Competition (baseline) ---
M['CandExecCoef']  = coef(r_cand['coef'])
M['CandExecSE']    = se_par(r_cand['se'])
M['CandExecP']     = pval(r_cand['p'])
M['CandExecTF']    = tick_cross(r_cand['reject_tF_5pct'])
M['CandExecPct']   = f1(abs(r_cand['coef']) * 100)  # pct interpretation

M['MarginCoef']    = coef(r_margin['coef'])
M['MarginSE']      = se_par(r_margin['se'])
M['MarginP']       = pval(r_margin['p'])
M['MarginTF']      = tick_cross(r_margin['reject_tF_5pct'])

M['RunnerUpCoef']  = coef(r_ruup['coef'])
M['RunnerUpSE']    = se_par(r_ruup['se'])
M['RunnerUpP']     = pval(r_ruup['p'])
M['RunnerUpTF']    = tick_cross(r_ruup['reject_tF_5pct'])

M['WinMajCoef']    = coef(r_wmaj['coef'])
M['WinMajSE']      = se_par(r_wmaj['se'])
M['WinMajP']       = pval(r_wmaj['p'])
M['WinMajTF']      = tick_cross(r_wmaj['reject_tF_5pct'])

M['WinShareCoef']  = coef(r_wshare['coef'])
M['WinShareSE']    = se_par(r_wshare['se'])
M['WinShareP']     = pval(r_wshare['p'])

# --- Female (baseline) ---
M['FemaleVSCoef']  = coef(r_female_vs['coef'])
M['FemaleVSSE']    = se_par(r_female_vs['se'])
M['FemaleVSP']     = pval(r_female_vs['p'])
M['FemaleVSTF']    = tick_cross(r_female_vs['reject_tF_5pct'])

M['FemaleWinCoef'] = coef(r_female_win['coef'])
M['FemaleWinSE']   = se_par(r_female_win['se'])
M['FemaleWinP']    = pval(r_female_win['p'])
M['FemaleWinTF']   = tick_cross(r_female_win['reject_tF_5pct'])

M['FemaleCandCoef'] = coef(r_female_cand['coef'])
M['FemaleCandSE']   = se_par(r_female_cand['se'])
M['FemaleCandP']    = pval(r_female_cand['p'])
M['FemaleCandTF']   = tick_cross(r_female_cand['reject_tF_5pct'])

# --- Open seat heterogeneity ---
M['OpenBlankCoef'] = coef(r_blank_open['coef'])
M['OpenBlankSE']   = se_par(r_blank_open['se'])
M['OpenBlankP']    = pval(r_blank_open['p'])
M['OpenBlankTF']   = tick_cross(r_blank_open['reject_tF_5pct'])

M['ContBlankCoef'] = coef(r_blank_cont['coef'])
M['ContBlankSE']   = se_par(r_blank_cont['se'])
M['ContBlankP']    = pval(r_blank_cont['p'])
M['ContBlankTF']   = tick_cross(r_blank_cont['reject_tF_5pct'])

# --- Legislative ---
M['LegCandCoef']   = coef(r_leg_cand['coef'])
M['LegCandSE']     = se_par(r_leg_cand['se'])
M['LegCandP']      = pval(r_leg_cand['p'])
M['LegCandPct']    = f1(abs(r_leg_cand['coef']) * 100)

# --- BHJ/AKM ---
M['KeffRotemberg'] = f1(er_blank['K_eff_rotemberg'])
M['BlankSEbhj']    = f'{er_blank["se_bhj"]:.3f}'
M['BlanktBHJ']     = f'{abs(t_bhj):.2f}'
M['BlankRatioBHJ'] = f'{ratio_bhj:.1f}'

# --- Magnitude ---
blank_rate_base = v20['blank_rate_pct'] / 100   # convert pct to rate (e.g. 0.034)
M['BlankRelEffect'] = f1(100 * r_blank['coef'] / blank_rate_base)  # % relative increase

# --- Percentage-point versions (share outcomes; unsigned, prose carries direction) ---
# A share coefficient of 0.01 = 1 percentage point. abs() so prose says
# "rises/falls by X.X percentage points" without a redundant +/- in the number.
M['BlankCoefPP']    = f1(abs(r_blank['coef'])      * 100)
M['ValidCoefPP']    = f1(abs(r_valid['coef'])      * 100)
M['TurnoutCoefPP']  = f1(abs(r_turnout['coef'])    * 100)
M['NullCoefPP']     = f1(abs(r_null['coef'])       * 100)
M['FemaleVSCoefPP'] = f1(abs(r_female_vs['coef'])   * 100)
M['FemaleWinCoefPP']= f1(abs(r_female_win['coef'])  * 100)
M['FemaleCandCoefPP']= f1(abs(r_female_cand['coef']) * 100)
M['OpenBlankCoefPP']= f1(abs(r_blank_open['coef']) * 100)
M['ContBlankCoefPP']= f1(abs(r_blank_cont['coef']) * 100)

# --- Per-1-SD-of-judicialization interpretation -------------------------------
# The treatment is D = Delta log(1 + adversarial lawsuits). To make magnitudes
# legible on the slides we report the effect of a ONE-STANDARD-DEVIATION increase
# in D over the estimation sample, rather than per raw log-unit. The IV slope tau
# is the effect per unit of D, so the per-SD effect is tau * SD(D).
#   * SD(D) is taken on the same non-missing (treatment, instrument) sample.
#   * Because D is a log change, a +1 SD move means lawsuits multiply by exp(SD):
#     TreatSDPct = (exp(SD) - 1) * 100  (percent more adversarial lawsuits).
#   * Share outcomes -> per-SD effect in percentage points: tau * SD * 100.
#   * Log-count outcomes -> per-SD effect as a percent: (exp(tau*SD) - 1) * 100.
dmask    = panel_ex[TREAT].notna() & panel_ex[INSTR].notna()
TREAT_SD = panel_ex.loc[dmask, TREAT].std()
M['TreatSD']     = f'{TREAT_SD:.3f}'
M['TreatSDPct']  = pct1(100 * (math.exp(TREAT_SD) - 1))   # % more lawsuits at +1 SD
M['TreatSDMult'] = f'{math.exp(TREAT_SD):.1f}'            # lawsuits multiply by ~x

def per_sd_pp(c):
    """Share outcome: effect of +1 SD in D, in percentage points (unsigned)."""
    return f1(abs(c) * TREAT_SD * 100)

def per_sd_pp_signed(c):
    return f'{c * TREAT_SD * 100:+.1f}'

def per_sd_pct_signed(c):
    """Log outcome: effect of +1 SD in D as a percent change (signed)."""
    return f'{(math.exp(c * TREAT_SD) - 1) * 100:+.1f}'

# Share-scale outcomes (coefficient in share units; x100 = pp).
_PERSD_SHARE = {
    'Blank': r_blank, 'Null': r_null, 'Valid': r_valid, 'Turnout': r_turnout,
    'Margin': r_margin, 'RunnerUp': r_ruup, 'WinMaj': r_wmaj, 'WinShare': r_wshare,
    'FemaleVS': r_female_vs, 'FemaleWin': r_female_win, 'FemaleCand': r_female_cand,
    'OpenBlank': r_blank_open, 'ContBlank': r_blank_cont,
    'BlankVer': r_blank_v, 'NullVer': r_null_v, 'ValidVer': r_valid_v,
}
for tag, r in _PERSD_SHARE.items():
    M[f'{tag}PerSD']       = per_sd_pp(r['coef'])
    M[f'{tag}PerSDSigned'] = per_sd_pp_signed(r['coef'])

# Log-count outcomes (proportional change).
for tag, r in (('CandExec', r_cand), ('LegCand', r_leg_cand)):
    M[f'{tag}PerSDPct']       = f1(abs((math.exp(r['coef'] * TREAT_SD) - 1) * 100))
    M[f'{tag}PerSDPctSigned'] = per_sd_pct_signed(r['coef'])

# --- Dependent-variable means (over estimation sample) ---
def m3(x):
    """Mean, signed, 3 dp."""
    return f'{x:.3f}'

open_mask = panel_ex['open_seat_2024'] == 1
cont_mask = panel_ex['open_seat_2024'] == 0
# Under the ANCOVA-2016 headline these report the 2024-LEVEL mean (the LHS the
# coefficient acts on); outcomes with no 2016 analog fall back to the delta mean.
M['BlankMean']     = m3(repmean(panel_ex,  'delta_blank_rate_2024_2020'))
M['ValidMean']     = m3(repmean(panel_ex,  'delta_valid_vote_rate_2024_2020'))
M['TurnoutMean']   = m3(repmean(panel_ex,  'delta_turnout_rate_2024_2020'))
M['NullMean']      = m3(repmean(panel_ex,  'delta_null_rate_2024_2020'))
M['BlankVerMean']  = m3(repmean(panel_ex,  'delta_blank_rate_vereador_2024_2020'))
M['NullVerMean']   = m3(repmean(panel_ex,  'delta_null_rate_vereador_2024_2020'))
M['ValidVerMean']  = m3(repmean(panel_ex,  'delta_valid_vote_rate_vereador_2024_2020'))
M['CandExecMean']  = m3(repmean(panel_ex,  'delta_log1p_n_candidates_with_votes_2024_2020'))
M['MarginMean']    = m3(repmean(panel_ex,  'delta_margin_top1_top2_2024_2020'))
M['RunnerUpMean']  = m3(repmean(panel_ex,  'delta_runnerup_vote_share_2024_2020'))
M['WinMajMean']    = m3(repmean(panel_ex,  'delta_winner_majority_2024_2020'))
M['FemaleVSMean']  = m3(repmean(panel_ex,  'delta_female_vote_share_2024_2020'))
M['FemaleWinMean'] = m3(repmean(panel_ex,  'delta_winner_is_female_2024_2020'))
M['FemaleCandMean']= m3(dvmean(panel_ex,  'delta_female_share_2024_2020'))
M['LegCandMean']   = m3(dvmean(panel_leg, 'delta_log1p_total_candidates_2024_2020'))
M['OpenBlankMean'] = m3(repmean(panel_ex,  'delta_blank_rate_2024_2020', extra=open_mask))
M['ContBlankMean'] = m3(repmean(panel_ex,  'delta_blank_rate_2024_2020', extra=cont_mask))

# ── Instrument-construction descriptives (subject-level design) ───────────────
# These replace the numbers that the deleted family-rework generators used to
# emit. Everything here is sourced from the committed subject-level pipeline.
shiftd = pd.read_csv(os.path.join(DESC, 'shift_descriptives.csv'))
N_SUBJECTS_KEPT = shiftd['subject_code'].nunique()

# Scale of filtering: total vs kept (adversarial) caseload, pooled 2020+2024.
tot_all = ovl['total_lawsuits'].sum()
tot_adv = ovl['adversarial_lawsuits'].sum()
M['NSubjectsKept']        = big(N_SUBJECTS_KEPT)
M['TotalAllLawsuits']     = millions(tot_all)
M['KeptAdversarialLawsuits'] = big(tot_adv)
M['KeptAdversarialPct']   = pct1(100 * tot_adv / tot_all)
M['DroppedNonAdvPct']     = pct1(100 * (1 - tot_adv / tot_all))

# Instrument distribution: raw mean and SD after residualising on state FE
# (within-state demean == residual on state dummies).
zname = INSTR
zraw  = panel_ex[zname]
zres  = zraw - panel_ex.groupby('cluster_id')[zname].transform('mean')
M['BartikZMeanRaw']  = f'{zraw.mean():.3f}'
M['BartikZSDResid']  = f'{zres.std():.3f}'

# Sample universe / unit-of-treatment counts (committed estimation panel).
n_munis_uni   = panel_ex['municipality_id_tse'].nunique()
n_zones_uni   = panel_ex['principal_zone_id'].nunique()
n_states_uni  = panel_ex['cluster_id'].nunique()
M['NMunisUniverse']  = big(n_munis_uni)
M['NZonesUniverse']  = big(n_zones_uni)
M['NStatesUniverse'] = big(n_states_uni)
M['AvgMunisPerZone'] = f1(n_munis_uni / n_zones_uni)
M['NClusters']       = big(int(fs_base['n_clusters']))

# Zone-size distribution: how many municipalities share an electoral zone.
zsize = panel_ex.groupby('principal_zone_id')['municipality_id_tse'].nunique()
nz = len(zsize)
b1  = (zsize == 1).sum()
b2  = (zsize == 2).sum()
b35 = ((zsize >= 3) & (zsize <= 5)).sum()
b6  = (zsize >= 6).sum()
M['ZoneDistOneN'], M['ZoneDistOnePct']         = big(b1),  pct1(100 * b1  / nz)
M['ZoneDistTwoN'], M['ZoneDistTwoPct']         = big(b2),  pct1(100 * b2  / nz)
M['ZoneDistThreeFiveN'], M['ZoneDistThreeFivePct'] = big(b35), pct1(100 * b35 / nz)
M['ZoneDistSixN'], M['ZoneDistSixPct']         = big(b6),  pct1(100 * b6  / nz)

# Aliases so legacy macro names in the report resolve to the canonical numbers.
M['HeadlineF']  = M['FSF']
M['NMunisFS']   = M['NMunis']

# --- Disaggregated turnout (facultative vs compulsory; education gradient) ----
DISAGG = {
    'Facultative': 'delta_facultative_turnout_2024_2020',
    'Compulsory':  'delta_compulsory_turnout_2024_2020',
    'LowEd':       'delta_low_ed_turnout_2024_2020',
    'HighEd':      'delta_high_ed_turnout_2024_2020',
    'Analfabeto':  'delta_analfabeto_turnout_2024_2020',
    'EduGap':      'delta_education_turnout_gap_2024_2020',
    'SexGap':      'delta_sex_turnout_gap_2024_2020',
}
for tag, outcome in DISAGG.items():
    try:
        r = get_iv('baseline', outcome)
    except AssertionError:
        continue
    M[f'{tag}Coef'] = coef(r['coef'])
    M[f'{tag}SE']   = se_par(r['se'])
    M[f'{tag}P']    = pval(r['p'])
    M[f'{tag}TF']   = tick_cross(r['reject_tF_5pct'])
    M[f'{tag}Mean'] = m3(dvmean(panel_ex, outcome))
    M[f'{tag}PerSD']       = per_sd_pp(r['coef'])
    M[f'{tag}PerSDSigned'] = per_sd_pp_signed(r['coef'])

# ── BHJ robustness: AR wild-cluster bootstrap + non-adversarial placebo ───────
# Few-cluster (G=26), weak-IV-robust inference for the headline margin outcome,
# and the discriminant-validity placebo (excluded mandatory/admin filings).
HEADLINE_Y = 'delta_margin_top1_top2_2024_2020'
try:
    ar = pd.read_csv(os.path.join(REG, 'wild_bootstrap_ar.csv'))
    arm = ar.loc[ar['outcome'] == HEADLINE_Y].iloc[0]
    M['ARMarginP']     = f"{arm['ar_wcr_p_at0']:.3f}"
    M['ARMarginCILo']  = f"{arm['ar_wcr_ci_lo']:+.3f}"
    M['ARMarginCIHi']  = f"{arm['ar_wcr_ci_hi']:+.3f}"
    M['ARMarginCI']    = f"[{arm['ar_wcr_ci_lo']:+.3f}, {arm['ar_wcr_ci_hi']:+.3f}]"
    M['ARNClusters']   = big(int(arm['n_clusters']))
    # Across all focus outcomes: do ANY AR 95% CIs exclude zero?
    M['ARAnyExcludeZero'] = r'\tick' if bool(ar['ci_excludes_0'].any()) else r'\cross'
    # Same AR-WCR objects for the other headline outcomes so the slides can cite
    # the weak-IV-robust p-value / CI directly (every number from a macro).
    for tag, oc in (('ARRunnerUp', 'delta_runnerup_vote_share_2024_2020'),
                    ('ARBlank',    'delta_blank_rate_2024_2020'),
                    ('ARTurnout',  'delta_turnout_rate_2024_2020'),
                    ('ARFemaleVS', 'delta_female_vote_share_2024_2020'),
                    ('ARWinMaj',   'delta_winner_majority_2024_2020')):
        row = ar.loc[ar['outcome'] == oc]
        if row.empty:
            continue
        row = row.iloc[0]
        M[f'{tag}P']  = f"{row['ar_wcr_p_at0']:.3f}"
        M[f'{tag}CI'] = f"[{row['ar_wcr_ci_lo']:+.3f}, {row['ar_wcr_ci_hi']:+.3f}]"
except (FileNotFoundError, IndexError):
    pass

try:
    plc = pd.read_csv(os.path.join(REG, 'nonadversarial_placebo.csv'))
    pm = plc.loc[plc['outcome'] == HEADLINE_Y].iloc[0]
    # Main coef and the same coef conditioning on the placebo Bartik / intensity.
    M['PlaceboMainCoef']   = coef(pm['main_coef'])
    M['PlaceboIntensCoef'] = coef(pm['intensity_coef'])
    M['PlaceboCtrlCoef']   = coef(pm['placebo_ctrl_coef'])
    # Placebo reduced-form coefficient (should be a null) on the headline outcome.
    M['PlaceboRFCoef']     = coef(pm['placebo_rf_coef'])
    M['PlaceboRFSE']       = se_par(pm['placebo_rf_se'])
    M['PlaceboRelevanceF'] = f1(pm['placebo_first_stage_F'])
except (FileNotFoundError, IndexError, KeyError):
    pass

# ── Write abstract_macros.tex ─────────────────────────────────────────────────
macros_path = os.path.join(TEX, 'abstract_macros.tex')
with open(macros_path, 'w', encoding='utf-8') as f:
    f.write('% abstract_macros.tex — auto-generated by 12_abstract_numbers.py\n')
    f.write('% DO NOT EDIT MANUALLY.\n\n')
    for name, val in M.items():
        # escape % in values
        safe = str(val).replace('%', r'\%')
        f.write(f'\\providecommand{{\\{name}}}{{{safe}}}\n')
        f.write(f'\\renewcommand{{\\{name}}}{{{safe}}}\n')

print(f'Wrote {len(M)} macros to {macros_path}')

# ── Write abstract_table.tex ──────────────────────────────────────────────────
def row(label, c, s, p, mean, bold=False):
    """Build one table row."""
    cv = f'\\textbf{{{c}}}' if bold else c
    sv = f'\\textbf{{{s}}}' if bold else s
    pv = f'\\textbf{{{p}}}' if bold else p
    mv = f'\\textbf{{{mean}}}' if bold else mean
    return f'  {label} & {cv} & {sv} & {pv} & {mv} \\\\\n'

table_path = os.path.join(TEX, 'abstract_table.tex')
with open(table_path, 'w', encoding='utf-8') as f:
    f.write('% abstract_table.tex — auto-generated by 12_abstract_numbers.py\n')
    f.write('% DO NOT EDIT MANUALLY.\n\n')

    f.write('\\begin{tabular}{lrrrr}\n')
    f.write('  \\toprule\n')
    f.write('  Outcome & Coef. & SE & $p$ & Dep.\\ mean \\\\\n')
    f.write('  \\midrule\n')

    # Panel A — ANCOVA-2016: LHS is the 2024 level (2016 level conditioned on),
    # so no "Delta" prefix; the two FD-only rows in Panel B keep the prefix.
    f.write('  \\multicolumn{5}{l}{\\textit{Panel A: Voter Behavior}} \\\\\n')
    f.write(row('\\quad Turnout (any ballot)',
                M['TurnoutCoef'], M['TurnoutSE'], M['TurnoutP'], M['TurnoutMean']))
    f.write(row('\\quad Blank rate (mayoral)',
                M['BlankCoef'], M['BlankSE'], M['BlankP'], M['BlankMean']))
    f.write(row('\\quad Null rate (mayoral)',
                M['NullCoef'], M['NullSE'], M['NullP'], M['NullMean']))
    f.write(row('\\quad Valid rate (mayoral)',
                M['ValidCoef'], M['ValidSE'], M['ValidP'], M['ValidMean']))
    f.write(row('\\quad Blank rate (council)',
                M['BlankVerCoef'], M['BlankVerSE'], M['BlankVerP'], M['BlankVerMean']))
    f.write(row('\\quad Null rate (council)',
                M['NullVerCoef'], M['NullVerSE'], M['NullVerP'], M['NullVerMean']))
    f.write(row('\\quad Valid rate (council)',
                M['ValidVerCoef'], M['ValidVerSE'], M['ValidVerP'], M['ValidVerMean']))
    f.write('  \\midrule\n')

    # Panel B — candidate performance (competition + gender composition).
    # "$\\Delta$" marks the two first-difference rows (no clean 2016 analog);
    # the rest are ANCOVA-2016 on the 2024 level.
    f.write('  \\multicolumn{5}{l}{\\textit{Panel B: Candidate Performance}} \\\\\n')
    f.write(row('\\quad Log candidates (exec.)',
                M['CandExecCoef'], M['CandExecSE'], M['CandExecP'], M['CandExecMean']))
    f.write(row('\\quad $\\Delta$ Log candidates (leg.)',
                M['LegCandCoef'], M['LegCandSE'], M['LegCandP'], M['LegCandMean']))
    f.write(row('\\quad Margin (W$-$RU)',
                M['MarginCoef'], M['MarginSE'], M['MarginP'], M['MarginMean']))
    f.write(row('\\quad Runner-up vote share',
                M['RunnerUpCoef'], M['RunnerUpSE'], M['RunnerUpP'], M['RunnerUpMean']))
    f.write(row('\\quad Winner majority',
                M['WinMajCoef'], M['WinMajSE'], M['WinMajP'], M['WinMajMean']))
    f.write(row('\\quad $\\Delta$ Female candidate share',
                M['FemaleCandCoef'], M['FemaleCandSE'], M['FemaleCandP'], M['FemaleCandMean']))
    f.write(row('\\quad Female vote share',
                M['FemaleVSCoef'], M['FemaleVSSE'], M['FemaleVSP'], M['FemaleVSMean']))
    f.write(row('\\quad Winner is female',
                M['FemaleWinCoef'], M['FemaleWinSE'], M['FemaleWinP'], M['FemaleWinMean']))
    f.write('  \\midrule\n')

    # Panel C — heterogeneity (open vs contested seats)
    f.write('  \\multicolumn{5}{l}{\\textit{Panel C: Heterogeneity --- Blank Rate (2024)}} \\\\\n')
    f.write(row(f'\\quad Open seat ($N={M["OpenN"]}$)',
                M['OpenBlankCoef'], M['OpenBlankSE'], M['OpenBlankP'], M['OpenBlankMean']))
    f.write(row(f'\\quad Contested ($N={M["ContN"]}$)',
                M['ContBlankCoef'], M['ContBlankSE'], M['ContBlankP'], M['ContBlankMean']))
    f.write('  \\bottomrule\n')
    f.write('\\end{tabular}\n')

    # Notes
    f.write('\\par\\vspace{4pt}\n')
    f.write('\\begin{minipage}{0.97\\linewidth}\n')
    f.write('\\footnotesize\n')
    f.write(f'\\textit{{Notes:}} Headline estimator: ANCOVA on the 2016 pre-window baseline, $Y_{{2024}} \\sim D + Y_{{2016}} + X$ (state FE + pre-determined controls), 2SLS with the Bartik instrument. The 2016 level enters as a free lag, so the dependent variable is the 2024 level and ``Dep.\\ mean\'\' is its 2024-level mean. Rows marked $\\Delta$ have no clean 2016 analog and are estimated in first differences. ')
    f.write(f'First-stage $F={M["FSF"]}$, $N={M["NMunis"]}$, ')
    f.write(f'{M["NClusters"]} clusters (states). SE clustered by state (UF). ')
    f.write(f'Panel~C open-seat sub-sample first-stage $F={M["OpenSeatF"]}$.\n')
    f.write('\\end{minipage}\n')

print(f'Wrote table to {table_path}')
print('\nKey numbers:')
for k in ['NMunis','NZones','FSF','tFcv','BlankCoef','BlankP','CandExecCoef','CandExecP',
          'OpenBlankCoef','OpenBlankP','LegCandCoef','LegCandP','KeffRotemberg','BlanktBHJ']:
    print(f'  \\{k} = {M[k]}')
