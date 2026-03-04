"""Load and parse YAML pipeline configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "orchestration" / "pipelines.yaml"


def load_orchestration_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load pipeline config from YAML file."""
    config_path = Path(path or os.environ.get("HALEBOPP_CONFIG", DEFAULT_CONFIG_PATH))

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
