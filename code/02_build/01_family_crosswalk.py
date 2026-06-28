"""
01_family_crosswalk.py — build the substance-based (classe, assunto) -> family
crosswalk for the shift-share families, and an AGGREGATION LADDER so the family
granularity is a tested/robustness dimension rather than a hard-coded set.

WHY a reconciled crosswalk (not raw classe or raw assunto). The §4 compatibility
analysis (32_sig_coding_compatibility.py) showed: the two fields are ~88% nested,
agree 98% on the mandatory drop, but a propaganda complaint is split across
classes differently by TRE. The §5 breakdown (33_sig_class_subject_breakdown.py)
revealed three traps that neither field alone avoids:
  (1) the big adversarial class REPRESENTACAO is, by subject, mostly PROPAGANDA;
  (2) an adversarial type (Impugnacao ao Registro de Candidatura) is buried inside
      the MANDATORY class Registro de Candidatura -> a pure class-drop loses it;
  (3) a subject that looks adversarial (Ausencia/Abandono) is poll-worker admin.

ARCHITECTURE = WHITELIST (audited 2026-06-24). Earlier versions blacklisted the
mandatory/admin classes and treated everything else as adversarial; the audit
showed that swept ~40 minor procedural/fiscal/admin classes and downstream
criminal-enforcement incidents into the kept set. We now WHITELIST the classes we
keep and DROP everything else (logging the dropped tail), on these rules:
  - rescue: assunto = Impugnacao ao Registro de Candidatura -> candidacy_challenge
    (it is adversarial but filed inside the mandatory Registro class) [trap 2];
  - ORIGINATING criminal CLASSES (accusations) -> criminal family, IN HEADLINE.
    Downstream criminal enforcement/incidents (Auto de Prisao, Execucao da Pena,
    Habeas Corpus, ...) are NOT kept -> they double-count the accusation, same
    logic that drops Cumprimento de Sentenca.
  - CORE adversarial civil CLASSES -> routed by ASSUNTO substance.
  - everything else -> drop.
CRIMINAL STATUS FOLLOWS THE CLASS (the procedural vehicle), never a subject
keyword: e.g. Captacao Ilicita de Sufragio (art. 41-A) is CIVIL-electoral
(AIME/AIJE/Representacao, art. 22 LC64) and routes to abuse_economic, not criminal.

TAXONOMY ON A SINGLE SUBSTANCE AXIS (audited 2026-06-25). Earlier the floor mixed
axes: it split the 85k propaganda blob by MEDIUM while routing everything else by
legal substance, and bundled candidatura ficticia (quota fraud) inside abuse of
economic power. The 2026-06-25 audit fixed both and dropped a metadata residual:
  - PROPAGANDA is split by SUBSTANCE, not medium:
      * content (false/defamatory/manipulated)  -> content_disinfo (the noise channel)
      * placement (where the ad ran)             -> prop_placement
      * official rules / airtime / limits        -> prop_regulatory
      * timing (premature campaigning)           -> prop_timing
  - CANDIDATURA FICTICIA (laranja / gender-quota fraud) is its OWN family
      (candidatura_ficticia) — it is candidacy integrity, not economic abuse, and
      bears directly on the female-candidate outcomes;
  - RIGHT OF REPLY folds into content_disinfo (it is a remedy to harmful content);
  - other_adversarial is DROPPED: its mass was office tags (Cargo-Prefeito) and
      bare procedure (Requerimento) — metadata, not a lawsuit type; it diluted the
      instrument without a mechanism interpretation.

FAMILY GRANULARITY IS NOT FIXED. The FLOOR is the 13-family substance level
(subst13). The ladder collapses it upward: subst13 -> subst11 (HEADLINE) ->
theme9 -> theme7 -> triad3. The 2026-06-25 coherence audit set subst11 as the
headline (propaganda folded, all else kept split where shocks oppose) and pushed
theme9/theme7/triad3 to robustness rungs (they merge opposing channels).
  - subst13 : finest substance families (criminal split into vote/speech/other,
              propaganda into content/placement/regulatory/timing);
  - theme9  : one family per legal theme, propaganda kept resolved into its three
              non-content sub-axes (placement/regulatory/timing), criminal as one
              track. HEADLINE. No theme mixes distinct sub-axes (only same-category
              merges: abuse econ+pol, candidacy challenge+ficticia, criminal track);
  - theme7  : theme9 with the propaganda sub-axes folded into one umbrella theme;
  - triad3  : mechanism trichotomy (information_env | strategic_attack | criminal).
Downstream the instrument is built and re-estimated at each rung; no rung is
privileged in the data — theme9 leads on relevance + shock diversity.

Reads the two SIG microdata zips. Writes:
  data/clean/sig_family_crosswalk.csv   (one row per distinct (classe, assunto),
       with volumes and the family label under every aggregation scheme)
  output/tables/descriptives/sig_family_coverage.csv  (volume per family/scheme)
"""
import zipfile, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW  = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
OUT  = ROOT / "output/tables/descriptives"; OUT.mkdir(parents=True, exist_ok=True)
COLS = ["ano","assunto","classe","data_dist","muni","tipo_origem","uf","zona",
        "qt_dec","qt_proc","tempo_med","data_carga"]
