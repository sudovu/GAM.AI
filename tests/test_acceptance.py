"""Comprehensive acceptance tests matching sections 52-57 of the GAM.AI Master Specification."""
import unittest
import os
import tempfile
from gam_ai.core.chat.engine import ChatEngine
from gam_ai.core.resources.capabilities import DeviceProfile, StoragePressure
from gam_ai.core.ai.context_budget import ContextBudgetManager

class TestGamAiAcceptance(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_gam.db")
        self.engine = ChatEngine(db_path=self.db_path, promotion_threshold=3)

    def tearDown(self):
        self.engine.models.unload_active_model()
        self.engine.db.close()
        self.tmp_dir.cleanup()

    def test_52_offline_acceptance(self):
        self.engine.capabilities.set_online_override(False)
        self.assertFalse(self.engine.capabilities.check_network_connectivity())

        self.engine.knowledge.add_knowledge(
            topic="OSPF",
            claim="OSPF is an interior gateway link-state routing protocol."
        )

        doc_path = os.path.join(self.tmp_dir.name, "network_notes.txt")
        with open(doc_path, "w") as f:
            f.write("Cisco router interfaces configured with OSPF automatically form adjacencies over Ethernet.")
        doc_res = self.engine.doc_processor.process_file(doc_path)
        self.assertEqual(doc_res["chunks_indexed"], 1)

        resp = self.engine.process_query("What is OSPF?")
        self.assertTrue(len(resp["response"]) > 10)
        self.assertIn(resp["source"], ["local_knowledge", "local_offline"])

        status = self.engine.get_system_status()
        self.assertIn("OFFLINE", status)

    def test_53_online_acceptance_and_cache_reuse(self):
        self.engine.capabilities.set_online_override(True)
        self.assertTrue(self.engine.capabilities.check_network_connectivity())

        q = "What is OSPF LFA?"
        resp1 = self.engine.process_query(q)
        self.assertTrue(len(resp1["response"]) > 20)
        self.assertEqual(resp1["source"], "web_research")

        sources_count = self.engine.db.execute("SELECT COUNT(*) as c FROM sources").fetchone()["c"]
        self.assertEqual(sources_count, 1)

        resp2 = self.engine.process_query("What is OSPF LFA?")
        self.assertIn(resp2["source"], ["cache", "local_knowledge"])
        self.assertIn("OSPF Loop-Free Alternate", resp2["response"])

    def test_54_cache_cleanup(self):
        self.engine.knowledge.add_knowledge("BGP", "BGP connects autonomous systems across the internet.")

        self.engine.cache.set("temp:calc_17_850", "144.5", ttl_seconds=-1, priority=0)
        self.engine.cache.set("temp:scratchpad", "intermediate computation", ttl_seconds=-1, priority=0)

        pre_stats = self.engine.cache.get_stats()
        self.assertEqual(pre_stats["total_entries"], 2)

        cleanup_res = self.engine.retention.enforce_retention(StoragePressure.NORMAL)
        self.assertGreaterEqual(cleanup_res["expired_cache_deleted"], 2)

        post_stats = self.engine.cache.get_stats()
        self.assertEqual(post_stats["total_entries"], 0)

        know_items = self.engine.knowledge.search_knowledge("BGP")
        self.assertEqual(len(know_items), 1)
        self.assertIn("autonomous systems", know_items[0]["claim"])

    def test_55_recurring_query_promotion(self):
        self.engine.capabilities.set_online_override(True)
        query = "What is BGP local preference?"

        self.engine.process_query(query)
        self.engine.process_query(query)
        self.engine.process_query(query)

        promoted = self.engine.knowledge.search_knowledge("BGP")
        self.assertGreaterEqual(len(promoted), 1)
        self.assertIn("LOCAL_PREF", promoted[0]["claim"])
        self.assertIn("promoted", promoted[0]["tags"])

    def test_56_storage_pressure_degradation(self):
        self.engine.memory.long_term.remember("network_os", "Cisco IOS-XE")
        self.engine.cache.set("temp:item1", "test data", ttl_seconds=3600, category="web_research")
        self.engine.cache.set("temp:item2", "more data", ttl_seconds=3600, category="web_research")

        ret_result = self.engine.retention.enforce_retention(StoragePressure.CRITICAL)
        self.assertGreaterEqual(ret_result["expired_cache_deleted"], 2)

        pref = self.engine.memory.long_term.recall("network_os")
        self.assertEqual(len(pref), 1)
        self.assertEqual(pref[0]["value"], "Cisco IOS-XE")

    def test_57_ram_low_resource_profile(self):
        engine_ultra = ChatEngine(override_profile=DeviceProfile.ULTRA_LOW)
        self.assertEqual(engine_ultra.config.default_model_tier, "nano")
        self.assertEqual(engine_ultra.config.max_context_tokens, 512)
        self.assertEqual(engine_ultra.config.max_cache_mb, 10)
        self.assertEqual(engine_ultra.config.max_history_in_ram, 3)

        model = engine_ultra.models.load_model("nano")
        self.assertTrue(model.is_loaded())
        self.assertLessEqual(model.get_info().ram_required_mb, 150)

        engine_ultra.models.unload_active_model()
        self.assertFalse(model.is_loaded())
        self.assertEqual(engine_ultra.models.get_ram_usage_mb(), 0)

    def test_security_protections(self):
        from gam_ai.core.security.guard import SecurityGuard
        self.assertFalse(SecurityGuard.is_safe_path("../../../etc/passwd", base_dir="/safe/dir"))
        self.assertTrue(SecurityGuard.is_safe_path("/safe/dir/file.txt", base_dir="/safe/dir"))
        self.assertFalse(SecurityGuard.is_safe_url("http://127.0.0.1/admin"))
        self.assertFalse(SecurityGuard.is_safe_url("http://localhost:8080/secrets"))
        self.assertFalse(SecurityGuard.is_safe_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(SecurityGuard.is_safe_url("file:///etc/hosts"))
        self.assertTrue(SecurityGuard.is_safe_url("https://datatracker.ietf.org/doc/html/rfc5286"))

    def test_database_init_and_stats(self):
        stats = self.engine.db.get_storage_stats()
        self.assertIn("counts", stats)
        self.assertEqual(stats["counts"]["messages"], 0)

    def test_smart_cache_lru_and_ttl(self):
        self.engine.cache.set("key1", "data1", ttl_seconds=3600)
        entry = self.engine.cache.get("key1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["content"], "data1")
        self.assertEqual(entry["access_count"], 2)

    def test_knowledge_graph(self):
        self.engine.knowledge.graph.add_relation("BGP", "Local Preference", "configures")
        self.engine.knowledge.graph.add_relation("BGP", "Path Selection", "influences")
        related = self.engine.knowledge.graph.get_related_topics("BGP")
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
        test_file = os.path.join(self.tmp_dir.name, "doc.txt")
        with open(test_file, "w") as f:
            f.write("Line 1 test content.\nLine 2 test content.\n")
        res = self.engine.doc_processor.process_file(test_file)
        self.assertEqual(res["chunks_indexed"], 1)

        chunks = self.engine.retriever.retrieve_context("content", top_k=1)
        self.assertEqual(len(chunks), 1)
        self.assertIn("test content", chunks[0]["content"])

    def test_model_manager_unloading(self):
        m1 = self.engine.models.load_model("nano")
        self.assertTrue(m1.is_loaded())
        m2 = self.engine.models.load_model("micro")
        self.assertTrue(m2.is_loaded())
        self.assertFalse(m1.is_loaded())
        self.engine.models.unload_active_model()
        self.assertFalse(m2.is_loaded())



    def test_network_subnet_calculator(self):
        from gam_ai.core.network.subnet import SubnetCalculator
        res = SubnetCalculator.calculate("192.168.10.35/27")
        self.assertEqual(res["network_address"], "192.168.10.32")
        self.assertEqual(res["broadcast_address"], "192.168.10.63")
        self.assertEqual(res["netmask"], "255.255.255.224")
        self.assertEqual(res["wildcard_mask"], "0.0.0.31")
        self.assertEqual(res["total_usable_hosts"], 30)

        # Test VLSM
        vlsm = SubnetCalculator.vlsm_plan("172.16.0.0/24", [
            {"name": "Engineering", "hosts": 100},
            {"name": "Sales", "hosts": 50},
            {"name": "Management", "hosts": 20}
        ])
        self.assertEqual(vlsm["total_allocated"], 3)
        self.assertEqual(vlsm["subnets"][0]["prefix"], "/25")
        self.assertEqual(vlsm["subnets"][1]["prefix"], "/26")

    def test_multivendor_config_generator(self):
        from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
        # Cisco
        cisco_cfg = MultiVendorConfigGenerator.cisco_ospf(1, "1.1.1.1", "0", "10.0.0.0", "0.0.0.255")
        self.assertIn("router ospf 1", cisco_cfg)

        # Huawei VRP
        huawei_cfg = MultiVendorConfigGenerator.huawei_trunk_port("GigabitEthernet0/0/1", "10 20 30")
        self.assertIn("port link-type trunk", huawei_cfg)

        # GPON OLT
        olt_cfg = MultiVendorConfigGenerator.huawei_olt_gpon_service("0/1/0", 1, "4857544312345678", 100)
        self.assertIn("dba-profile add", olt_cfg)
        self.assertIn("ont-srvprofile gpon", olt_cfg)
        self.assertIn("service-port", olt_cfg)

        # Firewall FortiGate & MikroTik
        forti_cfg = MultiVendorConfigGenerator.fortigate_policy(1, "LAN_to_WAN", "port2", "port1")
        self.assertIn("config firewall policy", forti_cfg)

        mikro_cfg = MultiVendorConfigGenerator.mikrotik_basic_setup()
        self.assertIn("action=masquerade", mikro_cfg)

    def test_network_knowledge_pack_seeding(self):
        from gam_ai.core.network.knowledge_pack import seed_network_knowledge
        seeded_count = seed_network_knowledge(self.engine.knowledge)
        self.assertGreaterEqual(seeded_count, 8)

        # Search for Huawei OLT knowledge
        results = self.engine.knowledge.search_knowledge("GPON OLT")
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("ITU-T G.984", results[0]["claim"])

if __name__ == '__main__':
    unittest.main()
