from __future__ import annotations

from csv import DictWriter
from datetime import datetime
from hashlib import sha256
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "logs" / "raw_data_manifest.csv"
REQUIRED_FILES = [
    PROJECT_ROOT / "data" / "raw" / "processo_eleitoral_2020.zip",
    PROJECT_ROOT / "data" / "raw" / "decisoes_2020.zip",
    PROJECT_ROOT / "data" / "raw" / "recursos_2020.zip",
    PROJECT_ROOT / "data" / "raw" / "processos_eleitorais_partes_2020.zip",
    PROJECT_ROOT / "data" / "raw" / "consulta_cand_2020.zip",
    PROJECT_ROOT / "data" / "raw" / "processo_eleitoral_2024.zip",
    PROJECT_ROOT / "data" / "raw" / "decisoes_2024.zip",
    PROJECT_ROOT / "data" / "raw" / "recursos_2024.zip",
]


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    for file_path in REQUIRED_FILES:
        if not file_path.exists():
            raise FileNotFoundError(f"Required raw file not found: {file_path}")

    rows = []
    verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for file_path in REQUIRED_FILES:
        rows.append(
            {
                "file_path": file_path.relative_to(PROJECT_ROOT).as_posix(),
                "algorithm": "SHA256",
                "sha256": file_sha256(file_path),
                "size_mb": f"{file_path.stat().st_size / (1024 * 1024):.3f}",
                "verified_at": verified_at,
            }
        )

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(
            handle,
            fieldnames=["file_path", "algorithm", "sha256", "size_mb", "verified_at"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Verified raw files and wrote {LOG_PATH.relative_to(PROJECT_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
