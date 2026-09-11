"""ShortTermMemory: Rolling in-memory conversation buffer with strict capacity limit."""
from typing import List, Dict
from collections import deque

class ShortTermMemory:
    def __init__(self, max_messages: int = 5):
        self.max_messages = max_messages
        self._buffer: deque = deque(maxlen=max_messages)

    def add_message(self, role: str, content: str) -> None:
        self._buffer.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self._buffer)

    def set_capacity(self, capacity: int) -> None:
        self.max_messages = capacity
        items = list(self._buffer)[-capacity:] if capacity > 0 else []
        self._buffer = deque(items, maxlen=capacity)

    def clear(self) -> None:
        self._buffer.clear()

    def get_ram_estimate_bytes(self) -> int:
        return sum(len(m.get("content", "")) for m in self._buffer)
