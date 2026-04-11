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


def get_ssl_config() -> dict | None:
    """Return SSL config dict with 'certfile' and 'keyfile', or None if not configured."""
    return _load().get("ssl")


def set_ssl_config(certfile: str, keyfile: str) -> None:
    """Persist SSL certificate and key file paths."""
    config = _load()
    config["ssl"] = {"certfile": certfile, "keyfile": keyfile}
    _save(config)


def clear_ssl_config() -> None:
    """Remove SSL configuration (reverts to HTTP)."""
    config = _load()
    config.pop("ssl", None)
    _save(config)
