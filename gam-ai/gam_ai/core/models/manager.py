"""ModelManager: Oversees model catalog, lazy loading, switching, and strict memory unloading."""
import logging
from typing import Dict, Optional, List
from gam_ai.interfaces.model import IModelProvider, ModelInfo
from gam_ai.core.models.providers import MicroLocalModelProvider

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self, default_tier: str = "micro"):
        self.default_tier = default_tier
        self._providers: Dict[str, IModelProvider] = {}
        self._active_model_name: Optional[str] = None
        self._register_default_models()

    def _register_default_models(self) -> None:
        models = [
            ("GAM.AI Nano", "nano", 120),
            ("GAM.AI Micro", "micro", 350),
            ("GAM.AI Small", "small", 900),
            ("GAM.AI Standard", "standard", 2200),
            ("GAM.AI Code", "coding", 500),
        ]
        for name, tier, ram in models:
            self._providers[name.lower()] = MicroLocalModelProvider(name=name, tier=tier, ram_mb=ram)

    def register_provider(self, provider: IModelProvider) -> None:
        info = provider.get_info()
        self._providers[info.name.lower()] = provider

    def get_available_models(self) -> List[ModelInfo]:
        return [p.get_info() for p in self._providers.values()]

    def get_model_for_tier(self, tier: str) -> IModelProvider:
        tier_lower = tier.lower()
        for p in self._providers.values():
            if p.get_info().tier == tier_lower:
                return p
        return self._providers.get("gam.ai micro")

    def load_model(self, model_name_or_tier: str) -> IModelProvider:
        target_name = model_name_or_tier.lower()
        provider = self._providers.get(target_name)
        if not provider:
            provider = self.get_model_for_tier(target_name)

        if not provider:
            raise ValueError(f"Unknown model or tier: {model_name_or_tier}")

        if self._active_model_name and self._active_model_name != provider.get_info().name.lower():
            old_provider = self._providers.get(self._active_model_name)
            if old_provider and old_provider.is_loaded():
                old_provider.unload()

        provider.load()
        self._active_model_name = provider.get_info().name.lower()
        return provider

    def unload_active_model(self) -> None:
        if self._active_model_name:
            provider = self._providers.get(self._active_model_name)
            if provider and provider.is_loaded():
                provider.unload()
            self._active_model_name = None

    def get_active_model(self) -> Optional[IModelProvider]:
        if self._active_model_name:
            return self._providers.get(self._active_model_name)
        return None

    def get_ram_usage_mb(self) -> int:
        total = 0
        for p in self._providers.values():
            info = p.get_info()
            if info.loaded:
                total += info.ram_required_mb
        return total
