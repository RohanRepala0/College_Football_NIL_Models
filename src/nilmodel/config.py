"""Paths and HTTP settings."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("NIL_ROOT", Path(__file__).resolve().parents[2]))
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPORTS_DIR = ROOT / "reports"
DB_PATH = Path(os.environ.get("NIL_DB", DATA_DIR / "nil.duckdb"))

USER_AGENT = "nilmodel/0.1 (personal research; contact via GitHub RohanRepala0)"
TIMEOUT_SECONDS = 30


def secret(name: str) -> str | None:
    """A secret from the environment, else from the git-ignored .env file in the repository root."""
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name and value.strip():
                return value.strip()
    return None

