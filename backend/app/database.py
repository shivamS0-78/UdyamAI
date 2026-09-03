import json
import os
import sqlite3
from pathlib import Path

from geoalchemy2 import Geography
from geoalchemy2.functions import GenericFunction
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Register sqlite3 adapter for list/dict serialization in SQLite databases
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if hasattr(dbapi_connection, "create_function"):
        try:
            dbapi_connection.create_function("AsBinary", 1, lambda val: val)
            dbapi_connection.create_function("ST_AsBinary", 1, lambda val: val)
            dbapi_connection.create_function("ST_GeomFromText", 1, lambda val: val)
            dbapi_connection.create_function("ST_GeomFromText", 2, lambda val, srid: val)
            dbapi_connection.create_function("ST_GeogFromText", 1, lambda val: val)
            dbapi_connection.create_function("ST_GeogFromText", 2, lambda val, srid: val)
        except Exception:
            pass
    if hasattr(dbapi_connection, "execute"):
        try:
            dbapi_connection.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass


@compiles(Geography, "sqlite")
def compile_geography_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(GenericFunction, "sqlite")
def compile_generic_function_sqlite(element, compiler, **kw):
    if element.name.lower() in ("asbinary", "st_asbinary"):
        return compiler.process(element.clauses.clauses[0], **kw)
    return compiler.visit_function(element, **kw)


_engine = None


def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    db_url = settings.DATABASE_URL
    allow_sqlite_fallback = os.getenv("ALLOW_SQLITE_FALLBACK", "false").lower() == "true"

    if "postgresql" in db_url:
        try:
            temp_eng = create_engine(db_url, connect_args={"connect_timeout": 10})
            with temp_eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            temp_eng.dispose()
        except Exception as exc:
            if allow_sqlite_fallback:
                root_db = Path(__file__).resolve().parent.parent.parent / "udyamai.db"
                db_url = f"sqlite:///{root_db.as_posix()}"
            else:
                raise RuntimeError(
                    "Failed to connect to configured PostgreSQL database. "
                    "Set ALLOW_SQLITE_FALLBACK=true only for offline development."
                ) from exc

    if "postgresql" in db_url:
        _engine = create_engine(
            db_url,
            poolclass=NullPool,
            connect_args={"connect_timeout": 15},
            echo=False,
        )
    else:
        connect_args = {"check_same_thread": False, "timeout": 30}
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,
            poolclass=StaticPool,
        )
    return _engine


class _EngineProxy:
    def __getattr__(self, name):
        return getattr(get_engine(), name)

    def __repr__(self):
        return repr(get_engine())


engine = _EngineProxy()


def init_db():
    from app.models import (  # noqa: F401
        agriculture,
        ai,
        analysis,
        budget,
        business,
        cash_flow,
        credit,
        debt,
        economic,
        expenses,
        finance,
        infrastructure,
        livestock,
        location,
        market,
        provenance,
        rag,
        report,
        savings,
        scheme,
        system,
        user,
        weather,
    )

    eng = get_engine()
    if "sqlite" in str(eng.url):
        with eng.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA busy_timeout=30000;")
            conn.commit()

    SQLModel.metadata.create_all(eng)

    # Ensure schema compatibility: add any columns that are defined in
    # the SQLAlchemy model but missing from an older database schema.
    if "postgresql" in str(eng.url):
        _ensure_profiles_columns(eng)


def _ensure_profiles_columns(eng):
    """Add missing optional columns to the profiles table if they were
    introduced after the table was first created."""
    required_columns = {
        "email": "TEXT",
        "phone": "TEXT",
        "business_name": "TEXT",
        "business_type": "TEXT",
    }
    from sqlalchemy import inspect

    inspector = inspect(eng)
    existing = {col["name"] for col in inspector.get_columns("profiles")}
    with eng.connect() as conn:
        for col_name, col_type in required_columns.items():
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def get_session():
    with Session(get_engine()) as session:
        yield session


def verify_db_connection() -> bool:
    """Verify that backend can communicate with PostgreSQL/Supabase/SQLite database."""
    try:
        with Session(get_engine()) as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
