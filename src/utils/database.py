"""
Database connection utilities for SQLite.
Provides reusable helpers for query execution and data loading.
"""
import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import DATABASE_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_connection():
    """Create a new SQLite connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.

    Args:
        query: SQL query string.
        params: Optional tuple of query parameters.

    Returns:
        DataFrame with query results.
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        logger.info("Query returned %d rows", len(df))
        return df
    except Exception as e:
        logger.error("Query failed: %s", e)
        raise
    finally:
        conn.close()


def execute_sql(query: str, params: tuple = None):
    """
    Execute a SQL statement (INSERT, UPDATE, CREATE, etc.) without returning data.
    """
    conn = get_connection()
    try:
        conn.execute(query, params or ())
        conn.commit()
        logger.info("SQL executed successfully")
    except Exception as e:
        logger.error("SQL execution failed: %s", e)
        raise
    finally:
        conn.close()


def load_df_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """Load a DataFrame into an SQLite table."""
    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        logger.info("Loaded %d rows into '%s'", len(df), table_name)
    finally:
        conn.close()
