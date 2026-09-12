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
    def __init__(self, max_context_tokens: int = 2048, min_generation_tokens: int = 256):
        self.max_context_tokens = max(32, max_context_tokens)
        # Scaled generation reservation: never starve generation, leaving at least 15%-25% for response
        self.min_generation_tokens = min(min_generation_tokens, max(16, int(self.max_context_tokens * 0.20)))

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text.split()) * 1.3))

    def compress_text_to_token_limit(self, text: str, max_tokens: int) -> str:
        """Deterministically compresses large text/queries to guarantee staying within token limits."""
        if not text or max_tokens <= 0:
            return ""
        est = self.estimate_tokens(text)
        if est <= max_tokens:
            return text

        words = text.split()
        target_words = max(1, int(max_tokens / 1.3))
        if len(words) <= target_words:
            return text

        head = max(1, target_words // 2)
        tail = max(0, target_words - head - 4)
        if tail > 0 and (head + tail) < len(words):
            omitted = len(words) - (head + tail)
            return " ".join(words[:head]) + f" [...compacted {omitted} words for token safety...] " + " ".join(words[-tail:])
        return " ".join(words[:target_words])

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

        # Available prompt ceiling strictly leaves headroom for generation
        prompt_ceiling = max(20, self.max_context_tokens - self.min_generation_tokens)

        # 1. System Instruction allocation (up to 25% of ceiling)
        max_sys_tokens = max(10, int(prompt_ceiling * 0.25))
        if self.estimate_tokens(system_instruction) > max_sys_tokens:
            system_instruction = self.compress_text_to_token_limit(system_instruction, max_sys_tokens)
        sys_tokens = self.estimate_tokens(system_instruction)

        # 2. Query allocation (up to 45% of ceiling or remaining)
        avail_for_query_and_ctx = max(10, prompt_ceiling - sys_tokens)
        max_query_tokens = max(10, int(avail_for_query_and_ctx * 0.50))
        if self.estimate_tokens(query) > max_query_tokens:
            query = self.compress_text_to_token_limit(query, max_query_tokens)
        query_tokens = self.estimate_tokens(query)

        # 3. Remaining context headroom
        remaining_ctx = max(0, prompt_ceiling - sys_tokens - query_tokens)

        # 4. Memory allocation (up to 25% of remaining context)
        mem_budget = int(remaining_ctx * 0.25)
        selected_memory = []
        current_mem_tokens = 0
        for m in memory_items:
            t = self.estimate_tokens(m)
            if current_mem_tokens + t <= mem_budget:
                selected_memory.append(m)
                current_mem_tokens += t
            else:
                break

        # 5. Knowledge allocation (up to 50% of remaining context)
        know_budget = int(remaining_ctx * 0.50)
        selected_knowledge = []
        current_know_tokens = 0
        for k in knowledge_items:
            t = self.estimate_tokens(k)
            if current_know_tokens + t <= know_budget:
                selected_knowledge.append(k)
                current_know_tokens += t
            else:
                break

        # 6. Conversation History allocation (fills remaining budget)
        hist_budget = max(0, remaining_ctx - current_mem_tokens - current_know_tokens)
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

        # Guaranteed safety clamp: prompt NEVER exceeds prompt_ceiling or max_context_tokens
        if total_tokens > prompt_ceiling:
            while selected_history and total_tokens > prompt_ceiling:
                dropped = selected_history.pop(0)
                total_tokens -= (self.estimate_tokens(dropped.get("content", "")) + 4)
            while selected_knowledge and total_tokens > prompt_ceiling:
                dropped_k = selected_knowledge.pop()
                total_tokens -= self.estimate_tokens(dropped_k)

        return ContextPayload(
            system_instruction=system_instruction,
            query=query,
            memory_snippets=selected_memory,
            knowledge_snippets=selected_knowledge,
            conversation_history=selected_history,
            total_estimated_tokens=total_tokens
        )

    def get_remaining_generation_tokens(self, payload: ContextPayload) -> int:
        """Returns guaranteed safe token limit for model completion so it never overflows."""
        headroom = self.max_context_tokens - payload.total_estimated_tokens
        return max(16, headroom)

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
