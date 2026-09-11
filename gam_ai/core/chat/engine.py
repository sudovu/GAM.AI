
CONVERSATIONAL_PHRASES = {
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "how are you", "how are you doing", "how's it going", "what's up",
    "thank you", "thanks", "bye", "goodbye", "see you", "tell me a joke",
    "say a joke", "tell a joke", "who are you", "what is your name",
    "what can you do", "help me", "नमस्ते", "नमस्कार", "धन्यवाद"
}

def is_conversational_query(text: str) -> bool:
    clean = text.lower().strip("?!.,'\" ")
    if clean in CONVERSATIONAL_PHRASES:
        return True
    for phrase in ("how are you", "tell me a joke", "say a joke", "who are you", "what can you do", "tell me a story"):
        if phrase in clean:
            return True
    return False

"""ChatEngine: Central orchestrator coordinating 3-level storage, models, and research."""
import logging
from typing import Dict, Any, Optional
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.resources.capabilities import DeviceCapabilityManager, StoragePressure
from gam_ai.core.models.manager import ModelManager
from gam_ai.core.memory.manager import MemoryManager
from gam_ai.core.cache.smart_cache import SmartCacheManager
from gam_ai.core.knowledge.manager import KnowledgeManager
from gam_ai.core.knowledge.retention import RetentionManager
from gam_ai.core.research.engine import WebResearchEngine
from gam_ai.core.documents.processor import DocumentProcessor
from gam_ai.core.rag.retriever import LocalRetriever
from gam_ai.core.ai.context_budget import ContextBudgetManager
from gam_ai.core.chat.commands import CommandHandler
from gam_ai.core.security.guard import SecurityGuard
from gam_ai.interfaces.model import GenerationRequest

logger = logging.getLogger(__name__)

class ChatEngine:
    def __init__(
        self,
        db_path: str = ":memory:",
        override_profile = None,
        promotion_threshold: int = 3
    ):
        self.db = DatabaseManager(db_path)
        self.db.initialize()

        self.capabilities = DeviceCapabilityManager(override_profile=override_profile)
        self.config = self.capabilities.get_effective_config()

        self.models = ModelManager(default_tier=self.config.default_model_tier)
        self.memory = MemoryManager(self.db, max_short_term=self.config.max_history_in_ram)
        self.cache = SmartCacheManager(self.db, max_cache_mb=self.config.max_cache_mb)
        self.knowledge = KnowledgeManager(self.db)
        self.retention = RetentionManager(self.db, self.cache, self.knowledge)

        self.research = WebResearchEngine(self.db, self.cache)
        self.doc_processor = DocumentProcessor(self.db)
        self.retriever = LocalRetriever(self.db)
        self.context_budget = ContextBudgetManager(max_context_tokens=self.config.max_context_tokens)

        self.commands = CommandHandler(self)
        self.promotion_threshold = promotion_threshold

    def process_query(self, user_text: str) -> Dict[str, Any]:
        user_text = SecurityGuard.sanitize_input(user_text.strip())
        if not user_text:
            return {"response": "", "source": "empty", "tokens": 0}

        if user_text.startswith("/"):
            cmd_result = self.commands.execute(user_text)
            return {
                "response": cmd_result["message"],
                "source": "command",
                "data": cmd_result.get("data")
            }

        freq = self.research.record_query(user_text)

        knowledge_matches = self.knowledge.search_knowledge(user_text, limit=2)
        source_type = "local_knowledge"
        knowledge_texts = [k["claim"] for k in knowledge_matches]

        cache_key = f"research:{user_text.lower()}"
        cached_entry = self.cache.get(cache_key)

        if not knowledge_matches and cached_entry:
            source_type = "cache"
            knowledge_texts.append(cached_entry["content"])

            if freq >= self.promotion_threshold or cached_entry["access_count"] >= self.promotion_threshold:
                promoted_id = self.knowledge.promote_from_cache(
                    topic=user_text.title(),
                    claim=cached_entry["content"],
                    source=cached_entry.get("source")
                )
                logger.info("Promoted query '%s' to permanent knowledge (id=%s)", user_text, promoted_id)

        if not knowledge_texts:
            is_online = self.capabilities.check_network_connectivity()
            if is_online:
                res = self.research.research(user_text)
                if res.get("content"):
                    knowledge_texts.append(res["content"])
                    source_type = "web_research"
            else:
                source_type = "local_offline"

        doc_chunks = self.retriever.retrieve_context(user_text, top_k=2)
        for dc in doc_chunks:
            knowledge_texts.append(f"[{dc['source']}] {dc['content']}")

        memories = self.memory.get_relevant_memory_strings(user_text)

        payload = self.context_budget.build_budgeted_prompt(
            query=user_text,
            memory_items=memories,
            knowledge_items=knowledge_texts,
            history=self.memory.short_term.get_messages()
        )
        prompt_str = self.context_budget.assemble_prompt_string(payload)

        model = self.models.load_model(self.config.default_model_tier)
        gen_request = GenerationRequest(prompt=prompt_str)
        gen_response = model.generate(gen_request)

        self.memory.add_interaction("user", user_text)
        self.memory.add_interaction("assistant", gen_response.text)
        self.memory.reset_active()

        return {
            "response": gen_response.text,
            "source": source_type,
            "prompt_tokens": gen_response.prompt_tokens,
            "completion_tokens": gen_response.completion_tokens,
            "model_name": gen_response.model_name,
            "frequency": freq
        }

    def get_system_status(self) -> str:
        d_sum = self.capabilities.get_summary()
        c_stats = self.cache.get_stats()
        k_stats = self.knowledge.get_stats()
        db_stats = self.db.get_storage_stats()
        active_model = self.models.get_active_model()
        model_name = active_model.get_info().name if active_model else self.config.default_model_tier

        lines = [
            "============================================================",
            "GAM.AI — MICRO RESOURCE STATUS",
            "============================================================",
            f"Device Profile:      {d_sum['device_profile']} (Cores: {d_sum['cores']})",
            f"Mode:                ● {'ONLINE' if d_sum['online'] else 'OFFLINE'}",
            f"Active Model:        {model_name} (RAM: ~{self.models.get_ram_usage_mb()} MB)",
            f"Total RAM:           {d_sum['total_ram_mb']} MB (Available: {d_sum['available_ram_mb']} MB)",
            f"Storage Pressure:    {d_sum['storage_pressure']} (Free: {d_sum['free_disk_mb']} MB)",
            f"SQLite DB Size:      {db_stats['db_size_kb']} KB",
            f"Smart Cache:         {c_stats['total_entries']} entries ({c_stats['total_size_kb']} KB / max {c_stats['max_cache_mb']} MB)",
            f"Permanent Knowledge: {k_stats['total_items']} items ({k_stats['total_topics']} topics)",
            "============================================================"
        ]
        return "\n".join(lines)
