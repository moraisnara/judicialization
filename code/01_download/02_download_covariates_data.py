"""
Downloads TSE data files needed for covariate construction:
  - votacao_candidato_munzona_2016  (2016 electoral controls)
  - consulta_cand_2012              (candidate history)
  - consulta_cand_2016              (candidate history)
  - detalhe_votacao_munzona_2020    (electoral admin outcomes)
  - detalhe_votacao_munzona_2024    (electoral admin outcomes)
"""
from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"

FILES = [
    (f"{BASE}/votacao_candidato_munzona/votacao_candidato_munzona_2016.zip",
     "votacao_candidato_munzona_2016"),
    (f"{BASE}/consulta_cand/consulta_cand_2012.zip",
     "consulta_cand_2012"),
    (f"{BASE}/consulta_cand/consulta_cand_2016.zip",
     "consulta_cand_2016"),
    (f"{BASE}/detalhe_votacao_munzona/detalhe_votacao_munzona_2020.zip",
     "detalhe_votacao_munzona_2020"),
    (f"{BASE}/detalhe_votacao_munzona/detalhe_votacao_munzona_2024.zip",
     "detalhe_votacao_munzona_2024"),
]


def download_and_unzip(url: str, dest_dir: str) -> None:
    dest = RAW_DIR / dest_dir
    if dest.exists() and any(dest.iterdir()):
        print(f"  Already exists: {dest_dir}", flush=True)
        return
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / f"{dest_dir}.zip"
    print(f"  Downloading {dest_dir} ...", flush=True)

    def _progress(count, block, total):
        if total > 0 and count % 500 == 0:
            pct = min(100, count * block / total * 100)
            print(f"    {pct:.0f}%", flush=True)

    urllib.request.urlretrieve(url, zip_path, reporthook=_progress)
    print(f"  Unzipping {dest_dir} ...", flush=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    zip_path.unlink()
    print(f"  Done: {dest_dir}", flush=True)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for url, dest_dir in FILES:
        download_and_unzip(url, dest_dir)
    print("\nAll downloads complete.")


if __name__ == "__main__":
    main()
