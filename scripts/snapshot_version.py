#!/usr/bin/env python3
"""Snapshot and Version Management Utility for GAM.AI.

Archives code snapshots, web assets, and compiled Android APKs into the
`versions/` folder for immutable version history and future reference.
"""

import os
import sys
import shutil
import hashlib
import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERSIONS_DIR = os.path.join(REPO_ROOT, "versions")
HISTORY_FILE = os.path.join(VERSIONS_DIR, "VERSION_HISTORY.md")

SNAPSHOT_FILES = [
    os.path.join("gam_ai", "ui", "dashboard.html"),
    os.path.join("gam_ai", "ui", "manifest.json"),
    os.path.join("gam_ai", "ui", "sw.js"),
    os.path.join("gam_ai", "__init__.py"),
    os.path.join("gam_ai", "server.py"),
    os.path.join("gam_ai", "config.py"),
    os.path.join("android", "app", "build.gradle"),
    os.path.join("android", "app", "src", "main", "AndroidManifest.xml"),
    os.path.join("android", "app", "src", "main", "java", "com", "gamai", "app", "MainActivity.java"),
    os.path.join("scripts", "build_apk.py"),
    os.path.join("scripts", "run_tests.py"),
]

def sha256_file(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def create_snapshot(version: str, title: str, description: str, apk_source: str = None) -> str:
    """Create a new version archive with code snapshot and APK."""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    v_dir = os.path.join(VERSIONS_DIR, version)
    code_dir = os.path.join(v_dir, "code_snapshot")
    os.makedirs(code_dir, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    checksums = []

    # 1. Copy source files
    copied_count = 0
    for rel_path in SNAPSHOT_FILES:
        src = os.path.join(REPO_ROOT, rel_path)
        if os.path.exists(src):
            dst = os.path.join(code_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied_count += 1
            f_hash = sha256_file(dst)
            checksums.append(f"{f_hash}  code_snapshot/{rel_path.replace(os.sep, '/')}")

    # 2. Copy APK if provided or found
    apk_name = f"gam-ai-{version}.apk"
    target_apk = os.path.join(v_dir, apk_name)
    if apk_source and os.path.exists(apk_source):
        shutil.copy2(apk_source, target_apk)
        apk_hash = sha256_file(target_apk)
        apk_size = os.path.getsize(target_apk)
        checksums.append(f"{apk_hash}  {apk_name}")
    else:
        # Check default locations
        candidate_apks = [
            os.path.join(REPO_ROOT, "dist", "gam-ai-universal-release.apk"),
            os.path.join(REPO_ROOT, "dist", "gam-ai-universal-debug.apk"),
            os.path.join(REPO_ROOT, "dist", "gam-ai.apk"),
            os.path.join(REPO_ROOT, "android", "app", "build", "outputs", "apk", "release", "app-release.apk"),
            os.path.join(REPO_ROOT, "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
        ]
        for c in candidate_apks:
            if os.path.exists(c):
                shutil.copy2(c, target_apk)
                apk_hash = sha256_file(target_apk)
                apk_size = os.path.getsize(target_apk)
                checksums.append(f"{apk_hash}  {apk_name}")
                break
        else:
            apk_hash = "N/A (pending build)"
            apk_size = 0

    # 3. Write CHECKSUMS.sha256
    with open(os.path.join(v_dir, "CHECKSUMS.sha256"), "w", encoding="utf-8") as f:
        f.write("\n".join(checksums) + "\n")

    # 4. Write README.md for version
    readme_content = f"""# GAM.AI Release {version}: {title}

- **Release Date:** {timestamp}
- **Version Tag:** `{version}`
- **Compiled APK:** `{apk_name}` ({apk_size:,} bytes)
- **APK SHA-256:** `{apk_hash}`

## Summary
{description}

## Preserved Files
- Source code snapshot: `code_snapshot/` ({copied_count} key files)
- Checksum ledger: `CHECKSUMS.sha256`
"""
    with open(os.path.join(v_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Snapshot {version} successfully created at: {v_dir}")
    return v_dir

if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "v1.3.0"
    title = sys.argv[2] if len(sys.argv) > 2 else "3-Mode Minimalist Redesign & Seamless Agent Handoff"
    desc = sys.argv[3] if len(sys.argv) > 3 else "Minimalist UI with Welcome to Local AI Assistant, 3 distinct modes (General Queries, Students, Network Mode) with automatic seamless agent handoff and network exclusivity."
    create_snapshot(ver, title, desc)
