import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visaflow.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from backend.models import db  # noqa: F401

    Base.metadata.create_all(bind=engine)
