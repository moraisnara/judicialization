from __future__ import annotations

import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

CDN_BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas"

# (cdn_zip_stem, local_folder_name)
TARGETS: list[tuple[str, str]] = [
    ("prestacao_de_contas_eleitorais_candidatos_2020", "spce_candidatos_2020"),
    ("prestacao_de_contas_eleitorais_candidatos_2024", "spce_candidatos_2024"),
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


def download_zip(cdn_stem: str, zip_path: Path) -> None:
    url = f"{CDN_BASE}/{cdn_stem}.zip"
    print(f"  Downloading {cdn_stem}.zip from TSE CDN ...")
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
            brasil_members = [m for m in zf.namelist() if "_BRASIL" in m]
            for member in brasil_members:
                zf.extract(member, dest_folder)
    except BadZipFile as exc:
        raise RuntimeError(f"Bad ZIP file {zip_path}: {exc}") from exc


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"TSE SPCE despesas download — {started_at}")
    print(f"Destination: {RAW_DIR}\n")

    downloaded: list[str] = []
    extracted: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for cdn_stem, folder_name in TARGETS:
        local_folder = RAW_DIR / folder_name
        zip_path = RAW_DIR / f"{cdn_stem}.zip"

        if folder_has_csv(local_folder):
            skipped.append(folder_name)
            print(f"SKIP  {folder_name}")
            continue

        print(f"FETCH {folder_name}")
        try:
            if not zip_path.exists():
                download_zip(cdn_stem, zip_path)
                downloaded.append(cdn_stem)
            else:
                print(f"  ZIP already on disk: {zip_path.name}")
                extracted.append(cdn_stem)

            print(f"  Extracting to {folder_name}/")
            extract_zip(zip_path, local_folder)
            csv_files = list(local_folder.glob("*.csv"))
            print(f"  OK — {len(csv_files)} CSV file(s) extracted")
        except RuntimeError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            failed.append((cdn_stem, str(exc)))

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
