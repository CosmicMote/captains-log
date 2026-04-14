import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# In development the database lives next to this file.
# In Docker, JOURNAL_DATA_DIR is set to /data (a persistent volume).
_data_dir = Path(os.environ.get("JOURNAL_DATA_DIR", Path(__file__).parent))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_data_dir / 'journal.db'}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
