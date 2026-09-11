#!/usr/bin/env python3
"""Model Download Utility for GAM.AI: Fetches recommended ultra-compact GGUF models."""

import sys
import os
import urllib.request
import argparse

MODELS = {
    "nano": {
        "name": "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size_mb": 398,
        "description": "Recommended for ULTRA_LOW & LOW devices (older phones, basic laptops)"
    },
    "micro": {
        "name": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size_mb": 776,
        "description": "Default recommended model for phones and tablets"
    },
    "small": {
        "name": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "size_mb": 1930,
        "description": "High accuracy model for laptops and desktops with 8GB+ RAM"
    }
}

def download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100.0, (downloaded / total_size) * 100.0)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\rDownloading: {percent:.1f}% ({mb_down:.1f} / {mb_total:.1f} MB)")
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="Download compact quantized GGUF models for GAM.AI")
    parser.add_argument("tier", choices=["nano", "micro", "small", "list"], help="Model tier to download")
    parser.add_argument("--dest", default="models", help="Destination folder (default: models/)")
    args = parser.parse_args()

    if args.tier == "list":
        print("Available Recommended GGUF Models for GAM.AI:")
        for tier, meta in MODELS.items():
            print(f"  [{tier.upper()}] {meta['name']} (~{meta['size_mb']} MB) - {meta['description']}")
            print(f"    URL: {meta['url']}")
        return

    meta = MODELS[args.tier]
    dest_dir = os.path.abspath(args.dest)
    os.makedirs(dest_dir, exist_ok=True)
    out_path = os.path.join(dest_dir, meta["name"])

    if os.path.exists(out_path):
        print(f"Model already exists at: {out_path}")
        return

    print(f"Downloading {meta['name']} (~{meta['size_mb']} MB)...")
    print(f"Destination: {out_path}")
    try:
        urllib.request.urlretrieve(meta["url"], out_path, reporthook=download_progress)
        print(f"\nSuccessfully downloaded model to: {out_path}")
        print("GAM.AI will automatically detect and load this model on startup.")
    except Exception as e:
        print(f"\nError downloading model: {e}")
        print(f"You can also download it manually from: {meta['url']}")
        print(f"and place it inside the '{args.dest}/' folder.")

if __name__ == "__main__":
    main()
