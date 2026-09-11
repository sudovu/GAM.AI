# GAM.AI System Architecture

## Overview
GAM.AI is designed with the primary engineering objective of **MINIMUM RESOURCE USAGE**.
It operates locally without mandatory cloud accounts, third-party analytics, or persistent background daemons.

---

## Component Details

### 1. DeviceCapabilityManager (`gam_ai/core/resources/capabilities.py`)
At application bootstrap, the capability manager queries the system without external dependencies:
- Detects `/proc/meminfo` (Linux/Android), `GlobalMemoryStatusEx` (Windows), or `sysctl` (macOS/iOS).
- Classifies the host device into one of five execution profiles:
  - `ULTRA_LOW`: < 1.5 GB RAM (Context: 512 tokens, Cache: 10 MB, Model: Nano)
  - `LOW`: 1.5 - 3.5 GB RAM (Context: 1024 tokens, Cache: 25 MB, Model: Micro)
  - `MEDIUM`: 3.5 - 7.5 GB RAM (Context: 2048 tokens, Cache: 50 MB, Model: Micro)
  - `HIGH`: 8 - 15 GB RAM (Context: 4096 tokens, Cache: 100 MB, Model: Small)
  - `DESKTOP`: >= 16 GB RAM (Context: 8192 tokens, Cache: 250 MB, Model: Standard)
- Dynamically downgrades profile if battery is discharging <= 20% or thermal throttling is active.

### 2. Micro Model Manager (`gam_ai/core/models/manager.py`)
- Provides an abstraction over local quantized inference runtimes.
- Implements the strict **Load -> Use -> Unload** memory lifecycle.
- When performing a coding task, GAM.AI unloads the general chatbot model and loads `GAM.AI Code`, ensuring only one model is active in RAM at any time.

### 3. ContextBudgetManager (`gam_ai/core/ai/context_budget.py`)
To prevent context explosion and high compute consumption:
- Calculates prompt token requirements before model invocation.
- Allocates fixed percentages:
  - System Instructions: ~15%
  - User Memory/Preferences: ~20%
  - Retrieved Knowledge/RAG Chunks: ~50%
  - Rolling History: remaining window
- Excess tokens are pruned prior to tokenization.

### 4. SmartCacheManager (`gam_ai/core/cache/smart_cache.py`)
- Temporary storage backed by SQLite and optional in-memory structures.
- Every entry tracks `access_count`, `priority`, `last_accessed`, `expires_at`, and `content_hash`.
- Supports TTL auto-expiry and LRU eviction when reaching the configured `max_cache_mb`.

### 5. SelectiveExtractor & WebResearchEngine (`gam_ai/core/research/`)
- Cache-First Policy: checks cold knowledge, then temporary cache before initiating any web query.
- Atomic Extraction: extracts key claims and relationships, discarding HTML headers, scripts, tracking pixels, and boilerplate.
- Minimal Source Metadata: stores only domain, URL, title, and timestamp.

### 6. KnowledgeManager & RetentionManager (`gam_ai/core/knowledge/`)
- Atomic facts are deduplicated by SHA-256 content hashes.
- Usage tracking in `query_history` monitors query frequency.
- Recurring Query Promotion: If a user asks a question repeatedly (e.g. 3 times), the distilled claim is promoted from Temporary Cache into Cold Storage.
- Under storage pressure (`LOW` or `CRITICAL`), the retention manager wipes non-essential cache and archives low-access knowledge, while never deleting user documents or explicit preferences.

### 7. DocumentProcessor (`gam_ai/core/documents/processor.py`)
- Indexes documents by file reference and hash.
- Chunks text into 150-word passages.
- Does NOT duplicate original files into application storage.
