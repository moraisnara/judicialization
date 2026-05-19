from __future__ import annotations

from csv import DictWriter
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOG_PATH = PROJECT_ROOT / "logs" / "tse_processual_inventory.csv"

# Canonical dataset entries: (dataset_name, folder, csv_glob_pattern)
# csv_glob_pattern is used when the exact filename is uncertain (e.g. assuntos files
# not yet downloaded when this list was written). A literal filename takes priority.
DATASETS: list[dict] = [
    # --- 2018 ---
    {"dataset_name": "processo_eleitoral_2018",
     "folder": "processo_eleitoral_2018",
     "csv_pattern": "processo_eleitoral_2018.csv"},
    {"dataset_name": "assuntos_2018",
     "folder": "processos_eleitorais_assuntos_2018",
     "csv_pattern": "*.csv"},
    {"dataset_name": "decisoes_2018",
     "folder": "decisoes_2018",
     "csv_pattern": "processos_eleitorais_decisoes_2018.csv"},
    {"dataset_name": "recursos_2018",
     "folder": "recursos_2018",
     "csv_pattern": "recursos_eleitorais_2018.csv"},
    # --- 2020 ---
    {"dataset_name": "processo_eleitoral_2020",
     "folder": "processo_eleitoral_2020",
     "csv_pattern": "processo_eleitoral_2020.csv"},
    {"dataset_name": "assuntos_2020",
     "folder": "processos_eleitorais_assuntos_2020",
     "csv_pattern": "*.csv"},
    {"dataset_name": "decisoes_2020",
     "folder": "decisoes_2020",
     "csv_pattern": "processos_eleitorais_decisoes_2020.csv"},
    {"dataset_name": "recursos_2020",
     "folder": "recursos_2020",
     "csv_pattern": "recursos_eleitorais_2020.csv"},
    {"dataset_name": "partes_2020",
     "folder": "processos_eleitorais_partes_2020",
     "csv_pattern": "processos_eleitorais_partes_2020.csv"},
    {"dataset_name": "consulta_cand_2020_brasil",
     "folder": "consulta_cand_2020",
     "csv_pattern": "consulta_cand_2020_BRASIL.csv"},
    # --- 2022 ---
    {"dataset_name": "processo_eleitoral_2022",
     "folder": "processo_eleitoral_2022",
     "csv_pattern": "processo_eleitoral_2022.csv"},
    {"dataset_name": "assuntos_2022",
     "folder": "processos_eleitorais_assuntos_2022",
     "csv_pattern": "*.csv"},
    {"dataset_name": "decisoes_2022",
     "folder": "decisoes_2022",
     "csv_pattern": "processos_eleitorais_decisoes_2022.csv"},
    {"dataset_name": "recursos_2022",
     "folder": "recursos_2022",
     "csv_pattern": "recursos_eleitorais_2022.csv"},
    # --- 2024 ---
    {"dataset_name": "processo_eleitoral_2024",
     "folder": "processo_eleitoral_2024",
     "csv_pattern": "processo_eleitoral_2024.csv"},
    {"dataset_name": "assuntos_2024",
     "folder": "processos_eleitorais_assuntos_2024",
     "csv_pattern": "*.csv"},
    {"dataset_name": "decisoes_2024",
     "folder": "decisoes_2024",
     "csv_pattern": "processos_eleitorais_decisoes_2024.csv"},
    {"dataset_name": "recursos_2024",
     "folder": "recursos_2024",
     "csv_pattern": "recursos_eleitorais_2024.csv"},
]


def resolve_csv(folder: Path, csv_pattern: str) -> Path | None:
    if "*" not in csv_pattern:
        candidate = folder / csv_pattern
        return candidate if candidate.exists() else None
    matches = [p for p in folder.glob(csv_pattern) if p.suffix == ".csv"]
    if not matches:
        return None
    # If multiple matches, prefer the largest file (skip leiame-style tiny files)
    return max(matches, key=lambda p: p.stat().st_size)


def read_head_lines(path: Path, n_lines: int) -> list[str]:
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _ in range(n_lines):
            line = handle.readline()
            if not line:
                break
            lines.append(line.rstrip("\n").rstrip("\r"))
    return lines


def main() -> None:
    rows = []
    inventoried_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    missing: list[str] = []

    for dataset in DATASETS:
        folder = RAW_DIR / dataset["folder"]
        csv_path = resolve_csv(folder, dataset["csv_pattern"])

        if csv_path is None:
            missing.append(dataset["dataset_name"])
            print(f"MISSING  {dataset['dataset_name']}  ({folder})")
            continue

        sample_lines = read_head_lines(csv_path, 3)
        if not sample_lines:
            print(f"EMPTY    {dataset['dataset_name']}")
            continue

        columns = sample_lines[0].split(";")
        rows.append(
            {
                "dataset_name": dataset["dataset_name"],
                "csv_path": csv_path.relative_to(PROJECT_ROOT).as_posix(),
                "file_size_mb": f"{csv_path.stat().st_size / (1024 * 1024):.3f}",
                "column_count": str(len(columns)),
                "columns": " | ".join(columns),
                "sample_row_1": sample_lines[1] if len(sample_lines) >= 2 else "",
                "sample_row_2": sample_lines[2] if len(sample_lines) >= 3 else "",
                "inventoried_at": inventoried_at,
            }
        )
        print(f"OK       {dataset['dataset_name']}  ({len(columns)} columns, "
              f"{csv_path.stat().st_size / (1024*1024):.1f} MB)")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(
            handle,
            fieldnames=[
                "dataset_name",
                "csv_path",
                "file_size_mb",
                "column_count",
                "columns",
                "sample_row_1",
                "sample_row_2",
                "inventoried_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nInventoried {len(rows)} datasets -> {LOG_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    if missing:
        print(f"Missing (run 01_download_processual.py first): {missing}")


if __name__ == "__main__":
    main()
