#!/usr/bin/env python3
"""Model Download Utility for GAM.AI: Fetches modular specialized GGUF models."""

import sys
import os
import urllib.request
import argparse

MODELS = {
    "nano": {
        "name": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size_mb": 398,
        "description": "GAM.AI Nano: 0.5B ultra-compact general model for < 1GB RAM devices"
    },
    "micro": {
        "name": "llama-3.2-1b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size_mb": 776,
        "description": "GAM.AI Micro: 1.5B balanced everyday conversational model"
    },
    "coder": {
        "name": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "size_mb": 920,
        "description": "GAM.AI Coder: Specialized in Python, Bash, network automation, and system scripts"
    },
    "descriptive": {
        "name": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "size_mb": 1930,
        "description": "GAM.AI Descriptive: 3.0B deep technical documentation and architectural analysis"
    },
    "picture": {
        "name": "gam-ai-diagram-v1.gguf",
        "url": "https://huggingface.co/gam-ai/models/resolve/main/diagram-generator.gguf",
        "size_mb": 650,
        "description": "GAM.AI Picture & Diagram: Network topology visualizer and ASCII/Mermaid layouts"
    },
    "neteng": {
        "name": "neteng-cisco-huawei-olt.gguf",
        "url": "https://huggingface.co/gam-ai/models/resolve/main/neteng.gguf",
        "size_mb": 850,
        "description": "GAM.AI NetEng: Cisco IOS, Huawei VRP, GPON OLT, and FortiGate configuration expert"
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
    parser = argparse.ArgumentParser(description="Download modular quantized models for GAM.AI")
    parser.add_argument("tier", choices=["nano", "micro", "coder", "descriptive", "picture", "neteng", "list"], help="Model to download")
    parser.add_argument("--dest", default="models", help="Destination folder (default: models/)")
    args = parser.parse_args()

    if args.tier == "list":
        print("Available Modular Models in GAM.AI Catalog:")
        for tier, meta in MODELS.items():
            print(f"  [{tier.upper()}] {meta['name']} (~{meta['size_mb']} MB) - {meta['description']}")
            print(f"    Direct URL: {meta['url']}\n")
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
        print(f"\nSuccessfully downloaded {meta['name']} to: {out_path}")
        print("GAM.AI will automatically detect and load this model on startup or via /switch.")
    except Exception as e:
        print(f"\nDownload note: {e}")
        print(f"You can also download the file manually from: {meta['url']}")
        print(f"and drop it directly into your '{args.dest}/' folder.")

if __name__ == "__main__":
    main()
