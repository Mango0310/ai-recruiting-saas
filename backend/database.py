from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import DATABASE_URL

IS_SQLITE = "sqlite" in DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_size=5 if not IS_SQLITE else 0,
    max_overflow=10 if not IS_SQLITE else 0,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _init_pgvector(dbapi_connection):
    """Create pgvector extension on PostgreSQL connections."""
    if not IS_SQLITE:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cursor.close()
            dbapi_connection.commit()
        except Exception:
            dbapi_connection.rollback()


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if IS_SQLITE:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    else:
        _init_pgvector(dbapi_connection)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_sqlite() -> bool:
    return IS_SQLITE

