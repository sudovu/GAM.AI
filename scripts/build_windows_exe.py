#!/usr/bin/env python3
"""Build script for packaging GAM.AI into a single standalone Windows .exe using PyInstaller."""

import subprocess
import sys
import os

def build_exe():
    print("============================================================")
    print("         GAM.AI STANDALONE WINDOWS .EXE BUILDER             ")
    print("============================================================")

    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Run: pip install pyinstaller")
        return

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app_entry = os.path.join(repo_root, "scripts", "run_app.py")
    ui_dir = os.path.join(repo_root, "gam_ai", "ui")
    output_dist = os.path.join(repo_root, "dist")

    add_data_arg = f"{ui_dir};gam_ai/ui" if os.name == 'nt' else f"{ui_dir}:gam_ai/ui"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "gam-ai",
        "--paths", repo_root,
        "--add-data", add_data_arg,
        "--clean",
        app_entry
    ]

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=repo_root)
    if result.returncode == 0:
        print(f"\nBuild Successful! Single-file binary located at: {output_dist}/gam-ai.exe")
    else:
        print(f"\nBuild Failed with exit code {result.returncode}")

if __name__ == "__main__":
    build_exe()
