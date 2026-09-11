# Cross-Platform Roadmap: Android, iOS, Windows, Embedded

GAM.AI is designed for lightweight deployment across diverse operating systems and device form factors.

## Phase 1: Android Support
- **Runtime**: Termux native packaging or standalone APK via Chaquopy / Python-for-Android with ONNX Runtime Mobile or llama.cpp NDK bindings.
- **Default Profile**: `LOW` (GAM.AI Micro, 4-bit quantization, 25 MB cache limit).
- **Power Management**: BroadcastReceiver listening for `ACTION_BATTERY_LOW` and `ACTION_POWER_DISCONNECTED` to automatically engage battery-constrained mode.

## Phase 2: iOS / iPadOS Support
- **Runtime**: Swift wrapper with embedded Python or compiled CoreML / Metal llama.cpp execution backend.
- **Default Profile**: `MEDIUM` (iPhone) or `HIGH` (iPad Pro with M-series silicon).
- **Memory Enforcement**: Integration with `os_proc_available_memory()` to yield model weights before jetsam termination.

## Phase 3: Windows / Linux / macOS Desktop
- **Runtime**: Single-binary PyInstaller / Nuitka distribution bundled with embedded SQLite.
- **Default Profile**: `HIGH` or `DESKTOP`.
- **GPU Acceleration**: Optional pluggable Vulkan / DirectML / Metal backends enabled on hardware detection.

## Phase 4: Future Embedded & IoT Devices
- **Runtime**: Micro-Python or C++ core port targeting Raspberry Pi Zero 2W, RISC-V SBCs, and smart home gateways.
- **Default Profile**: `ULTRA_LOW` (GAM.AI Nano, 512 context tokens, 10 MB cache quota).
