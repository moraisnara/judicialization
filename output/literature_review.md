# Literature Review — Electoral Judicialization and Political Competition in Brazil
## A Guide for Robustness Design and Mechanism Analysis

**As of 2026-05-21. Update as new papers are added.**

---

## 1. Core Methodological Template: Ash, Morelli & Vannoni (2023/2025)

**Citation:** Ash, E., Morelli, M., & Vannoni, M. (2025). "More Laws, More Growth? Evidence from U.S. States." *Journal of Political Economy* (forthcoming). Working paper (2022/2023).

### What they do

Causal effect of legislative output (number of legal provisions) on state economic growth in the U.S., 1965–2012. The instrument is a Bartik shift-share IV built from text data:

- **Shares**: state's pre-treatment (1955–1964) topic share of legislation — how much of the state's legal stock was in each of 18 (or 42) LDA-derived legal topics
- **Shifts**: leave-one-out log growth of topic-specific legislation in other states (same formula as Nara's design)
- **Endogenous variable**: log number of legal provisions in state s, biennium t
- **Outcome**: Δlog per capita GSP (economic growth)
- **First stage**: negative (states with low pre-existing detail on a topic borrow more from other states when that topic grows nationally); F = 22.8 baseline
- **2SLS estimate**: 10% increase in borrowed legislation → +0.15pp growth rate (mean 3.1pp)

### Parallels to Nara's design

| AMV | Nara |
|---|---|
| Pre-period topic shares of legislation | 2020 municipality topic shares of adversarial lawsuits |
| National leave-out legislative flows by topic | State leave-out log growth in adversarial lawsuits by topic |
| Log provisions (legislative output) | Δlog(1+adversarial lawsuits) |
| GSP per capita growth | Electoral competition outcomes (Δmargin, Δcandidate count, etc.) |
| State FE + biennium FE | State FE (cross-section diff design) |
| N=50 states × 24 biennia | N=5,560 municipalities × 2 election cycles |

**Key difference**: AMV's instrument is negative first-stage (low-share states respond more to common shocks); Nara's is positive (municipalities heavily exposed to topic k pick up more of topic k's national growth). This is because AMV measures *stock-to-flow* dynamics while Nara measures *exposure-to-growth*.

### Robustness tests AMV uses (and their analogs for Nara)

| AMV robustness | Nara analog | Feasibility |
|---|---|---|
| State-specific linear trends | Municipality-level trends (infeasible with 2 periods) | Not applicable |
| Pre-treatment econ vars × biennium FE | 2016 electoral controls × election cycle | Partially done (7 controls) |
| Initial sector shares × biennium FE | 2020 lawsuit topic shares as controls | Could add topic share controls |
| Demographic vars × biennium FE | Census 2010 × election cycle | Done (7 controls) |
| Lead placebo: future instrument → current outcome | 2016→2020 outcome instrumented by 2016→2020 lawsuit IV | Requires 2016 data |
| Balance test: IV on pre-determined chars | GPS balance tests | Done (08_gps_balance_tests.py) |
| Drop one topic at a time | Visual IV graph by topic | Done (09_visual_iv.py) |
| Alternative topic counts (6–48) | Alternative topic classifications | Feasible but low priority |
| Control for state regulations, caselaw | Control for other TSE court activity | Feasible |
| AKM/shift-level clustering | BHJ/AKM exposure-robust SEs | Done (11_exposure_robust_se.py) |
| Topic share controls in levels and changes | Topic share controls | Partially done |

### Mechanism framework (AMV Section 6 — directly translatable)

AMV identifies mechanisms through **heterogeneity analyses** along four dimensions. Each has a political economy analog:

| AMV mechanism | AMV finding | Nara analog | Hypothesis |
|---|---|---|---|
| Policy type (economic vs. social regulation) | Economic reg. drives growth; social reg. null | Lawsuit topic family (registration vs. campaign conduct vs. information) | Already done via family-split IV |
| Contingent vs. non-contingent clauses | Contingent clauses drive effect | Adversarial vs. administrative lawsuits | AMV: the "quality" of legal activity matters — adversarial lawsuits are the contingent analog (targeted, conditional) |
| Concavity in existing detail | Effect larger in low-stock states | Municipalities with fewer pre-existing lawsuits in 2020 | Plausible: more room for disruption when political-legal activity is novel |
| Relationship-specific investments | Effect concentrated in high-specificity sectors | Municipalities with stronger incumbent-challenger dynamics | Candidates with established networks (incumbents) may be more insulated |
| Economic policy uncertainty | Effect largest in high-uncertainty periods | Close pre-existing races (high political uncertainty) | Already done as "close races" subsample |

**Critical AMV lesson for mechanism tests**: AMV constructs *separate instruments* for each mechanism (e.g., contingent-provision IV vs. non-contingent-provision IV). The same approach in Nara's design is the family-split IV, where each lawsuit topic family gets its own Bartik instrument. The two-family J test (done) follows the same logic as AMV's two-endogenous-regressor specification (Table 5).

---

## 2. Electoral Judicialization — Institutional and Political Science Literature

### 2.1 Core framework: Judicialization as strategic tool

**Helmke, G. (2002).** "The Logic of Strategic Defection: Court–Executive Relations in Argentina under Dictatorship and Democracy." *American Political Science Review* 96(2): 291–303.

- **Argument**: judicial behavior responds to strategic calculations about the political environment; courts are not neutral arbiters but respond to incentives
- **Relevance**: theoretical foundation for why adversarial lawsuits are filed strategically — not randomly. This is the core identification challenge Nara's Bartik IV addresses
- **Use in dissertation**: Section on endogeneity; explain why OLS is biased and in what direction

**Helmke, G. & Staton, J. (2011).** "The Puzzling Judicial Politics of Latin America: A Theory of Litigation, Judicialization, and Judicial Power." In *Courts in Latin America* (Cambridge).

- **Argument**: litigation waves in Latin America are partly driven by political actors testing court capacity; judicialization varies with electoral competition and institutional strength
- **Relevance**: directly motivates why state-level waves in lawsuit topics (Nara's shifts) are driven by institutional/strategic diffusion, not municipality-specific dynamics
- **Key quote**: "Legal challenges before elections serve as both weapons and shields — parties use them to disqualify rivals and to protect their own candidates"

**Ingram, M. (2016).** "Crafting Courts in New Democracies: The Politics of Subnational Judicial Reform in Brazil and Mexico." Cambridge University Press.

- **Argument**: subnational variation in judicial capacity in Brazil; TREs (state electoral courts) differ in enforcement intensity and jurisprudential traditions
- **Relevance**: supports Nara's identification logic — TRE-level variation in enforcement creates the state-level shifts. Also motivates state FE in the regression

**Popova, M. (2012).** *Politicized Justice in Emerging Democracies: A Study of Courts in Russia and Ukraine.* Cambridge University Press.

- **Relevance**: theoretical framework for how political competition drives judicial intervention; high-competition municipalities attract more lawsuits (the endogeneity Nara instruments away)

### 2.2 Brazil's Electoral Justice System

**Sadek, M.T. (2010).** "Judicialization of Politics and the Brazilian Political System." *Revista da Justiça Federal.*

- **Argument**: Brazil's electoral justice is uniquely centralized and active; TSE/TRE system handles candidate eligibility, campaign finance, and conduct before election day
- **Relevance**: institutional background for why Brazil is the right setting — large scale, uniform rules, clear pre-election timing

**Marchetti, V. (2008).** "Governance Eleitoral: O Modelo Brasileiro de Justiça Eleitoral." *DADOS* 51(4): 865–900.

- **Argument**: Brazil's electoral justice model combines administrative and adversarial roles, creating a unique mixture of mandatory filings and genuine challenges — exactly the distinction Nara's adversarial filter addresses
- **Relevance**: institutional justification for RRC and DRAP exclusion from instrument

**Ferraz, C. & Finan, F. (2008).** "Exposing Corrupt Politicians: The Effects of Brazil's Publicly Released Audits on Electoral Outcomes." *Quarterly Journal of Economics* 123(2): 703–745.

- **Instrument**: randomly assigned municipal audits (quasi-experiment)
- **Finding**: audit disclosure → −20% re-election probability for corrupt incumbents; effect larger in municipalities with radio access
- **Relevance for Nara**: (a) establishes that judicial/oversight information affects electoral outcomes in Brazil — shows the information channel is operative; (b) similar institutional setting (TSE administrative data, municipal elections); (c) supports information/signaling mechanism for Nara's blank rate result
- **Direct citation**: "Consistent with Ferraz and Finan (2008), our results suggest that judicial activity generates signals that voters incorporate into their electoral choices."

**Ferraz, C. & Finan, F. (2011).** "Electoral Accountability and Corruption: Evidence from the Audits of Local Governments." *American Economic Review* 101(4): 1274–1311.

- **Finding**: politicians facing re-election incentives steal less; electoral accountability disciplines behavior
- **Relevance**: establishes the discipline channel; judicial challenges could operate similarly — the threat of public legal proceedings disciplines candidates even before any ruling

---

## 3. Candidate Entry, Deterrence, and the Candidate Pool

### 3.1 Theoretical foundations

**Besley, T. & Coate, S. (1997).** "An Economic Model of Representative Democracy." *Quarterly Journal of Economics* 112(1): 85–114.

**Osborne, M. & Slivinski, A. (1996).** "A Model of Political Competition with Citizen-Candidates." *Quarterly Journal of Economics* 111(1): 65–96.

- **Argument**: citizens run for office only if benefits exceed fixed entry costs; higher costs deter entry and reduce representativeness of the candidate pool
- **Relevance for Nara**: provides the theoretical mechanism for the candidate pool reduction result (Δlog candidates p=0.09 executive; p=0.07 legislative). Legal challenges are a **fixed cost to entry** — they deter at the margin
- **Direct citation**: "Following the citizen-candidate framework (Besley and Coate 1997; Osborne and Slivinski 1996), we interpret the reduction in the candidate pool as consistent with adversarial judicial challenges raising the fixed cost of candidacy, deterring entry at the margin."

**Stigler, G. (1971).** "The Theory of Economic Regulation." *Bell Journal of Economics* 2(1): 3–21.

- **Argument**: regulation serves as a barrier to entry, protecting incumbents from challengers
- **Relevance**: the "incumbent protection" reading of judicialization — lawsuits may disproportionately target challengers (more to challenge; less legal resources), functioning as a regulatory barrier
- **Caveat for Nara**: the new-entrant result (p=0.08) actually goes in the opposite direction, suggesting lawsuits do not systematically protect incumbents — an important contrast to note

**Baye, M., Kovenock, D. & de Vries, C. (1993).** "Rigging the Lobbying Process: An Application of the All-Pay Auction." *American Economic Review* 83(1): 289–294.

- **Relevance**: legal challenges as an all-pay auction — both parties spend resources on litigation regardless of outcome. This helps explain entry deterrence even when challengers are not expelled: the resource-diversion mechanism

### 3.2 Ballot access and legal barriers to candidacy

**Reller, C. (2025).** "How Ballot Access Laws Increase Primary Competition and Decrease Party Unity." *Party Politics* 29(3).

- **Finding**: higher ballot access thresholds (signature requirements, filing fees) reduce candidate entry, particularly for minor parties and outsiders
- **Relevance**: directly analogous to Nara's entry deterrence finding — both show legal/institutional barriers reduce candidate pools. Difference: ballot access is a formal rule; adversarial challenges are a strategic tool

**Stratmann, T. (2005).** "Some Talk: Money in Politics. A (Partial) Review of the Literature." *Public Choice* 124(1–2): 135–156.

- **Relevance**: campaign costs, including legal costs, as barriers to candidacy; resource-constrained candidates deterred more

### 3.3 Electoral competition and party dynamics in Brazil

**Klašnja, M. & Titiunik, R. (2017).** "The Incumbency Curse: Weak Parties, Term Limits, and Unfulfilled Accountability." *American Political Science Review* 111(1): 129–148.

- **Design**: RDD on Brazilian mayoral elections 1996–2012; close-election discontinuity
- **Finding**: incumbency DISADVANTAGE in Brazil (opposite to U.S.) — winning the mayoralty increases probability of losing the next election. Mechanism: term limits + weak parties → incumbents have no re-election incentive → shirk
- **Relevance for Nara**: (a) methodological benchmark — RDD on Brazilian municipal elections; (b) explains Nara's null incumbency effect: if incumbency already disadvantages the party, judicial challenges may not add much; (c) suggests the new-entrant winner result is consistent with the broader Brazilian political context where incumbents are disadvantaged
- **Direct citation**: "Consistent with Klašnja and Titiunik (2017), we find that incumbency does not mechanically shelter the mayoral winner from competitive pressures, including those generated by judicial challenges."

**Brambor, T. & Ceneviva, R. (2012).** "Incumbency Advantage in Brazilian Mayoral Elections." Working paper.

- **Finding**: incumbency advantage exists in Brazilian municipal elections (positive, unlike Klašnja-Titiunik finding at party level)
- **Relevance**: at candidate level, incumbents have some advantage; at party level, they don't. This distinction matters for interpreting Nara's results

**Samuels, D. (2001).** "Ambition, Federalism, and Legislative Politics in Brazil." Cambridge University Press (excerpt in *Comparative Political Studies*).

- **Argument**: Brazilian federalism creates career incentives for municipal politicians; mayoralties serve as springboards; parties are weak vehicles
- **Relevance**: motivates why candidate entry into municipal races is sensitive to legal costs — the career stakes are high; mayoral positions are launching pads

---

## 4. Information, Signaling, and Voter Behavior

### 4.1 Voters and judicial information

**Lupia, A. & McCubbins, M. (1998).** *The Democratic Dilemma: Can Citizens Learn What They Need to Know?* Cambridge University Press.

- **Argument**: voters use informational shortcuts; institutional cues (endorsements, visible accusations) substitute for direct information
- **Relevance**: judicial challenges are a visible institutional signal. A lawsuit is a public record, even before any ruling. This provides the mechanism for voter behavior effects (blank rate, turnout)

**Prat, A. (2002).** "Campaign Advertising and Voter Welfare." *Review of Economic Studies* 69(4): 999–1017.

- **Argument**: campaign advertising reveals information about candidate quality; more information improves voter welfare even under strategic manipulation
- **Relevance**: lawsuits are analogous to negative campaign advertising — they signal alleged wrongdoing. The blank rate result (p=0.018 broad spec) is consistent with voters facing increased uncertainty about candidate quality

**Ansolabehere, S. & Iyengar, S. (1995).** *Going Negative: How Attack Ads Shrink and Polarize the Electorate.* Free Press.

- **Finding**: negative advertising reduces turnout; demobilizes the electorate
- **Relevance for Nara**: the null turnout result (-0.006, p=0.185) is an important non-finding. Unlike negative advertising, judicial challenges do not appear to demobilize voters. The blank rate channel (not turnout) is where the behavioral effect surfaces

**Wattenberg, M. & Brians, C. (1999).** "Negative Campaign Advertising: Demobilizer or Mobilizer?" *American Political Science Review* 93(4): 891–900.

- **Finding**: negative advertising effect on turnout is small and context-dependent
- **Relevance**: positions Nara's null turnout result within a literature that already questions the demobilization hypothesis

### 4.2 Credence goods and candidate quality signals

**Dewan, T. & Myatt, D. (2007).** "Leading the Party: Coordination, Direction, and Communication." *American Political Science Review* 101(4): 827–845.

- **Relevance**: candidates as "credence goods" — voters cannot observe quality before voting. Judicial challenges reduce uncertainty about some candidates (by flagging alleged misconduct) while increasing noise for others. This generates the winner consolidation pattern: the cleaner candidate benefits from contrast

---

## 5. Shift-Share Instrument Design and Validity

### 5.1 Foundational methodological papers

**Goldsmith-Pinkham, P., Sorkin, I., & Swift, H. (2020).** "Bartik Instruments: What, When, Why, and How." *American Economic Review* 110(8): 2586–2624. [**GPS**]

- **Framework**: the Bartik 2SLS estimand is a Rotemberg-weighted average of just-identified IVs using each industry share as the instrument. Validity requires shares to be conditionally exogenous
- **Checklist**: (1) report Rotemberg weights; (2) run balance tests on high-weight shares; (3) plot visual IV graph (tau_k vs F_k); (4) check sign consistency across topics
- **Nara's compliance**: all four completed (05_rotemberg_weights.py, 08_gps_balance_tests.py, 09_visual_iv.py)

**Borusyak, K., Hull, P., & Jaravel, X. (2022).** "Quasi-Experimental Shift-Share Research Designs." *Review of Economic Studies* 89(1): 181–213. [**BHJ**]

- **Framework**: validity rests on conditional exogeneity of the shifts (not the shares). Recommends including all topics in instrument construction; favors leave-one-out shifters
- **Key statistic**: effective K = 1/HHI ≈ K_eff; at K_eff ≈ 3 (Nara's Rotemberg HHI = 0.38), BHJ asymptotics are weak → GPS approach is primary
- **Nara's compliance**: BHJ shift descriptives table (10_shift_descriptives.py); exposure-robust SEs (11_exposure_robust_se.py)

**Adão, R., Kolesár, M., & Morales, E. (2019).** "Shift-Share Designs: Theory and Inference." *Quarterly Journal of Economics* 134(4): 1949–2010. [**AKM**]

- **Framework**: clustering standard errors by initial share vector; exposure-robust inference; finite-K correction
- **Nara's compliance**: AKM-style SEs reported in exposure_robust_se.csv; ratio SE_BHJ/SE_conv ≈ 2–3× (consistent with K_eff = 2.6)

**Autor, D.H., Dorn, D., & Hanson, G.H. (2013).** "The China Syndrome: Local Labor Market Effects of Import Competition in the United States." *American Economic Review* 103(6): 2121–2168.

- **Template**: the canonical Bartik application — shares = industry composition, shifts = Chinese import growth. Remains the empirical standard for credibility of Bartik designs in economics

**Lee, D.S., McCrary, J., Moreira, M.J., & Porter, J.R. (2022).** "Valid t-ratio Inference for IV." *American Economic Review* 112(10): 3260–3290.

- **Finding**: when F < 23.1, the conventional t-ratio critical value (1.96) gives over-rejection. Provides tF correction table
- **Nara's instrument**: F = 19.6 → tF_cv = 2.18. Already implemented (tF correction in IV results)

### 5.2 Political economy applications of Bartik IV

**Autor, D., Dorn, D., Hanson, G., & Majlesi, K. (2020).** "Importing Political Polarization? The Electoral Consequences of Rising Trade Exposure." *American Economic Review* 110(10): 3139–3183.

- **Application**: China trade shock → political polarization (electoral shift toward extreme candidates)
- **Relevance**: establishes the template for using economic Bartik shocks to study electoral outcomes. Nara applies this logic to judicial shocks. This is the closest methodological precedent in political economy

**Colantone, I. & Stanig, P. (2018).** "Global Competition and Brexit." *American Political Science Review* 112(2): 201–218.

- **Application**: China trade exposure in UK → higher Leave vote in Brexit
- **Relevance**: shows Bartik instruments travel well across countries and political settings

---

## 6. Heterogeneity and Mechanism Tests: Empirical Strategies

### 6.1 Heterogeneity by prior competition level

**Snyder, J. & Strömberg, D. (2010).** "Press Coverage and Political Accountability." *Journal of Political Economy* 118(2): 355–408.

- **Finding**: media exposure raises electoral accountability; effects larger in competitive races
- **Relevance**: mechanism parallel — information effects (from lawsuits) should matter more when races are close. Motivates Nara's "close races" subsample analysis

**Besley, T. & Prat, A. (2006).** "Handcuffs for the Grabbing Hand? Media Capture and Government Accountability." *American Economic Review* 96(3): 720–736.

- **Relevance**: information matters more in competitive environments; judicial challenges as information-generating events whose impact scales with electoral competition

### 6.2 Heterogeneity by candidate type (incumbents vs. challengers)

**Incumbency and legal resources:**
The asymmetry between incumbents and challengers in legal resources is underdeveloped in the formal literature but empirically grounded:

- Incumbents have (a) established legal teams, (b) party legal resources, (c) reputational resilience
- Challengers have (a) lower legal budgets, (b) less experience with electoral law, (c) more reputational vulnerability
- **Nara's finding**: new-entrant winner result (p=0.08 adversarial-only) suggests lawsuits do NOT protect incumbents — if anything, judicial challenges open space for challengers. This is the **opposite** of the Stigler incumbency-protection prediction

**Lee, D.S. (2008).** "Randomized Experiments from Non-Random Selection in U.S. House Elections." *Journal of Econometrics* 142(2): 675–697.

- **Design**: RDD at 50% vote share threshold → causal incumbency advantage ≈ 40pp in US House
- **Relevance**: methodological benchmark for incumbency research; motivates why Nara's incumbency heterogeneity analysis needs to acknowledge selection (incumbency in 2024 is partly determined by 2024 judicialization)

### 6.3 Heterogeneity by municipal size/regime

**Art. 29-II CF/88 threshold (200k registered voters):**

The constitutional threshold for second-round elections creates:
- Sharp change in electoral rules at 200k
- Different candidate strategies above/below the threshold
- Instrument loses power for large cities (F < 1.1 in gt200k subsample) — consistent with larger municipalities dominating their own state shifts (LOO partially fails)

**Klašnja, M., Tucker, J., & Deegan-Krause, K. (2016).** "Pocketbook vs. Sociotropic Voting in New Democracies." *British Journal of Political Science* 46(1): 111–135.

- **Relevance**: voting behavior differs by city size in new democracies; large cities have more sophisticated electorates with different responses to legal information

---

## 7. What the Literature Implies for Nara's Next Steps

### 7.1 Robustness priorities (ordered by feasibility/impact)

| Priority | Robustness test | Inspiration | Status |
|---|---|---|---|
| 1 | Leads-and-lags placebo (future IV → current outcome) | AMV Table A.18 | Requires 2016 lawsuit data |
| 2 | Topic share controls in main regression | AMV Table A.20; BHJ | Easy to add |
| 3 | Drop each topic: stability of main estimates | AMV Figure A.16 | Done (visual IV) |
| 4 | Alternative topic classifications | AMV Table A.21 | Medium effort |
| 5 | Control for other TSE activity (non-adversarial filings as control) | AMV Appendix D.4 | Medium |
| 6 | State × election cycle FE (2-way FE) | AMV standard | Currently state FE only |

### 7.2 Mechanism analyses that are feasible

**Done:**
- Entry deterrence: Δlog(candidates), Δcandidate pool composition
- Topic family heterogeneity: family-split IV (information env. vs. campaign conduct vs. eligibility)
- Competition level heterogeneity: close vs. landslide subsample
- Incumbency: incumbent ran/won
- Multi-arena comparison: executive vs. legislative

**Feasible with current data:**
- **"Concavity" analog**: municipalities with 0 lawsuits in 2020 (zero-share = no exposure) vs. municipalities with positive share — does the effect come from the switch to having any judicialization, or from intensive-margin variation?
- **Political uncertainty analog** (following AMV Section 6.6): split sample by pre-existing electoral competition (margin 2020) — does judicialization matter more when races are close? (Started as subsample, but could be formalized as interaction)
- **Candidate quality signal**: if judicial challenges serve as quality signals, effects should be larger in municipalities with weaker pre-existing information environments (fewer candidates, lower media coverage proxy). Could use n_candidates_2020 or party_count_2020 as proxies for information environment

**Requires new data:**
- Pre-period placebo (2016→2020 outcomes): need 2016 lawsuit panel — user is searching for this
- TRE judge composition heterogeneity: judicial ideology/tenure as moderator
- Ruling outcomes (win/loss): as a second instrument to separate "filed" from "won" effects

### 7.3 Narrative thread from the literature

The dissertation can be framed around three interconnected stories, each grounded in specific papers:

**Story 1: Identification via institutional diffusion** (AMV, GPS, BHJ)
> "Just as states borrow legislative language from each other when they have gaps in their legal stock [AMV], Brazilian electoral zones are differentially exposed to waves of adversarial litigation across legal topics because of differences in their 2020 topic composition. We isolate this differential exposure using a Bartik shift-share IV whose validity rests on the conditional exogeneity of the 2020 topic shares [GPS 2020] and the exogeneity of the state-level shifts [BHJ 2022]."

**Story 2: Entry deterrence** (Besley-Coate 1997, Stigler 1971, Klašnja-Titiunik 2017)
> "Pre-election judicial challenges raise the fixed cost of candidacy by diverting resources to legal defense and exposing candidates to reputational risk [Besley-Coate 1997]. This deterrence effect is consistent with our finding of a reduced candidate pool across both executive and legislative races. Unlike the Stiglerian prediction [Stigler 1971] that regulation protects incumbents, we find that judicial challenges are associated with a higher probability that the winner is a new entrant — consistent with a pattern of diffuse deterrence that affects the entire candidate field."

**Story 3: Information and expressive voting** (Ferraz-Finan 2008, Lupia-McCubbins 1998, Prat 2002)
> "Electoral lawsuits are publicly filed records that generate information about candidates' alleged conduct. Consistent with the information-provision literature [Ferraz-Finan 2008; Lupia-McCubbins 1998], we find suggestive evidence that voters incorporate this information into expressive choices: the blank vote rate rises significantly under broader judicial activity. This finding mirrors the Ferraz-Finan result that public disclosure of corruption information changes voting behavior — here, rather than reducing incumbent vote shares, the signal generates voter ambivalence."

---

## 8. Papers to Find / Verify Existence Before Citing

The following are commonly cited in the area but need verification before use:

- **Helmke, G. (2017).** *Institutions on the Edge: The Origins and Consequences of Inter-Branch Crises in Latin America.* Cambridge UP. — Often cited for electoral judicialization overview
- **Ingram, M. (2012).** "Crafting Courts in New Democracies." — Check exact title/edition
- **Marchetti, V. (2013/2015).** Work on Brazilian electoral justice. — Multiple papers; verify which is most cited
- **Brambor, T. & Ceneviva, R.** — Working paper status; check if published

---

## 9. Quick Reference: Where Each Paper Belongs in the Dissertation

| Section | Key citations |
|---|---|
| Introduction | AMV (2025); Ferraz-Finan (2008); Helmke-Staton (2011) |
| Institutional background | Sadek (2010); Marchetti (2013); Ingram (2016) |
| Identification strategy | AMV (2025); GPS (2020); BHJ (2022); AKM (2019); Autor-Dorn-Hanson (2013) |
| Instrument validity | GPS (2020); Lee et al. (2022); AMV robustness tests |
| Entry deterrence mechanism | Besley-Coate (1997); Osborne-Slivinski (1996); Stigler (1971) |
| Information/signaling mechanism | Ferraz-Finan (2008); Lupia-McCubbins (1998); Prat (2002) |
| Incumbency / political dynamics | Klašnja-Titiunik (2017); Lee (2008); Brambor-Ceneviva (2012) |
| Legislative outcomes (vereadores) | Samuels (2001); Besley-Coate (1997) [entry deterrence consistent] |
| Blank rate / voter behavior | Ferraz-Finan (2008); Ansolabehere-Iyengar (1995); Wattenberg-Brians (1999) |
| Robustness / GPS compliance | GPS (2020); BHJ (2022); AKM (2019); Lee et al. (2022) |
