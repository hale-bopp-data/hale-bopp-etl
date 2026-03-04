from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_orchestration_config(path: str | Path) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config not found: {file_path}")

    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML structure must be a dictionary")

    return data
