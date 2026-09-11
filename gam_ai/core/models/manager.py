"""ModelManager: Oversees model catalog, GGUF auto-discovery, lazy loading, and strict memory unloading."""

import os
import glob
import logging
from typing import Dict, Optional, List
from gam_ai.interfaces.model import IModelProvider, ModelInfo
from gam_ai.core.models.providers import MicroLocalModelProvider, GGUFModelProvider

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages active models, ensuring only the needed model is resident in RAM."""

    def __init__(self, default_tier: str = "micro", models_dir: str = "models"):
        self.default_tier = default_tier
        self.models_dir = models_dir
        self._providers: Dict[str, IModelProvider] = {}
        self._active_model_name: Optional[str] = None
        self._register_default_models()
        self.scan_models_dir(models_dir)

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

    def scan_models_dir(self, models_dir: str = "models") -> int:
        """Scan directory for downloaded .gguf models and register them automatically."""
        if not os.path.exists(models_dir):
            return 0

        count = 0
        for gguf_file in glob.glob(os.path.join(models_dir, "*.gguf")):
            base_name = os.path.basename(gguf_file)
            clean_name = os.path.splitext(base_name)[0]
            
            # Infer tier from filename if possible
            lower_name = clean_name.lower()
            if "0.5b" in lower_name or "nano" in lower_name:
                tier = "nano"
            elif "1b" in lower_name or "micro" in lower_name or "1.5b" in lower_name:
                tier = "micro"
            elif "3b" in lower_name or "small" in lower_name:
                tier = "small"
            elif "code" in lower_name:
                tier = "coding"
            else:
                tier = "standard"

            provider = GGUFModelProvider(
                model_path=gguf_file,
                name=f"GGUF: {clean_name}",
                tier=tier
            )
            self._providers[clean_name.lower()] = provider
            self._providers[provider.get_info().name.lower()] = provider
            count += 1
            logger.info("Auto-registered GGUF model: %s (Tier: %s)", clean_name, tier)
        return count

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

        # If another model is currently active, unload it immediately to prevent RAM bloat
        current_name = provider.get_info().name.lower()
        if self._active_model_name and self._active_model_name != current_name:
            old_provider = self._providers.get(self._active_model_name)
            if old_provider and old_provider.is_loaded():
                logger.info("Unloading '%s' from RAM before loading '%s'", self._active_model_name, provider.get_info().name)
                old_provider.unload()

        provider.load()
        self._active_model_name = current_name
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
