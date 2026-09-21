#!/usr/bin/env python3
"""Build and packaging script for GAM.AI Android APK.

Synchronizes dashboard web assets into the Android project, compiles
universal APKs locally via Gradle (auto-detecting local JDK & Android SDK),
and optionally deploys directly to connected Android devices (e.g. Google Pixel)
via USB debugging (`adb install`).
"""

import os
import sys
import shutil
import subprocess

def detect_toolchain():
    """Auto-detect JDK and Android SDK on system if environment variables are not set."""
    user_home = os.path.expanduser("~")

    # 1. Detect JAVA_HOME
    if not os.environ.get("JAVA_HOME"):
        candidates = [
            os.path.join(user_home, ".jdks", "jbr-21.0.11"),
            r"C:\Program Files\Android\Android Studio\jbr",
            r"C:\Program Files\Java\jdk-21",
            r"C:\Program Files\Java\jdk-17",
        ]
        for c in candidates:
            if os.path.isdir(c) and os.path.exists(os.path.join(c, "bin", "java.exe" if sys.platform == "win32" else "java")):
                os.environ["JAVA_HOME"] = c
                bin_dir = os.path.join(c, "bin")
                if bin_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                break

    # 2. Detect ANDROID_HOME
    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
        sdk_candidates = [
            os.path.join(user_home, "AppData", "Local", "Android", "Sdk"),
            os.path.join(user_home, "Android", "Sdk"),
            r"C:\Android\sdk",
        ]
        for s in sdk_candidates:
            if os.path.isdir(s):
                os.environ["ANDROID_HOME"] = s
                os.environ["ANDROID_SDK_ROOT"] = s
                platform_tools = os.path.join(s, "platform-tools")
                if os.path.isdir(platform_tools) and platform_tools not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = platform_tools + os.pathsep + os.environ.get("PATH", "")
                break

def ensure_local_properties(repo_root: str):
    """Ensure android/local.properties points to valid Android SDK."""
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        loc_prop = os.path.join(repo_root, "android", "local.properties")
        clean_sdk_path = android_home.replace("\\", "/")
        with open(loc_prop, "w", encoding="utf-8") as f:
            f.write(f"sdk.dir={clean_sdk_path}\n")

def sync_assets(repo_root: str) -> None:
    """Sync latest dashboard UI assets to Android project assets directory."""
    src_ui = os.path.join(repo_root, "gam_ai", "ui")
    dst_assets = os.path.join(repo_root, "android", "app", "src", "main", "assets")
    os.makedirs(dst_assets, exist_ok=True)

    files_to_sync = ["dashboard.html", "manifest.json", "sw.js", "developer.jpg", "three.min.js"]
    synced_count = 0
    for fname in files_to_sync:
        s = os.path.join(src_ui, fname)
        if os.path.exists(s):
            d = os.path.join(dst_assets, fname)
            shutil.copy2(s, d)
            synced_count += 1
            print(f"  -> Synced: {fname} ({os.path.getsize(d):,} bytes)")

    print(f"Assets synchronized successfully ({synced_count} files).")

def ensure_gradle_wrapper(repo_root: str) -> None:
    """Ensure gradle-wrapper.jar exists; download if missing."""
    wrapper_jar = os.path.join(repo_root, "android", "gradle", "wrapper", "gradle-wrapper.jar")
    if not os.path.exists(wrapper_jar):
        print("  * gradle-wrapper.jar not found; fetching official Gradle 8.5 wrapper...")
        import urllib.request
        os.makedirs(os.path.dirname(wrapper_jar), exist_ok=True)
        url = "https://raw.githubusercontent.com/gradle/gradle/v8.5.0/gradle/wrapper/gradle-wrapper.jar"
        try:
            urllib.request.urlretrieve(url, wrapper_jar)
            print(f"  * Downloaded gradle-wrapper.jar ({os.path.getsize(wrapper_jar):,} bytes)")
        except Exception as e:
            print(f"  * Warning: Could not download gradle-wrapper.jar: {e}")
    else:
        print("  * gradle-wrapper.jar verified.")

def check_command(cmd: list) -> bool:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0
    except Exception:
        return False

def get_adb_command():
    adb_name = "adb.exe" if sys.platform == "win32" else "adb"
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        pt_adb = os.path.join(android_home, "platform-tools", adb_name)
        if os.path.exists(pt_adb):
            return pt_adb
    if check_command([adb_name, "version"]):
        return adb_name
    return None

