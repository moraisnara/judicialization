"""
Download TSE 'Comparecimento e Abstencao' profile data for 2020 and 2024.

This is the DISAGGREGATED turnout product: it reports QT_APTOS,
QT_COMPARECIMENTO and QT_ABSTENCAO broken out by voter characteristics
(sex, age band, education, marital status) at municipality x zone level.

Unlike detalhe_votacao_munzona (which the aggregate electoral-admin build
uses), this file lets us separate COMPULSORY (ages 18-69) from FACULTATIVE
(16, 17, 70+) voters and study turnout by education / gender.

It does NOT carry blank/null counts, so spoilage stays aggregate-only.

Source dataset: dadosabertos.tse.jus.br -> 'Comparecimento e Abstencao - {year}'
Main resource:  perfil_comparecimento_abstencao_{year}.zip (per-UF CSVs).

Output: data/raw/perfil_comparecimento_abstencao_{year}/ (extracted CSVs).
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from zipfile import BadZipFile, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

CKAN_BASE = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id="
# (CKAN slug, resource-name substring, local folder name)
TARGETS: list[tuple[str, str, str]] = [
    ("comparecimento-e-abstencao-2020", "Comparecimento e Absten",
     "perfil_comparecimento_abstencao_2020"),
    ("comparecimento-e-abstencao-2024", "Comparecimento e Absten",
     "perfil_comparecimento_abstencao_2024"),
]


def folder_has_csv(folder: Path) -> bool:
    return folder.exists() and any(folder.glob("*.csv"))


def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100.0, downloaded * 100.0 / total_size)
        mb = downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        print(f"\r  {mb:.1f} / {total_mb:.1f} MB  ({pct:.0f}%)", end="", flush=True)


def fetch_dataset_metadata(slug: str) -> dict:
    with urllib.request.urlopen(CKAN_BASE + slug, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("success"):
        raise RuntimeError(f"CKAN lookup failed for {slug}")
    return payload["result"]


def find_resource_url(meta: dict, name_sub: str) -> str:
    # Prefer the EXACT main resource (avoid 'deficiente' / 'tte' siblings).
    main = [r for r in meta.get("resources", [])
            if name_sub.lower() in r.get("name", "").lower()
            and "defici" not in r.get("name", "").lower()
            and "tempor" not in r.get("name", "").lower()]
    if not main:
        raise RuntimeError(f"Main resource '{name_sub}' not found in {meta.get('name')}")
    url = main[0].get("url")
    if not url:
        raise RuntimeError(f"Resource '{name_sub}' has no URL")
    return url


def download_zip(url: str, zip_path: Path) -> None:
    print(f"  Downloading {zip_path.name} ...")
    urllib.request.urlretrieve(url, zip_path, reporthook=progress_hook)
    print()


def extract_zip(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(zip_path, "r") as zf:
            zf.extractall(dest)
    except BadZipFile as exc:
        raise RuntimeError(f"Bad ZIP {zip_path}: {exc}") from exc


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"TSE comparecimento/abstencao download\nDestination: {RAW_DIR}\n")

    failed: list[tuple[str, str]] = []
    for slug, name_sub, folder_name in TARGETS:
        local = RAW_DIR / folder_name
        zip_path = RAW_DIR / f"{folder_name}.zip"
        if folder_has_csv(local):
            print(f"SKIP  {folder_name}")
            continue
        print(f"FETCH {folder_name}")
        try:
            meta = fetch_dataset_metadata(slug)
            url = find_resource_url(meta, name_sub)
            if not zip_path.exists():
                download_zip(url, zip_path)
            else:
                print(f"  ZIP already on disk: {zip_path.name}")
            print(f"  Extracting to {folder_name}/")
            extract_zip(zip_path, local)
            print(f"  OK - {len(list(local.glob('*.csv')))} CSV file(s)")
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}", file=sys.stderr)
            failed.append((folder_name, str(exc)))

    if failed:
        print(f"\nFailed: {len(failed)}", file=sys.stderr)
        for name, err in failed:
            print(f"  ! {name}: {err}", file=sys.stderr)
        sys.exit(1)
    print("\nDone.")


if __name__ == "__main__":
    main()
