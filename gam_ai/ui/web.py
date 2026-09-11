"""Zero-Dependency Embedded Web Server & REST API for GAM.AI ChatGPT-Inspired Dashboard."""

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
<title>GAM.AI — Local-First Intelligent Assistant</title>
<style>
  :root {
    --bg: #090d16;
    --sidebar-bg: #0f172a;
    --card-bg: #1e293b;
    --card-hover: #334155;
    --border: #1e293b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.15);
    --green: #10b981;
    --user-msg: #1e3a8a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: var(--bg); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }

  /* Left Sidebar */
  #sidebar {
    width: 280px; background: var(--sidebar-bg); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; padding: 16px; flex-shrink: 0;
  }
  .brand { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .brand-title { font-size: 1.15rem; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px; }
  .brand-title span { color: var(--accent); }
  .badge-nano { font-size: 0.65rem; background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 9999px; padding: 2px 8px; }

  .new-chat-btn {
    display: flex; align-items: center; gap: 10px; width: 100%;
    padding: 10px 14px; background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 8px; color: var(--text-main); font-size: 0.88rem; font-weight: 500;
    cursor: pointer; transition: all 0.2s; margin-bottom: 16px;
  }
  .new-chat-btn:hover { background: var(--card-hover); border-color: #475569; }

  .nav-section-title { font-size: 0.7rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.08em; margin-bottom: 8px; padding-left: 4px; }
  .history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; }
  .history-item { padding: 8px 12px; font-size: 0.82rem; color: var(--text-muted); border-radius: 6px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .history-item:hover { background: rgba(255,255,255,0.05); color: var(--text-main); }

  .sidebar-footer { border-top: 1px solid var(--border); padding-top: 12px; display: flex; flex-direction: column; gap: 6px; }
  .menu-action-btn {
    display: flex; align-items: center; gap: 10px; width: 100%;
    padding: 9px 12px; background: none; border: none; border-radius: 6px;
    color: var(--text-muted); font-size: 0.85rem; font-weight: 500; cursor: pointer; text-align: left;
  }
  .menu-action-btn:hover { background: rgba(255,255,255,0.06); color: var(--text-main); }

  /* Main Conversational Canvas */
  #main-viewport { flex: 1; display: flex; flex-direction: column; height: 100vh; position: relative; }
  .top-header {
    height: 56px; border-bottom: 1px solid var(--border); display: flex; align-items: center;
    justify-content: space-between; padding: 0 24px; background: rgba(9, 13, 22, 0.7); backdrop-filter: blur(8px);
  }
  .model-select-capsule {
    display: flex; align-items: center; gap: 8px; background: var(--card-bg);
    border: 1px solid var(--border); border-radius: 20px; padding: 4px 12px; font-size: 0.82rem;
  }
  .model-select-capsule select { background: transparent; border: none; color: var(--text-main); font-size: 0.82rem; outline: none; cursor: pointer; }
  .status-indicators { display: flex; align-items: center; gap: 12px; font-size: 0.75rem; color: var(--text-muted); }
  .status-pill { display: inline-flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.1); color: var(--green); padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2); }

  /* Message Stream */
  #chat-scroll-area { flex: 1; overflow-y: auto; padding: 24px 0; display: flex; flex-direction: column; }
  .chat-thread-width { width: 100%; max-width: 820px; margin: 0 auto; padding: 0 20px; }

  /* Hero welcome */
  .hero-welcome { text-align: center; margin: 60px auto 40px auto; max-width: 600px; }
  .hero-welcome h2 { font-size: 1.8rem; font-weight: 700; margin-bottom: 8px; color: var(--text-main); }
  .hero-welcome p { font-size: 0.92rem; color: var(--text-muted); line-height: 1.6; }
  .quick-chips-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 24px; }
  .chip-card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; text-align: left; cursor: pointer; transition: all 0.2s;
  }
  .chip-card:hover { border-color: var(--accent); background: rgba(56, 189, 248, 0.04); transform: translateY(-1px); }
  .chip-title { font-size: 0.84rem; font-weight: 600; color: var(--text-main); }
  .chip-desc { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

  .message-wrapper { margin-bottom: 24px; display: flex; flex-direction: column; }
  .msg-row { display: flex; gap: 14px; align-items: flex-start; }
  .msg-row.user { justify-content: flex-end; }
  .avatar {
    width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; flex-shrink: 0;
  }
  .avatar.ai { background: var(--accent); color: #000; }
  .msg-content {
    max-width: 78%; font-size: 0.92rem; line-height: 1.6; border-radius: 12px; padding: 12px 18px;
    word-break: break-word;
  }
  .msg-content.user { background: var(--user-msg); color: #fff; border-bottom-right-radius: 2px; }
  .msg-content.ai { background: var(--card-bg); border: 1px solid var(--border); border-bottom-left-radius: 2px; }

  /* Bottom Floating Input Pill */
  .input-container { padding: 16px 20px 24px 20px; width: 100%; max-width: 820px; margin: 0 auto; }
  .input-capsule {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 24px;
    display: flex; align-items: flex-end; padding: 8px 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  .input-capsule:focus-within { border-color: #475569; }
  textarea#prompt-input {
    flex: 1; background: transparent; border: none; color: var(--text-main);
    font-size: 0.95rem; line-height: 1.4; resize: none; max-height: 160px; height: 28px;
    outline: none; padding: 4px 6px;
  }
  button#send-btn {
    background: var(--accent); color: #000; border: none; width: 32px; height: 32px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.2s; flex-shrink: 0; margin-left: 6px;
  }
  button#send-btn:hover { background: #7dd3fc; }

  /* Modals */
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
    display: none; align-items: center; justify-content: center; z-index: 1000;
  }
  .modal-overlay.open { display: flex; }
  .modal-box {
    background: var(--sidebar-bg); border: 1px solid var(--border); border-radius: 14px;
    width: 90%; max-width: 680px; max-height: 85vh; overflow-y: auto; padding: 24px; display: flex; flex-direction: column;
  }
  .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
  .modal-title { font-size: 1.15rem; font-weight: 700; color: var(--text-main); }
  .close-btn { background: none; border: none; color: var(--text-muted); font-size: 1.2rem; cursor: pointer; }

  /* Model Store Cards */
  .model-grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
  .model-card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px; display: flex; justify-content: space-between; align-items: center;
  }
  .model-name { font-size: 0.95rem; font-weight: 600; }
  .model-meta { font-size: 0.78rem; color: var(--text-muted); margin-top: 3px; }
  .btn-download {
    background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(56,189,248,0.4);
    padding: 6px 14px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer;
  }
  .btn-download.ready { background: rgba(16,185,129,0.15); color: var(--green); border-color: rgba(16,185,129,0.4); }

  pre { background: #040711; border: 1px solid var(--border); padding: 12px; border-radius: 8px; overflow-x: auto; color: #38bdf8; font-family: monospace; font-size: 0.85rem; margin-top: 8px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.85rem; }
  th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  th { background: rgba(255,255,255,0.05); }
</style>
</head>
<body>

<!-- Left Sidebar -->
<div id="sidebar">
  <div class="brand">
    <div class="brand-title">GAM<span>.AI</span></div>
    <div class="badge-nano">MICRO v2.1</div>
  </div>

  <button class="new-chat-btn" onclick="startNewChat()">
    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
    New Conversation
  </button>

  <div class="nav-section-title">Recent Topics</div>
  <div class="history-list" id="history-container">
    <div class="history-item" onclick="loadQuery('OSPF LFA fast reroute')">OSPF LFA Fast Reroute</div>
    <div class="history-item" onclick="loadQuery('Calculate subnet 192.168.10.0/27')">Subnet 192.168.10.0/27</div>
    <div class="history-item" onclick="loadQuery('Huawei GPON OLT Service-Port')">Huawei GPON OLT Service</div>
    <div class="history-item" onclick="loadQuery('FortiGate LAN to WAN firewall policy')">FortiGate Firewall Policy</div>
  </div>

  <div class="sidebar-footer">
    <button class="menu-action-btn" onclick="openModal('modal-models')">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
      Model Store (Modular)
    </button>
    <button class="menu-action-btn" onclick="openModal('modal-tools')">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      Network & Sysadmin Tools
    </button>
    <button class="menu-action-btn" onclick="openModal('modal-settings')">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
      System & Cache Settings
    </button>
  </div>
</div>

<!-- Main Conversation Workspace -->
<div id="main-viewport">
  <div class="top-header">
    <div class="model-select-capsule">
      <span style="color:var(--text-muted); font-size:0.75rem;">Model:</span>
      <select id="active-model-dropdown" onchange="switchActiveModel(this.value)">
        <option value="nano">GAM.AI Nano (0.5B) — Active</option>
        <option value="micro">GAM.AI Micro (1.5B)</option>
        <option value="coder">GAM.AI Coder (1.5B)</option>
        <option value="descriptive">GAM.AI Descriptive (3.0B)</option>
        <option value="picture">GAM.AI Picture & Diagram</option>
        <option value="neteng">GAM.AI NetEng Specialist</option>
      </select>
    </div>
    <div class="status-indicators">
      <span id="ram-meter">RAM: ~120 MB</span>
      <span class="status-pill">● Local-First</span>
    </div>
  </div>

  <div id="chat-scroll-area">
    <div class="chat-thread-width" id="thread-container">
      <div class="hero-welcome" id="hero-welcome">
        <h2>What would you like to build or troubleshoot?</h2>
        <p>GAM.AI is designed with the primary engineering objective of minimal resource usage. Ask any network, coding, or technical research question.</p>
        <div class="quick-chips-grid">
          <div class="chip-card" onclick="loadQuery('Calculate subnet 172.16.10.0/26 with usable hosts and broadcast')">
            <div class="chip-title">Subnet Calculation</div>
            <div class="chip-desc">Analyze network ID, netmask, wildcard & host range</div>
          </div>
          <div class="chip-card" onclick="loadQuery('Generate Huawei GPON OLT service-port and ONT lineprofile for VLAN 100')">
            <div class="chip-title">Huawei OLT Configuration</div>
            <div class="chip-desc">Generate DBA, srvprofile & service-port syntax</div>
          </div>
          <div class="chip-card" onclick="loadQuery('Draw a network diagram of dual-homed OSPF core routers connected to Huawei switch')">
            <div class="chip-title">Topology Diagram</div>
            <div class="chip-desc">Generate visual ASCII and Mermaid network diagrams</div>
          </div>
          <div class="chip-card" onclick="loadQuery('Write a Python script to check TCP port latency across multiple devices')">
            <div class="chip-title">Python Network Script</div>
            <div class="chip-desc">Zero-dependency automated device health check</div>
          </div>
        </div>
      </div>
      <div id="messages-stream"></div>
    </div>
  </div>

  <!-- Bottom Floating Input Capsule -->
  <div class="input-container">
    <div class="input-capsule">
      <textarea id="prompt-input" rows="1" placeholder="Ask GAM.AI anything (coding, subnetting, OLT/Huawei configs, research)..." onkeydown="handleKey(event)"></textarea>
      <button id="send-btn" onclick="submitMessage()">
        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      </button>
    </div>
  </div>
</div>

<!-- Modal 1: Modular Model Store -->
<div id="modal-models" class="modal-overlay" onclick="closeOnBackdrop(event, 'modal-models')">
  <div class="modal-box">
    <div class="modal-header">
      <div class="modal-title">Modular Model Store</div>
      <button class="close-btn" onclick="closeModal('modal-models')">✕</button>
    </div>
    <p style="font-size:0.84rem; color:var(--text-muted); margin-bottom:16px;">
      GAM.AI never forces you to download multi-gigabyte models upfront. Download only what you need; all models exit RAM automatically when idle.
    </p>
    <div class="model-grid" id="model-store-grid">
      <!-- Populated dynamically -->
    </div>
  </div>
</div>

<!-- Modal 2: Sub-Menu Network & Sysadmin Tools -->
<div id="modal-tools" class="modal-overlay" onclick="closeOnBackdrop(event, 'modal-tools')">
  <div class="modal-box">
    <div class="modal-header">
      <div class="modal-title">Network & Sysadmin Utilities</div>
      <button class="close-btn" onclick="closeModal('modal-tools')">✕</button>
    </div>
    <div style="display:flex; gap:10px; margin-bottom:14px;">
      <input type="text" id="tool-subnet-input" placeholder="e.g. 192.168.10.0/27 or 10.0.0.0/19" style="flex:1; background:var(--card-bg); border:1px solid var(--border); padding:8px 12px; border-radius:6px; color:#fff;">
      <button class="btn-download ready" onclick="runSubnetTool()">Calculate Subnet</button>
    </div>
    <div id="tool-subnet-output"></div>

    <hr style="border-color:var(--border); margin:18px 0;">
    <div style="font-size:0.9rem; font-weight:600; margin-bottom:8px;">Multi-Vendor Config Generator</div>
    <div style="display:flex; gap:10px; margin-bottom:12px;">
      <select id="tool-vendor-select" style="flex:1; background:var(--card-bg); border:1px solid var(--border); padding:8px 12px; border-radius:6px; color:#fff;">
        <option value="cisco">Cisco IOS (OSPF, SVI & Trunk)</option>
        <option value="huawei">Huawei VRP (VLAN, Trunk & OSPF)</option>
        <option value="olt">Huawei SmartAX GPON OLT (ONT Service)</option>
        <option value="fortigate">Fortinet FortiGate (Firewall Policy)</option>
        <option value="mikrotik">MikroTik RouterOS (Bridge & WAN NAT)</option>
      </select>
      <button class="btn-download ready" onclick="runConfigTool()">Generate Syntax</button>
    </div>
    <pre id="tool-config-output" style="max-height:220px;">// Configuration will appear here...</pre>
  </div>
</div>

<!-- Modal 3: System & Cache Settings -->
<div id="modal-settings" class="modal-overlay" onclick="closeOnBackdrop(event, 'modal-settings')">
  <div class="modal-box">
    <div class="modal-header">
      <div class="modal-title">System Health & Storage Retention</div>
      <button class="close-btn" onclick="closeModal('modal-settings')">✕</button>
    </div>
    <div style="display:flex; flex-direction:column; gap:12px;" id="settings-details">
      <div class="model-card">
        <div>
          <div class="model-name">Three-Level Storage Engine</div>
          <div class="model-meta" id="settings-cache-meta">SmartCache: Loading... | Permanent SQLite: Loading...</div>
        </div>
        <button class="btn-download" onclick="triggerCleanCache()">Clear Cache</button>
      </div>
      <div class="model-card">
        <div>
          <div class="model-name">Memory Management</div>
          <div class="model-meta">Strict Load -> Use -> Unload pattern</div>
        </div>
        <button class="btn-download" style="color:#ef4444; border-color:#ef4444;" onclick="triggerUnload()">Unload (0 MB)</button>
      </div>
      <div class="model-card">
        <div>
          <div class="model-name">Offline Mode</div>
          <div class="model-meta">Toggle zero-cloud local execution vs web research</div>
        </div>
        <button class="btn-download ready" id="toggle-online-btn" onclick="toggleOnline()">Toggle Mode</button>
      </div>
    </div>
  </div>
</div>

<script>
let currentModel = 'nano';

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
function closeOnBackdrop(e, id) { if(e.target.id === id) closeModal(id); }

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('ram-meter').innerText = 'RAM: ~' + data.ram_mb + ' MB';
    document.getElementById('settings-cache-meta').innerText = 'SmartCache: ' + data.cache_entries + ' items (' + data.cache_kb + ' KB) | Permanent: ' + data.knowledge_items + ' items';
  } catch(e) {}
}
setInterval(fetchStatus, 4000);
fetchStatus();

