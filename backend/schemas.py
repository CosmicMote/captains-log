from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class JournalEntryResponse(BaseModel):
    id: int
    date: date
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    prev_date: Optional[date] = None
    next_date: Optional[date] = None

    model_config = {"from_attributes": True}


class JournalEntryUpsert(BaseModel):
    content: str
