import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visaflow.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def configure_database(database_url: str):
    global DATABASE_URL, engine

    DATABASE_URL = database_url
    engine.dispose()
    engine = create_engine(DATABASE_URL, future=True)
    SessionLocal.configure(bind=engine)
    return engine


def init_db() -> None:
    from backend.models import db  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_compat_columns()


def _ensure_compat_columns() -> None:
    inspector = inspect(engine)
    compatibility_columns = {
        "agent_runs": [
            ("trace_id", _column_ddl("trace_id", default="")),
            ("observation_id", _column_ddl("observation_id", default="")),
            ("observability_export_status", _column_ddl("observability_export_status", default="DISABLED")),
            ("observability_target", _column_ddl("observability_target", default="LOCAL_ONLY")),
            ("evaluation_labels", _json_column_ddl("evaluation_labels", default="[]")),
        ],
        "audit_events": [
            ("trace_id", _column_ddl("trace_id", default="")),
            ("observation_id", _column_ddl("observation_id", default="")),
            ("observability_export_status", _column_ddl("observability_export_status", default="DISABLED")),
            ("observability_target", _column_ddl("observability_target", default="LOCAL_ONLY")),
            ("evaluation_labels", _json_column_ddl("evaluation_labels", default="[]")),
        ],
    }

    with engine.begin() as connection:
        for table_name, columns in compatibility_columns.items():
            try:
                existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            except Exception:
                continue
            for column_name, ddl in columns:
                if column_name in existing_columns:
                    continue
                connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def _column_ddl(name: str, *, default: str) -> str:
    return f"{name} TEXT NOT NULL DEFAULT '{default}'"


def _json_column_ddl(name: str, *, default: str) -> str:
    dialect = engine.dialect.name
    if dialect == "postgresql":
        return f"{name} JSON NOT NULL DEFAULT '{default}'::json"
    return f"{name} TEXT NOT NULL DEFAULT '{default}'"