SOURCES = ["processos_eleitorais.csv.zip", "processos_eleitorais_2024.csv"]

def up(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).upper().strip()

# ------------------------------------------------------------ class whitelists
# ORIGINATING criminal accusations (the judicialization signal). Downstream
# criminal enforcement/incident classes are intentionally NOT here -> they drop.
ORIG_CRIMINAL_CLASSES = {
    "INQUERITO POLICIAL", "ACAO PENAL ELEITORAL",
    "REPRESENTACAO CRIMINAL/NOTICIA DE CRIME", "TERMO CIRCUNSTANCIADO",
    "PROCEDIMENTO INVESTIGATORIO CRIMINAL (PIC-MP)"}
# core adversarial civil actions, routed by assunto substance.
CORE_ADVERSARIAL_CLASSES = {
    "REPRESENTACAO", "NOTICIA DE IRREGULARIDADE EM PROPAGANDA ELEITORAL",
    "ACAO DE INVESTIGACAO JUDICIAL ELEITORAL", "DIREITO DE RESPOSTA",
    "REPRESENTACAO ESPECIAL", "ACAO DE IMPUGNACAO DE MANDATO ELETIVO",
    "TUTELA CAUTELAR ANTECEDENTE", "TUTELA ANTECIPADA ANTECEDENTE"}

# --------------------------------------------------- assunto substance keywords
# Within the kept classes only. Order matters: first matching group wins.
# Polls: registration/methodology/access disputes -> electoral_polls; a FRAUDULENT
# poll is voter-facing disinformation -> content_disinfo (the noise channel).
POLL_KEYS = ["PESQUISA"]
POLL_FRAUD_KEYS = ["FRAUDULENT", "IRREGULARIDADES DOS DADOS"]
# content (the noise channel): false / manipulated / defamatory propaganda content.
DISINFO_KEYS = ["SABIDAMENTE FALSA", "FATOS INVERIDICOS", "FALSA IMPUTACAO"]
RIGHTREPLY_KEYS = ["DIREITO DE RESPOSTA"]                 # remedy to harmful content
PROPAGANDA_KEYS = ["PROPAGANDA"]   # generic propaganda; then split by substance below
# propaganda SUBSTANCE split (within the propaganda branch). content first.
PROP_CONTENT_KEYS = ["SABIDAMENTE FALSA", "FATOS INVERIDICOS", "FALSA IMPUTACAO",
    "TRUNCAGEM", "MONTAGEM", "DEEP FAKE", "CALUNIA", "DIFAMACAO", "INJURIA"]
PROP_TIMING_KEYS  = ["EXTEMPORANEA", "ANTECIPADA", "DIA DA ELEICAO", "BOCA DE URNA"]
PROP_REG_KEYS     = ["HORARIO ELEITORAL", "INSERCAO", "INSERCOES", "PROGRAMA EM BLOCO",
    "DISTRIBUICAO DE TEMPO", "INVASAO DE HORARIO", "LIMITE LEGAL",
    "OMISSAO DE INFORMACOES", "INSTITUCIONAL", "CONDUTA VEDADA", "LEI DE POSTURA",
    "DEBATE", "EMISSORA"]
# placement (where the ad ran) is the propaganda default (no content/timing/reg hit).
FINANCE_KEYS = ["DOACAO DE RECURSOS ACIMA DO LIMITE",
    "CAPTACAO OU GASTO ILICITO DE RECURSOS", "RECURSOS FINANCEIROS DE CAMPANHA"]
