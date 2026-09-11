"""RetentionManager: Governs data lifecycle: KEEP, COMPRESS, CACHE, ARCHIVE, DELETE."""
import logging
from enum import Enum
from typing import Dict, Any
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.cache.smart_cache import SmartCacheManager
from gam_ai.core.knowledge.manager import KnowledgeManager
from gam_ai.core.resources.capabilities import StoragePressure

logger = logging.getLogger(__name__)

class RetentionDecision(str, Enum):
    KEEP = "KEEP"
    COMPRESS = "COMPRESS"
    CACHE = "CACHE"
    ARCHIVE = "ARCHIVE"
    DELETE = "DELETE"

class RetentionManager:
    def __init__(self, db: DatabaseManager, cache: SmartCacheManager, knowledge: KnowledgeManager):
        self.db = db
        self.cache = cache
        self.knowledge = knowledge

    def evaluate_item(self, category: str, frequency: int, age_days: int, is_explicit: bool) -> RetentionDecision:
        if is_explicit:
            return RetentionDecision.KEEP
        if category == "temporary_cache":
            return RetentionDecision.DELETE if age_days > 1 else RetentionDecision.CACHE
        if category == "knowledge":
            if frequency >= 3:
                return RetentionDecision.KEEP
            elif age_days > 30 and frequency <= 1:
                return RetentionDecision.ARCHIVE
            return RetentionDecision.KEEP
        return RetentionDecision.KEEP

    def enforce_retention(self, storage_pressure: StoragePressure = StoragePressure.NORMAL) -> Dict[str, Any]:
        results = {
            "pressure": storage_pressure.value,
            "expired_cache_deleted": 0,
            "stale_knowledge_archived": 0,
            "freed_bytes": 0
        }

        expired = self.cache.cleanup_expired()
        results["expired_cache_deleted"] += expired

        if storage_pressure in (StoragePressure.LOW, StoragePressure.CRITICAL):
            sql = "DELETE FROM cache_entries WHERE last_accessed <= datetime('now', '-2 hours');"
            c = self.db.execute(sql)
            results["expired_cache_deleted"] += c.rowcount
            self.db.commit()

        if storage_pressure == StoragePressure.CRITICAL:
            sql = "DELETE FROM cache_entries WHERE category = 'web_research';"
            c = self.db.execute(sql)
            results["expired_cache_deleted"] += c.rowcount

            sql = "UPDATE knowledge_items SET status = 'archived' WHERE access_count <= 1 AND created_at <= datetime('now', '-14 days');"
            c2 = self.db.execute(sql)
            results["stale_knowledge_archived"] = c2.rowcount
            self.db.commit()

        vac_stats = self.db.vacuum_and_optimize()
        results["freed_bytes"] = vac_stats.get("freed_bytes", 0)

        return results
