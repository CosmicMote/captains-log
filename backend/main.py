import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

import models
import schemas
import auth
import auth_config
import backup as backup_utils
import dropbox_backup
from database import engine, get_db, DB_PATH

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)


# ── Periodic Dropbox backup task ──────────────────────────────────────────────

async def _dropbox_backup_loop() -> None:
    """Check every 30 minutes whether a scheduled Dropbox backup is due."""
    # Initial delay so a restart doesn't hammer Dropbox immediately
    await asyncio.sleep(30 * 60)
    while True:
        try:
            config = auth_config.get_dropbox_config()
            if config and config.get("backup_password", "").strip():
                interval_hours = config.get("interval_hours", 24)
                last_at = config.get("last_backup_at")
                if last_at:
                    last_dt = datetime.fromisoformat(last_at)
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    due = last_dt + timedelta(hours=interval_hours)
                    should_run = datetime.now(timezone.utc) >= due
                else:
                    should_run = True  # never backed up → do it now

                if should_run:
                    filename = dropbox_backup.run_backup()
                    logger.info("Scheduled Dropbox backup complete: %s", filename)
        except Exception as exc:
            logger.error("Scheduled Dropbox backup failed: %s", exc)

        await asyncio.sleep(30 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_dropbox_backup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Personal Journal API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(body: schemas.LoginRequest):
    stored_hash = auth_config.get_password_hash()
    if not stored_hash:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No password configured. Run setup_password.py first.",
        )
    if not auth.verify_password(body.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    return {"access_token": auth.create_token(), "token_type": "bearer"}


# ── File backup (export / import) ─────────────────────────────────────────────

@app.post("/backup/export")
def export_backup(
    body: dict,
    _: None = Depends(auth.require_auth),
):
    password = body.get("password", "").strip()
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    try:
        encrypted = backup_utils.encrypt_db(DB_PATH, password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"captains-log-{today}.clog"
    return Response(
        content=encrypted,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/backup/import")
async def import_backup(
    file: UploadFile = File(...),
    password: str = Form(...),
    _: None = Depends(auth.require_auth),
):
    data = await file.read()

    try:
        db_bytes = backup_utils.decrypt_backup(data, password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not backup_utils.is_valid_sqlite(db_bytes):
        raise HTTPException(
            status_code=400,
            detail="Decrypted data is not a valid SQLite database",
        )

    engine.dispose()

    try:
        DB_PATH.write_bytes(db_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write database: {e}")

    models.Base.metadata.create_all(bind=engine)
    return {"message": "Database restored successfully"}


# ── Dropbox settings ──────────────────────────────────────────────────────────

@app.get("/settings/dropbox")
def get_dropbox_settings(_: None = Depends(auth.require_auth)):
    config = auth_config.get_dropbox_config()
    if not config or not config.get("refresh_token"):
        return {"configured": False}
    return {
        "configured": True,
        "app_key":          config.get("app_key", ""),
        "dropbox_path":     config.get("dropbox_path", "/Captain's Log Backups"),
        "interval_hours":   config.get("interval_hours", 24),
        "has_password":     bool(config.get("backup_password", "").strip()),
        "last_backup_at":   config.get("last_backup_at"),
        "last_backup_file": config.get("last_backup_file"),
        # Secrets (app_secret, refresh_token, backup_password) are never returned
    }


@app.put("/settings/dropbox")
def save_dropbox_settings(body: dict, _: None = Depends(auth.require_auth)):
    # Validate that new credentials are complete when no credentials exist yet
    existing = auth_config.get_dropbox_config() or {}
    is_new = not existing.get("refresh_token")
    if is_new:
        missing = [k for k in ("app_key", "app_secret", "refresh_token", "backup_password")
                   if not body.get(k, "").strip()]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}",
            )
    auth_config.set_dropbox_config(body)
    return {"ok": True}


@app.delete("/settings/dropbox")
def clear_dropbox_settings(_: None = Depends(auth.require_auth)):
    auth_config.clear_dropbox_config()
    return {"ok": True}


@app.post("/settings/dropbox/backup-now")
def dropbox_backup_now(_: None = Depends(auth.require_auth)):
    try:
        filename = dropbox_backup.run_backup()
        return {"ok": True, "filename": filename}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dropbox upload failed: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_adjacent_dates(entry_date, db: Session):
    prev = (
        db.query(models.JournalEntry.date)
        .filter(models.JournalEntry.date < entry_date)
        .order_by(desc(models.JournalEntry.date))
        .first()
    )
    next_ = (
        db.query(models.JournalEntry.date)
        .filter(models.JournalEntry.date > entry_date)
        .order_by(asc(models.JournalEntry.date))
        .first()
    )
    return (prev.date if prev else None, next_.date if next_ else None)


# ── Entries (protected) ───────────────────────────────────────────────────────

@app.get("/entries/dates", response_model=List[str])
def list_entry_dates(
    db: Session = Depends(get_db),
    _: None = Depends(auth.require_auth),
):
    entries = (
        db.query(models.JournalEntry.date)
        .order_by(asc(models.JournalEntry.date))
        .all()
    )
    return [str(e.date) for e in entries]


@app.get("/entries/{entry_date}", response_model=schemas.JournalEntryResponse)
def get_entry(
    entry_date: date,
    db: Session = Depends(get_db),
    _: None = Depends(auth.require_auth),
):
    entry = (
        db.query(models.JournalEntry)
        .filter(models.JournalEntry.date == entry_date)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    prev_date, next_date = _get_adjacent_dates(entry_date, db)
    result = schemas.JournalEntryResponse.model_validate(entry)
    result.prev_date = prev_date
    result.next_date = next_date
    return result


@app.put("/entries/{entry_date}", response_model=schemas.JournalEntryResponse)
def upsert_entry(
    entry_date: date,
    body: schemas.JournalEntryUpsert,
    db: Session = Depends(get_db),
    _: None = Depends(auth.require_auth),
):
    entry = (
        db.query(models.JournalEntry)
        .filter(models.JournalEntry.date == entry_date)
        .first()
    )
    if entry:
        entry.content = body.content
        entry.updated_at = datetime.now(timezone.utc)
    else:
        entry = models.JournalEntry(date=entry_date, content=body.content)
        db.add(entry)
    db.commit()
    db.refresh(entry)
    prev_date, next_date = _get_adjacent_dates(entry_date, db)
    result = schemas.JournalEntryResponse.model_validate(entry)
    result.prev_date = prev_date
    result.next_date = next_date
    return result
