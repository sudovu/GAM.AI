#!/usr/bin/env python3
"""Runner script for GAM.AI Web Dashboard & REST API."""
import sys
import os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from gam_ai.core.chat.engine import ChatEngine
from gam_ai.ui.web import run_web_server

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    engine = ChatEngine("gam_ai_data.db")
    run_web_server(engine, host="0.0.0.0", port=port)
