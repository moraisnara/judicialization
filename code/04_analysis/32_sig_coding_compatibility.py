"""
32_sig_coding_compatibility.py — exploration (b), step 3: are classe and assunto
coded consistently, and can the two taxonomy choices be reconciled?

Reads the raw SIG microdata (both classe AND assunto on every row) and asks:

  A. NESTEDNESS. Is classe a clean coarsening of assunto (each assunto sits in
     ~one classe), or do they cross-cut? Uncertainty coefficients U(classe|assunto)
     and U(assunto|classe) in [0,1]: 1 = the row's value in one field is fully
     determined by the other.

  B. MANDATORY RECONCILIATION. Define the "mandatory mass-filing" bucket under
     EACH taxonomy independently and cross-tab. High agreement => the drop
     decision is robust to which field we use.

  C. CROSS-TRE CODING STABILITY. For each adversarial category, the within-state
     share across the 27 TREs, summarized by coefficient of variation (sd/mean).
     Benchmarked against the mandatory "noise floor" (Registro de Candidatura):
     even a nationally-uniform filing has some cross-TRE spread; categories far
     above that floor are coding-unstable (or genuinely concentrated). Compares
     the mean CV of classe vs assunto -> which field do TREs code more uniformly.

  D. SUBSTANTIVE-TOPIC SPLIT. Demonstrates the concrete incompatibility: the
     "propaganda" complaint is split across several classes AND several assuntos,
     and the split differs by TRE. Motivates a reconciled substantive family that
     pools across both fields (the crosswalk we'd build if neither raw field wins).

Output: output/tables/descriptives/sig_coding_stability.csv
"""
import zipfile, unicodedata
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW  = ROOT / "data" / "raw"
OUT  = ROOT / "output/tables/descriptives"; OUT.mkdir(parents=True, exist_ok=True)
COLS = ["ano","assunto","classe","data_dist","muni","tipo_origem","uf","zona",
        "qt_dec","qt_proc","tempo_med","data_carga"]
SOURCES = ["processos_eleitorais.csv.zip", "processos_eleitorais_2024.csv"]

# mandatory mass-filing buckets, defined independently per taxonomy
MAND_CLASSE  = {"REGISTRO DE CANDIDATURA", "PRESTACAO DE CONTAS ELEITORAIS"}
MAND_ASSUNTO_KEYS = ["REGISTRO DE CANDIDATURA", "DRAP", "CARGO -", "ORGAO DE DIRECAO",
                     "PRESTACAO DE CONTAS"]

def up(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).upper().strip()

def load():
    parts = []
    for fn in SOURCES:
        with zipfile.ZipFile(RAW / fn) as z:
            d = pd.read_csv(z.open(z.namelist()[0]), sep=";", encoding="latin-1",
                            dtype=str, low_memory=False)
        d.columns = COLS
        d["qt"] = pd.to_numeric(d.qt_proc, errors="coerce").fillna(0)
        d["C"] = d.classe.map(up); d["A"] = d.assunto.map(up)
        parts.append(d[["ano","uf","zona","muni","C","A","qt"]])
    return pd.concat(parts, ignore_index=True)

def cond_entropy(df, x, y):  # H(y | x), and U(y|x)=1-H(y|x)/H(y)
    p = df.groupby([x, y]).qt.sum(); tot = p.sum()
    pxy = p / tot
    px = df.groupby(x).qt.sum() / tot
    py = df.groupby(y).qt.sum() / tot
    Hy = -(py * np.log(py)).sum()
    # H(y|x) = sum_x px * H(y|x)
    Hyx = 0.0
    for xv, sub in (pxy / pxy.groupby(level=0).sum()).groupby(level=0):
        Hyx += px[xv] * -(sub * np.log(sub)).sum()
    return Hyx, 1 - Hyx / Hy

def cv_across_states(df, dim, min_states=15):
    """unweighted CV of within-state share across TREs, per category."""
    st = df.groupby(["uf", dim]).qt.sum()
    st_tot = df.groupby("uf").qt.sum()
    share = (st / st_tot).rename("s").reset_index()
    g = share.groupby(dim)["s"]
    res = pd.DataFrame({"nat_share": df.groupby(dim).qt.sum()/df.qt.sum(),
                        "cv": g.std()/g.mean(),
                        "n_states": g.count()})
    return res[res.n_states >= min_states].sort_values("nat_share", ascending=False)

