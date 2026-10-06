"""Portable configuration and credential path resolution."""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "gmail-cleaner"
CONFIG_DIR_ENV = "GMAIL_CLEANER_CONFIG_DIR"
CREDENTIALS_ENV = "GMAIL_CREDENTIALS"
TOKEN_ENV = "GMAIL_TOKEN"
PRESET_DIR_ENV = "GMAIL_CLEANER_PRESET_DIR"


def config_dir() -> Path:
    """Return the application configuration directory."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / APP_DIR_NAME


def _legacy_local_path(filename: str) -> Path | None:
    """Return a legacy working-directory path when it already exists."""
    if CONFIG_DIR_ENV in os.environ:
        return None
    path = Path(filename)
    return path if path.is_file() else None


def credentials_path(explicit: Path | None = None) -> Path:
    """Resolve OAuth client credentials with compatibility fallback."""
    if explicit is not None:
        return explicit.expanduser()
    override = os.environ.get(CREDENTIALS_ENV)
    if override:
        return Path(override).expanduser()
    legacy = _legacy_local_path("credentials.json")
    if legacy is not None:
        return legacy
    return config_dir() / "credentials.json"


def token_path(explicit: Path | None = None) -> Path:
    """Resolve OAuth token with compatibility fallback."""
    if explicit is not None:
        return explicit.expanduser()
    override = os.environ.get(TOKEN_ENV)
    if override:
        return Path(override).expanduser()
    legacy = _legacy_local_path("token.json")
    if legacy is not None:
        return legacy
    return config_dir() / "token.json"


def preset_dir(explicit: Path | None = None) -> Path:
    """Resolve local preset directory with explicit/env/default precedence."""
    if explicit is not None:
        return explicit.expanduser()
    override = os.environ.get(PRESET_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return config_dir() / "presets"
