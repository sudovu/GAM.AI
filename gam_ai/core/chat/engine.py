
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

import uuid
import logging
from typing import Dict, Any, Optional, List
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

FOLLOW_UP_TRIGGERS = {
    "next", "another", "another one", "one more", "more", "next one", "tell me another",
    "continue", "next please", "keep going", "and next", "what next",
    "अगला", "और एक", "दूसरा", "एक और", "और सुनाओ", "आगे", "अगला चुटकुला", "एक और चुटकुला",
    "अर्को", "अर्को भन", "अर्को जोक", "थप", "अगाडि बढ", "फेरि भन"
}

REFERENTIAL_TRIGGERS = {
    "why", "why?", "why is that", "why is that?", "explain", "explain more", "elaborate",
    "give an example", "give example", "show in python", "how does it work", "how does that work",
    "ऐसा क्यों", "विस्तार से समझाओ", "और बताओ", "किन यस्तो भयो", "थप व्याख्या गर्नुहोस्"
}

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

    def save_message_to_db(self, conversation_id: str, role: str, content: str, token_count: int = 0) -> str:
        """Persist a conversation turn to SQLite for persistent local chat storage."""
        msg_id = str(uuid.uuid4())
        try:
            title = (content[:40] + "...") if role == "user" else "Chat Session"
            self.db.execute(
                "INSERT OR IGNORE INTO conversations (id, title) VALUES (?, ?);",
                (conversation_id, title)
            )
            self.db.execute(
                "UPDATE conversations SET last_active = CURRENT_TIMESTAMP WHERE id = ?;",
                (conversation_id,)
            )
            self.db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, token_count) VALUES (?, ?, ?, ?, ?);",
                (msg_id, conversation_id, role, content, token_count)
            )
            self.db.commit()
        except Exception as e:
            logger.warning("Failed to save message to SQLite: %s", e)
        return msg_id

    def get_chat_history(self, conversation_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve locally stored conversation messages from SQLite."""
        try:
            if conversation_id:
                cursor = self.db.execute(
                    "SELECT id, conversation_id, role, content, timestamp, token_count FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?;",
                    (conversation_id, limit)
                )
            else:
                cursor = self.db.execute(
                    "SELECT id, conversation_id, role, content, timestamp, token_count FROM messages ORDER BY timestamp ASC LIMIT ?;",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Failed to retrieve chat history from SQLite: %s", e)
            return []

    def clear_chat_history(self, conversation_id: Optional[str] = None) -> int:
        """Clear local chat messages from SQLite and reset memory buffers."""
        try:
            if conversation_id:
                cursor = self.db.execute("DELETE FROM messages WHERE conversation_id = ?;", (conversation_id,))
                self.db.execute("DELETE FROM conversations WHERE id = ?;", (conversation_id,))
            else:
                cursor = self.db.execute("DELETE FROM messages;")
                self.db.execute("DELETE FROM conversations;")
            self.db.commit()
            deleted = cursor.rowcount
        except Exception as e:
            logger.warning("Failed to clear chat history from SQLite: %s", e)
            deleted = 0
        self.memory.short_term.clear()
        return deleted

    def _resolve_contextual_query(self, user_text: str) -> str:
        """Enrich short follow-up queries ('next', 'why', 'explain that') with prior conversation context."""
        clean = user_text.lower().strip("?!.,'\" ")
        history = self.memory.short_term.get_messages()
        if not history:
            return user_text

        # Find the last user and assistant interactions
        last_user = next((m["content"] for m in reversed(history) if m.get("role") == "user"), "")
        last_assistant = next((m["content"] for m in reversed(history) if m.get("role") == "assistant"), "")

        if clean in FOLLOW_UP_TRIGGERS:
            # If the user asks for "next" or "another one"
            if "joke" in last_user.lower() or "joke" in last_assistant.lower():
                return f"Tell me another funny joke (different from: {last_assistant[:60]})"
            if "riddle" in last_user.lower():
                return f"Tell me another clever riddle"
            if "quote" in last_user.lower():
                return f"Give me another motivational quote"
            if "story" in last_user.lower() or "poem" in last_user.lower():
                return f"Continue the story or poem"
            if last_user:
                return f"Next step or continuation for: {last_user}"

        if clean in REFERENTIAL_TRIGGERS or clean.startswith("why ") or clean.startswith("explain "):
            if last_assistant:
                return f"Elaborate and explain the following concept in detail with examples: {last_assistant[:150]}"
            if last_user:
                return f"Elaborate in detail on: {last_user}"

        return user_text

    def process_query(self, user_text: str, mode: str = "auto", conversation_id: str = "default") -> Dict[str, Any]:
        user_text = SecurityGuard.sanitize_input(user_text.strip())
        if not user_text:
            return {"response": "", "source": "empty", "mode": "offline", "tokens": 0}

        if user_text.startswith("/"):
            cmd_result = self.commands.execute(user_text)
            return {
                "response": cmd_result["message"],
                "source": "command",
                "mode": "offline",
                "data": cmd_result.get("data")
            }

        # Multi-turn context resolution
        effective_query = self._resolve_contextual_query(user_text)

        freq = self.research.record_query(effective_query)

        knowledge_matches = self.knowledge.search_knowledge(effective_query, limit=2)
        source_type = "local_knowledge"
        knowledge_texts = [k["claim"] for k in knowledge_matches]

        cache_key = f"research:{effective_query.lower()}"
        cached_entry = self.cache.get(cache_key)

        if not knowledge_matches and cached_entry:
            source_type = "cache"
            knowledge_texts.append(cached_entry["content"])

            if freq >= self.promotion_threshold or cached_entry["access_count"] >= self.promotion_threshold:
                promoted_id = self.knowledge.promote_from_cache(
                    topic=effective_query.title(),
                    claim=cached_entry["content"],
                    source=cached_entry.get("source")
                )
                logger.info("Promoted query '%s' to permanent knowledge (id=%s)", effective_query, promoted_id)

        if not knowledge_texts:
            is_online = (mode != "offline") and self.capabilities.check_network_connectivity()
            if is_online:
                res = self.research.research(effective_query)
                if res.get("content"):
                    knowledge_texts.append(res["content"])
                    source_type = "web_research"
            else:
                source_type = "local_offline"

        doc_chunks = self.retriever.retrieve_context(effective_query, top_k=2)
        for dc in doc_chunks:
            knowledge_texts.append(f"[{dc['source']}] {dc['content']}")

        memories = self.memory.get_relevant_memory_strings(effective_query)

        payload = self.context_budget.build_budgeted_prompt(
            query=effective_query,
            memory_items=memories,
            knowledge_items=knowledge_texts,
            history=self.memory.short_term.get_messages()
        )
        prompt_str = self.context_budget.assemble_prompt_string(payload)

        model = self.models.load_model(self.config.default_model_tier)
        gen_request = GenerationRequest(prompt=prompt_str)
        gen_response = model.generate(gen_request)

        # Update in-memory rolling history
        self.memory.add_interaction("user", user_text)
        self.memory.add_interaction("assistant", gen_response.text)
        self.memory.reset_active()

        # Persist conversation turn in SQLite database
        self.save_message_to_db(conversation_id, "user", user_text, token_count=len(user_text.split()))
        self.save_message_to_db(conversation_id, "assistant", gen_response.text, token_count=gen_response.completion_tokens)

        is_offline_result = (mode == "offline") or (source_type != "web_research")

        return {
            "response": gen_response.text,
            "source": source_type,
            "mode": "offline" if is_offline_result else "online",
            "prompt_tokens": gen_response.prompt_tokens,
            "completion_tokens": gen_response.completion_tokens,
            "model_name": gen_response.model_name,
            "frequency": freq,
            "conversation_id": conversation_id
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
            "GAM.AI - MICRO RESOURCE STATUS",
            "============================================================",
            f"Device Profile:      {d_sum['device_profile']} (Cores: {d_sum['cores']})",
            f"Mode:                [{'ONLINE' if d_sum['online'] else 'OFFLINE'}]",
            f"Active Model:        {model_name} (RAM: ~{self.models.get_ram_usage_mb()} MB)",
            f"Total RAM:           {d_sum['total_ram_mb']} MB (Available: {d_sum['available_ram_mb']} MB)",
            f"Storage Pressure:    {d_sum['storage_pressure']} (Free: {d_sum['free_disk_mb']} MB)",
            f"SQLite DB Size:      {db_stats['db_size_kb']} KB",
            f"Smart Cache:         {c_stats['total_entries']} entries ({c_stats['total_size_kb']} KB / max {c_stats['max_cache_mb']} MB)",
            f"Permanent Knowledge: {k_stats['total_items']} items ({k_stats['total_topics']} topics)",
            "============================================================"
        ]
        return "\n".join(lines)

    def close(self) -> None:
        """Close underlying database connection and release resources."""
        if hasattr(self, "db") and self.db:
            self.db.close()
