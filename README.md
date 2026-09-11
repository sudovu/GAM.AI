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

## 4. Quickstart

### Running Tests
Execute the comprehensive test suite (13 unit and acceptance tests covering offline operation, cache reuse, cleanup, promotion, storage pressure, and RAM limits):
```bash
python3 scripts/run_tests.py
```

### Running Profiling Benchmarks
```bash
python3 scripts/run_benchmark.py
```

### Starting the Interactive CLI
```bash
python3 scripts/run_cli.py
```

---

## 5. Built-in Slash Commands

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

## 6. License
MIT License. See [LICENSE](LICENSE) for details.