def install_via_adb(apk_path: str):
    adb = get_adb_command()
    if not adb:
        print("ADB not found. Cannot perform USB debugging install.")
        return False

    print("\n[USB Debugging] Checking connected Android devices...")
    try:
        res = subprocess.run([adb, "devices", "-l"], stdout=subprocess.PIPE, text=True)
        print(res.stdout.strip())
        lines = [line for line in res.stdout.splitlines() if line.strip() and not line.startswith("List of")]
        connected = [line.split()[0] for line in lines if "device" in line.split()]
        if not connected:
            print("No device authorized for USB debugging. Connect phone and enable USB Debugging.")
            return False

        target_device = connected[0]
        print(f"\n[USB Debugging] Setting up ADB port forwarding (reverse tcp:8080 -> tcp:8080)...")
        subprocess.run([adb, "-s", target_device, "reverse", "tcp:8080", "tcp:8080"])
        install_res = subprocess.run([adb, "-s", target_device, "install", "-r", "-d", "-g", apk_path])
        if install_res.returncode != 0:
            print("\n[USB Debugging] Existing signature mismatch detected. Performing clean reinstall...")
            subprocess.run([adb, "-s", target_device, "uninstall", "com.gamai.app"])
            install_res = subprocess.run([adb, "-s", target_device, "install", "-r", "-d", "-g", apk_path])

        if install_res.returncode == 0:
            print("\nSUCCESS: GAM.AI successfully deployed to device via USB debugging!")
            print("[USB Debugging] Launching GAM.AI application...")
            subprocess.run([adb, "-s", target_device, "shell", "am", "start", "-n", "com.gamai.app/.MainActivity"])
            return True
        else:
            print(f"Failed to install APK. adb exit code: {install_res.returncode}")
            return False
    except Exception as e:
        print(f"Error during ADB install: {e}")
        return False

def build_apk():
    print("=" * 66)
    print("      GAM.AI ANDROID UNIVERSAL APK BUILDER & USB DEPLOYER         ")
    print("=" * 66)

    detect_toolchain()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    android_dir = os.path.join(repo_root, "android")
    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    ensure_local_properties(repo_root)

    print("\n[1] Synchronizing Web & PWA Assets into Android Project...")
    sync_assets(repo_root)
    ensure_gradle_wrapper(repo_root)

    print("\n[2] Verifying Android Toolchain...")
    java_home = os.environ.get("JAVA_HOME")
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    print(f"  * JAVA_HOME:         {java_home if java_home else 'NOT SET'}")
    print(f"  * ANDROID_HOME:      {android_home if android_home else 'NOT SET'}")

    is_windows = sys.platform == "win32"
    gradlew_script = os.path.join(android_dir, "gradlew.bat" if is_windows else "gradlew")

    if java_home and android_home and os.path.exists(gradlew_script):
        build_task = "assembleDebug" if "--debug" in sys.argv else "assembleRelease"
        print(f"\n[3] Building Signed Universal Android APK with Gradle ({build_task}, Android 7+ API 24-34)...")
        cmd = [gradlew_script, build_task, "--stacktrace"]
        print(f"Executing: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, cwd=android_dir)
            if res.returncode == 0:
                if build_task == "assembleRelease":
                    apk_src = os.path.join(android_dir, "app", "build", "outputs", "apk", "release", "app-release.apk")
                    apk_dest_name = "gam-ai-universal-release.apk"
                else:
                    apk_src = os.path.join(android_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
                    apk_dest_name = "gam-ai-universal-debug.apk"

                if not os.path.exists(apk_src):
                    # Fallback check
                    for candidate in [
                        os.path.join(android_dir, "app", "build", "outputs", "apk", "release", "app-release.apk"),
                        os.path.join(android_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
                    ]:
                        if os.path.exists(candidate):
                            apk_src = candidate
                            break

                if os.path.exists(apk_src):
                    target_apk = os.path.join(dist_dir, apk_dest_name)
                    shutil.copy2(apk_src, target_apk)
                    shutil.copy2(apk_src, os.path.join(dist_dir, "gam-ai.apk"))
                    print(f"\nBUILD SUCCESSFUL! Signed Universal APK located at:\n  -> {target_apk} ({os.path.getsize(target_apk):,} bytes)")

                    # Auto archive snapshot into versions/ directory
                    try:
                        sys.path.insert(0, os.path.dirname(__file__))
                        from snapshot_version import create_snapshot
                        create_snapshot("v1.4.0", "Online vs Offline Distinction, Auto-Switch & Live Refresh",
                                        "Automated build snapshot with online/offline mode distinction, auto-switching, live refresh, and lens accuracy.", target_apk)
                    except Exception as snap_err:
                        print(f"  * Snapshot archiving note: {snap_err}")

                    # Auto deploy if requested or if USB device is attached
                    should_install = "--install" in sys.argv or "-i" in sys.argv
                    if should_install:
                        install_via_adb(target_apk)
                    else:
                        adb = get_adb_command()
                        if adb:
                            try:
                                d_out = subprocess.check_output([adb, "devices"], text=True)
                                if "device" in [line.split()[-1] for line in d_out.splitlines() if line.strip() and not line.startswith("List")]:
                                    print("\n[USB Debugging] Connected device detected! Installing directly...")
                                    install_via_adb(target_apk)
                            except Exception:
                                pass
                    return 0
        except Exception as e:
            print(f"Build failed with error: {e}")

    print("\n" + "=" * 66)
    print("    GITHUB ACTIONS CLOUD BUILD READY (CI/CD)                    ")
    print("=" * 66)
    print("You can also push to GitHub to generate the APK via Actions:")
    print("   git push origin main")
    print("=" * 66)
    return 0

if __name__ == "__main__":
    sys.exit(build_apk())
