"""ModelManager: Oversees model catalog, modular model downloads, and strict memory unloading."""

import os
import glob
import time
import logging
from typing import Dict, Optional, List, Any
from gam_ai.interfaces.model import IModelProvider, ModelInfo
from gam_ai.core.models.providers import MicroLocalModelProvider, GGUFModelProvider

logger = logging.getLogger(__name__)

# Catalog of available modular models
MODULAR_CATALOG: Dict[str, Dict[str, Any]] = {
    "nano": {
        "id": "nano",
        "name": "GAM.AI Nano",
        "role": "general",
        "tier": "nano",
        "parameters": "0.5B",
        "ram_mb": 120,
        "download_size_mb": 398,
        "default_installed": True,
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "description": "Ultra-lightweight micro model for general chat and low-resource devices (< 1GB RAM)."
    },
    "micro": {
        "id": "micro",
        "name": "GAM.AI Micro",
        "role": "general",
        "tier": "micro",
        "parameters": "1.5B",
        "ram_mb": 350,
        "download_size_mb": 776,
        "default_installed": True,
        "filename": "llama-3.2-1b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "description": "Balanced everyday conversational assistant with low CPU overhead."
    },
    "coder": {
        "id": "coder",
        "name": "GAM.AI Coder",
        "role": "coding",
        "tier": "coding",
        "parameters": "1.5B",
        "ram_mb": 450,
        "download_size_mb": 920,
        "default_installed": False,
        "filename": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "description": "Specialized in Python, Bash, network automation, and system administration scripts."
    },
    "descriptive": {
        "id": "descriptive",
        "name": "GAM.AI Descriptive",
        "role": "documentation",
        "tier": "small",
        "parameters": "3.0B",
        "ram_mb": 900,
        "download_size_mb": 1930,
        "default_installed": False,
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "description": "In-depth technical explanations, architecture design docs, and long-form analysis."
    },
    "picture": {
        "id": "picture",
        "name": "GAM.AI Picture & Diagram",
        "role": "diagram",
        "tier": "vision",
        "parameters": "1.0B",
        "ram_mb": 380,
        "download_size_mb": 650,
        "default_installed": False,
        "filename": "gam-ai-diagram-v1.gguf",
        "url": "https://huggingface.co/gam-ai/models/resolve/main/diagram-generator.gguf",
        "description": "Generates network topology diagrams (Mermaid & ASCII) and visual architecture layouts."
    },
    "neteng": {
        "id": "neteng",
        "name": "GAM.AI NetEng",
        "role": "sysadmin",
        "tier": "micro",
        "parameters": "1.5B",
        "ram_mb": 390,
        "download_size_mb": 850,
        "default_installed": False,
        "filename": "neteng-cisco-huawei-olt.gguf",
        "url": "https://huggingface.co/gam-ai/models/resolve/main/neteng.gguf",
        "description": "Cisco IOS, Huawei VRP, GPON OLT, and Fortinet/MikroTik configuration specialist."
    }
}

class ModelManager:
    def __init__(self, default_tier: str = "nano", models_dir: str = "models", idle_timeout_seconds: int = 300):
        self.default_tier = default_tier
        self.models_dir = models_dir
        self.idle_timeout_seconds = idle_timeout_seconds
        self._providers: Dict[str, IModelProvider] = {}
        self._active_model_name: Optional[str] = None
        self._last_used_timestamp: float = time.time()
        
        self._register_catalog_providers()
        self.scan_models_dir(models_dir)

    def _register_catalog_providers(self) -> None:
        for model_id, meta in MODULAR_CATALOG.items():
            provider = MicroLocalModelProvider(
                name=meta["name"],
                tier=meta["tier"],
                ram_mb=meta["ram_mb"],
                specialized_role=meta["role"]
            )
            self._providers[model_id] = provider
            self._providers[meta["name"].lower()] = provider

    def scan_models_dir(self, models_dir: str = "models") -> int:
        if not os.path.exists(models_dir):
            return 0

        count = 0
        for gguf_file in glob.glob(os.path.join(models_dir, "*.gguf")):
            base_name = os.path.basename(gguf_file)
            clean_name = os.path.splitext(base_name)[0]
            provider = GGUFModelProvider(
                model_path=gguf_file,
                name=f"GGUF: {clean_name}"
            )
            self._providers[clean_name.lower()] = provider
            count += 1
        return count

    def get_catalog_with_status(self) -> List[Dict[str, Any]]:
        """Return all catalog models along with their local installation and memory status."""
        catalog = []
        os.makedirs(self.models_dir, exist_ok=True)

        for mid, meta in MODULAR_CATALOG.items():
            model_file = os.path.join(self.models_dir, meta["filename"])
            is_file_on_disk = os.path.exists(model_file)
            
            # Built-in micro engine is always ready; GGUF file is installed if on disk
            is_installed = meta["default_installed"] or is_file_on_disk
            provider = self._providers.get(mid)
            is_loaded = provider.is_loaded() if provider else False

            item = dict(meta)
            item["is_installed"] = is_installed
            item["is_loaded"] = is_loaded
            item["is_active"] = (self._active_model_name == meta["name"].lower())
            catalog.append(item)
        return catalog

    def get_available_models(self) -> List[ModelInfo]:
        return [p.get_info() for p in self._providers.values()]

    def load_model(self, model_name_or_id: str) -> IModelProvider:
        target_name = model_name_or_id.lower()
        provider = self._providers.get(target_name)

        if not provider:
            # Fallback to tier lookup
            for p in self._providers.values():
                if p.get_info().tier == target_name:
                    provider = p
                    break

        if not provider:
            provider = self._providers.get("nano") or self._providers.get("gam.ai nano")

        current_name = provider.get_info().name.lower()
        if self._active_model_name and self._active_model_name != current_name:
            old_provider = self._providers.get(self._active_model_name)
            if old_provider and old_provider.is_loaded():
                logger.info("Unloading '%s' from RAM before loading '%s'", self._active_model_name, provider.get_info().name)
                old_provider.unload()

        provider.load()
        self._active_model_name = current_name
        self._last_used_timestamp = time.time()
        return provider

    def unload_active_model(self) -> None:
        if self._active_model_name:
            provider = self._providers.get(self._active_model_name)
            if provider and provider.is_loaded():
                provider.unload()
            self._active_model_name = None

    def check_idle_timeout(self) -> bool:
        """Unload active model if idle longer than timeout."""
        if self._active_model_name and (time.time() - self._last_used_timestamp) > self.idle_timeout_seconds:
            logger.info("Idle timeout reached (%ds). Unloading model to reclaim RAM.", self.idle_timeout_seconds)
            self.unload_active_model()
            return True
        return False

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
