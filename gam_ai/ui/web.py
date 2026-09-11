"""Zero-Dependency Embedded Web Server & REST API for GAM.AI Dashboard."""
import http.server
import json
import urllib.parse
from typing import Optional, Any
from gam_ai.core.chat.engine import ChatEngine
from gam_ai.core.network.subnet import SubnetCalculator
from gam_ai.core.network.multivendor import MultiVendorConfigGenerator

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GAM.AI — Micro Local-First AI</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --text-dim: #94a3b8;
    --accent: #38bdf8; --accent-hover: #0284c7; --border: #334155; --green: #22c55e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
  #sidebar { width: 320px; background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 20px; }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  h1 { font-size: 1.25rem; font-weight: 700; color: var(--accent); display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .badge { font-size: 0.7rem; background: rgba(56, 189, 248, 0.2); color: var(--accent); padding: 2px 8px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.4); }
  .subtitle { font-size: 0.75rem; color: var(--text-dim); margin-bottom: 20px; }
  .stat-card { background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 12px; }
  .stat-title { font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
  .stat-value { font-size: 1.1rem; font-weight: 600; margin-top: 4px; }
  .nav-tabs { display: flex; gap: 8px; border-bottom: 1px solid var(--border); padding: 12px 24px; background: var(--card); }
  .tab-btn { background: none; border: none; color: var(--text-dim); padding: 8px 16px; font-size: 0.9rem; font-weight: 500; cursor: pointer; border-radius: 6px; }
  .tab-btn.active { background: rgba(56, 189, 248, 0.15); color: var(--accent); }
  .content-pane { flex: 1; display: none; flex-direction: column; overflow-y: auto; padding: 24px; }
  .content-pane.active { display: flex; }
  #chat-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
  .msg { max-width: 80%; padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; }
  .msg.user { align-self: flex-end; background: #2563eb; color: #fff; }
  .msg.assistant { align-self: flex-start; background: var(--card); border: 1px solid var(--border); }
  .input-bar { display: flex; gap: 12px; }
  input[type="text"], select, textarea { flex: 1; background: var(--card); border: 1px solid var(--border); color: var(--text); padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; }
  button.action-btn { background: var(--accent); color: #000; font-weight: 600; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; }
  button.action-btn:hover { background: var(--accent-hover); color: #fff; }
  pre { background: #000; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 0.85rem; color: #38bdf8; border: 1px solid var(--border); }
</style>
</head>
<body>
<div id="sidebar">
  <h1>GAM.AI <span class="badge">MICRO v1.1</span></h1>
  <div class="subtitle">Local-First Resource-Efficient AI</div>
  <div class="stat-card">
    <div class="stat-title">Active Model & RAM</div>
    <div class="stat-value" id="stat-model">Loading...</div>
  </div>
  <div class="stat-card">
    <div class="stat-title">Smart Cache & Storage</div>
    <div class="stat-value" id="stat-cache">Loading...</div>
  </div>
  <div class="stat-card">
    <div class="stat-title">Permanent Knowledge</div>
    <div class="stat-value" id="stat-knowledge">Loading...</div>
  </div>
  <div style="margin-top: auto; display: flex; flex-direction: column; gap: 8px;">
    <button class="action-btn" onclick="unloadModel()" style="background:#e11d48; color:#fff;">Unload Model (0 MB)</button>
    <button class="action-btn" onclick="clearCache()" style="background:#475569; color:#fff;">Clear Temp Cache</button>
  </div>
</div>
<div id="main">
  <div class="nav-tabs">
    <button class="tab-btn active" onclick="switchTab('chat')">AI Assistant</button>
    <button class="tab-btn" onclick="switchTab('subnet')">Subnet Calculator</button>
    <button class="tab-btn" onclick="switchTab('config')">Config Generator</button>
  </div>
  <div id="tab-chat" class="content-pane active">
    <div id="chat-messages">
      <div class="msg assistant">Welcome to GAM.AI. System operates strictly locally with minimal resource footprint. Ask a technical, sysadmin, or networking query.</div>
    </div>
    <div class="input-bar">
      <input type="text" id="chat-input" placeholder="Type a message or /command..." onkeydown="if(event.key==='Enter') sendChat()">
      <button class="action-btn" onclick="sendChat()">Send</button>
    </div>
  </div>
  <div id="tab-subnet" class="content-pane">
    <h2 style="margin-bottom:12px;">Local IPv4/IPv6 Subnet Calculator</h2>
    <div class="input-bar" style="margin-bottom:16px;">
      <input type="text" id="subnet-input" placeholder="e.g. 192.168.1.100/26 or 10.0.0.0/19">
      <button class="action-btn" onclick="calcSubnet()">Calculate</button>
    </div>
    <div id="subnet-result" style="display:none;"></div>
  </div>
  <div id="tab-config" class="content-pane">
    <h2 style="margin-bottom:12px;">Multi-Vendor Configuration Generator</h2>
    <div style="display:flex; gap:12px; margin-bottom:12px;">
      <select id="cfg-vendor">
        <option value="cisco">Cisco IOS (OSPF / SVI / Trunk)</option>
        <option value="huawei">Huawei VRP (VLAN / Trunk / OSPF)</option>
        <option value="olt">Huawei SmartAX GPON OLT (ONT Service)</option>
        <option value="fortigate">Fortinet FortiGate (Firewall Policy)</option>
        <option value="mikrotik">MikroTik RouterOS (WAN NAT & Bridge)</option>
      </select>
      <button class="action-btn" onclick="generateConfig()">Generate</button>
    </div>
    <pre id="config-result">// Click Generate to produce verified multi-vendor network syntax.</pre>
  </div>
</div>
<script>
async function refreshStatus() {
  const r = await fetch('/api/status');
  const d = await r.json();
  document.getElementById('stat-model').innerText = d.active_model + ' (' + d.ram_mb + ' MB)';
  document.getElementById('stat-cache').innerText = d.cache_entries + ' items (' + d.cache_kb + ' KB)';
  document.getElementById('stat-knowledge').innerText = d.knowledge_items + ' items';
}
setInterval(refreshStatus, 3000);
refreshStatus();

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.content-pane').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if(!text) return;
  input.value = '';
  const box = document.getElementById('chat-messages');
  box.innerHTML += `<div class="msg user">${text}</div>`;
  box.scrollTop = box.scrollHeight;
  const res = await fetch('/api/chat', {method:'POST', body:JSON.stringify({query: text})});
  const data = await res.json();
  box.innerHTML += `<div class="msg assistant">${data.response}</div>`;
  box.scrollTop = box.scrollHeight;
  refreshStatus();
}

async function unloadModel() {
  await fetch('/api/model/unload', {method:'POST'});
  alert('Model unloaded from RAM.');
  refreshStatus();
}

async function clearCache() {
  await fetch('/api/chat', {method:'POST', body:JSON.stringify({query: '/clear-cache'})});
  alert('Temporary cache cleared.');
  refreshStatus();
}

async function calcSubnet() {
  const v = document.getElementById('subnet-input').value;
  const res = await fetch('/api/network/subnet', {method:'POST', body:JSON.stringify({cidr: v})});
  const data = await res.json();
  const div = document.getElementById('subnet-result');
  div.style.display = 'block';
  div.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

async function generateConfig() {
  const vendor = document.getElementById('cfg-vendor').value;
  const res = await fetch('/api/network/config', {method:'POST', body:JSON.stringify({vendor: vendor})});
  const data = await res.json();
  document.getElementById('config-result').innerText = data.config;
}
</script>
</body>
</html>
"""

class GAMAIWebHandler(http.server.BaseHTTPRequestHandler):
    engine: Optional[ChatEngine] = None

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            body = HTML_DASHBOARD.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
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
            query = req_data.get("query", "")
            result = self.engine.process_query(query)
            self._send_json(result)
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
        elif self.path == "/api/model/unload":
            self.engine.models.unload_active_model()
            self._send_json({"status": "unloaded"})
        else:
            self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        pass

def run_web_server(engine: ChatEngine, host: str = "127.0.0.1", port: int = 8080):
    GAMAIWebHandler.engine = engine
    server = http.server.HTTPServer((host, port), GAMAIWebHandler)
    print(f"GAM.AI Web Dashboard running at: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        server.server_close()
