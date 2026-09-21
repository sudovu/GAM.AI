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

    def test_omni_generative_prompt_synthesis(self):
        from gam_ai.core.models.providers import MicroLocalModelProvider, GenerationRequest
        provider = MicroLocalModelProvider("nano")
        provider.load()

        # Math / Quadratic
        r_math = provider.generate(GenerationRequest(prompt="User Query: solve 2x^2 + 5x - 3 = 0"))
        self.assertIn("Mathematical Derivation", r_math.text)
        self.assertIn("Discriminant", r_math.text)

        # Email
        r_email = provider.generate(GenerationRequest(prompt="User Query: write an email requesting sick leave"))
        self.assertIn("Sick Leave Application", r_email.text)

        # Concept
        r_concept = provider.generate(GenerationRequest(prompt="User Query: explain quantum computing like I'm 5"))
        self.assertIn("Quantum Computing Explained", r_concept.text)

        # Workout
        r_plan = provider.generate(GenerationRequest(prompt="User Query: create a workout routine for gym"))
        self.assertIn("4-Day Hypertrophy Split", r_plan.text)

        # Strategic Analysis
        r_strat = provider.generate(GenerationRequest(prompt="User Query: how to launch an AI startup"))
        self.assertIn("Strategic Analysis", r_strat.text)

    def test_multiturn_context_and_sqlite_persistence(self):
        """Verify local conversation storage in SQLite and multi-turn context resolution."""
        from gam_ai.core.chat.engine import ChatEngine
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_chat.db")
            engine = ChatEngine(db_path=db_path)

            # Turn 1: Ask for a joke
            res1 = engine.process_query("Tell me a funny joke", conversation_id="conv_1")
            self.assertTrue(len(res1["response"]) > 0)

            # Turn 2: Follow up with "next"
            res2 = engine.process_query("next", conversation_id="conv_1")
            self.assertTrue(len(res2["response"]) > 0)

            # Verify SQLite persistence
            history = engine.get_chat_history(conversation_id="conv_1")
            self.assertEqual(len(history), 4) # 2 user turns + 2 assistant turns
            self.assertEqual(history[0]["role"], "user")
            self.assertEqual(history[0]["content"], "Tell me a funny joke")
            self.assertEqual(history[1]["role"], "assistant")
            self.assertEqual(history[2]["role"], "user")
            self.assertEqual(history[2]["content"], "next")
            self.assertEqual(history[3]["role"], "assistant")

            # Turn 3: Referential follow-up
            res3 = engine.process_query("why?", conversation_id="conv_1")
            self.assertTrue(len(res3["response"]) > 0)

            history3 = engine.get_chat_history(conversation_id="conv_1")
            self.assertEqual(len(history3), 6)

            # Clear chat history
            deleted = engine.clear_chat_history(conversation_id="conv_1")
            self.assertEqual(deleted, 6)
            cleared_history = engine.get_chat_history(conversation_id="conv_1")
            self.assertEqual(len(cleared_history), 0)

            # Close database connection cleanly before tempdir removal
            engine.close()

    def test_never_run_out_of_tokens(self):
        """Verify that massive queries and long histories never exceed context or starve generation."""
        from gam_ai.core.ai.context_budget import ContextBudgetManager
        from gam_ai.core.chat.engine import ChatEngine

        # Test 1: ContextBudgetManager with micro context (150 tokens) and massive 3,000 word query
        cbm = ContextBudgetManager(max_context_tokens=150)
        massive_query = "analyze this complex network telemetry packet " * 500  # 2,500 words
        long_knowledge = ["RFC 793 Transmission Control Protocol specification details " * 20 for _ in range(10)]
        long_history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"Turn {i} message " * 15} for i in range(20)]

        payload = cbm.build_budgeted_prompt(
            query=massive_query,
            knowledge_items=long_knowledge,
            history=long_history
        )

        # Must strictly stay within context ceiling and leave room for generation
        self.assertLessEqual(payload.total_estimated_tokens, 150)
        remaining_gen = cbm.get_remaining_generation_tokens(payload)
        self.assertGreaterEqual(remaining_gen, 16)
        self.assertLessEqual(payload.total_estimated_tokens + remaining_gen, 150)

        # Test 2: ChatEngine live execution with massive input
        engine = ChatEngine(db_path=":memory:")
        res = engine.process_query(massive_query[:1000], conversation_id="conv_stress")
        self.assertTrue(len(res["response"]) > 0)
        self.assertLessEqual(res["prompt_tokens"], engine.config.max_context_tokens)
        engine.close()

    def test_multimodal_generator(self):
        """Verify MultimodalGenerator prompt enhancement, image generation, storyboards, and motions."""
        from gam_ai.core.multimodal.generator import MultimodalGenerator

        mg = MultimodalGenerator()

        # 1. Prompt Enhancement
        enh = mg.enhance_prompt("cyberpunk car", media_type="video", style="cinematic")
        self.assertEqual(enh["original"], "cyberpunk car")
        self.assertIn("cinematic camera motion", enh["enhanced"])
        self.assertIn("60fps photorealistic motion blur", enh["enhanced"])

        # 2. Image URL Generation (Pollinations Zero-Key)
        img_res = mg.generate_image_url("cyberpunk car", aspect_ratio="16:9", style="cinematic")
        self.assertEqual(img_res["status"], "success")
        self.assertEqual(img_res["provider"], "pollinations_flux")
        self.assertIn("https://image.pollinations.ai/prompt/", img_res["image_url"])
        self.assertEqual(img_res["width"], 1024)
        self.assertEqual(img_res["height"], 576)

        # 3. Gemini / Imagen 3 API Configuration
        gem_res = mg.generate_image_url("cyberpunk car", provider="gemini", api_key="test_key_123")
        self.assertEqual(gem_res["status"], "success")
        self.assertEqual(gem_res["provider"], "gemini")
        self.assertEqual(gem_res["model"], "imagen-3.0-generate-002")

        # 4. Text-to-Video Multi-Scene Storyboard
        sb = mg.generate_video_storyboard("spaceship entering hyperspace", num_scenes=3)
        self.assertEqual(sb["status"], "success")
        self.assertEqual(len(sb["scenes"]), 3)
        self.assertEqual(sb["scenes"][0]["scene_index"], 1)
        self.assertIn("keyframe_url", sb["scenes"][0])
        self.assertIn("motion_config", sb["scenes"][0])

        # 5. Motion Profiles
        motions = mg.get_motion_profiles()
        self.assertIn("push_in", motions)
        self.assertIn("pan_right", motions)
        self.assertIn("parallax_3d", motions)
        self.assertIn("drone_orbit", motions)

        # 6. Verify Three.js asset file exists and is populated
        from gam_ai.ui import get_ui_dir
        three_js_file = os.path.join(get_ui_dir(), "three.min.js")
        self.assertTrue(os.path.isfile(three_js_file))
        self.assertGreater(os.path.getsize(three_js_file), 100000)

    def test_gpon_olt_and_ont_profile_resolution(self):
        """Verify dashboard.html contains dedicated GPON OLT, ONT lineprofile, and ZTE OLT templates."""
        from gam_ai.ui import get_ui_dir
        dash_path = os.path.join(get_ui_dir(), "dashboard.html")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify ONT lineprofile, serviceprofile and DBA profile in dashboard
        self.assertIn("ont-lineprofile gpon", content)
        self.assertIn("ont-srvprofile gpon", content)
        self.assertIn("dba-profile add", content)
        self.assertIn("service-port 100 vlan 100", content)
        self.assertIn("ZTE C300/C320 GPON OLT", content)
        self.assertIn("onu-profile gpon line", content)

        # Verify Section 16 OLT / ONT check is prioritized before switch trunks
        olt_pos = content.find("GPON OLT, ONT & ROUTER CONFIGS")
        trunk_pos = content.find("Huawei Switch Trunk Configuration")
        self.assertNotEqual(olt_pos, -1)
        self.assertNotEqual(trunk_pos, -1)
        self.assertLess(olt_pos, trunk_pos)

    def test_three_mode_persona_and_seamless_handoff(self):
        """Verify 3-mode persona structure, seamless agent handoff, and network exclusivity."""
        from gam_ai.ui import get_ui_dir
        dash_path = os.path.join(get_ui_dir(), "dashboard.html")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Verify "Welcome to Local AI Assistant" hero heading
        self.assertIn('<h2 id="hero-title">Welcome to Local AI Assistant</h2>', content)
        self.assertIn("heroTitle: 'Welcome to Local AI Assistant'", content)

        # 2. Verify 3 strict modes in HTML
        self.assertIn('id="pill-general"', content)
        self.assertIn('id="pill-student"', content)
        self.assertIn('id="pill-neteng"', content)

        # 3. Verify seamless agent handoff functions
        self.assertIn("switchPersonaSeamless(targetPersona, reason)", content)
        self.assertIn("Seamless Agent Handoff", content)
        self.assertIn("isNetworkQuery", content)
        self.assertIn("isStudentQuery", content)

        # 4. Verify Student Mode pedagogical questions
        self.assertIn("Gravity & Our Solar System (Explained for Grade 6)", content)
        self.assertIn("Step-by-Step Train Speed Solution", content)
        self.assertIn("RAM vs. Storage Explained for Beginners", content)

    def test_version_history_and_snapshots(self):
        """Verify versions directory, VERSION_HISTORY.md, and snapshot integrity."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        versions_dir = os.path.join(repo_root, "versions")
        self.assertTrue(os.path.isdir(versions_dir))

        hist_file = os.path.join(versions_dir, "VERSION_HISTORY.md")
        self.assertTrue(os.path.isfile(hist_file))

        with open(hist_file, "r", encoding="utf-8") as f:
            hist_content = f.read()
        self.assertIn("v1.0.0", hist_content)
        self.assertIn("v1.1.0", hist_content)
        self.assertIn("v1.2.0", hist_content)
        self.assertIn("v1.3.0", hist_content)

        # Verify snapshots exist
        for v in ["v1.0.0", "v1.1.0", "v1.2.0", "v1.3.0"]:
            v_path = os.path.join(versions_dir, v)
            self.assertTrue(os.path.isdir(v_path), f"Missing version folder: {v}")
            self.assertTrue(os.path.isfile(os.path.join(v_path, "README.md")))
            self.assertTrue(os.path.isfile(os.path.join(v_path, "CHECKSUMS.sha256")))
            self.assertTrue(os.path.isdir(os.path.join(v_path, "code_snapshot")))

    def test_online_offline_mode_distinction_and_auto_switch(self):
        """Verify clear online vs offline distinction, auto-switch, live refresh, and lens accuracy."""
        from gam_ai.ui import get_ui_dir
        dash_path = os.path.join(get_ui_dir(), "dashboard.html")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Verify header toggle button and mode state
        self.assertIn('id="btn-mode-toggle"', content)
        self.assertIn("toggleOnlineOfflineMode()", content)
        self.assertIn("setExecutionMode(mode, skipRefresh)", content)

        # 2. Verify auto-refresh on offline -> online toggle
        self.assertIn("refreshLastQueryWithOnlineData(lastUserQuery)", content)
        self.assertIn("action:refresh_online", content)
        self.assertIn("btn:🌐 Refresh with Latest Online Data", content)

        # 3. Verify auto-switch when offline query not found
        self.assertIn("Auto-Switched to Online Mode", content)
        self.assertIn("isNetAvailable", content)

        # 4. Verify greeting responder prevents Pareto essay hallucinations
        self.assertIn("getGreetingOrCapabilityResponse", content)
        self.assertIn("allowUniversalFallback", content)

        # 5. Verify camera lens persona & object awareness (textiles vs switches)
        self.assertIn("Floral Fabric & Textile", content)
        self.assertIn("Patterned Fabric & Textile Material", content)

if __name__ == "__main__":
    unittest.main()



