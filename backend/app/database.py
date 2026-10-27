"""SQLite engine/session management.

The engine can be re-pointed at runtime (`configure`) because the API swaps in
fresh database snapshots published by the pipeline."""
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)
_engine: Engine | None = None


def configure(db_path: Path | str) -> Engine:
    """(Re)create the engine for the given SQLite file."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal.configure(bind=_engine)
    return _engine


def get_engine() -> Engine:
    return _engine if _engine is not None else configure(config.DB_PATH)


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables)

    engine = get_engine()
    Base.metadata.create_all(engine)
    _add_missing_columns(engine)


def _add_missing_columns(engine: Engine) -> None:
    """Minimal forward-only migration: add columns introduced after a database
    snapshot was created. (create_all only creates missing *tables*.)"""
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                col_type = column.type.compile(dialect=engine.dialect)
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
                conn.execute(text(ddl + _default_clause(column)))


def _default_clause(column) -> str:
    default = column.default.arg if column.default is not None else None
    if isinstance(default, bool):
        return f" DEFAULT {int(default)}"
    if isinstance(default, (int, float)):
        return f" DEFAULT {default}"
    return ""


def vacuum() -> None:
    """Shrink the file before publishing a snapshot."""
    with get_engine().connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("VACUUM"))


def get_db():
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
