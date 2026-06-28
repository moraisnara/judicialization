r"""
09_download_bd_municipio_directory.py

Download the Base dos Dados municipality directory
(`basedosdados.br_bd_diretorios_brasil.municipio`) and build a region crosswalk
keyed by the TSE municipality id, so the analysis designs can carry IBGE
sub-state geography (meso/micro/immediate/intermediate region) for tighter
fixed-effects specifications.

Source: BD public one-click export (stable public bucket, no credentials).
  https://storage.googleapis.com/basedosdados-public/one-click-download/
      br_bd_diretorios_brasil/municipio/municipio.csv.gz

Writes:
  data/raw/bd_diretorio_municipio.csv        -- full directory table (archival)
  data/clean/municipio_region_crosswalk.csv  -- id_municipio_tse + region codes
"""
import gzip
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
RAW.mkdir(parents=True, exist_ok=True)
CLEAN.mkdir(parents=True, exist_ok=True)

URL = ("https://storage.googleapis.com/basedosdados-public/one-click-download/"
       "br_bd_diretorios_brasil/municipio/municipio.csv.gz")
RAW_CSV = RAW / "bd_diretorio_municipio.csv"

# ---- download (skip if already present) ----
if not RAW_CSV.exists():
    print(f"Downloading {URL} ...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        RAW_CSV.write_bytes(gzip.decompress(r.read()))
    print(f"  saved {RAW_CSV}")
else:
    print(f"Using cached {RAW_CSV}")

d = pd.read_csv(RAW_CSV, dtype=str)
print(f"Directory rows: {len(d):,}")

# ---- build crosswalk ----
REGION_COLS = [
    "id_municipio", "id_municipio_tse", "nome", "sigla_uf",
    "id_mesorregiao", "nome_mesorregiao",
    "id_microrregiao", "nome_microrregiao",
    "id_regiao_imediata", "nome_regiao_imediata",
    "id_regiao_intermediaria", "nome_regiao_intermediaria",
]
cw = d[[c for c in REGION_COLS if c in d.columns]].copy()
cw = cw[cw["id_municipio_tse"].notna()]

out = CLEAN / "municipio_region_crosswalk.csv"
cw.to_csv(out, index=False)
print(f"Wrote {out}  ({len(cw):,} rows)")
for lvl in ["sigla_uf", "id_mesorregiao", "id_microrregiao",
            "id_regiao_imediata", "id_regiao_intermediaria"]:
    if lvl in cw.columns:
        print(f"  {lvl:28s}: {cw[lvl].nunique()} unique")
