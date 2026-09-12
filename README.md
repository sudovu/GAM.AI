# GAM.AI — Micro, Local-First, Resource-Efficient AI Assistant

> **Core Philosophy**: *"Keep the minimum data required to produce the maximum useful result."*

**GAM.AI** is a micro, offline-capable, local-first artificial intelligence assistant engineered from the ground up for minimal resource usage across RAM, CPU, GPU, storage, battery, and network bandwidth. Unlike conventional AI systems that hoard conversational history, web pages, and vector databases, GAM.AI uses a strict **Three-Level Storage Hierarchy** that retains only actionable, verified knowledge while auto-expiring temporary research.

---

## 1. Three-Level Storage Hierarchy

```text
                  GAM.AI
                    │
             ┌──────┴──────┐
             │             │
          HOT DATA      COLD DATA
             │             │
             ↓             ↓
           RAM          SQLite
      (Current task) (Permanent knowledge)
             │             │
             └──────┬──────┘
                    │
                 CACHE
                    │
             Temporary research
                    │
               Auto-delete
```

1. **Hot Data (RAM)**:
   - Contains only the active context of the current conversational turn and an in-memory rolling window of recent messages.
   - Cleared immediately upon completion of the inference task to guarantee near-zero idle memory.
2. **Temporary Cache (SmartCache)**:
   - Stores distilled research, query answers, and transient web extracts with explicit Time-To-Live (TTL), LRU eviction, and size quotas.
   - Self-cleaning: Expired items and low-priority cache entries are automatically purged.
3. **Cold Data (SQLite Permanent Knowledge)**:
   - Stores strictly verified atomic claims, explicit user preferences, and file references (never raw duplicate documents).
   - Knowledge Promotion: If a user asks about a cached topic repeatedly (frequency threshold reached), GAM.AI automatically promotes and compresses the claim into permanent Cold Storage.

---

## 2. Key Architecture Components

- **`DeviceCapabilityManager`**: Detects OS, CPU cores, RAM, storage, battery level, and thermal state at startup. Automatically selects hardware profiles (`ULTRA_LOW`, `LOW`, `MEDIUM`, `HIGH`, `DESKTOP`).
- **`ModelManager` & Micro Model Strategy**:
  - Dynamically switches models (`GAM.AI Nano`, `GAM.AI Micro`, `GAM.AI Small`, `GAM.AI Standard`, `GAM.AI Code`).
  - Strict **Load -> Use -> Unload** lifecycle ensuring models are evicted from RAM when not in use.
- **`SmartCacheManager`**: Enforces strict TTL, LRU eviction, and priority ordering.
- **`SelectiveExtractor` & `WebResearchEngine`**: When online, extracts only atomic claims, confidence scores, and minimal source metadata (URL, domain, title). Discards 99.9% of raw web bloat.
- **`RetentionManager`**: Governs data lifecycle (`KEEP`, `COMPRESS`, `CACHE`, `ARCHIVE`, `DELETE`) and applies aggressive eviction under storage pressure (`NORMAL`, `LOW`, `CRITICAL`).
- **`ContextBudgetManager`**: Enforces strict token allocations for system instructions, memory, knowledge, and recent history.
- **`SecurityGuard`**: Enforces path traversal protection, SSRF prevention against private networks/cloud metadata endpoints, and zero hidden telemetry.

---

## 3. Performance & Profiling Benchmarks

Benchmarked on Linux x86_64:

| Metric | Measured Value | Architectural Benefit |
| :--- | :--- | :--- |
| **Cold Startup Time** | **31.6 ms** | Instant availability on low-end hardware |
| **Idle RAM (RSS)** | **46.8 MB** | Minimal background footprint |
| **Fresh Research Latency** | **3.8 ms** | Fast atomic extraction pipeline |
| **Cached Query Latency** | **1.2 ms** | **3.1x faster** response via SmartCache reuse |
| **Database Disk Footprint** | **4.0 KB** | Portable, embedded SQLite |
| **Distilled Knowledge** | **185 bytes** | **99.93% storage saved** vs. storing raw HTML |
| **RAG Retrieval Lookup** | **0.69 ms** | Sub-millisecond compact semantic search |
| **Model Unloading** | **0 MB active RAM** | Full memory reclamation after idle |

---

## 4. Cross-Platform Downloads & Installation

GAM.AI is packaged with dedicated, ready-to-install executables and packages for all major platforms:

