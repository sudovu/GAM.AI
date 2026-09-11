"""Lightweight Knowledge Graph: Minimal semantic linkage between topics."""
import uuid
from typing import List, Dict, Any
from gam_ai.core.database.db import DatabaseManager

class KnowledgeGraph:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add_relation(self, source_topic: str, target_topic: str, relation_type: str = "relates_to", weight: float = 1.0) -> str:
        edge_id = str(uuid.uuid4())
        sql = """
        INSERT INTO knowledge_edges (id, source_topic, target_topic, relation_type, weight)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(source_topic, target_topic, relation_type) DO UPDATE SET
            weight = excluded.weight;
        """
        self.db.execute(sql, (edge_id, source_topic.strip(), target_topic.strip(), relation_type, weight))
        self.db.commit()
        return edge_id

    def get_related_topics(self, topic: str, max_depth: int = 1) -> List[Dict[str, Any]]:
        sql = """
        SELECT source_topic, target_topic, relation_type, weight
        FROM knowledge_edges
        WHERE source_topic = ? OR target_topic = ?
        ORDER BY weight DESC;
        """
        t = topic.strip()
        cursor = self.db.execute(sql, (t, t))
        results = []
        for r in cursor.fetchall():
            other = r["target_topic"] if r["source_topic"].lower() == t.lower() else r["source_topic"]
            results.append({
                "topic": other,
                "relation": r["relation_type"],
                "weight": r["weight"]
            })
        return results

    def get_all_edges(self) -> List[Dict[str, Any]]:
        cursor = self.db.execute("SELECT source_topic, target_topic, relation_type, weight FROM knowledge_edges")
        return [dict(r) for r in cursor.fetchall()]
