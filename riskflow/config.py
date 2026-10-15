"""Configuration with explicit paths; no third-party runtime dependencies."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def rules():
    return json.loads((ROOT / "config/rules.json").read_text(encoding="utf-8"))
