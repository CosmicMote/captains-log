"""Manages the auth config file (hashed password + JWT secret)."""

import json
import secrets
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "auth_config.json"


def _load() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text())


def _save(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_jwt_secret() -> str:
    """Return the JWT signing secret, generating and persisting one if needed."""
    config = _load()
    if "jwt_secret" not in config:
        config["jwt_secret"] = secrets.token_hex(32)
        _save(config)
    return config["jwt_secret"]


def get_password_hash() -> str | None:
    """Return the stored bcrypt password hash, or None if not yet set."""
    return _load().get("password_hash")


def set_password_hash(hashed: str) -> None:
    """Persist a new bcrypt password hash."""
    config = _load()
    config["password_hash"] = hashed
    _save(config)
