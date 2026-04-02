from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib


@dataclass(slots=True)
class RuntimeConfig:
    timeouts: dict[str, int]
    limits: dict[str, int]
    file_types: dict[str, list[str]]
    selectors: dict[str, Any]

    def selectors_list(self, key: str) -> list[str]:
        value = self.selectors.get(key, [])
        if isinstance(value, list):
            return [str(x) for x in value]
        return []

    def selector_string(self, key: str, default: str = "") -> str:
        value = self.selectors.get(key, default)
        return str(value)


def default_config_path() -> str:
    return str(Path(__file__).resolve().parents[1] / "config.toml")


def load_runtime_config(path: str | None = None) -> RuntimeConfig:
    config_path = Path(path or default_config_path())
    with config_path.open("rb") as f:
        data = tomllib.load(f)

    return RuntimeConfig(
        timeouts=data.get("timeouts", {}),
        limits=data.get("limits", {}),
        file_types=data.get("file_types", {}),
        selectors=data.get("selectors", {}),
    )
