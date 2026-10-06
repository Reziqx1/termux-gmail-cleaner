"""Local, credential-free cleanup presets for Termux Gmail Cleaner."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

PRESET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DEFAULT_PRESET_DIR = Path.home() / ".config" / "gmail-cleaner" / "presets"

_PRESET_TYPES = {
    "query": str,
    "max_results": int,
    "preview": int,
    "candidate_older_than": int,
    "report_format": str,
}


def validate_preset_name(name: str) -> str:
    """Validate a preset name and return it unchanged."""
    if not PRESET_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            "Preset name must contain only letters, numbers, '.', '_' or '-'."
        )
    return name


def preset_path(name: str, preset_dir: Path = DEFAULT_PRESET_DIR) -> Path:
    """Return the validated path for a local preset."""
    validate_preset_name(name)
    return preset_dir.expanduser() / f"{name}.toml"


def _validate_mapping(data: dict[str, Any], source: Path) -> dict[str, Any]:
    """Validate supported preset fields and return a normalized mapping."""
    unknown = set(data) - set(_PRESET_TYPES) - {"candidate_categories"}
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"{source}: unsupported field(s): {names}")

    normalized: dict[str, Any] = {}
    for field, expected in _PRESET_TYPES.items():
        if field not in data:
            continue
        value = data[field]
        if expected is int and isinstance(value, bool):
            raise TypeError(f"{source}: {field} must be an integer")
        if not isinstance(value, expected):
            raise TypeError(
                f"{source}: {field} must be {expected.__name__}, got {type(value).__name__}"
            )
        normalized[field] = value

    categories = data.get("candidate_categories")
    if categories is not None:
        if not isinstance(categories, list) or not categories or not all(
            isinstance(item, str) and item.strip() for item in categories
        ):
            raise ValueError(
                f"{source}: candidate_categories must be a non-empty string list"
            )
        normalized["candidate_categories"] = list(categories)

    if "query" not in normalized or not normalized["query"].strip():
        raise ValueError(f"{source}: query is required")
    if "max_results" in normalized and normalized["max_results"] <= 0:
        raise ValueError(f"{source}: max_results must be greater than zero")
    if "preview" in normalized and normalized["preview"] < 0:
        raise ValueError(f"{source}: preview cannot be negative")
    if (
        "candidate_older_than" in normalized
        and normalized["candidate_older_than"] < 0
    ):
        raise ValueError(f"{source}: candidate_older_than cannot be negative")
    if "report_format" in normalized and normalized["report_format"] not in {
        "json",
        "human",
    }:
        raise ValueError(f"{source}: report_format must be 'json' or 'human'")

    return normalized


def load_preset(name: str, preset_dir: Path = DEFAULT_PRESET_DIR) -> dict[str, Any]:
    """Load and strictly validate one local TOML preset."""
    path = preset_path(name, preset_dir)
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Preset not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path}: invalid TOML: {exc}") from exc

    if not isinstance(raw, dict):
        raise TypeError(f"{path}: preset root must be a TOML table")
    return _validate_mapping(raw, path)


def list_presets(preset_dir: Path = DEFAULT_PRESET_DIR) -> list[str]:
    """Return valid-looking preset names in deterministic order."""
    directory = preset_dir.expanduser()
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise NotADirectoryError(f"Preset directory is not a directory: {directory}")
    return sorted(
        path.stem
        for path in directory.glob("*.toml")
        if path.is_file() and PRESET_NAME_PATTERN.fullmatch(path.stem)
    )


def preset_to_toml(name: str, preset_dir: Path = DEFAULT_PRESET_DIR) -> str:
    """Return the raw TOML text of one validated preset."""
    path = preset_path(name, preset_dir)
    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {path}")
    load_preset(name, preset_dir)
    return path.read_text(encoding="utf-8")
