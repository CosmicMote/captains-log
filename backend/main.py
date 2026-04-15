from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import date, datetime, timezone
from typing import List, Optional

import models
import schemas
import auth
import auth_config
import backup as backup_utils
from database import engine, get_db, DB_PATH

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Journal API")

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_adjacent_dates(entry_date: date, db: Session):
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


# ── Backup (protected) ───────────────────────────────────────────────────────

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

    # Close all pooled connections before swapping the file
    engine.dispose()

    try:
        DB_PATH.write_bytes(db_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write database: {e}")

    # Ensure schema is current on the restored database
    models.Base.metadata.create_all(bind=engine)

    return {"message": "Database restored successfully"}


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
