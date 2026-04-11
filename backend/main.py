from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import date, datetime, timezone
from typing import List, Optional

import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Journal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/entries/dates", response_model=List[str])
def list_entry_dates(db: Session = Depends(get_db)):
    entries = (
        db.query(models.JournalEntry.date)
        .order_by(asc(models.JournalEntry.date))
        .all()
    )
    return [str(e.date) for e in entries]


@app.get("/entries/{entry_date}", response_model=schemas.JournalEntryResponse)
def get_entry(entry_date: date, db: Session = Depends(get_db)):
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
    entry_date: date, body: schemas.JournalEntryUpsert, db: Session = Depends(get_db)
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