| Platform | Target Form Factor | Deliverable / Package | Installation / Quickstart |
| :--- | :--- | :--- | :--- |
| **Android** | Android 7.0+ (Phones, Tablets, Foldables, TV) | [`gam-ai-universal-release.apk`](dist/gam-ai-universal-release.apk) | Direct install: `adb install -r dist/gam-ai-universal-release.apk` or tap APK on device. |
| **Android (Termux)** | CLI & Developer Mode | [`scripts/setup_android_termux.sh`](scripts/setup_android_termux.sh) | In Termux: `bash scripts/setup_android_termux.sh` |
| **Windows** | Windows 10, 11, Server x64 | [`gam-ai.exe`](dist/gam-ai.exe) / [`scripts/install_windows.ps1`](scripts/install_windows.ps1) | Run `powershell -ExecutionPolicy Bypass scripts/install_windows.ps1` to create Desktop shortcut or launch `dist/gam-ai.exe`. |
| **macOS** | Mac (Intel & Apple Silicon M1/M2/M3/M4) | [`scripts/install_macos.sh`](scripts/install_macos.sh) | In Terminal: `bash scripts/install_macos.sh` (sets up virtualenv, pip package, and launcher). |
| **iOS / iPadOS / Tablets** | iPhone, iPad, Safari Mobile | [`dist/gam-ai-web-app.zip`](dist/gam-ai-web-app.zip) / [`scripts/host_ios_pwa.py`](scripts/host_ios_pwa.py) | Run `python scripts/host_ios_pwa.py`, open Safari on iOS, tap **Share** -> **"Add to Home Screen"** for full standalone PWA. |
| **Linux / Server** | Desktop & Headless Servers | Standard Python Package | `pip install .` (via `pyproject.toml`) or `python3 scripts/run_app.py` |
| **Cross-Platform PWA** | Chrome, Edge, Safari, Firefox | Hosted Web Dashboard | Works offline with Service Worker caching and local SQLite/IndexedDB persistence. |

---

## 5. Continuous Context & Token Safety ("Never Runs Out of Tokens")

GAM.AI is architected with a strict **Never Run Out of Tokens** engine that guarantees the model and client interface never crash, reject requests, or truncate mid-sentence due to context saturation:

1. **Guaranteed Output Headroom Reservation**:
   - The engine automatically reserves 20%–25% of the total context window exclusively for model completion (`safe_max_tokens`), ensuring generations are never starved.
2. **Deterministic Sliding-Window Query Compaction**:
   - If a user pastes large logs, codebases, or documents, `ContextBudgetManager` automatically preserves the leading intent and trailing constraints with an informative compaction marker (`[...compacted X words for token safety...]`), preventing prompt overflow.
3. **Infinite Multi-Turn Rolling History**:
   - When conversations grow beyond token thresholds, earlier turns are automatically consolidated into an atomic context digest while keeping recent turns intact.
4. **Client-Side Token Meter**:
   - `dashboard.html` dynamically calculates token usage in real time, auto-compacts local storage, and displays a live status indicator (`● Safe Tokens`) so conversations can run indefinitely.

---

## 6. Quickstart

### Packaging All Platforms in 1 Step
```bash
python scripts/package_all_platforms.py
```

### Running Tests
Execute the full 30-test acceptance and unit suite:
```bash
python scripts/run_tests.py
```

### Running Profiling Benchmarks
```bash
python scripts/run_benchmark.py
```

### Starting the Standalone App
```bash
python scripts/run_app.py
```

### Starting the Interactive CLI
```bash
python scripts/run_cli.py
```

---

## 7. Built-in Slash Commands

| Command | Action |
| :--- | :--- |
| `/status` | Displays resource dashboard (profile, RAM, cache, storage, mode). |
| `/search <query>` | Explicit web search with atomic fact extraction. |
| `/research <topic>` | Technical deep research into cache. |
| `/knowledge [topic]` | Inspect permanent verified knowledge items. |
| `/clear-cache` | Purges all temporary cache while preserving permanent knowledge. |
| `/forget <target>` | Selectively forgets a topic, memory key, or conversation. |
| `/offline` | Forces strictly offline local execution. |
| `/online` | Enables web research capabilities. |
| `/compact` | Triggers database vacuum and expired retention cleanup. |
| `/help` | Shows available command options. |

---

## 8. License
MIT License. See [LICENSE](LICENSE) for details.