def main():
    df = load()
    print(f"loaded {len(df):,} rows | classes {df.C.nunique()} | assuntos {df.A.nunique()}")

    # ---- A. nestedness
    print("\n=== A. NESTEDNESS (uncertainty coefficients) ===")
    _, u_c_given_a = cond_entropy(df, "A", "C")
    _, u_a_given_c = cond_entropy(df, "C", "A")
    print(f"  U(classe | assunto) = {u_c_given_a:.3f}   (1 => assunto pins down classe)")
    print(f"  U(assunto | classe) = {u_a_given_c:.3f}   (1 => classe pins down assunto)")

    # ---- B. mandatory reconciliation
    df["mand_C"] = df.C.isin(MAND_CLASSE)
    df["mand_A"] = df.A.apply(lambda a: any(k in a for k in MAND_ASSUNTO_KEYS))
    ct = df.groupby(["mand_C","mand_A"]).qt.sum().unstack(fill_value=0)
    tot = df.qt.sum()
    agree = df.loc[df.mand_C == df.mand_A, "qt"].sum() / tot
    print("\n=== B. MANDATORY RECONCILIATION (qt, % of all) ===")
    print((ct/tot*100).round(2).to_string())
    print(f"  classe & assunto AGREE on mandatory-vs-adversarial for {agree*100:.1f}% of lawsuits")

    # ---- C. cross-TRE stability, classe vs assunto
    cvc = cv_across_states(df, "C"); cva = cv_across_states(df, "A")
    floor = cvc.loc["REGISTRO DE CANDIDATURA", "cv"] if "REGISTRO DE CANDIDATURA" in cvc.index else np.nan
    print("\n=== C. CROSS-TRE CODING STABILITY (CV of within-state share) ===")
    print(f"  mandatory noise floor (Registro de Candidatura) CV = {floor:.2f}")
    advc = cvc.drop(index=[c for c in MAND_CLASSE if c in cvc.index]).head(10)
    print("\n  top classes by volume — CV across TREs:")
    for k, r in advc.iterrows():
        flag = "  <-- unstable" if r.cv > 2*floor else ""
        print(f"    {k[:46]:46s} nat={r.nat_share*100:5.2f}%  CV={r.cv:4.2f}{flag}")
    print(f"\n  mean CV, top-12 adversarial CLASSES : {advc.head(12).cv.mean():.2f}")
    adva = cva.drop(index=[i for i in cva.index if any(k in i for k in MAND_ASSUNTO_KEYS)]).head(12)
    print(f"  mean CV, top-12 adversarial ASSUNTOS: {adva.cv.mean():.2f}")

    cvc.assign(dim="classe").to_csv(OUT/"sig_coding_stability_classe.csv")
    cva.assign(dim="assunto").to_csv(OUT/"sig_coding_stability_assunto.csv")

    # ---- D. propaganda topic split across classes & assuntos
    print("\n=== D. SUBSTANTIVE SPLIT: where does a 'propaganda' complaint live? ===")
    prop = df[df.A.str.contains("PROPAGANDA")]
    by_cls = prop.groupby("C").qt.sum().sort_values(ascending=False)
    print(f"  rows mentioning PROPAGANDA in assunto: {prop.qt.sum():,.0f}, spread over classes:")
    for k, v in by_cls.head(6).items():
        print(f"    {v/prop.qt.sum()*100:5.1f}%  {k[:50]}")
    # does that class-split vary by TRE?
    pc = prop.groupby(["uf","C"]).qt.sum()/prop.groupby("uf").qt.sum()
    rep_share_by_uf = pc.xs("REPRESENTACAO", level="C", drop_level=True) if "REPRESENTACAO" in prop.C.values else None
    if rep_share_by_uf is not None:
        print(f"\n  share of propaganda complaints filed as class REPRESENTACAO, across TREs:")
        print(f"    min={rep_share_by_uf.min()*100:.0f}%  median={rep_share_by_uf.median()*100:.0f}%  max={rep_share_by_uf.max()*100:.0f}%")
        print("    => same substantive complaint, different class label by TRE (the incompatibility)")

if __name__ == "__main__":
    main()
