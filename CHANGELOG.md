# Changelog

## [1.0.0] - 2026-09-11
### Initial Production Release
- **Three-Level Storage Engine**:
  - Hot Data (Active RAM context + rolling short-term buffer)
  - Temporary Cache (SmartCacheManager with TTL, LRU eviction, and size enforcement)
  - Cold Data (SQLite-backed permanent knowledge and atomic claims)
- **Dynamic Hardware Adaptation**:
  - `DeviceCapabilityManager` supporting `ULTRA_LOW`, `LOW`, `MEDIUM`, `HIGH`, and `DESKTOP` profiles.
  - Battery, thermal, and storage pressure monitors.
- **Micro Model Strategy**:
  - Pluggable `ModelManager` with `GAM.AI Nano`, `Micro`, `Small`, `Standard`, and `Code`.
  - Strict Load -> Use -> Unload memory reclamation.
- **Selective Web Research**:
  - Cache-first research engine with atomic claim extraction and 99.9% storage reduction.
  - Frequency tracking and automatic knowledge promotion from cache to cold storage.
- **Local RAG & Reference Document Processing**:
  - Reference-only document indexing without duplicating source files.
  - Sub-millisecond TF-IDF / compact vector semantic search.
- **Command & Security Infrastructure**:
  - Slash commands (`/status`, `/search`, `/research`, `/knowledge`, `/forget`, `/clear-cache`, `/offline`, `/online`, `/compact`).
  - SSRF protection and path traversal guards.
- **Comprehensive Test & Profiling Suite**:
  - 13 acceptance and unit tests covering all operational constraints.
  - Automated profiling benchmarks measuring latency, RAM, and storage savings.
