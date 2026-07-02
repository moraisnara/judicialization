from __future__ import annotations

import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

CDN_BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"

TARGETS: list[tuple[str, str, str]] = [
    ("consulta_cand", "consulta_cand_2024", "consulta_cand_2024"),
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
    print(f"TSE candidate-data download — {started_at}")
    print(f"Destination: {RAW_DIR}\n")

    downloaded: list[str] = []
    extracted: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for family, zip_stem, folder_name in TARGETS:
        local_folder = RAW_DIR / folder_name
        zip_path = RAW_DIR / f"{zip_stem}.zip"
        url = f"{CDN_BASE}/{family}/{zip_stem}.zip"

        if folder_has_csv(local_folder):
            skipped.append(folder_name)
            print(f"SKIP  {folder_name}")
            continue

        print(f"FETCH {folder_name}")
        try:
            if not zip_path.exists():
                download_zip(url, zip_path)
                downloaded.append(zip_stem)
            else:
                print(f"  ZIP already on disk: {zip_path.name}")
                extracted.append(zip_stem)

            print(f"  Extracting to {folder_name}/")
            extract_zip(zip_path, local_folder)
            csv_files = list(local_folder.glob("*.csv"))
            print(f"  OK — {len(csv_files)} CSV file(s) extracted")
        except RuntimeError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            failed.append((zip_stem, str(exc)))

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