async function renderModelCatalog() {
  const res = await fetch('/api/models/catalog');
  const catalog = await res.json();
  const grid = document.getElementById('model-store-grid');
  grid.innerHTML = '';

  catalog.forEach(m => {
    const isReady = m.is_installed;
    const btnLabel = isReady ? (m.is_active ? 'Active' : 'Switch') : `Download (${m.download_size_mb} MB)`;
    const btnClass = isReady ? 'btn-download ready' : 'btn-download';

    grid.innerHTML += `
      <div class="model-card">
        <div>
          <div class="model-name">${m.name} <span class="badge-nano">${m.parameters}</span></div>
          <div class="model-meta">${m.description}</div>
          <div class="model-meta" style="color:var(--accent);">RAM required: ~${m.ram_mb} MB</div>
        </div>
        <button class="${btnClass}" onclick="handleModelAction('${m.id}', ${isReady})">${btnLabel}</button>
      </div>
    `;
  });
}
renderModelCatalog();

async function handleModelAction(id, isReady) {
  if(isReady) {
    await switchActiveModel(id);
    closeModal('modal-models');
  } else {
    alert(`To download ${id.toUpperCase()} modular weights, run in PowerShell:\npython scripts/download_model.py ${id}`);
  }
}

async function switchActiveModel(id) {
  await fetch('/api/model/switch', {method:'POST', body:JSON.stringify({model: id})});
  currentModel = id;
  document.getElementById('active-model-dropdown').value = id;
  fetchStatus();
}

