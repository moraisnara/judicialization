"""
00_sig_lawsuit_panel.py — NEW canonical lawsuit source (SIG TSE microdata).

Replaces the raw-TSE `01_lawsuit_panel.py` build (now demoted to a stale
version). The SIG "Processos eleitorais" export resolves each lawsuit to its
**municipality of origin** (not just the electoral zona), with filing date and
origin type. That eliminates the zona->connected-component reconstruction the
old design needed.

Inputs (data/raw/, SIG sig.tse.jus.br exports, sep=';', latin-1):
  - processos_eleitorais.csv.zip          (2020, Ano de eleicao == 2020)
  - processos_eleitorais_2024.csv         (2024; despite the .csv name it is a zip)
  Schema (12 cols): Ano de eleicao; Assunto principal; Classe; Data de
  distribuicao; Municipio de origem; Tipo de origem; UF de origem; Zona;
  Quantidade de decisoes; Quantidade de processos; Tempo medio de tramitacao;
  Data de carga

Crosswalk: data/raw/bd_diretorio_municipio.csv (basedosdados) — name+UF -> IBGE
  (id_municipio) + TSE (id_municipio_tse). ~99.85% match by volume; the handful
  of TSE/IBGE spelling variants are resolved by within-UF fuzzy match and printed.

Outputs (data/clean/):
  - sig_muni_name_to_ibge.csv            crosswalk actually used (audit trail)
  - sig_lawsuits_muni_zona_assunto.csv   panel: muni x zona x assunto x year
  - sig_lawsuits_muni_zona_classe.csv    panel: muni x zona x classe x year
  - sig_lawsuits_muni_zona_classe_assunto.csv  panel: muni x zona x (classe,assunto)
       x year — the JOINT key the family crosswalk merges onto (instrument bridge)

Design choices are NOT baked in. Each panel row carries:
  n_proc            all filings in the election cycle (SIG "Ano de eleicao")
  n_proc_orig       Tipo de origem == Originario only (first-instance)
  n_proc_pre_eleic  filed on/before 1st-round election day (campaign-window)
  n_dec             sum Quantidade de decisoes
  tempo_med_dias    qt-weighted mean Tempo medio de tramitacao
so exploration can pick the originario filter / pre-election cutoff downstream.
Mandatory mass filings (Registro de Candidatura / Prestacao de Contas / DRAP)
are kept and flagged, not dropped, for the same reason.
"""
import zipfile, re, unicodedata, difflib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW  = ROOT / "data" / "raw"
CLEAN= ROOT / "data" / "clean"
COLS = ["ano","assunto","classe","data_dist","muni","tipo_origem","uf","zona",
        "qt_dec","qt_proc","tempo_med","data_carga"]
# 1st-round municipal election day per cycle (campaign-window cutoff)
ELECTION_DAY = {"2020": "2020-11-15", "2024": "2024-10-06"}
SOURCES = [("data/raw/processos_eleitorais.csv.zip", "2020"),
           ("data/raw/processos_eleitorais_2024.csv", "2024")]

def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', str(s).strip())
                if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Za-z0-9 ]', ' ', s)).upper().strip()

def load_sig(rel):
    f = RAW.parent.parent / rel
    with zipfile.ZipFile(f) as z:                 # both files are zips
        d = pd.read_csv(z.open(z.namelist()[0]), sep=";", encoding="latin-1",
                        dtype=str, low_memory=False)
    d.columns = COLS
    d["qt_proc"] = pd.to_numeric(d.qt_proc, errors="coerce").fillna(0)
    d["qt_dec"]  = pd.to_numeric(d.qt_dec,  errors="coerce").fillna(0)
    d["tempo_med"] = pd.to_numeric(d.tempo_med.str.replace(",", ".", regex=False),
                                   errors="coerce")
    d["dt"] = pd.to_datetime(d.data_dist, errors="coerce")
    return d

# TSE spellings the fuzzy matcher can't bridge (too far from the IBGE name).
# key = "UF|NORMALIZED NAME" -> (id_municipio, id_municipio_tse, ibge_name)
# "Boa Esperanca do Norte/MT" is intentionally absent: its creation was never
# installed (law suspended by the STF), so it has no IBGE code -> dropped.
MANUAL_OVERRIDE = {
    "RN|ASSU": ("2400208", "16039", "Acu"),   # Assu (TSE) == Acu (IBGE)
}

