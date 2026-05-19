from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

CKAN_BASE = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id="
TARGET_DATASETS: list[tuple[str, str, str]] = [
    ("resultados-2020", "Votação nominal por município e zona", "votacao_candidato_munzona_2020"),
    ("resultados-2024", "Votação nominal por município e zona", "votacao_candidato_munzona_2024"),
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


def fetch_dataset_metadata(dataset_slug: str) -> dict:
    with urllib.request.urlopen(CKAN_BASE + dataset_slug) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("success"):
        raise RuntimeError(f"CKAN lookup failed for {dataset_slug}")
    return payload["result"]


def find_resource_url(dataset_meta: dict, resource_name: str) -> str:
    candidates = []
    for resource in dataset_meta.get("resources", []):
        name = resource.get("name", "")
        if resource_name.lower() in name.lower():
            candidates.append(resource)
    if not candidates:
        raise RuntimeError(f"Resource '{resource_name}' not found in dataset {dataset_meta.get('name')}")
    resource = candidates[0]
    url = resource.get("url")
    if not url:
        raise RuntimeError(f"Resource '{resource_name}' has no download URL")
    return url


def download_zip(url: str, zip_path: Path) -> None:
    print(f"  Downloading {zip_path.name} ...")
    try:
        urllib.request.urlretrieve(url, zip_path, reporthook=progress_hook)
        print()
    except Exception as exc:
        print()
        raise RuntimeError(f"Download failed for {url}: {exc}") from exc


def extract_zip(zip_path: Path, dest_folder: Path) -> None:
    dest_folder.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_folder)
    except BadZipFile as exc:
        raise RuntimeError(f"Bad ZIP file {zip_path}: {exc}") from exc


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"TSE vote-results download - {started_at}")
    print(f"Destination: {RAW_DIR}\n")

    downloaded: list[str] = []
    extracted: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for dataset_slug, resource_name, folder_name in TARGET_DATASETS:
        local_folder = RAW_DIR / folder_name
        zip_path = RAW_DIR / f"{folder_name}.zip"

        if folder_has_csv(local_folder):
            skipped.append(folder_name)
            print(f"SKIP  {folder_name}")
            continue

        print(f"FETCH {folder_name}")
        try:
            dataset_meta = fetch_dataset_metadata(dataset_slug)
            url = find_resource_url(dataset_meta, resource_name)
            if not zip_path.exists():
                download_zip(url, zip_path)
                downloaded.append(folder_name)
            else:
                print(f"  ZIP already on disk: {zip_path.name}")
                extracted.append(folder_name)
            print(f"  Extracting to {folder_name}/")
            extract_zip(zip_path, local_folder)
            csv_files = list(local_folder.glob("*.csv"))
            print(f"  OK - {len(csv_files)} CSV file(s) extracted")
        except RuntimeError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            failed.append((folder_name, str(exc)))

    print(f"\n--- Summary ({datetime.now().strftime('%H:%M:%S')}) ---")
    print(f"Downloaded and extracted : {len(downloaded)}")
    for name in downloaded:
        print(f"  + {name}")
    print(f"Extracted from existing ZIP: {len(extracted)}")
    for name in extracted:
        print(f"  + {name}")
    print(f"Skipped (already present): {len(skipped)}")
    if failed:
        print(f"Failed: {len(failed)}", file=sys.stderr)
        for name, err in failed:
            print(f"  ! {name}: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
