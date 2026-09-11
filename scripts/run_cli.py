#!/usr/bin/env python3
import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, repo_root)

from gam_ai.ui.cli import CommandLineInterface

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else ":memory:"
    cli = CommandLineInterface(db_path=db)
    cli.run()
