"""Abstract base classes for Web Search & Source Retrieval."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    domain: str
    score: float = 1.0
    published_date: Optional[str] = None
    raw_content: Optional[str] = None

class ISearchProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def search(self, query: str, max_results: int = 3) -> List[SearchResultItem]:
        pass
