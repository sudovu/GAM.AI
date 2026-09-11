"""Abstract base interfaces for Storage and Cache."""
from abc import ABC, abstractmethod

class IStorage(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
