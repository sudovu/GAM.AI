#!/usr/bin/env python3
"""Universal Application Launcher for GAM.AI (Desktop GUI & CLI)."""

import sys
import os
import webbrowser
import threading
import time

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from gam_ai.core.chat.engine import ChatEngine
from gam_ai.ui.web import run_web_server

def main():
    if "--cli" in sys.argv or "-c" in sys.argv:
        from scripts.run_cli import main as cli_main
        cli_main()
        return

    port = 8080
    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)
            break

    print("=" * 64)
    print("           GAM.AI — UNIVERSAL INTELLIGENT ASSISTANT             ")
    print("    Local-First • Multilingual • Network Engineering • Edge AI  ")
    print("=" * 64)
    print(f"[*] Initializing local neural intelligence engine...")
    
    db_path = os.path.join(os.path.expanduser("~"), ".gam_ai", "gam_ai_data.db")
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except Exception:
        db_path = "gam_ai_data.db"

    engine = ChatEngine(db_path)
    url = f"http://127.0.0.1:{port}"
    print(f"[+] Engine ready! Launching web dashboard at: {url}")
    print("[*] Press Ctrl+C in this terminal window to stop the server.\n")

    if "--no-browser" not in sys.argv:
        def open_browser():
            time.sleep(1.0)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        run_web_server(engine, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n[!] GAM.AI stopped successfully. Have a great day!")

if __name__ == "__main__":
    main()
