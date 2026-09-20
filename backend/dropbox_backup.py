"""Dropbox backup integration for Captain's Log.

Encrypts the SQLite database using the same AES-256-GCM scheme as the manual
export feature and uploads the result to the user's Dropbox.
"""

import logging
import os
import re
from datetime import datetime, timezone

import dropbox
from dropbox import files as dbx_files

import auth_config
import backup as backup_utils
from database import DB_PATH

logger = logging.getLogger(__name__)

DEFAULT_MAX_BACKUPS = 5

# Only files matching our own naming scheme are ever pruned
_BACKUP_NAME_RE = re.compile(r"^captains-log-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.clog$")


def get_max_backups() -> int:
    """Number of backups to retain, from MAX_BACKUPS (default 5, minimum 1)."""
    raw = os.environ.get("MAX_BACKUPS", "").strip()
    if not raw:
        return DEFAULT_MAX_BACKUPS
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid MAX_BACKUPS %r; using %d", raw, DEFAULT_MAX_BACKUPS)
        return DEFAULT_MAX_BACKUPS
    if value < 1:
        logger.warning("MAX_BACKUPS must be at least 1 (got %d); using 1", value)
        return 1
    return value


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


def prune_backups(dbx: dropbox.Dropbox, dropbox_path: str, keep: int) -> None:
    """Delete the oldest backups in dropbox_path so that at most `keep` remain."""
    result = dbx.files_list_folder(dropbox_path)
    entries = list(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)

    # The filename embeds a sortable timestamp, so name order is age order
    backups = sorted(
        e.name for e in entries
        if isinstance(e, dbx_files.FileMetadata) and _BACKUP_NAME_RE.match(e.name)
    )
    for name in backups[:max(len(backups) - keep, 0)]:
        dbx.files_delete_v2(f"{dropbox_path}/{name}")
        logger.info("Deleted old Dropbox backup: %s/%s", dropbox_path, name)


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

    # The upload already succeeded, so a cleanup failure must not fail the backup
    try:
        prune_backups(dbx, dropbox_path, get_max_backups())
    except Exception as exc:
        logger.warning("Could not prune old Dropbox backups: %s", exc)

    return filename
