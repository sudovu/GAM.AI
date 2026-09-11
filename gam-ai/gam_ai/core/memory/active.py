"""ActiveContext: Ephemeral in-memory context for the ongoing request."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class ActiveContext:
    query: str = ""
    intent: str = "general"
    extracted_entities: List[str] = field(default_factory=list)
    cache_hit: bool = False
    source_used: Optional[str] = None
    intermediate_data: Dict[str, Any] = field(default_factory=dict)

    def clear(self) -> None:
        self.query = ""
        self.intent = "general"
        self.extracted_entities.clear()
        self.cache_hit = False
        self.source_used = None
        self.intermediate_data.clear()