# candidatura ficticia (laranja / quota fraud) -> own family, checked before abuse.
FICTICIA_KEYS = ["CANDIDATURA FICTICIA"]
# abuse split: economic power / vote-buying vs political power / public-office misuse
ABUSE_ECON_KEYS = ["PODER ECONOMICO",
    "CAPTACAO ILICITA DE SUFRAGIO", "CAPTACAO ILICITA DE VOTOS"]   # 41-A: civil
ABUSE_POL_KEYS = ["PODER POLITICO", "AUTORIDADE", "CONDUTA VEDADA",
    "IMPROBIDADE ADMINISTRATIVA", "USO INDEVIDO DE MEIO", "ABUSO"]  # bare ABUSO -> political
CHALLENGE_KEYS = ["IMPUGNACAO AO REGISTRO DE CANDIDATURA",
    "CANCELAMENTO DE REGISTRO DE CANDIDATURA", "CONDICAO DE ELEGIBILIDADE",
    "INELEGIBILIDADE", "ARGUICAO DE INELIGIBILIDADE", "ARGUICAO DE INELEGIBILIDADE"]
# criminal split (within ORIG_CRIMINAL_CLASSES, routed by the crime in the assunto)
CRIME_SPEECH_KEYS = ["CALUNIA", "DIFAMACAO", "INJURIA", "FALSIDADE IDEOLOGICA",
    "FATOS INVERIDICOS", "SABIDAMENTE FALSA"]
# audit 2026-06-25: "Inscricao Fraudulenta" (fraudulent voter REGISTRATION) is NOT
# vote-buying and its shock is +0.42 (rising) vs the falling vote-buying track ->
# removed from the vote keys so it falls to crime_other (the residual), instead of
# cancelling against the genuine vote-buying members inside crime_vote.
CRIME_VOTE_KEYS = ["ARREGIMENTACAO", "BOCA DE URNA", "CORRUPCAO ELEITORAL",
    "CAPTACAO ILICITA DE VOTOS", "CORRUPCAO OU FRAUDE"]

def any_in(A, keys):
    return any(k in A for k in keys)

# ---------------------------------------------------------------------------
# ARCHIVE-FAITHFUL fine7 ("fine7_literal"): a VERBATIM port of the archived
# code/_archive/02_build/instrument/grouping_schemes.py::base_grievance + the
# 7-block _COLLAPSE (identity). This is the engine that produced the old
# "11/19 significant, F~22" pro-competition result, run here on the CORRECTED
# muni-resolved SIG floor so we can tell whether that significance came from the
# DATA (pre-correction floor) or from this GROUPING/routing. It defines its own
# kept universe (returns "drop" where no rule fires), independent of subst13.
# Routing = eligibility kw -> reply kw -> TPU level-3 node -> keyword fallbacks.
_ASC = lambda s: "".join(c for c in unicodedata.normalize("NFKD", str(s).lower())
                         if not unicodedata.combining(c))
_ELIG_KW = ["impugnacao ao registro", "impugnacao de registro",
            "inelegibilidade", "condicao de elegibilidade"]
_L3_GRIEVANCE = {"11652": "propaganda", "11770": "propaganda", "11716": "abuse",
                 "11648": "pesquisa", "11482": "speech_crime", "3394": "speech_crime",
                 "11497": "vote_crime", "3523": "vote_crime"}

def load_subj_anc3():
    t = pd.read_csv(ROOT / "data" / "reference" / "tpu_subjects.csv")
    out = {}
    for code, anc3 in zip(t["cod_item"], t["anc3_code"]):
        if pd.notna(code):
            out[str(int(code))] = (str(int(anc3)) if pd.notna(anc3) else str(int(code)))
    return out

def base_grievance(sc, sn, subj_anc3):
    s = _ASC(sn)
    if any(k in s for k in _ELIG_KW): return "eligibility"
    if "direito de resposta" in s: return "reply"
    sc_str = str(int(sc)) if pd.notna(sc) else ""
    g = _L3_GRIEVANCE.get(subj_anc3.get(sc_str, ""))
    if g: return g
    if any(k in s for k in ["calunia", "difamacao", "injuria",
                            "fatos inveridicos", "sabidamente falsa"]): return "speech_crime"
    if any(k in s for k in ["corrupcao eleitoral", "falsidade ideologica"]): return "vote_crime"
    if any(k in s for k in ["conduta vedada", "abuso -", "abuso do poder",
                            "captacao ilicita", "captacao ou gasto"]): return "abuse"
    if "pesquisa eleitoral" in s: return "pesquisa"
    if "propaganda" in s: return "propaganda"
    return "drop"

