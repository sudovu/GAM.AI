#!/usr/bin/env python3
"""Local LAN Server for iOS / iPadOS / Android PWA Installation and Browser Testing."""

import http.server
import socketserver
import socket
import os
import sys

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def run_pwa_server(port=8080):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ui_dir = os.path.join(repo_root, "gam_ai", "ui")
    os.chdir(ui_dir)

    lan_ip = get_lan_ip()
    url = f"http://{lan_ip}:{port}/dashboard.html"

    print("=" * 65)
    print("      GAM.AI iOS / iPadOS / Android PWA LOCAL HOST SERVER        ")
    print("=" * 65)
    print(f"\nLocal Access:    http://localhost:{port}/dashboard.html")
    print(f"LAN Device URL:  {url}\n")
    print("HOW TO INSTALL ON iPhone / iPad / Tablets:")
    print("  1. Connect your iPhone or iPad to the same Wi-Fi network.")
    print(f"  2. Open Safari on iOS and navigate to: {url}")
    print("  3. Tap the 'Share' button (square with arrow pointing up).")
    print("  4. Scroll down and tap 'Add to Home Screen'.")
    print("  5. GAM.AI will install as a full standalone app with offline support!")
    print("=" * 65)
    print("Serving from:", ui_dir)
    print("Press Ctrl+C to stop the server.\n")

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_pwa_server(port)
