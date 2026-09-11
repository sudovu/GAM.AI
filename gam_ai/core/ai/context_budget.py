"""ContextBudgetManager: Strictly manages LLM prompt token allocations."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class ContextPayload:
    system_instruction: str
    query: str
    memory_snippets: List[str] = field(default_factory=list)
    knowledge_snippets: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    total_estimated_tokens: int = 0

class ContextBudgetManager:
    def __init__(self, max_context_tokens: int = 2048):
        self.max_context_tokens = max_context_tokens

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text.split()) * 1.3))

    def build_budgeted_prompt(
        self,
        query: str,
        system_instruction: str = "You are GAM.AI, a micro, local-first, resource-efficient AI assistant.",
        memory_items: Optional[List[str]] = None,
        knowledge_items: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> ContextPayload:
        memory_items = memory_items or []
        knowledge_items = knowledge_items or []
        history = history or []

        sys_tokens = self.estimate_tokens(system_instruction)
        query_tokens = self.estimate_tokens(query)
        remaining = max(100, self.max_context_tokens - sys_tokens - query_tokens - 100)

        mem_budget = int(remaining * 0.20)
        selected_memory = []
        current_mem_tokens = 0
        for m in memory_items:
            t = self.estimate_tokens(m)
            if current_mem_tokens + t <= mem_budget:
                selected_memory.append(m)
                current_mem_tokens += t
            else:
                break

        know_budget = int(remaining * 0.50)
        selected_knowledge = []
        current_know_tokens = 0
        for k in knowledge_items:
            t = self.estimate_tokens(k)
            if current_know_tokens + t <= know_budget:
                selected_knowledge.append(k)
                current_know_tokens += t
            else:
                break

        hist_budget = remaining - current_mem_tokens - current_know_tokens
        selected_history = []
        current_hist_tokens = 0
        for msg in reversed(history):
            content = msg.get("content", "")
            t = self.estimate_tokens(content) + 4
            if current_hist_tokens + t <= hist_budget:
                selected_history.insert(0, msg)
                current_hist_tokens += t
            else:
                break

        total_tokens = sys_tokens + query_tokens + current_mem_tokens + current_know_tokens + current_hist_tokens
        return ContextPayload(
            system_instruction=system_instruction,
            query=query,
            memory_snippets=selected_memory,
            knowledge_snippets=selected_knowledge,
            conversation_history=selected_history,
            total_estimated_tokens=total_tokens
        )

    def assemble_prompt_string(self, payload: ContextPayload) -> str:
        parts = [f"System: {payload.system_instruction}\n"]
        if payload.memory_snippets:
            parts.append("User Context & Preferences:")
            for m in payload.memory_snippets:
                parts.append(f"- {m}")
            parts.append("")
        if payload.knowledge_snippets:
            parts.append("Retrieved Knowledge:")
            for k in payload.knowledge_snippets:
                parts.append(f"- {k}")
            parts.append("")
        if payload.conversation_history:
            parts.append("Recent Conversation:")
            for msg in payload.conversation_history:
                role = msg.get("role", "user").capitalize()
                parts.append(f"{role}: {msg.get('content', '')}")
            parts.append("")
        parts.append(f"User Query: {payload.query}\nAssistant:")
        return "\n".join(parts)