def prop_substance(A):
    """split a propaganda complaint by SUBSTANCE (not medium). content first."""
    if any_in(A, PROP_CONTENT_KEYS): return "content_disinfo"
    if any_in(A, PROP_TIMING_KEYS):  return "prop_timing"
    if any_in(A, PROP_REG_KEYS):     return "prop_regulatory"
    return "prop_placement"          # where the ad ran (default)

def family_substance(C, A):
    """assign the FINEST (subst13) substance family from (classe, assunto).
    The aggregation ladder collapses these upward; this is the floor."""
    # 0. rescue the adversarial candidacy challenge buried in a mandatory class
    if "IMPUGNACAO AO REGISTRO DE CANDIDATURA" in A:
        return "candidacy_challenge"
    # 1. originating criminal accusations (by CLASS) -> split by crime type
    if C in ORIG_CRIMINAL_CLASSES:
        if any_in(A, CRIME_SPEECH_KEYS):  return "crime_speech"
        if any_in(A, CRIME_VOTE_KEYS):    return "crime_vote"
        return "crime_other"
    # 2. core adversarial civil classes -> route by assunto substance
    if C in CORE_ADVERSARIAL_CLASSES:
        if any_in(A, FICTICIA_KEYS):    return "candidatura_ficticia"
        if any_in(A, POLL_KEYS):
            # audit 2026-06-25: a fraudulent poll is still a POLL dispute (and the
            # civil poll-litigation shock is +0.44, opposite the falling defamation
            # track). Route ALL poll subjects to electoral_polls; do not bleed the
            # fraudulent ones into content_disinfo (that mixed two opposing shocks).
            return "electoral_polls"
        if any_in(A, DISINFO_KEYS):     return "content_disinfo"
        if any_in(A, RIGHTREPLY_KEYS):  return "content_disinfo"   # content remedy
        if any_in(A, PROPAGANDA_KEYS):  return prop_substance(A)
        if any_in(A, FINANCE_KEYS):     return "campaign_finance"
        if any_in(A, ABUSE_ECON_KEYS):  return "abuse_economic"
        if any_in(A, ABUSE_POL_KEYS):   return "abuse_political"
        if any_in(A, CHALLENGE_KEYS):   return "candidacy_challenge"
        # residual adversarial: office tags / bare procedure (Cargo-*, Requerimento)
        # -> metadata, not a lawsuit type. DROPPED (no mechanism interpretation).
        return "drop"
    # 3. everything else (mandatory, admin, criminal-enforcement, procedural tail)
    return "drop"

# ------------------------------------------------------------ aggregation ladder
# The subst13 level is the floor; every scheme maps it to a coarser label. The
# ladder runs subst13 -> theme9 (HEADLINE) -> theme7 -> triad3. criminal stays a
# distinct track until triad3. 'drop' is never instrumented. Each rung is
# re-estimated as robustness.
SUBST = ["content_disinfo", "prop_placement", "prop_regulatory", "prop_timing",
         "electoral_polls", "abuse_economic", "abuse_political", "campaign_finance",
         "candidacy_challenge", "candidatura_ficticia",
         "crime_vote", "crime_speech", "crime_other"]
# subst13 -> subst11 (HEADLINE, audit 2026-06-25). The only aggregation endorsed by
# the data-driven coherence rule (merge same-signed shocks, split opposing ones):
# fold the 3 propaganda sub-axes (all falling, +0.18-0.23 co-moving) into one
# "illegal advertisement" family. EVERYTHING ELSE stays at the substance floor --
# abuse econ/pol, candidacy challenge/ficticia, and criminal vote/speech/other are
# all kept SPLIT because each boundary separates opposing (rising-vs-falling) shocks
# (the civil/criminal substitution: civil rising, criminal falling). Anchored on the
# "Electoral Litigation in Political Campaigns" conduct taxonomy.
TO_SUBST11 = {m: m for m in SUBST}
TO_SUBST11.update({"prop_placement": "illegal_advertisement",
                   "prop_regulatory": "illegal_advertisement",
                   "prop_timing": "illegal_advertisement"})
