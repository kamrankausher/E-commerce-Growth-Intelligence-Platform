"""Database helpers for SQLAlchemy."""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.utils.config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def run_sql_file(engine: Engine, file_path: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
