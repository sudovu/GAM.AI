"""SmartCacheManager: High-efficiency, auto-expiring temporary storage layer."""
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from gam_ai.core.database.db import DatabaseManager

class SmartCacheManager:
    def __init__(self, db: DatabaseManager, max_cache_mb: int = 25, default_ttl_seconds: int = 3600):
        self.db = db
        self.max_cache_mb = max_cache_mb
        self.default_ttl_seconds = default_ttl_seconds

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def set(
        self,
        key: str,
        content: str,
        ttl_seconds: Optional[int] = None,
        priority: int = 1,
        source: Optional[str] = None,
        category: str = "web_research"
    ) -> str:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        content_hash = self._compute_hash(content)
        size_bytes = len(content.encode("utf-8"))
        entry_id = str(uuid.uuid4())

        self._enforce_size_limit(incoming_bytes=size_bytes)

        sql = """
        INSERT INTO cache_entries (
            id, cache_key, content, content_hash, size_bytes,
            created_at, last_accessed, expires_at, access_count, priority, source, category
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, 1, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            content = excluded.content,
            content_hash = excluded.content_hash,
            size_bytes = excluded.size_bytes,
            last_accessed = CURRENT_TIMESTAMP,
            expires_at = excluded.expires_at,
            access_count = cache_entries.access_count + 1,
            priority = excluded.priority,
            source = excluded.source,
            category = excluded.category;
        """
        self.db.execute(sql, (
            entry_id, key, content, content_hash, size_bytes,
            expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            priority, source, category
        ))
        self.db.commit()
        return entry_id

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT id, cache_key, content, content_hash, size_bytes, created_at,
               last_accessed, expires_at, access_count, priority, source, category
        FROM cache_entries
        WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP;
        """
        cursor = self.db.execute(sql, (key,))
        row = cursor.fetchone()
        if not row:
            return None

        new_access_count = row["access_count"] + 1
        update_sql = """
        UPDATE cache_entries
        SET last_accessed = CURRENT_TIMESTAMP, access_count = ?
        WHERE id = ?;
        """
        self.db.execute(update_sql, (new_access_count, row["id"]))
        self.db.commit()

        res = dict(row)
        res["access_count"] = new_access_count
        return res

    def cleanup_expired(self) -> int:
        sql = "DELETE FROM cache_entries WHERE expires_at <= CURRENT_TIMESTAMP;"
        cursor = self.db.execute(sql)
        deleted = cursor.rowcount
        self.db.commit()
        return deleted

    def _enforce_size_limit(self, incoming_bytes: int = 0) -> int:
        max_bytes = self.max_cache_mb * 1024 * 1024
        current_bytes = self.get_total_size_bytes()

        if current_bytes + incoming_bytes <= max_bytes:
            return 0

        target_evict = (current_bytes + incoming_bytes) - max_bytes
        evicted_count = 0
        evicted_bytes = 0

        sql = "SELECT id, size_bytes FROM cache_entries ORDER BY priority ASC, last_accessed ASC;"
        cursor = self.db.execute(sql)
        rows = cursor.fetchall()
        for r in rows:
            if evicted_bytes >= target_evict:
                break
            self.db.execute("DELETE FROM cache_entries WHERE id = ?;", (r["id"],))
            evicted_bytes += r["size_bytes"]
            evicted_count += 1

        self.db.commit()
        return evicted_count

    def clear_all(self) -> int:
        cursor = self.db.execute("DELETE FROM cache_entries;")
        count = cursor.rowcount
        self.db.commit()
        return count

    def get_total_size_bytes(self) -> int:
        cursor = self.db.execute("SELECT SUM(size_bytes) as total FROM cache_entries;")
        row = cursor.fetchone()
        return row["total"] if row and row["total"] else 0

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.db.execute("""
        SELECT COUNT(*) as total_entries,
               SUM(size_bytes) as total_bytes,
               SUM(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as expired_entries,
               AVG(access_count) as avg_access
        FROM cache_entries;
        """)
        row = cursor.fetchone()
        total_bytes = row["total_bytes"] or 0
        return {
            "total_entries": row["total_entries"] or 0,
            "expired_entries": row["expired_entries"] or 0,
            "total_size_bytes": total_bytes,
            "total_size_kb": round(total_bytes / 1024, 2),
            "max_cache_mb": self.max_cache_mb,
            "storage_saved_pct": round(max(0, 100 - (total_bytes / max(1, self.max_cache_mb * 1024 * 1024) * 100)), 1)
        }
