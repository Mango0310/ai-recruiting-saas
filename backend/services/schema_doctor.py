"""Startup schema doctor: auto-adds missing columns without dropping the database.

Runs on every startup. For each SQLAlchemy model, checks which columns exist
in the actual database and adds any that are missing. This means you can add
a new Column() to any model and restart — no manual migration needed.
"""

import re
from sqlalchemy import inspect, text, Column
from sqlalchemy.engine import Engine

# Maps SQLAlchemy types to SQLite type strings for ALTER TABLE
_TYPE_MAP = {
    "INTEGER": "INTEGER",
    "BIGINT": "INTEGER",
    "SMALLINT": "INTEGER",
    "VARCHAR": "TEXT",
    "NVARCHAR": "TEXT",
    "TEXT": "TEXT",
    "CLOB": "TEXT",
    "DATE": "TEXT",
    "DATETIME": "TEXT",
    "TIMESTAMP": "TEXT",
    "FLOAT": "REAL",
    "NUMERIC": "REAL",
    "BOOLEAN": "INTEGER",
    "JSON": "TEXT",
}


def _sqlite_type(col_type: str) -> str:
    """Map SQLAlchemy column type name to simplest SQLite type."""
    upper = col_type.upper()
    return _TYPE_MAP.get(upper, "TEXT")


def _run_for_sqlite(engine: Engine, table_name: str, missing: list[tuple[str, str]]):
    """Add missing columns to a SQLite table."""
    with engine.connect() as conn:
        for col_name, col_type in missing:
            safe_col = f'"{col_name}"'
            sql_type = _sqlite_type(col_type)
            sql = f"ALTER TABLE {table_name} ADD COLUMN {safe_col} {sql_type}"
            conn.execute(text(sql))
            conn.commit()


def _run_for_postgres(engine: Engine, table_name: str, missing: list[tuple[str, str]]):
    """Add missing columns to a PostgreSQL table (with IF NOT EXISTS)."""
    with engine.connect() as conn:
        for col_name, col_type in missing:
            safe_name = col_name.replace('"', '""')
            # Map common types to PG equivalents
            pg_type = _postgres_type(col_type)
            sql = f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{safe_name}" {pg_type}'
            conn.execute(text(sql))
            conn.commit()


def _postgres_type(col_type: str) -> str:
    """Map SQLAlchemy type to PostgreSQL type."""
    upper = col_type.upper()
    mapping = {
        "INTEGER": "INTEGER",
        "BIGINT": "BIGINT",
        "SMALLINT": "INTEGER",
        "VARCHAR": "VARCHAR(500)",
        "NVARCHAR": "VARCHAR(500)",
        "TEXT": "TEXT",
        "CLOB": "TEXT",
        "DATE": "DATE",
        "DATETIME": "TIMESTAMP",
        "TIMESTAMP": "TIMESTAMP",
        "FLOAT": "DOUBLE PRECISION",
        "NUMERIC": "NUMERIC",
        "BOOLEAN": "BOOLEAN",
        "JSON": "JSONB",
    }
    return mapping.get(upper, "TEXT")


def apply_migrations(engine: Engine, base_metadata):
    """Check all tables and add any missing columns. Idempotent — safe to run every startup."""
    inspector = inspect(engine)
    is_sqlite = "sqlite" in str(engine.url)

    total_added = 0

    for table in base_metadata.sorted_tables:
        table_name = table.name

        # Check if table exists
        if table_name not in inspector.get_table_names():
            # Table doesn't exist at all — create_all handles this
            continue

        # Get existing columns
        existing = {c["name"] for c in inspector.get_columns(table_name)}

        # Find model columns that don't exist in the DB
        missing = []
        for col in table.columns:
            if col.name not in existing:
                col_type = str(col.type)
                missing.append((col.name, col_type))

        if missing:
            names = [f"{n} ({t})" for n, t in missing]
            print(f"[migrate] {table_name}: adding {', '.join(names)}")
            if is_sqlite:
                _run_for_sqlite(engine, table_name, missing)
            else:
                _run_for_postgres(engine, table_name, missing)
            total_added += len(missing)

    if total_added:
        print(f"[migrate] done — {total_added} column(s) added")
