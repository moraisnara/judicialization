"""Load the canonical estimation-design config (code/spec_config.json).

Single source of truth for control lists, FE, clustering, and the per-outcome
lagged-DV map. See SPECIFICATION.md. Import from estimation/analysis scripts
instead of hard-coding control lists.

Usage:
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1] / "utils"))
    from spec_config import CONFIG, baseline_controls, extended_controls, lagged_dv

    controls = baseline_controls() + [lagged_dv(outcome)]   # per-outcome spec
"""
from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "spec_config.json"

with _CONFIG_PATH.open(encoding="utf-8") as _fh:
    CONFIG = json.load(_fh)


def baseline_controls() -> list[str]:
    """Universal baseline controls (lagged DV is appended per-outcome)."""
    return list(CONFIG["baseline_controls"])


def extended_controls() -> list[str]:
    """Baseline controls plus the extended robustness block."""
    return baseline_controls() + list(CONFIG["extended_controls_extra"])


def lagged_dv(outcome: str) -> str | None:
    """2020 level column to include as the lagged DV for a delta outcome."""
    return CONFIG["lagged_dv"].get(outcome)


def fe_col(which: str = "baseline") -> str:
    return CONFIG["fe"][which]


def cluster_col() -> str:
    return CONFIG["cluster"]


def instrument() -> str:
    return CONFIG["instrument"]


def endogenous() -> str:
    return CONFIG["endogenous"]

