"""Unit tests for individual GAM.AI core components."""
import unittest
import os
import tempfile
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.models.manager import ModelManager
from gam_ai.core.cache.smart_cache import SmartCacheManager
from gam_ai.core.knowledge.graph import KnowledgeGraph
from gam_ai.core.documents.processor import DocumentProcessor
from gam_ai.core.rag.retriever import LocalRetriever
from gam_ai.core.ai.context_budget import ContextBudgetManager

class TestCoreComponents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = DatabaseManager(":memory:")
        self.db.initialize()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_database_init_and_stats(self):
        stats = self.db.get_storage_stats()
        self.assertIn("counts", stats)
        self.assertEqual(stats["counts"]["messages"], 0)

    def test_smart_cache_lru_and_ttl(self):
        cache = SmartCacheManager(self.db, max_cache_mb=1)
        cache.set("key1", "data1", ttl_seconds=3600)
        entry = cache.get("key1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["content"], "data1")
        self.assertEqual(entry["access_count"], 2)

    def test_knowledge_graph(self):
        kg = KnowledgeGraph(self.db)
        kg.add_relation("BGP", "Local Preference", "configures")
        kg.add_relation("BGP", "Path Selection", "influences")
        related = kg.get_related_topics("BGP")
        self.assertEqual(len(related), 2)

    def test_context_budget_manager(self):
        cbm = ContextBudgetManager(max_context_tokens=100)
        long_knowledge = ["Fact " * 20 for _ in range(5)]
        payload = cbm.build_budgeted_prompt(
            query="Test query?",
            knowledge_items=long_knowledge
        )
        self.assertLessEqual(payload.total_estimated_tokens, 100)

    def test_document_processor(self):
        doc_proc = DocumentProcessor(self.db)
        test_file = os.path.join(self.tmp.name, "doc.txt")
        with open(test_file, "w") as f:
            f.write("Line 1 test content.\nLine 2 test content.\n")
        res = doc_proc.process_file(test_file)
        self.assertEqual(res["chunks_indexed"], 1)

        retriever = LocalRetriever(self.db)
        chunks = retriever.retrieve_context("content", top_k=1)
        self.assertEqual(len(chunks), 1)
        self.assertIn("test content", chunks[0]["content"])

    def test_model_manager_unloading(self):
        mm = ModelManager()
        m1 = mm.load_model("nano")
        self.assertTrue(m1.is_loaded())
        m2 = mm.load_model("micro")
        self.assertTrue(m2.is_loaded())
        self.assertFalse(m1.is_loaded())
        mm.unload_active_model()
        self.assertFalse(m2.is_loaded())

if __name__ == "__main__":
    unittest.main()
