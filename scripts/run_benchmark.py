#!/usr/bin/env python3
import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "benchmarks"))

from benchmark_resources import run_benchmarks

if __name__ == "__main__":
    run_benchmarks()
