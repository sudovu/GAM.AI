"""Cross-platform hardware and system environment inspector."""
import platform
import os
import sys
import shutil
from typing import Dict, Any

def get_platform_info() -> Dict[str, Any]:
    system_name = platform.system().lower()
    is_android = "android" in sys.platform or "ANDROID_ROOT" in os.environ
    is_ios = sys.platform == "ios" or "IPHONE_SIMULATOR_ROOT" in os.environ
    return {
        "os": "android" if is_android else ("ios" if is_ios else system_name),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_mobile": is_android or is_ios or "arm" in platform.machine().lower(),
    }

def get_memory_info() -> Dict[str, int]:
    total_mb = 1024
    available_mb = 512
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                mem_data = {}
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val_str = parts[1].strip().split()[0]
                        mem_data[key] = int(val_str)
                if "MemTotal" in mem_data:
                    total_mb = mem_data["MemTotal"] // 1024
                if "MemAvailable" in mem_data:
                    available_mb = mem_data["MemAvailable"] // 1024
                elif "MemFree" in mem_data:
                    available_mb = (mem_data.get("MemFree", 0) + mem_data.get("Buffers", 0) + mem_data.get("Cached", 0)) // 1024
            return {"total_ram_mb": total_mb, "available_ram_mb": available_mb}
        except Exception:
            pass
    return {"total_ram_mb": total_mb, "available_ram_mb": available_mb}

def get_disk_info(path: str = ".") -> Dict[str, int]:
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "total_disk_mb": total // (1024 * 1024),
            "free_disk_mb": free // (1024 * 1024),
        }
    except Exception:
        return {"total_disk_mb": 4096, "free_disk_mb": 1024}

def get_cpu_info() -> Dict[str, Any]:
    count = os.cpu_count() or 1
    return {
        "cores": count,
        "recommended_threads": max(1, min(count - 1, 4)) if count > 1 else 1
    }