function handleKey(e) {
  if(e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submitMessage();
  }
}

function loadQuery(q) {
  document.getElementById('prompt-input').value = q;
  submitMessage();
}

function startNewChat() {
  document.getElementById('messages-stream').innerHTML = '';
  document.getElementById('hero-welcome').style.display = 'block';
}

async function submitMessage() {
  const input = document.getElementById('prompt-input');
  const query = input.value.trim();
  if(!query) return;

  document.getElementById('hero-welcome').style.display = 'none';
  input.value = '';

  const stream = document.getElementById('messages-stream');
  stream.innerHTML += `
    <div class="message-wrapper">
      <div class="msg-row user">
        <div class="msg-content user">${escapeHtml(query)}</div>
      </div>
    </div>
  `;

  // Temporary bot typing
  const loadingId = 'loading-' + Date.now();
  stream.innerHTML += `
    <div class="message-wrapper" id="${loadingId}">
      <div class="msg-row">
        <div class="avatar ai">G</div>
        <div class="msg-content ai">Thinking...</div>
      </div>
    </div>
  `;
  document.getElementById('chat-scroll-area').scrollTop = document.getElementById('chat-scroll-area').scrollHeight;

  const res = await fetch('/api/chat', {method:'POST', body:JSON.stringify({query: query})});
  const data = await res.json();

  document.getElementById(loadingId).remove();
  stream.innerHTML += `
    <div class="message-wrapper">
      <div class="msg-row">
        <div class="avatar ai">G</div>
        <div class="msg-content ai">${formatResponse(data.response)}</div>
      </div>
    </div>
  `;
  document.getElementById('chat-scroll-area').scrollTop = document.getElementById('chat-scroll-area').scrollHeight;
  fetchStatus();
}