def build_crosswalk(sig_all):
    dx = pd.read_csv(RAW / "bd_diretorio_municipio.csv", dtype=str, encoding="utf-8")
    dx["key"] = dx.sigla_uf.str.upper() + "|" + dx.nome.map(norm)
    dx = dx.drop_duplicates("key")
    base = dx.set_index("key")[["id_municipio", "id_municipio_tse", "nome", "sigla_uf"]]

    pairs = (sig_all.groupby(["uf", "muni"])["qt_proc"].sum().reset_index())
    pairs["key"] = pairs.uf.str.upper() + "|" + pairs.muni.map(norm)
    pairs["matched"] = pairs.key.isin(base.index)

    # resolve unmatched by within-UF fuzzy match on normalized name
    by_uf = {uf: g for uf, g in dx.groupby(dx.sigla_uf.str.upper())}
    overrides = {}
    for _, r in pairs[~pairs.matched].iterrows():
        if r.key in MANUAL_OVERRIDE:
            ibge, tse, nm = MANUAL_OVERRIDE[r.key]
            overrides[r.key] = (ibge, tse, nm, r.uf.upper()); continue
        uf = r.uf.upper(); target = norm(r.muni)
        cand = by_uf.get(uf)
        if cand is None: continue
        names = cand.nome.map(norm).tolist()
        hit = difflib.get_close_matches(target, names, n=1, cutoff=0.80)
        if hit:
            row = cand[cand.nome.map(norm) == hit[0]].iloc[0]
            overrides[r.key] = (row.id_municipio, row.id_municipio_tse, row.nome, uf)

    print("=== fuzzy-resolved TSE/IBGE name variants ===")
    for k, v in overrides.items():
        print(f"  {k:32s} -> {v[2]} ({v[3]})  ibge={v[0]} tse={v[1]}")
    still = pairs[~pairs.matched & ~pairs.key.isin(overrides)]
    if len(still):
        print("  STILL UNMATCHED (dropped):")
        for _, r in still.iterrows(): print(f"    {r.uf} {r.muni!r} qt={r.qt_proc:.0f}")

    # final key -> codes
    cw = base.reset_index()[["key","id_municipio","id_municipio_tse"]]
    extra = pd.DataFrame([(k, v[0], v[1]) for k, v in overrides.items()],
                         columns=["key","id_municipio","id_municipio_tse"])
    cw = pd.concat([cw, extra], ignore_index=True).drop_duplicates("key")
    return cw

def aggregate(d, topic_cols, name, pair_map=None):
    if isinstance(topic_cols, str):
        topic_cols = [topic_cols]
    eday = d.ano.map(ELECTION_DAY)
    pre  = d.dt <= pd.to_datetime(eday, errors="coerce")
    orig = d.tipo_origem.str.startswith("Origin", na=False)
    w = d.assign(
        n_proc=d.qt_proc,
        n_proc_orig=d.qt_proc.where(orig, 0),
        n_proc_pre_eleic=d.qt_proc.where(pre, 0),
        n_dec=d.qt_dec,
        tempo_w=d.tempo_med * d.qt_proc,
    )
    g = (w.groupby(["ano","uf","zona","id_municipio","id_municipio_tse", *topic_cols])
           .agg(n_proc=("n_proc","sum"), n_proc_orig=("n_proc_orig","sum"),
                n_proc_pre_eleic=("n_proc_pre_eleic","sum"), n_dec=("n_dec","sum"),
                tempo_w=("tempo_w","sum"))
           .reset_index())
    g["tempo_med_dias"] = (g.tempo_w / g.n_proc.where(g.n_proc > 0)).round(1)
    g = g.drop(columns="tempo_w").rename(columns={"ano":"election_year"})
    # INSTRUMENT panel only: replace the (classe, assunto) NAME pair with the
    # canonical integer pair_id from the family crosswalk, so every downstream
    # merge keys on the code, not on ~50-char text. The join here is an exact,
    # same-source string equality (both sides are SIG raw names) -> 0 unmatched;
    # we assert that. Long names then live only in the crosswalk dictionary.
    if pair_map is not None:
        before = len(g)
        g = g.merge(pair_map, on=["classe", "assunto"], how="left")
        miss = g.pair_id.isna()
        assert not miss.any(), (f"{int(miss.sum())} (classe,assunto) rows have no "
                                f"pair_id — crosswalk out of sync with panel")
        assert len(g) == before, "pair_id merge changed row count (non-unique key)"
        g = g.drop(columns=["classe", "assunto"])
        lead = [c for c in ["election_year","uf","zona","id_municipio",
                            "id_municipio_tse","pair_id"] if c in g.columns]
        g = g[lead + [c for c in g.columns if c not in lead]]
    out = CLEAN / name
    g.to_csv(out, index=False)
    print(f"  wrote {out.name}: {len(g):,} rows | proc {g.n_proc.sum():,.0f}")
    return g

def main():
    sig = pd.concat([load_sig(rel).assign(ano=yr) for rel, yr in SOURCES],
                    ignore_index=True)
    print(f"loaded SIG: {len(sig):,} rows | years {sorted(sig.ano.unique())}")
    cw = build_crosswalk(sig)
    cw.to_csv(CLEAN / "sig_muni_name_to_ibge.csv", index=False)

    sig["key"] = sig.uf.str.upper() + "|" + sig.muni.map(norm)
    sig = sig.merge(cw, on="key", how="left")
    drop = sig.id_municipio.isna()
    print(f"merge: {drop.sum():,} rows unmatched "
          f"({100*sig.loc[drop,'qt_proc'].sum()/sig.qt_proc.sum():.2f}% of proc) -> dropped")
    sig = sig[~drop]

    print("\nbuilding panels:")
    # marginal panels (exploratory; never merged into estimation) keep their single
    # name field as the descriptive topic label.
    aggregate(sig, "assunto", "sig_lawsuits_muni_zona_assunto.csv")
    aggregate(sig, "classe",  "sig_lawsuits_muni_zona_classe.csv")
    # joint (classe, assunto) panel — the INSTRUMENT input. The family crosswalk is
    # keyed on the PAIR; we stamp its canonical integer pair_id here and drop the
    # names, so the bridge merges on the code. Requires 01_family_crosswalk.py to
    # have run first (it builds the pair_id <-> (classe,assunto) dictionary).
    xw = pd.read_csv(CLEAN / "sig_family_crosswalk.csv",
                     usecols=["pair_id", "classe", "assunto"])
    aggregate(sig, ["classe", "assunto"],
              "sig_lawsuits_muni_zona_classe_assunto.csv", pair_map=xw)

if __name__ == "__main__":
    main()
