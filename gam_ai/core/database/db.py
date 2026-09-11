"""Database connection and lifecycle manager for SQLite with low-resource pragmas."""
import sqlite3
import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from gam_ai.core.database.schema import CREATE_TABLES_SQL

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        if self.db_path != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            os.makedirs(db_dir, exist_ok=True)

        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self._conn.row_factory = sqlite3.Row

        cursor = self._conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA temp_store = MEMORY;")
            cursor.execute("PRAGMA cache_size = -2000;")
        cursor.close()
        self._conn.commit()
        return self._conn

    def initialize(self) -> None:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executescript(CREATE_TABLES_SQL)
        conn.commit()
        cursor.close()

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            return self.connect()
        return self._conn

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(self, sql: str, seq_of_params: List[Tuple]) -> sqlite3.Cursor:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, seq_of_params)
        return cursor

    def commit(self) -> None:
        if self._conn:
            self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def vacuum_and_optimize(self) -> Dict[str, Any]:
        if self.db_path == ":memory:":
            return {"status": "skipped_in_memory", "freed_bytes": 0}

        conn = self.get_connection()
        initial_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        conn.execute("PRAGMA optimize;")
        conn.commit()
        try:
            conn.execute("VACUUM;")
        except sqlite3.OperationalError:
            pass

        final_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {
            "initial_size_bytes": initial_size,
            "final_size_bytes": final_size,
            "freed_bytes": max(0, initial_size - final_size)
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        conn = self.get_connection()
        tables = [
            "long_term_memory", "knowledge_items", "sources",
            "knowledge_edges", "cache_entries", "query_history",
            "document_references", "document_chunks", "messages"
        ]
        counts = {}
        for t in tables:
            try:
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {t}").fetchone()
                counts[t] = row["cnt"] if row else 0
            except sqlite3.OperationalError:
                counts[t] = 0

        disk_bytes = os.path.getsize(self.db_path) if self.db_path != ":memory:" and os.path.exists(self.db_path) else 0
        return {
            "counts": counts,
            "db_size_bytes": disk_bytes,
            "db_size_kb": round(disk_bytes / 1024, 2)
        }
