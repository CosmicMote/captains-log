"""Dropbox backup integration for Captain's Log.

Encrypts the SQLite database using the same AES-256-GCM scheme as the manual
export feature and uploads the result to the user's Dropbox.
"""

import logging
from datetime import datetime, timezone

import dropbox
from dropbox import files as dbx_files

import auth_config
import backup as backup_utils
from database import DB_PATH

logger = logging.getLogger(__name__)


def get_client() -> dropbox.Dropbox:
    """Return an authenticated Dropbox client, or raise ValueError if not configured."""
    config = auth_config.get_dropbox_config()
    if not config:
        raise ValueError("Dropbox is not configured")
    for key in ("app_key", "app_secret", "refresh_token"):
        if not config.get(key, "").strip():
            raise ValueError(f"Dropbox config is missing: {key}")
    return dropbox.Dropbox(
        app_key=config["app_key"],
        app_secret=config["app_secret"],
        oauth2_refresh_token=config["refresh_token"],
    )


def run_backup() -> str:
    """Encrypt the database and upload to Dropbox. Returns the uploaded filename."""
    config = auth_config.get_dropbox_config()
    if not config:
        raise ValueError("Dropbox is not configured")

    password = config.get("backup_password", "").strip()
    if not password:
        raise ValueError("No backup password configured for Dropbox backups")

    if not DB_PATH.exists():
        raise ValueError("Database file not found")

    dropbox_path = config.get("dropbox_path", "/Captain's Log Backups").rstrip("/")

    # Encrypt using the same scheme as the manual export
    encrypted = backup_utils.encrypt_db(DB_PATH, password)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"captains-log-{ts}.clog"
    dest_path = f"{dropbox_path}/{filename}"

    dbx = get_client()
    dbx.files_upload(encrypted, dest_path, mode=dbx_files.WriteMode.add)

    # Record the successful backup
    auth_config.record_dropbox_backup(
        filename=filename,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    logger.info("Dropbox backup uploaded: %s", dest_path)
    return filename