# NESTED LADDER (audit 2026-06-25): every coarser rung is a STRICT coarsening of
# subst11 (the headline) -- it only ever MERGES families, never splits. So the
# propaganda fold (-> illegal_advertisement) made at subst11 is inherited by every
# rung below; theme9/theme7/triad3 then re-merge the opposing-shock boundaries we
# deliberately kept split (abuse econ/pol, candidacy challenge/ficticia, criminal
# vote/speech/other). That re-merging is their PURPOSE: they are the "naive
# aggregation" rungs that demonstrate the cancellation, built honestly on top of
# the corrected floor rather than as an independently-cut sibling taxonomy.
#
# subst13 -> theme9: subst11, then fold the two same-name conduct pairs
TO_THEME9 = dict(TO_SUBST11)   # inherit the propaganda fold; defined just below
TO_THEME9.update({
    "abuse_economic": "abuse_power", "abuse_political": "abuse_power",
    "candidacy_challenge": "candidacy", "candidatura_ficticia": "candidacy"})
# subst13 -> theme7: theme9, then fold the 3 criminal vehicles into one
TO_THEME7 = dict(TO_THEME9)
TO_THEME7.update({"crime_vote": "criminal", "crime_speech": "criminal",
                  "crime_other": "criminal"})
# subst13 -> triad3 (mechanism trichotomy)
TO_TRIAD = {
    "content_disinfo": "information_env", "prop_placement": "information_env",
    "prop_regulatory": "information_env", "prop_timing": "information_env",
    "electoral_polls": "information_env",
    "abuse_economic": "strategic_attack", "abuse_political": "strategic_attack",
    "campaign_finance": "strategic_attack", "candidacy_challenge": "strategic_attack",
    "candidatura_ficticia": "strategic_attack",
    "crime_vote": "criminal", "crime_speech": "criminal", "crime_other": "criminal"}
SCHEMES = {
    "subst13": {m: m for m in SUBST},   # identity (finest floor)
    "subst11": dict(TO_SUBST11),        # HEADLINE: floor with propaganda folded
    "theme9":  dict(TO_THEME9),
    "theme7":  dict(TO_THEME7),
    "triad3":  dict(TO_TRIAD),
}

def load_pairs():
    parts = []
    for fn in SOURCES:
        with zipfile.ZipFile(RAW / fn) as z:
            d = pd.read_csv(z.open(z.namelist()[0]), sep=";", encoding="latin-1",
                            dtype=str, low_memory=False)
        d.columns = COLS
        d["qt"] = pd.to_numeric(d.qt_proc, errors="coerce").fillna(0)
        d["year"] = pd.to_numeric(d.ano, errors="coerce")
        d["C"] = d.classe.map(up); d["A"] = d.assunto.map(up)
        parts.append(d[["year","classe","assunto","C","A","qt"]])
    return pd.concat(parts, ignore_index=True)

# ----------------------------------------------------------- official-code lookup
# The SIG export ships NO codes, only names. To avoid carrying ~50-char strings as
# join keys downstream we (a) mint a stable internal pair_id (canonical key) and
# (b) attach the official CNJ/TSE codes from the TPU reference tables as REFERENCE-
# ONLY columns (exact normalized-name match; nullable; coverage reported). The
# official codes are never used as a pipeline merge key -> a partial name match can
# never corrupt the instrument; pair_id (100% coverage) carries the joins.
def attach_official_codes(out):
    def codemap(path, name_col, code_col):
        t = pd.read_csv(RAW / path)
        t["_k"] = t[name_col].map(up)
        return dict(zip(t.drop_duplicates("_k")._k, t.drop_duplicates("_k")[code_col]))
    amap = codemap("tpu_assunto_reference.csv", "official_name", "subject_code")
    cmap = codemap("tpu_classe_reference.csv",  "official_name", "class_code")
    out["cod_assunto"] = out.assunto.map(up).map(amap).astype("Int64")
    out["cod_classe"]  = out.classe.map(up).map(cmap).astype("Int64")
    na = 100 * out.cod_assunto.isna().mean(); nc = 100 * out.cod_classe.isna().mean()
    print(f"official-code attach (reference only): cod_assunto {100-na:.1f}% matched, "
          f"cod_classe {100-nc:.1f}% matched (unmatched -> <NA>, never a merge key)")
    return out