function escapeHtml(t) {
  return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatResponse(text) {
  // Convert markdown code blocks
  let formatted = text.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Convert bold
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  return formatted;
}

async function triggerUnload() {
  await fetch('/api/model/unload', {method:'POST'});
  alert('Model unloaded from RAM (0 MB).');
  fetchStatus();
}

async function triggerCleanCache() {
  await fetch('/api/chat', {method:'POST', body:JSON.stringify({query: '/clear-cache'})});
  alert('Temporary cache cleared.');
  fetchStatus();
}

async function toggleOnline() {
  await fetch('/api/chat', {method:'POST', body:JSON.stringify({query: '/offline'})});
  alert('Mode updated.');
}

async function runSubnetTool() {
  const cidr = document.getElementById('tool-subnet-input').value;
  const res = await fetch('/api/network/subnet', {method:'POST', body:JSON.stringify({cidr: cidr})});
  const data = await res.json();
  document.getElementById('tool-subnet-output').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

async function runConfigTool() {
  const vendor = document.getElementById('tool-vendor-select').value;
  const res = await fetch('/api/network/config', {method:'POST', body:JSON.stringify({vendor: vendor})});
  const data = await res.json();
  document.getElementById('tool-config-output').innerText = data.config;
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
        elif parsed.path == "/api/models/catalog":
            catalog = self.engine.models.get_catalog_with_status()
            self._send_json(catalog)
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
        elif self.path == "/api/model/switch":
            model_id = req_data.get("model", "nano")
            self.engine.models.load_model(model_id)
            self._send_json({"status": "switched", "active": model_id})
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
    print(f"GAM.AI Dashboard running at: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server...")
        server.server_close()
