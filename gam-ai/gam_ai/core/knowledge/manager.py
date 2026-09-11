"""KnowledgeManager: Cold storage operations, atomic claims, promotion, and search."""
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.knowledge.graph import KnowledgeGraph

class KnowledgeManager:
    def __init__(self, db: DatabaseManager, graph: Optional[KnowledgeGraph] = None):
        self.db = db
        self.graph = graph or KnowledgeGraph(db)

    def add_knowledge(
        self,
        topic: str,
        claim: str,
        source_url: Optional[str] = None,
        confidence: float = 1.0,
        tags: Optional[List[str]] = None
    ) -> str:
        content_hash = hashlib.sha256(claim.encode("utf-8")).hexdigest()
        item_id = str(uuid.uuid4())
        tags_str = ",".join(tags) if tags else ""

        source_id = None
        if source_url:
            source_id = hashlib.md5(source_url.encode("utf-8")).hexdigest()

        sql = """
        INSERT INTO knowledge_items (
            id, topic, claim, source_id, confidence, tags, status, content_hash,
            created_at, last_accessed, access_count
        )
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(content_hash) DO UPDATE SET
            last_accessed = CURRENT_TIMESTAMP,
            access_count = access_count + 1;
        """
        self.db.execute(sql, (item_id, topic, claim, source_id, confidence, tags_str, content_hash))
        self.db.commit()
        return item_id

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        sql = """
        SELECT k.id, k.topic, k.claim, k.confidence, k.tags, k.access_count, k.status,
               s.url as source_url, s.domain as source_domain
        FROM knowledge_items k
        LEFT JOIN sources s ON k.source_id = s.id
        WHERE (k.topic LIKE ? OR k.claim LIKE ? OR k.tags LIKE ?) AND k.status = 'active'
        ORDER BY k.access_count DESC, k.confidence DESC
        LIMIT ?;
        """
        pattern = f"%{query.strip()}%"
        cursor = self.db.execute(sql, (pattern, pattern, pattern, limit))
        results = [dict(r) for r in cursor.fetchall()]

        for it in results:
            self.db.execute("UPDATE knowledge_items SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE id = ?", (it["id"],))
        self.db.commit()
        return results

    def promote_from_cache(self, topic: str, claim: str, source: Optional[str] = None, confidence: float = 0.95) -> str:
        return self.add_knowledge(
            topic=topic,
            claim=claim,
            source_url=source,
            confidence=confidence,
            tags=["promoted", topic.lower()]
        )

    def forget_topic(self, topic: str) -> int:
        cursor = self.db.execute("DELETE FROM knowledge_items WHERE topic LIKE ?;", (f"%{topic}%",))
        count = cursor.rowcount
        self.db.commit()
        return count

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.db.execute("""
        SELECT COUNT(*) as total_items,
               COUNT(DISTINCT topic) as total_topics,
               SUM(CASE WHEN status = 'stale' THEN 1 ELSE 0 END) as stale_items
        FROM knowledge_items;
        """)
        row = cursor.fetchone()
        return {
            "total_items": row["total_items"] or 0,
            "total_topics": row["total_topics"] or 0,
            "stale_items": row["stale_items"] or 0,
        }