def main():
    df = load_pairs()
    grand = df.qt.sum()
    piv = (df.groupby(["classe","assunto","C","A"])
             .apply(lambda g: pd.Series({
                 "n_2020": g.loc[g.year == 2020, "qt"].sum(),
                 "n_2024": g.loc[g.year == 2024, "qt"].sum(),
                 "n_total": g.qt.sum()}), include_groups=False)
             .reset_index())
    piv["family_micro"] = [family_substance(c, a) for c, a in zip(piv.C, piv.A)]
    for sch, mp in SCHEMES.items():
        piv["fam_" + sch] = piv.family_micro.map(lambda f: mp.get(f, "drop"))

    # GRIEVANCE taxonomy (fine7 / fine8): the archived legal-tree families
    # (grouping_schemes.py::base_grievance) ported as a coarsening of subst13. A
    # family = a class of regulated behaviour under a distinct national rule. The
    # ONLY thing the dict schemes can't express is peeling direito de resposta out
    # of content_disinfo, so it is detected at the pair level here.
    #   fine8 = grievances with false-content disinfo as its OWN family.
    #   fine7 = fine8 with {illegal_advertisement, content_disinfo} -> propaganda
    #           (faithful to the legal tree: fake-news suits ARE propaganda suits).
    # fine7 vs fine8 instrument the IDENTICAL kept set; the only partition that
    # moves is whether rising disinfo stands alone or is bundled into falling
    # propaganda -- so any second-stage gap is attributable solely to that choice.
    GRIEV8 = {
        "prop_placement": "illegal_advertisement", "prop_regulatory": "illegal_advertisement",
        "prop_timing": "illegal_advertisement", "content_disinfo": "content_disinfo",
        "abuse_economic": "abuse", "abuse_political": "abuse", "campaign_finance": "abuse",
        "electoral_polls": "pesquisa", "crime_speech": "speech_crime",
        "crime_vote": "vote_crime", "crime_other": "vote_crime",
        "candidacy_challenge": "eligibility", "candidatura_ficticia": "eligibility"}
    def grievance8(fmicro, A):
        if fmicro == "drop": return "drop"
        if fmicro == "content_disinfo" and any_in(A, RIGHTREPLY_KEYS): return "reply"
        return GRIEV8.get(fmicro, "drop")
    piv["fam_fine8"] = [grievance8(f, a) for f, a in zip(piv.family_micro, piv.A)]
    piv["fam_fine7"] = piv["fam_fine8"].map(
        lambda g: "propaganda" if g in ("illegal_advertisement", "content_disinfo") else g)
    # fine7_archive: the LITERAL archived fine7 kept set. The original
    # base_grievance() returned None (-> drop) for sham candidacies and for crimes
    # outside the two hard-coded vote/speech L3 nodes, so candidatura_ficticia and
    # crime_other were dropped BY OMISSION (no rule matched them), not by an ex-ante
    # substantive call. Reproduced here as fine7 minus those two micros, holding the
    # disinfo-into-propaganda fold fixed -- so fine7_archive -> fine7 isolates ONLY
    # the keep/drop of those two families, and fine7 -> fine8 isolates ONLY the
    # disinfo split. (Same kept set as subst13 for fine7/fine8; strictly smaller for
    # fine7_archive.)
    _ARCH_DROP = {"candidatura_ficticia", "crime_other"}
    piv["fam_fine7_archive"] = [
        "drop" if f in _ARCH_DROP else g
        for f, g in zip(piv.family_micro, piv["fam_fine7"])]
    out = piv.drop(columns=["C","A"])
    # CANONICAL KEY: stable integer pair_id per distinct (classe, assunto), assigned
    # by sorted name so it is reproducible run-to-run and independent of row order.
    out = out.sort_values(["classe", "assunto"]).reset_index(drop=True)
    out.insert(0, "pair_id", out.index + 1)
    out = attach_official_codes(out)
    # ARCHIVE-FAITHFUL fine7 needs the subject code for its TPU level-3 lookup, so
    # it runs here (after codes are attached) on the corrected floor's pairs.
    _subj_anc3 = load_subj_anc3()
    out["fam_fine7_literal"] = [
        base_grievance(sc, sn, _subj_anc3)
        for sc, sn in zip(out.cod_assunto, out.assunto)]
    # column order: keys first (pair_id, codes), then names, volumes, families
    lead = ["pair_id", "cod_classe", "cod_assunto", "classe", "assunto"]
    out = out[lead + [c for c in out.columns if c not in lead]]
    out = out.sort_values("n_total", ascending=False)
    out.to_csv(CLEAN / "sig_family_crosswalk.csv", index=False)

    # coverage report at every rung
    print(f"grand total processos (both years): {grand:,.0f}")
    cov_rows = []
    ALL_SCHEMES = list(SCHEMES) + ["fine7_archive", "fine7", "fine8"]
    for sch in ALL_SCHEMES:
        g = piv.groupby("fam_" + sch).n_total.sum().sort_values(ascending=False)
        for fam, v in g.items():
            cov_rows.append({"scheme": sch, "family": fam, "n_total": int(v),
                             "share_of_all": round(v / grand, 4)})
    cov = pd.DataFrame(cov_rows)
    cov.to_csv(OUT / "sig_family_coverage.csv", index=False)
    for sch in ["subst13", "subst11"]:
        print(f"\n=== {sch} families — volume & coverage ===")
        s = cov[cov.scheme == sch].set_index("family")
        fams = sorted([f for f in s.index if f != "drop"], key=lambda f: -s.loc[f, "n_total"])
        col = "fam_" + sch
        for fam in fams:
            r = s.loc[fam]
            npairs = (piv[col] == fam).sum()
            print(f"  {fam:20s} {int(r.n_total):>9,d}  {r.share_of_all*100:5.2f}%  ({npairs} pairs)")
    kept = cov[(cov.scheme=="theme9") & (cov.family!="drop")].n_total.sum()
    print(f"\n  KEPT (instrumented) = {kept:,.0f}  = {kept/grand*100:.2f}% of all lawsuits")

    # grievance taxonomy (fine7_archive / fine7 / fine8) — block volumes + kept totals
    for sch in ["fine7_archive", "fine7", "fine8"]:
        print(f"\n=== {sch} grievance blocks — volume & coverage ===")
        s = cov[cov.scheme == sch].set_index("family")
        fams = sorted([f for f in s.index if f != "drop"], key=lambda f: -s.loc[f, "n_total"])
        col = "fam_" + sch
        for fam in fams:
            r = s.loc[fam]
            npairs = (piv[col] == fam).sum()
            print(f"  {fam:22s} {int(r.n_total):>9,d}  {r.share_of_all*100:5.2f}%  ({npairs} pairs)")
        keptk = s.loc[[f for f in fams], "n_total"].sum()
        print(f"  -> KEPT = {keptk:,.0f} = {keptk/grand*100:.2f}%  ({len(fams)} blocks)")

    # ARCHIVE-FAITHFUL fine7_literal coverage (computed on `out`, its own universe)
    gl = out.groupby("fam_fine7_literal").n_total.sum().sort_values(ascending=False)
    print("\n=== fine7_literal (VERBATIM archived base_grievance) blocks ===")
    keptl = 0
    for fam, v in gl.items():
        if fam == "drop": continue
        npairs = int((out.fam_fine7_literal == fam).sum())
        print(f"  {fam:22s} {int(v):>9,d}  {v/grand*100:5.2f}%  ({npairs} pairs)")
        keptl += v
    print(f"  -> KEPT = {keptl:,.0f} = {keptl/grand*100:.2f}%  "
          f"({(gl.index!='drop').sum()} blocks)")

    # audit log: the largest DROPPED classes, so nothing material is silently lost
    classes = piv.groupby("classe").agg(
        n=("n_total","sum"),
        kept=("family_micro", lambda s: (s != "drop").any())).reset_index()
    dropped = classes[~classes.kept].sort_values("n", ascending=False).head(15)
    print("\n=== largest DROPPED classes (audit trail) ===")
    for _, r in dropped.iterrows():
        print(f"  {r.n:>9,.0f}  {r.classe}")
    print(f"\nwrote {CLEAN/'sig_family_crosswalk.csv'}")
    print(f"wrote {OUT/'sig_family_coverage.csv'}")

if __name__ == "__main__":
    main()
