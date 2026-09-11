"""LongTermMemory: SQLite-backed persistent memory for high-value user preferences & facts."""
import uuid
from typing import List, Dict, Any
from gam_ai.core.database.db import DatabaseManager

class LongTermMemory:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def remember(self, key: str, value: str, category: str = "preference", confidence: float = 1.0) -> str:
        mem_id = str(uuid.uuid4())
        sql = """
        INSERT INTO long_term_memory (id, category, key, value, confidence, last_accessed, access_count)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            confidence = excluded.confidence,
            last_accessed = CURRENT_TIMESTAMP,
            access_count = access_count + 1;
        """
        self.db.execute(sql, (mem_id, category, key, value, confidence))
        self.db.commit()
        return key

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        sql = """
        SELECT id, category, key, value, confidence, access_count, last_accessed
        FROM long_term_memory
        WHERE key LIKE ? OR value LIKE ?
        ORDER BY access_count DESC, last_accessed DESC
        LIMIT ?;
        """
        pattern = f"%{query}%"
        cursor = self.db.execute(sql, (pattern, pattern, limit))
        return [dict(r) for r in cursor.fetchall()]

    def get_all_preferences(self) -> List[Dict[str, Any]]:
        sql = "SELECT key, value, category FROM long_term_memory ORDER BY access_count DESC;"
        cursor = self.db.execute(sql)
        return [dict(r) for r in cursor.fetchall()]

    def forget(self, key_or_pattern: str) -> int:
        sql = "DELETE FROM long_term_memory WHERE key LIKE ? OR value LIKE ?;"
        pattern = f"%{key_or_pattern}%"
        cursor = self.db.execute(sql, (pattern, pattern))
        deleted = cursor.rowcount
        self.db.commit()
        return deleted

    def clear_all(self) -> int:
        cursor = self.db.execute("DELETE FROM long_term_memory;")
        count = cursor.rowcount
        self.db.commit()
        return count
