"""Zero-Dependency Embedded Web Server & REST API with Live Model Downloader & PWA."""

import http.server
import json
import urllib.parse
import urllib.request
import os
import threading
import time
from typing import Optional, Any, Dict
from gam_ai.core.chat.engine import ChatEngine
from gam_ai.core.network.subnet import SubnetCalculator
from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
from gam_ai.core.models.manager import MODULAR_CATALOG

_HTML_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")

DOWNLOAD_STATUS: Dict[str, Dict[str, Any]] = {}

def _download_worker(model_id: str, url: str, dest_path: str, size_mb: int):
    DOWNLOAD_STATUS[model_id] = {
        "status": "downloading",
        "percent": 0.0,
        "downloaded_mb": 0.0,
        "total_mb": size_mb,
        "error": None
    }

    def _hook(blocks, block_size, total_size):
        bytes_down = blocks * block_size
        tot = total_size if total_size > 0 else (size_mb * 1024 * 1024)
        pct = min(100.0, round((bytes_down / tot) * 100.0, 1))
        DOWNLOAD_STATUS[model_id]["percent"] = pct
        DOWNLOAD_STATUS[model_id]["downloaded_mb"] = round(bytes_down / (1024 * 1024), 1)

    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        urllib.request.urlretrieve(url, dest_path, reporthook=_hook)
        DOWNLOAD_STATUS[model_id]["status"] = "completed"
        DOWNLOAD_STATUS[model_id]["percent"] = 100.0
    except Exception as e:
        DOWNLOAD_STATUS[model_id]["status"] = "error"
        DOWNLOAD_STATUS[model_id]["error"] = str(e)


class GAMAIWebHandler(http.server.BaseHTTPRequestHandler):
    engine: Optional[ChatEngine] = None

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            try:
                with open(_HTML_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                content = "<h1>GAM.AI Universal Dashboard</h1>"

            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/manifest.json":
            manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
            body = b'{"name":"GAM.AI","short_name":"GAM.AI","start_url":"/","display":"standalone"}'
            if os.path.exists(manifest_path):
                with open(manifest_path, "rb") as f:
                    body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/sw.js":
            sw_path = os.path.join(os.path.dirname(__file__), "sw.js")
            body = b'// GAM.AI Service Worker'
            if os.path.exists(sw_path):
                with open(sw_path, "rb") as f:
                    body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/api/status":
            act = self.engine.models.get_active_model()
            m_name = act.get_info().name if act else self.engine.config.default_model_tier
            c_stats = self.engine.cache.get_stats()
            k_stats = self.engine.knowledge.get_stats()
            self._send_json({
                "active_model": m_name,
                "ram_mb": self.engine.models.get_ram_usage_mb(),
                "cache_entries": c_stats["total_entries"],
                "cache_kb": c_stats["total_size_kb"],
                "knowledge_items": k_stats["total_items"]
            })

        elif parsed.path in ("/api/model/catalog", "/api/models/catalog"):
            catalog = self.engine.models.get_catalog_with_status()
            self._send_json(catalog)

        elif parsed.path.startswith("/api/models/download_status") or parsed.path.startswith("/api/model/download_status"):
            query_params = urllib.parse.parse_qs(parsed.query)
            model_id = query_params.get("model_id", ["nano"])[0]
            st = DOWNLOAD_STATUS.get(model_id, {
                "status": "idle",
                "percent": 0.0,
                "downloaded_mb": 0.0,
                "total_mb": 0.0
            })
            self._send_json(st)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            req_data = json.loads(raw_body)
        except Exception:
            req_data = {}

        if self.path == "/api/chat":
            query = req_data.get("query") or req_data.get("message") or req_data.get("prompt") or ""
            result = self.engine.process_query(query)
            self._send_json(result)

        elif self.path in ("/api/model/switch", "/api/models/switch"):
            model_id = req_data.get("model", "nano")
            self.engine.models.load_model(model_id)
            self._send_json({"status": "switched", "active": model_id})

        elif self.path in ("/api/model/download", "/api/models/download"):
            model_id = req_data.get("model_id", "nano")
            meta = MODULAR_CATALOG.get(model_id)
            if meta:
                dest = os.path.join(self.engine.models.models_dir, meta["filename"])
                t = threading.Thread(
                    target=_download_worker,
                    args=(model_id, meta["url"], dest, meta["download_size_mb"]),
                    daemon=True
                )
                t.start()
                self._send_json({"status": "started", "model_id": model_id})
            else:
                self._send_json({"status": "error", "message": "Unknown model"}, 400)

        elif self.path == "/api/network/subnet":
            cidr = req_data.get("cidr", "192.168.1.0/24")
            result = SubnetCalculator.calculate(cidr)
            self._send_json(result)

        elif self.path == "/api/network/config":
            vendor = req_data.get("vendor", "cisco")
            if vendor == "cisco":
                cfg = MultiVendorConfigGenerator.cisco_ospf(1, "1.1.1.1", "0", "192.168.1.0", "0.0.0.255")
            elif vendor == "huawei":
                cfg = MultiVendorConfigGenerator.huawei_trunk_port("GigabitEthernet0/0/1", "10 20 30")
            elif vendor == "olt":
                cfg = MultiVendorConfigGenerator.huawei_olt_gpon_service("0/1/0", 1, "4857544312345678", 100)
            elif vendor == "fortigate":
                cfg = MultiVendorConfigGenerator.fortigate_policy(1, "LAN_to_WAN", "port2", "port1")
            elif vendor == "mikrotik":
                cfg = MultiVendorConfigGenerator.mikrotik_basic_setup()
            else:
                cfg = "# Unknown vendor template"
            self._send_json({"vendor": vendor, "config": cfg})

        elif self.path in ("/api/model/unload", "/api/models/unload"):
            self.engine.models.unload_active_model()
            self._send_json({"status": "unloaded"})

        else:
            self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        pass

def run_web_server(engine: ChatEngine, host: str = "127.0.0.1", port: int = 8080):
    GAMAIWebHandler.engine = engine
    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer((host, port), GAMAIWebHandler)
    print(f"GAM.AI Universal Dashboard running at: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        server.server_close()
