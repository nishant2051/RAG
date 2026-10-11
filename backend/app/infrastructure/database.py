"""Short-lived synchronous sessions; callers own commit/rollback boundaries.

RAG_DATABASE_PATH is a file path relative to backend/ (default data/rag.sqlite3).
Only file-backed SQLite is supported. Importing creates its parent, not tables.
Close sessions before long-running model or network operations.
"""

from collections.abc import Iterator

from sqlalchemy import URL, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import load_settings


class Base(DeclarativeBase):
    pass


settings = load_settings()
settings.database_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    URL.create("sqlite", database=str(settings.database_path)),
    connect_args={"check_same_thread": False, "timeout": 5},
)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=engine)


def get_db_session() -> Iterator[Session]:
    """Yield one session and close it, rolling back any uncommitted work."""
    with SessionLocal() as session:
        yield session
