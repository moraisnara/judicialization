"""
33_sig_class_subject_breakdown.py — exploration (b), step 4: validate the
keep/drop class buckets by looking at the assuntos inside each class.

For every class assigned to a bucket (mandatory-drop / admin-drop /
adversarial-keep / criminal-toggle), list its top subjects, so we can confirm
the content matches the label and catch any class that is mislabeled by its name.
Reads the raw SIG microdata (both years). Writes a tidy CSV of the top subjects
per class and prints a grouped report.
Output: output/tables/descriptives/sig_class_subject_breakdown.csv
"""
import zipfile, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW  = ROOT / "data" / "raw"
OUT  = ROOT / "output/tables/descriptives"; OUT.mkdir(parents=True, exist_ok=True)
COLS = ["ano","assunto","classe","data_dist","muni","tipo_origem","uf","zona",
        "qt_dec","qt_proc","tempo_med","data_carga"]

def up(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).upper().strip()

# proposed buckets (normalized class names)
BUCKETS = {
 "mandatory_drop": ["REGISTRO DE CANDIDATURA","PRESTACAO DE CONTAS ELEITORAIS",
    "REQUERIMENTO DE REGULARIZACAO DE OMISSAO DE PRESTACAO DE CONTAS ELEITORAIS",
    "FILIACAO PARTIDARIA","LISTA DE APOIAMENTO PARA CRIACAO DE PARTIDO POLITICO"],
 "admin_drop": ["COMPOSICAO DE MESA RECEPTORA","APURACAO DE ELEICAO",
    "RECURSO/IMPUGNACAO DE ALISTAMENTO ELEITORAL","CARTA PRECATORIA CIVEL",
    "CARTA PRECATORIA CRIMINAL","CARTA DE ORDEM CIVEL","PET-ADM",
    "PROCESSO ADMINISTRATIVO","EXECUCAO DE MEDIDAS ALTERNATIVAS NO JUIZO COMUM",
    "PETICAO CIVEL","CUMPRIMENTO DE SENTENCA","SUSPENSAO DE ORGAO PARTIDARIO"],
 "adversarial_keep": ["REPRESENTACAO","NOTICIA DE IRREGULARIDADE EM PROPAGANDA ELEITORAL",
    "ACAO DE INVESTIGACAO JUDICIAL ELEITORAL","DIREITO DE RESPOSTA",
    "REPRESENTACAO ESPECIAL","ACAO DE IMPUGNACAO DE MANDATO ELETIVO",
    "TUTELA CAUTELAR ANTECEDENTE","TUTELA ANTECIPADA ANTECEDENTE"],
 "criminal_toggle": ["ACAO PENAL ELEITORAL","REPRESENTACAO CRIMINAL/NOTICIA DE CRIME",
    "INQUERITO POLICIAL","TERMO CIRCUNSTANCIADO"],
}
CLS2BUCKET = {c: b for b, cs in BUCKETS.items() for c in cs}

def load():
    parts = []
    for fn in ["processos_eleitorais.csv.zip", "processos_eleitorais_2024.csv"]:
        z = zipfile.ZipFile(RAW / fn)
        d = pd.read_csv(z.open(z.namelist()[0]), sep=";", encoding="latin-1",
                        dtype=str, low_memory=False)
        d.columns = COLS
        d["qt"] = pd.to_numeric(d.qt_proc, errors="coerce").fillna(0)
        d["C"] = d.classe.map(up)
        parts.append(d[["C","assunto","qt"]])
    return pd.concat(parts, ignore_index=True)

def main():
    df = load()
    grand = df.qt.sum()
    rows = []
    for bucket in ["adversarial_keep","criminal_toggle","mandatory_drop","admin_drop"]:
        print(f"\n############## {bucket.upper()} ##############")
        for c in BUCKETS[bucket]:
            sub = df[df.C == c]
            if not len(sub): print(f"\n-- {c}: (absent)"); continue
            tot = sub.qt.sum()
            top = sub.groupby("assunto").qt.sum().sort_values(ascending=False).head(6)
            print(f"\n-- {c}  ({tot:,.0f} proc, {tot/grand*100:.2f}% of all)")
            for a, v in top.items():
                print(f"     {v/tot*100:5.1f}%  {a}")
                rows.append({"bucket":bucket,"classe":c,"class_proc":int(tot),
                             "assunto":a,"assunto_share_in_class":round(v/tot,4)})
    pd.DataFrame(rows).to_csv(OUT/"sig_class_subject_breakdown.csv", index=False)
    print(f"\nwrote {OUT/'sig_class_subject_breakdown.csv'}")

if __name__ == "__main__":
    main()
