"""MemoryManager: Coordinates ActiveContext, ShortTermMemory, and LongTermMemory."""
from typing import List
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.memory.active import ActiveContext
from gam_ai.core.memory.short_term import ShortTermMemory
from gam_ai.core.memory.long_term import LongTermMemory

class MemoryManager:
    def __init__(self, db: DatabaseManager, max_short_term: int = 5):
        self.db = db
        self.active = ActiveContext()
        self.short_term = ShortTermMemory(max_messages=max_short_term)
        self.long_term = LongTermMemory(db)

    def set_short_term_capacity(self, max_messages: int) -> None:
        self.short_term.set_capacity(max_messages)

    def add_interaction(self, role: str, content: str) -> None:
        self.short_term.add_message(role, content)

    def get_relevant_memory_strings(self, query: str) -> List[str]:
        items = self.long_term.recall(query, limit=3)
        return [f"{it['key']}: {it['value']}" for it in items]

    def reset_active(self) -> None:
        self.active.clear()
