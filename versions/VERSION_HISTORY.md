# GAM.AI Version Archive & History Ledger

This directory stores historical releases, code snapshots, and compiled Android APKs for immutable future reference. Each release contains:
1. `code_snapshot/` — Exact core source files at release time (`dashboard.html`, python backend, Gradle files, MainActivity).
2. `gam-ai-<version>.apk` — Standalone compiled universal Android APK ready for offline deployment.
3. `CHECKSUMS.sha256` — Cryptographic integrity hashes of every preserved asset.
4. `README.md` — Release notes, technical architectural summary, and change log.

---

## Release Catalog

| Version | Codename / Focus | Status | Key Features | Preserved Artifacts |
| :--- | :--- | :--- | :--- | :--- |
| **`v1.3.0`** | **3-Mode Minimalist Redesign & Seamless Agent Handoff** | **Current** | - Hero: *"Welcome to Local AI Assistant"*<br>- 3 Strict Modes: General Queries (`general`), Students (`student`), Network Mode (`neteng`)<br>- Network query exclusivity: network commands only execute in NetEng Mode<br>- Automatic seamless agent handoff across modes with inline banners<br>- Cleaned chips: zero telecom noise in General Mode, pedagogical math/science in Student Mode | `versions/v1.3.0/`<br>`gam-ai-v1.3.0.apk`<br>`code_snapshot/` |
| **`v1.2.0`** | **Huawei & ZTE GPON OLT/ONT Profiles & Fiber Diagnostics** | Preserved | - SmartAX MA5600T/MA5800 GPON OLT lineprofile/srvprofile resolution<br>- ZTE C300/C320 GPON ONU profile generators<br>- Optical link budget & attenuation calculations<br>- Suppression of Section 7 generic essays for telecom queries | `versions/v1.2.0/`<br>`gam-ai-v1.2.0.apk`<br>`code_snapshot/` |
| **`v1.1.0`** | **Multimodal 3D Studio & Zero-Key Generation** | Preserved | - Zero-key text-to-video, image-to-video, and text-to-image via Pollinations AI<br>- Three.js 3D kinetic canvas visualization<br>- Integrated camera OCR & Google Lens reverse search | `versions/v1.1.0/`<br>`gam-ai-v1.1.0.apk`<br>`code_snapshot/` |
| **`v1.0.0`** | **Universal Baseline Release** | Baseline | - Local Python backend (`server.py`) and PWA dashboard<br>- Android WebView wrapper (`MainActivity.java`)<br>- Multilingual NLP (English, Hindi, Nepali)<br>- Continuous token safety (zero token exhaustion) | `versions/v1.0.0/`<br>`gam-ai-v1.0.0.apk`<br>`code_snapshot/` |

---

## Snapshot Utility Usage
To generate a new version snapshot archive at any point:
```powershell
python scripts/snapshot_version.py <version> "<Title>" "<Detailed Changelog>"
```
Example:
```powershell
python scripts/snapshot_version.py v1.4.0 "Voice Intelligence Enhancement" "Added on-device whisper voice recognition."
```
