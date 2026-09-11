#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# GAM.AI Android Termux Automated Setup Script
# Configures ultra-low resource profile with CPU optimizations
# ============================================================

set -e

echo "=== Updating Termux Packages ==="
pkg update -y && pkg upgrade -y
pkg install -y python git clang libopenblas

echo "=== Setting up GAM.AI Environment ==="
export GAM_AI_PROFILE="LOW"
python -m pip install --upgrade pip

echo "=== Verifying GAM.AI Test Suite on Android ==="
python scripts/run_tests.py

echo "=== Launching GAM.AI Assistant ==="
python scripts/run_cli.py
