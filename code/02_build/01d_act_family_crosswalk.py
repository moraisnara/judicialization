"""
01d_act_family_crosswalk.py — the ACT-BASED 10-family crosswalk (version 2026-06-26).

A NEW, parallel version of the family taxonomy — it does NOT replace the substance
crosswalk in 01_family_crosswalk.py (subst13/subst11/theme9/...). Per the
design-preservation rule every taxonomy generation is kept as a revisitable
version; this one is written to its own file (data/clean/act_family_crosswalk.csv)
and joined on pair_id exactly like the production crosswalk.

WHY a separate taxonomy. The substance crosswalk routes CRIMINAL STATUS BY THE
PROCEDURAL CLASS (vehicle) and keeps propaganda split by substance. This session
converged on a different, AMV/shift-exogeneity-motivated cut:

  - ACT-BASED, NOT VEHICLE-BASED. Families are the ACT alleged, merging the civil
    and criminal vehicles of the same act (e.g. captacao ilicita art.41-A AND
    corrupcao eleitoral art.299 both -> vote_buying). This deliberately RESCUES the
    criminal-vehicle vote-buying/fraud incidents the whitelist drops: validated as
    only 1.7% of kept volume, all on-act (Corrupcao Eleitoral, arregimentacao,
    Alistamento-Fraude, Inscricao Fraudulenta, Falsidade Ideologica).
  - PROPAGANDA IS DROPPED ENTIRELY. It is 54% of the adversarial universe, 25% of it
    reform-contaminated (online), and including it collapses K_eff 7->2.7 and F
    27->3.7 by dominating the shares. Defamation (honra) is kept as its OWN act
    family — it does NOT ride inside propaganda here.
  - CANDIDATURA FICTICIA FOLDS INTO FRAUDE. As a standalone family it carried 52% of
    the Var(B)/Rotemberg weight (drop-top-1 F=6.6, fragile). Folded into fraude
    (sham candidacy IS document/registration fraud), top weight falls to 33%,
    drop-top-1 F=31.4, F unchanged ~27. Behaviorally coherent and per the user's
    instruction NOT to mix it with inelegibility/candidacy-challenge.
  - BALLOT INTEGRITY IS KEPT (vote tally / sufragio interference). Substance-only
    F=23.2; +ballot F=27.5.

10 families: abuso, vote_buying, finance, inelegib, fraude (incl. cand_ficticia),
honra, direito_resposta, conduta_vedada, pesquisa_adv, ballot_integrity.

Diagnostics (scratchpad/amv_diagnostics.py, 2026-06-26): K_eff~6.8, first-stage
F~26.7, Rotemberg all-positive weights (top fraude 0.33), leave-state shock sd<=0.03,
covariate balance joint F=2.83 p=0.037 (log_pop & log_votes load — both 2nd-stage
controls).

EXCLUSIONS (shared with the substance crosswalk's intent):
  - MANDATORY administrative filings (RRC/DRAP/prestacao de contas) dropped by code.
  - ANCILLARY / downstream procedural vehicles dropped by class keyword (execucao,
    cumprimento de sentenca, habeas, embargos, ...): they double-count the accusation.
  - ONLINE propaganda dropped (reform-contaminated) — moot since all propaganda is
    dropped, but kept explicit for the keyword fallback path.

Output: data/clean/act_family_crosswalk.csv  (pair_id, cod_classe, classe,
cod_assunto, assunto, fam_act10, kept) and
output/tables/descriptives/act_family_coverage.csv.
"""
import os
import re
import unicodedata
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def up(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


# ---- exclusions -------------------------------------------------------------
MANDATORY = {11532, 12193, 12550, 12554, 12633, 12560, 11530, 12557, 11533,
             11546, 12555, 12556, 11531}
ANCILLARY_KW = ["cumprimento de sentenca", "execucao", "carta precatoria",
                "carta de ordem", "citacao", "intimacao", "tutela",
                "mandado de seguranca", "processo administrativo", "pet-adm",
                "excecao", "embargos", "cautelar inominada",
                "medidas alternativas", "restauracao", "habeas",
                "suspensao de seguranca", "conflito", "reclamacao", "peticao"]
ONLINE_KW = re.compile("internet|rede social|redes sociais|site|aplicativo|"
                       "impulsion|whatsapp|digital|web")


def is_ancillary(classe_up):
    return any(k in classe_up for k in ANCILLARY_KW)


# ---- explicit act-based code sets (cod_assunto) -----------------------------
ABUSO = {11718, 11719, 11720, 11717, 11596, 11722}
VOTEBUY = {11501, 11513, 10751, 11721, 10755, 11502, 11503, 11455, 10752, 11491}
FINANCE = {11700, 11699, 12062, 12634, 11684}
INELEG = {11605, 11600, 11522}
# fraude includes candidatura ficticia (12597), folded in per the AMV concentration fix
FRAUDE = {11473, 11475, 11472, 14221, 11476, 11467, 11438, 12564, 12597}
HONRA = {11484, 11486, 11483, 3396, 3395, 11487, 3397, 11485, 15020, 11488}
DRESP = {11593}
CONDUTA = {12063, 11663}
PESQADV = {11649, 11650, 11495, 10820, 11524, 10822, 11523}
BALLOT = {11508, 11507, 11470, 11497, 11499, 11504, 11443, 11509, 11489}
DROP = {11633, 11638, 11640, 11642, 11643, 11646, 11647, 12600, 12601, 11584,
        11778, 11428, 11716, 12588, 11767, 11766, 11518, 11519, 11773, 11776,
        11771, 11575, 11576, 11578, 7929, 15056, 12640, 11746, 11559, 3515,
        11651, 11648, 11698, 11770, 15141, 11772}

CODEMAP = {}
for _codes, _name in [(ABUSO, "abuso"), (VOTEBUY, "vote_buying"),
                      (FINANCE, "finance"), (INELEG, "inelegib"),
                      (FRAUDE, "fraude"), (HONRA, "honra"),
                      (DRESP, "direito_resposta"), (CONDUTA, "conduta_vedada"),
                      (PESQADV, "pesquisa_adv"), (BALLOT, "ballot_integrity")]:
    for _c in _codes:
        CODEMAP[_c] = _name

FAMILIES = ["abuso", "vote_buying", "finance", "inelegib", "fraude", "honra",
            "direito_resposta", "conduta_vedada", "pesquisa_adv", "ballot_integrity"]


def act_family(cod_assunto, assunto_up):
    """Route a (cod_assunto, assunto) to one of the 10 act families, or None to drop.
    Explicit code sets first; then keyword fallback for the long tail. Propaganda is
    always dropped (online or not)."""
    cod = cod_assunto
    if cod in DROP:
        return None
    if cod in CODEMAP:
        return CODEMAP[cod]
    a = assunto_up
    if a.startswith("propaganda politica"):
        return None  # propaganda dropped entirely (reform-contaminated + share-dominating)
    if "abuso" in a:
        return "abuso"
    if "conduta vedada" in a:
        return "conduta_vedada"
    if "direito de resposta" in a:
        return "direito_resposta"
    if any(k in a for k in ["calunia", "difamacao", "injuria", "falsa imputacao",
                            "fatos inveridicos", "denunciacao caluniosa"]):
        return "honra"
    if any(k in a for k in ["captacao", "corrupcao eleitoral", "boca de urna",
                            "arregimentacao", "coacao", "aliciamento"]):
        return "vote_buying"
    if any(k in a for k in ["doacao", "gasto ilicito", "recursos financeiros",
                            "apropriacao indebita"]):
        return "finance"
    if any(k in a for k in ["falsidade", "documento falso", "falsificacao",
                            "fe publica", "fraude", "candidatura ficticia"]):
        return "fraude"
    if "inelegibilidade" in a:
        return "inelegib"
    if "pesquisa" in a and "registro de pesquisa" not in a:
        return "pesquisa_adv"
    return None


def main():
    xw_path = os.path.join(ROOT, "data", "clean", "sig_family_crosswalk.csv")
    xw = pd.read_csv(xw_path)
    need = ["pair_id", "cod_classe", "classe", "cod_assunto", "assunto"]
    xw = xw[need].drop_duplicates("pair_id").copy()

    xw["classe_up"] = xw["classe"].map(up)
    xw["assunto_up"] = xw["assunto"].map(up)

    # exclusions
    excl_mandatory = xw["cod_classe"].isin(MANDATORY)
    excl_ancillary = xw["classe_up"].map(is_ancillary)
    in_scope = ~(excl_mandatory | excl_ancillary)

    fam = []
    for cod, a, ok in zip(xw["cod_assunto"], xw["assunto_up"], in_scope):
        if not ok or pd.isna(cod):
            fam.append(None)
        else:
            fam.append(act_family(int(cod), a))
    xw["fam_act10"] = fam
    xw["kept"] = xw["fam_act10"].notna()

    out = xw[["pair_id", "cod_classe", "classe", "cod_assunto", "assunto",
              "fam_act10", "kept"]].copy()
    out_path = os.path.join(ROOT, "data", "clean", "act_family_crosswalk.csv")
    out.to_csv(out_path, index=False, encoding="utf-8")

    # coverage table by family (pair count; volume needs the panel join downstream)
    cov = (out[out["kept"]].groupby("fam_act10").size()
           .reindex(FAMILIES, fill_value=0).rename("n_pairs").reset_index())
    cov_path = os.path.join(ROOT, "output", "tables", "descriptives",
                            "act_family_coverage.csv")
    os.makedirs(os.path.dirname(cov_path), exist_ok=True)
    cov.to_csv(cov_path, index=False, encoding="utf-8")

    n_pairs = len(out)
    n_kept = int(out["kept"].sum())
    print(f"act_family_crosswalk: {n_pairs} pairs, {n_kept} kept ({100*n_kept/n_pairs:.0f}%)")
    print(f"  families: {', '.join(FAMILIES)}")
    print(f"  wrote {out_path}")
    print(f"  wrote {cov_path}")
    print(cov.to_string(index=False))


if __name__ == "__main__":
    main()
