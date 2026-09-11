"""Abstract base classes and dataclasses for Model Providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Generator

@dataclass
class ModelInfo:
    name: str
    tier: str  # nano, micro, small, standard
    parameters_billion: float
    quantization: str
    context_window: int
    ram_required_mb: int
    disk_required_mb: int
    loaded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationRequest:
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.2
    stop_sequences: List[str] = field(default_factory=list)
    system_instruction: Optional[str] = None

@dataclass
class GenerationResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model_name: str
    finish_reason: str = "stop"

class IModelProvider(ABC):
    @abstractmethod
    def get_info(self) -> ModelInfo:
        pass

    @abstractmethod
    def load(self) -> bool:
        pass

    @abstractmethod
    def unload(self) -> bool:
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        pass

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        pass

    @abstractmethod
    def generate_stream(self, request: GenerationRequest) -> Generator[str, None, None]:
        pass
