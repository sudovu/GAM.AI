# Changelog

## [1.7.1] - 2026-10-30
### Settings, iOS Install & Cross-Platform Version Tracking
- **Phone screen fix**: The assistant reply typewriter reveal no longer stalls in backgrounded Android WebViews. It skips animation when the page is hidden, finishes on `visibilitychange`, and has a watchdog fallback so answers are never left blank.
- **Settings cleanup**: Removed the duplicate `Install App` button from the sidebar and the header overflow menu. Install/download options now live under **Settings → Version & Updates → Downloads & Platforms**.
- **iOS link refresh**: The IPA download and AltStore one-tap install now point to `gam-ai-v1.7.1.ipa` instead of the stale `v1.6.4` build.
- **Version & Updates card**: Settings now shows installed version, build number, release date, platform and a **Check for Updates** button.
- **`version.json` manifest**: Added a shared release manifest served at `/version.json` and published with the web app, so Android, iOS, Windows, PWA and the website all report the same version.
- **Unified release**: Android `versionCode 15` / `versionName 1.7.1`, iOS build `15`, service-worker cache `gam-ai-cache-v1.7.1`.

## [1.7.0] - 2026-10-29
### Responsive & Generative Interface
- **Adaptive Layouts Across Every Screen**:
  - Fluid header with a compact `⋯` overflow menu on phones, so model, mode, language and generative actions always fit without horizontal overflow.
  - Full-screen, safe-area-aware modals on mobile with sticky headers, scrollable bodies and 44 px touch targets.
  - Reworked chat bubbles, avatars, hero, mode switcher, suggestion chips, tables and code blocks for narrow and landscape viewports.
  - Composer now auto-grows, uses 16 px text to prevent iOS focus zoom, and respects the on-screen keyboard via `visualViewport`.
  - Restored pinch-to-zoom accessibility by removing `maximum-scale` / `user-scalable=no`.
- **Generative Chat Experience**:
  - Assistant replies now stream in with a real DOM-level typewriter reveal (markup, code cards and action buttons stay intact).
  - Generative shimmer placeholder replaces the static "Processing..." bubble.
  - New `✨` composer action expands a rough idea into a structured, persona-aware prompt fully offline.
  - New "Generate new ideas" synthesiser produces fresh, shuffled suggestion cards for General, Student, NetEng and Coder modes.
- **Faster First Paint & Repeat Loads**:
  - Three.js is now deferred, so the dashboard paints instantly on low-end phones.
  - The embedded web server gzip-compresses HTML/JS and serves ETag-validated `304` responses.
  - Added missing `/dashboard.html` and `/icons/*` static routes so the PWA manifest icons load correctly.
- **Accessibility**: `prefers-reduced-motion` disables typewriter/shimmer animations, and touch devices no longer get sticky hover transforms.

## [2.5.0] - 2026-09-12
### Multi-Platform Production Release & Multi-Turn Contextual Persistence
- **All-Platform Ready-to-Install Packaging**:
  - **Android (7.0+ Phones, Tablets, TV)**: Universal Release APK (`dist/gam-ai-universal-release.apk`) verified on Google Pixel 7 Pro with native WebBridge, camera lens integration, and hardware acceleration.
  - **Windows (10/11/Server x64)**: Single-file standalone portable binary (`dist/gam-ai.exe`) with embedded UI and zero prerequisite setup.
  - **iOS & iPadOS**: Progressive Web App package (`dist/gam-ai-web-app.zip`) with Safari "Add to Home Screen" support, offline service workers, and touch/tablet gesture optimization.
  - **Linux & macOS**: Full Python packaging via `pyproject.toml` (`pip install .`) and CLI/Desktop run modes.
  - **Automated Master Packaging**: `scripts/package_all_platforms.py` builds and stages deliverables for all platforms.
  - **Multi-Platform CI/CD Pipeline**: GitHub Actions matrix workflow (`build-apk.yml`) building APK, Windows EXE, Linux binary, macOS binary, and Web PWA archive with automatic release asset attachment.
- **Local Conversation Persistence & Context Reasoning**:
  - Multi-turn state tracking (`GAM_CONTEXT`) with non-repeating sequential item delivery ("next", "another one", "one more", "और एक", "अर्को").
  - Rich offline catalogs: 25 English, 12 Hindi, 10 Nepali jokes, 15 riddles, 10 facts, 8 quotes.
  - Referential context grounding ("why?", "explain more", "give an example") inspecting previous conversational turns.
  - Persistent storage across reloads/reboots in `localStorage` and SQLite `conversations`/`messages` tables.
  - 1-tap new chat / clear history button (`🗑️`) with confirmation modal and reset toast.
- **Continuous Context & Token Safety ("Never Runs Out of Tokens")**:
  - `ContextBudgetManager` guarantees prompt ceiling and strictly reserves generation headroom (`safe_max_tokens`), preventing generation starvation.
  - Deterministic sliding-window compaction with `compress_text_to_token_limit` handles massive queries and long pastes safely.
  - Client-side real-time token tracking (`getTotalHistoryTokens`) and auto-compaction in `dashboard.html` with live status indicator.
  - Automated stress unit test `test_never_run_out_of_tokens` verifying massive inputs within micro token budgets.
- **Dedicated Platform Installer Scripts**:
  - `scripts/install_windows.ps1` (automated Windows Desktop shortcut and setup).
  - `scripts/install_macos.sh` (one-command macOS installer).
  - `scripts/host_ios_pwa.py` (local LAN PWA server for iPhone, iPad, and Android tablets).
- **Expanded Test Suite**:
  - 30 unit and acceptance tests covering multi-turn context resolution, token headroom guarantees, and multi-platform packaging.

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
