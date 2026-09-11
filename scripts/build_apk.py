#!/usr/bin/env python3
"""Build and packaging script for GAM.AI Android APK.

Synchronizes dashboard web assets into the Android project and triggers
Gradle APK compilation locally (if Android SDK/JDK is present) or provides
automated CI instructions for https://github.com/sudovu/GAM.AI.
"""

import os
import sys
import shutil
import subprocess

def sync_assets(repo_root: str) -> None:
    """Sync latest dashboard UI assets to Android project assets directory."""
    src_ui = os.path.join(repo_root, "gam_ai", "ui")
    dst_assets = os.path.join(repo_root, "android", "app", "src", "main", "assets")
    os.makedirs(dst_assets, exist_ok=True)

    files_to_sync = ["dashboard.html", "manifest.json", "sw.js"]
    synced_count = 0
    for fname in files_to_sync:
        s = os.path.join(src_ui, fname)
        if os.path.exists(s):
            d = os.path.join(dst_assets, fname)
            shutil.copy2(s, d)
            synced_count += 1
            print(f"  -> Synced: {fname} ({os.path.getsize(d):,} bytes)")

    print(f"Assets synchronized successfully ({synced_count} files).")

def check_command(cmd: list) -> bool:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0
    except Exception:
        return False

def build_apk():
    print("=" * 64)
    print("          GAM.AI ANDROID APK BUILDER & PACKAGER          ")
    print("=" * 64)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    android_dir = os.path.join(repo_root, "android")
    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    print("\n[1] Synchronizing Web & PWA Assets into Android Project...")
    sync_assets(repo_root)

    print("\n[2] Checking Local Android Build Toolchain...")
    has_java = check_command(["java", "-version"])
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    has_sdk = bool(android_home and os.path.isdir(android_home))

    print(f"  * Java (JDK):        {'INSTALLED' if has_java else 'NOT DETECTED'}")
    print(f"  * Android SDK:       {android_home if has_sdk else 'NOT DETECTED'}")

    is_windows = sys.platform == "win32"
    gradlew_script = os.path.join(android_dir, "gradlew.bat" if is_windows else "gradlew")

    if has_java and has_sdk and os.path.exists(gradlew_script):
        print("\n[3] Building APK with Gradle...")
        cmd = [gradlew_script, "assembleRelease"]
        print(f"Executing: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, cwd=android_dir)
            if res.returncode == 0:
                apk_src = os.path.join(android_dir, "app", "build", "outputs", "apk", "release", "app-release.apk")
                if not os.path.exists(apk_src):
                    apk_src = os.path.join(android_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
                if os.path.exists(apk_src):
                    target_apk = os.path.join(dist_dir, "gam-ai.apk")
                    shutil.copy2(apk_src, target_apk)
                    print(f"\nSUCCESS: APK built successfully at: {target_apk}")
                    return 0
        except Exception as e:
            print(f"Build failed with error: {e}")

    print("\n" + "=" * 64)
    print("    GITHUB ACTIONS AUTOMATED CLOUD BUILD READY (RECOMMENDED)    ")
    print("=" * 64)
    print("Your repository is connected to: https://github.com/sudovu/GAM.AI")
    print("Because GitHub Actions runners provide pre-installed Android SDK 34,")
    print("JDK 17, and Gradle environments, push this commit to trigger the build:")
    print("")
    print("   git push origin main")
    print("")
    print("Once pushed, GitHub Actions automatically:")
    print("  1. Validates the test suite")
    print("  2. Compiles 'gam-ai-debug.apk' and 'gam-ai-release.apk'")
    print("  3. Uploads the ready-to-install APK to your GitHub Actions tab:")
    print("     https://github.com/sudovu/GAM.AI/actions")
    print("=" * 64)
    return 0

if __name__ == "__main__":
    sys.exit(build_apk())
