from __future__ import annotations

import os
from pathlib import Path

from core import build_dags_from_config, load_orchestration_config

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = BASE_DIR / "config" / "orchestration" / "pipelines.yaml"
CONFIG_PATH = Path(os.getenv("ETLBELVISO_ORCHESTRATION_CONFIG", str(DEFAULT_CONFIG)))

config = load_orchestration_config(CONFIG_PATH)
globals().update(build_dags_from_config(config))
