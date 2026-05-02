"""Manages the auth config file (hashed password + JWT secret)."""

import json
import os
import secrets
from pathlib import Path

# Mirrors the logic in database.py — dev uses the backend dir, Docker uses /data.
_data_dir = Path(os.environ.get("JOURNAL_DATA_DIR", Path(__file__).parent))
CONFIG_PATH = _data_dir / "auth_config.json"


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


# ── Dropbox backup config ──────────────────────────────────────────────────────

def get_dropbox_config() -> dict | None:
    """Return the Dropbox config dict, or None if not configured."""
    return _load().get("dropbox")


def set_dropbox_config(updates: dict) -> None:
    """Merge updates into the Dropbox config, preserving existing secret fields
    when the caller passes an empty string (i.e. 'leave unchanged')."""
    config = _load()
    existing = config.get("dropbox", {})
    # Secret fields: keep existing value when update is blank
    for secret_key in ("app_secret", "refresh_token", "backup_password"):
        if not updates.get(secret_key, "").strip():
            updates[secret_key] = existing.get(secret_key, "")
    existing.update(updates)
    config["dropbox"] = existing
    _save(config)


def clear_dropbox_config() -> None:
    """Remove Dropbox configuration entirely."""
    config = _load()
    config.pop("dropbox", None)
    _save(config)


def record_dropbox_backup(filename: str, timestamp: str) -> None:
    """Persist the timestamp and filename of the most recent successful backup."""
    config = _load()
    if "dropbox" in config:
        config["dropbox"]["last_backup_at"] = timestamp
        config["dropbox"]["last_backup_file"] = filename
        _save(config)
