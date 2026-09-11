"""DeviceCapabilityManager: Detects hardware and selects optimal micro-resource execution profile."""
import os
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from gam_ai.platform.detector import get_platform_info, get_memory_info, get_disk_info, get_cpu_info

class DeviceProfile(str, Enum):
    ULTRA_LOW = "ULTRA_LOW" # < 1.5 GB RAM, older phone / IoT
    LOW = "LOW"             # 1.5 - 3.5 GB RAM, budget mobile
    MEDIUM = "MEDIUM"       # 3.5 - 7.5 GB RAM, mid-range phone / tablet
    HIGH = "HIGH"           # 8 - 15 GB RAM, laptop / flagship phone
    DESKTOP = "DESKTOP"     # >= 16 GB RAM, desktop workstation

class StoragePressure(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"

@dataclass
class HardwareProfileConfig:
    profile: DeviceProfile
    default_model_tier: str       # 'nano', 'micro', 'small', 'standard'
    default_quantization: str     # 'q4_k_m', 'q8_0', 'fp16', 'embedded'
    max_context_tokens: int       # e.g., 512, 1024, 2048, 4096
    max_history_in_ram: int       # e.g., 3, 5, 10, 20 messages
    max_cache_mb: int             # e.g., 10, 25, 50, 200 MB
    threads: int                  # inference thread count
    batch_size: int               # chunk batch size
    enable_background_work: bool  # background cleanup/sync
    compact_embeddings: bool      # use 64 or 128 dim instead of 384+

PROFILE_CONFIGS: Dict[DeviceProfile, HardwareProfileConfig] = {
    DeviceProfile.ULTRA_LOW: HardwareProfileConfig(
        profile=DeviceProfile.ULTRA_LOW,
        default_model_tier="nano",
        default_quantization="q4_k_m",
        max_context_tokens=512,
        max_history_in_ram=3,
        max_cache_mb=10,
        threads=1,
        batch_size=1,
        enable_background_work=False,
        compact_embeddings=True
    ),
    DeviceProfile.LOW: HardwareProfileConfig(
        profile=DeviceProfile.LOW,
        default_model_tier="micro",
        default_quantization="q4_k_m",
        max_context_tokens=1024,
        max_history_in_ram=5,
        max_cache_mb=25,
        threads=2,
        batch_size=2,
        enable_background_work=False,
        compact_embeddings=True
    ),
    DeviceProfile.MEDIUM: HardwareProfileConfig(
        profile=DeviceProfile.MEDIUM,
        default_model_tier="micro",
        default_quantization="q4_k_m",
        max_context_tokens=2048,
        max_history_in_ram=10,
        max_cache_mb=50,
        threads=4,
        batch_size=4,
        enable_background_work=True,
        compact_embeddings=False
    ),
    DeviceProfile.HIGH: HardwareProfileConfig(
        profile=DeviceProfile.HIGH,
        default_model_tier="small",
        default_quantization="q8_0",
        max_context_tokens=4096,
        max_history_in_ram=15,
        max_cache_mb=100,
        threads=4,
        batch_size=8,
        enable_background_work=True,
        compact_embeddings=False
    ),
    DeviceProfile.DESKTOP: HardwareProfileConfig(
        profile=DeviceProfile.DESKTOP,
        default_model_tier="standard",
        default_quantization="fp16",
        max_context_tokens=8192,
        max_history_in_ram=25,
        max_cache_mb=250,
        threads=8,
        batch_size=16,
        enable_background_work=True,
        compact_embeddings=False
    ),
}

class DeviceCapabilityManager:
    def __init__(self, override_profile: Optional[DeviceProfile] = None, data_dir: str = "."):
        self.override_profile = override_profile
        self.data_dir = data_dir
        self.platform_info = get_platform_info()
        self.memory_info = get_memory_info()
        self.disk_info = get_disk_info(data_dir)
        self.cpu_info = get_cpu_info()
        self.battery_level: Optional[int] = 100
        self.is_charging: bool = True
        self.is_thermal_throttling: bool = False
        self._online_status: Optional[bool] = None

        self.profile = self._resolve_profile()
        self.config = PROFILE_CONFIGS[self.profile]

    def _resolve_profile(self) -> DeviceProfile:
        if self.override_profile:
            return self.override_profile

        ram_mb = self.memory_info.get("available_ram_mb", 1024)
        total_ram = self.memory_info.get("total_ram_mb", 1024)
        effective_ram = min(total_ram, ram_mb * 2)

        if effective_ram < 1500:
            return DeviceProfile.ULTRA_LOW
        elif effective_ram < 3800:
            return DeviceProfile.LOW
        elif effective_ram < 7500:
            return DeviceProfile.MEDIUM
        elif effective_ram < 15000:
            return DeviceProfile.HIGH
        else:
            return DeviceProfile.DESKTOP

    def refresh(self) -> None:
        self.memory_info = get_memory_info()
        self.disk_info = get_disk_info(self.data_dir)
        if not self.override_profile:
            self.profile = self._resolve_profile()
            self.config = PROFILE_CONFIGS[self.profile]

    def get_storage_pressure(self) -> StoragePressure:
        free_mb = self.disk_info.get("free_disk_mb", 1024)
        total_mb = max(1, self.disk_info.get("total_disk_mb", 4096))
        pct_free = (free_mb / total_mb) * 100.0

        if free_mb < 200 or pct_free < 3.0:
            return StoragePressure.CRITICAL
        elif free_mb < 1000 or pct_free < 10.0:
            return StoragePressure.LOW
        return StoragePressure.NORMAL

    def is_battery_constrained(self) -> bool:
        if self.battery_level is not None and not self.is_charging:
            if self.battery_level <= 20:
                return True
        return False

    def check_network_connectivity(self, test_host: str = "1.1.1.1", port: int = 53, timeout: float = 0.5) -> bool:
        if self._online_status is not None:
            return self._online_status
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((test_host, port))
            s.close()
            return True
        except Exception:
            return False

    def set_online_override(self, online: Optional[bool]) -> None:
        self._online_status = online

    def get_effective_config(self) -> HardwareProfileConfig:
        base = PROFILE_CONFIGS[self.profile]
        if self.is_battery_constrained() or self.is_thermal_throttling:
            downgrade_map = {
                DeviceProfile.DESKTOP: DeviceProfile.HIGH,
                DeviceProfile.HIGH: DeviceProfile.MEDIUM,
                DeviceProfile.MEDIUM: DeviceProfile.LOW,
                DeviceProfile.LOW: DeviceProfile.ULTRA_LOW,
                DeviceProfile.ULTRA_LOW: DeviceProfile.ULTRA_LOW,
            }
            return PROFILE_CONFIGS[downgrade_map[self.profile]]
        return base

    def get_summary(self) -> Dict[str, Any]:
        return {
            "os": self.platform_info["os"],
            "arch": self.platform_info["architecture"],
            "cores": self.cpu_info["cores"],
            "total_ram_mb": self.memory_info["total_ram_mb"],
            "available_ram_mb": self.memory_info["available_ram_mb"],
            "free_disk_mb": self.disk_info["free_disk_mb"],
            "device_profile": self.profile.value,
            "recommended_model": self.config.default_model_tier,
            "max_context_tokens": self.config.max_context_tokens,
            "storage_pressure": self.get_storage_pressure().value,
            "battery_constrained": self.is_battery_constrained(),
            "online": self.check_network_connectivity()
        }
