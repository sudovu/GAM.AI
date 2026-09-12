#!/usr/bin/env python3
"""Master packaging script to generate ready-to-install files for all supported platforms: Android (7.0+), Windows, iOS/iPad, Linux, macOS, and Web PWA."""

import os
import sys
import zipfile
import platform
import subprocess

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dist_dir = os.path.join(repo_root, "dist")
ui_dir = os.path.join(repo_root, "gam_ai", "ui")

def ensure_dist():
    os.makedirs(dist_dir, exist_ok=True)

def package_web_pwa():
    print("\n[1] Packaging Cross-Platform Web & iOS PWA (gam-ai-web-app.zip)...")
    out_zip = os.path.join(dist_dir, "gam-ai-web-app.zip")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(ui_dir):
            for file in files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, ui_dir)
                zf.write(full, arcname=rel)
    print(f"  -> Created: {out_zip} ({os.path.getsize(out_zip):,} bytes)")
    return out_zip

def build_windows_exe():
    if platform.system() != "Windows":
        print("\n[2] Windows .exe build skipped (not on Windows).")
        return None
    print("\n[2] Building Standalone Windows .exe (gam-ai.exe) in dist/...")
    build_script = os.path.join(repo_root, "scripts", "build_windows_exe.py")
    res = subprocess.run([sys.executable, build_script], cwd=repo_root)
    out = os.path.join(dist_dir, "gam-ai.exe")
    if res.returncode == 0 and os.path.exists(out):
        print(f"  -> Windows EXE ready: {out} ({os.path.getsize(out):,} bytes)")
        return out
    return None

def verify_android_apk():
    print("\n[3] Checking Android Release set dist/gam-ai-universal-release.apk...")
    apk = os.path.join(dist_dir, "gam-ai-universal-release.apk")
    if os.path.exists(apk):
        print(f"  -> Android Universal APK ready: {apk} ({os.path.getsize(apk):,} bytes)")
        return apk
    print("  ! APK not yet pre-built in dist/. Run scripts/build_apk.py or gradlew assembleRelease.")
    return None

def main():
    ensure_dist()
    print("=" * 60)
    print("       GAM.AI CROSS-PLATFORM PACKAGING SUITE      ")
    print("=" * 60)

    pwa_zip = package_web_pwa()
    exe = build_windows_exe()
    apk = verify_android_apk()

    print("\n" + "=" * 60)
    print("READY-TO-INSTALL ARTIFACTS:")
    print("=" * 60)
    if apk:
        print(f"-  Android (7.0+ Phones, Tablets, TV): {apk}")
    if exe:
        print(f"-  Windows (10/11/Server x64):         {exe}")
    if pwa_zip:
        print(f"-  iOS / iPadOS / Web PWA:            {pwa_zip}")
    print("-  Linux / macOS / Termux:              pip install . (pyproject.toml)")
    print("=" * 60)

if __name__ == "__main__":
    main()
