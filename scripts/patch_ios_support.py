#!/usr/bin/env python3
"""Patch GAM.AI for iOS direct download & installation support (v1.6.0)."""

import os
import re

DASHBOARD_UI = r"c:\Users\Sudo\Projects\gam-ai\gam_ai\ui\dashboard.html"
DASHBOARD_ASSETS = r"c:\Users\Sudo\Projects\gam-ai\android\app\src\main\assets\dashboard.html"
MANIFEST_PATH = r"c:\Users\Sudo\Projects\gam-ai\gam_ai\ui\manifest.json"
SW_PATH = r"c:\Users\Sudo\Projects\gam-ai\gam_ai\ui\sw.js"

def patch_dashboard(path):
    print(f"Patching {path}...")
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update version badges to v1.6.0
    html = re.sub(r'<div class="badge-nano">v1\.[0-9]+\.[0-9]+</div>', '<div class="badge-nano">v1.6.0</div>', html)
    html = re.sub(r'>v1\.[0-9]+\.[0-9]+</span>', '>v1.6.0</span>', html)

    # 2. Add Apple PWA & touch icons in <head>
    head_meta = """<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="GAM.AI">
<link rel="apple-touch-icon" sizes="180x180" href="icons/icon-180.png">
<link rel="apple-touch-icon" sizes="152x152" href="icons/icon-152.png">
<link rel="apple-touch-icon" sizes="120x120" href="icons/icon-120.png">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icons/icon-512.png">
<link rel="manifest" href="manifest.json">"""

    # Replace old apple-touch-icon or manifest lines
    html = re.sub(
        r'<meta name="apple-mobile-web-app-capable"[^>]*>[\s\S]*?<link rel="manifest"[^>]*>',
        head_meta,
        html
    )

    # 3. Add sidebar button if not present
    ios_sidebar_btn = """    <button class="menu-action-btn" id="btn-open-ios" onclick="closeSidebar(); showModal('modal-ios-install');">
      <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12 6.48 2 12 2z"/><path d="M12 8v8M8 12h8"/></svg>
      <span>🍏 Install on iOS / iPad</span>
    </button>
    <button class="menu-action-btn" id="btn-open-models">"""

    if 'id="btn-open-ios"' not in html:
        html = html.replace('<button class="menu-action-btn" id="btn-open-models">', ios_sidebar_btn)

    # 4. Add modal-ios-install modal before </body>
    ios_modal_html = """
<!-- MODAL: DIRECT IOS / IPADOS INSTALLATION -->
<div class="modal-overlay" id="modal-ios-install" style="display:none; align-items:center; justify-content:center; padding:16px;">
  <div class="modal-card" style="max-width:540px; width:100%; max-height:90vh; overflow-y:auto; border-radius:18px; border:1px solid rgba(56,189,248,0.3); background:#0f172a; box-shadow:0 25px 50px -12px rgba(0,0,0,0.85); padding:24px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px;">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg, #0284c7, #0f172a); border:1px solid #38bdf8; display:flex; align-items:center; justify-content:center; font-size:1.5rem;">
          🍏
        </div>
        <div>
          <h2 style="font-size:1.25rem; font-weight:800; color:#f8fafc; margin:0;">Install on iPhone & iPad</h2>
          <div style="font-size:0.78rem; color:#38bdf8; font-weight:600;">Direct Installation • No App Store Required • 100% Offline</div>
        </div>
      </div>
      <button onclick="closeModal('modal-ios-install')" style="background:none; border:none; color:#94a3b8; font-size:1.4rem; cursor:pointer; padding:4px 8px;">✕</button>
    </div>

    <!-- OPTION 1: 1-TAP PROFILE (RECOMMENDED) -->
    <div style="background:#1e293b; border:1px solid rgba(16,185,129,0.4); border-radius:14px; padding:16px; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong style="color:#10b981; font-size:0.95rem; display:flex; align-items:center; gap:6px;">
          <span>⚡</span> Method 1: 1-Tap Apple Profile (.mobileconfig)
        </strong>
        <span style="font-size:0.68rem; background:rgba(16,185,129,0.2); color:#10b981; padding:2px 8px; border-radius:10px; font-weight:700;">RECOMMENDED</span>
      </div>
      <p style="font-size:0.83rem; color:#cbd5e1; line-height:1.45; margin:0 0 12px 0;">
        Installs GAM.AI permanently as a full-screen, standalone app on your iOS Home Screen. Never expires, zero certificates or PC needed.
      </p>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <a href="https://gautambhuwan.com.np/downloads/gam-ai/gam-ai.mobileconfig" class="btn btn-primary" style="flex:1; text-align:center; padding:10px 16px; font-size:0.85rem; font-weight:700; background:#10b981; border-color:#10b981; color:#000; text-decoration:none; border-radius:10px; display:inline-block;" download>
          📲 Download & Install Profile
        </a>
      </div>
      <div style="font-size:0.75rem; color:#94a3b8; margin-top:10px; background:rgba(0,0,0,0.25); padding:8px 10px; border-radius:8px;">
        <strong>How to complete:</strong> 1. Tap Download & Allow → 2. Open iPhone <em>Settings</em> → 3. Tap <em>Profile Downloaded</em> at top → 4. Tap <em>Install</em>.
      </div>
    </div>

    <!-- OPTION 2: SAFARI ADD TO HOME SCREEN (PWA) -->
    <div style="background:#1e293b; border:1px solid #2e3d56; border-radius:14px; padding:16px; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong style="color:#38bdf8; font-size:0.95rem; display:flex; align-items:center; gap:6px;">
          <span>🌐</span> Method 2: Safari "Add to Home Screen"
        </strong>
        <span style="font-size:0.68rem; background:rgba(56,189,248,0.15); color:#38bdf8; padding:2px 8px; border-radius:10px; font-weight:600;">INSTANT</span>
      </div>
      <p style="font-size:0.83rem; color:#cbd5e1; line-height:1.45; margin:0 0 10px 0;">
        When visiting in Safari, tap the <strong>Share</strong> button (box with upward arrow) at the bottom toolbar, scroll down, and tap <strong>"Add to Home Screen"</strong> (➕).
      </p>
      <a href="https://gautambhuwan.com.np/gam-ai/" target="_blank" class="btn btn-secondary" style="display:block; text-align:center; padding:9px 14px; font-size:0.82rem; font-weight:600; text-decoration:none; border-radius:10px; border:1px solid #38bdf8; color:#38bdf8; background:rgba(56,189,248,0.08);">
        🚀 Launch Live Web App (PWA)
      </a>
    </div>

    <!-- OPTION 3: SIDELOADING (.IPA) -->
    <div style="background:#1e293b; border:1px solid #2e3d56; border-radius:14px; padding:16px; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <strong style="color:#f8fafc; font-size:0.95rem; display:flex; align-items:center; gap:6px;">
          <span>📦</span> Method 3: Direct IPA Download (AltStore / TrollStore)
        </strong>
        <span style="font-size:0.68rem; background:#334155; color:#94a3b8; padding:2px 8px; border-radius:10px; font-weight:600;">ADVANCED</span>
      </div>
      <p style="font-size:0.83rem; color:#cbd5e1; line-height:1.45; margin:0 0 10px 0;">
        Download the standalone <code>.ipa</code> binary package to install via AltStore, SideStore, Scarlet, TrollStore, or Sideloadly.
      </p>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <a href="https://gautambhuwan.com.np/downloads/gam-ai/gam-ai-v1.6.0.ipa" class="btn btn-secondary" style="flex:1; text-align:center; padding:8px 12px; font-size:0.8rem; font-weight:600; text-decoration:none; border-radius:8px; border:1px solid var(--border); color:#fff; background:#0f172a;" download>
          📦 Download IPA (v1.6.0)
        </a>
        <a href="altstore://install?url=https://gautambhuwan.com.np/downloads/gam-ai/gam-ai-v1.6.0.ipa" class="btn btn-secondary" style="flex:1; text-align:center; padding:8px 12px; font-size:0.8rem; font-weight:600; text-decoration:none; border-radius:8px; border:1px solid #38bdf8; color:#38bdf8; background:rgba(56,189,248,0.1);">
          ⚡ Open in AltStore
        </a>
      </div>
    </div>

    <!-- OPTION 4: OTA / GITHUB -->
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:12px;">
      <a href="itms-services://?action=download-manifest&url=https://gautambhuwan.com.np/downloads/gam-ai/manifest.plist" style="flex:1; text-align:center; padding:10px; border-radius:10px; background:rgba(255,255,255,0.06); border:1px solid var(--border); color:#cbd5e1; font-size:0.8rem; text-decoration:none; font-weight:600;">
        📲 Apple OTA Install
      </a>
      <a href="https://github.com/sudovu/GAM.AI/releases" target="_blank" style="flex:1; text-align:center; padding:10px; border-radius:10px; background:rgba(255,255,255,0.06); border:1px solid var(--border); color:#cbd5e1; font-size:0.8rem; text-decoration:none; font-weight:600;">
        🐙 GitHub Releases
      </a>
    </div>
  </div>
</div>
"""

    if 'id="modal-ios-install"' not in html:
        html = html.replace('</body>', ios_modal_html + '\n</body>')

    # 5. Add smart iOS detection banner
    ios_script = """
<script>
// Smart iOS & iPadOS Direct Install Detector
(function() {
  var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  var isStandalone = window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;
  if (isIOS && !isStandalone && !sessionStorage.getItem('gam_ios_prompt_dismissed')) {
    setTimeout(function() {
      var bar = document.createElement('div');
      bar.id = 'ios-install-banner';
      bar.style.cssText = 'position:fixed; bottom:80px; left:16px; right:16px; background:#0f172a; border:1px solid #10b981; border-radius:14px; padding:12px 16px; z-index:9999; display:flex; align-items:center; justify-content:space-between; box-shadow:0 10px 25px rgba(0,0,0,0.7); backdrop-filter:blur(8px);';
      bar.innerHTML = '<div style="display:flex; align-items:center; gap:10px;"><span style="font-size:1.4rem;">🍏</span><div><strong style="color:#f8fafc; font-size:0.88rem; display:block;">Install GAM.AI on iPhone</strong><span style="color:#94a3b8; font-size:0.75rem;">Run offline & full-screen</span></div></div><div style="display:flex; align-items:center; gap:8px;"><button onclick="showModal(\\'modal-ios-install\\')" style="background:#10b981; color:#000; font-weight:700; border:none; padding:6px 12px; border-radius:8px; font-size:0.8rem; cursor:pointer;">Install</button><button onclick="document.getElementById(\\'ios-install-banner\\').remove(); sessionStorage.setItem(\\'gam_ios_prompt_dismissed\\', \\'1\\');" style="background:none; border:none; color:#94a3b8; font-size:1.1rem; cursor:pointer; padding:4px;">✕</button></div>';
      document.body.appendChild(bar);
    }, 1500);
  }
})();
</script>
"""

    if 'ios-install-banner' not in html:
        html = html.replace('</body>', ios_script + '\n</body>')

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully patched {path}!")

def patch_manifest():
    manifest_content = """{
  "name": "GAM.AI - Universal Edge Intelligence",
  "short_name": "GAM.AI",
  "start_url": "./",
  "display": "standalone",
  "background_color": "#090d16",
  "theme_color": "#090d16",
  "description": "Micro, Local-First, Resource-Efficient AI Assistant for Android, iOS, Windows, macOS, Linux, and Tablets",
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
"""
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print(f"Updated {MANIFEST_PATH}")

def patch_sw():
    sw_content = """// GAM.AI Universal Offline Service Worker v1.6.0
const CACHE_NAME = 'gam-ai-cache-v1.6.0';
const OFFLINE_URLS = [
  './',
  './index.html',
  './dashboard.html',
  './three.min.js',
  './developer.jpg',
  './manifest.json',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(OFFLINE_URLS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).catch(() => caches.match('./index.html') || caches.match('./dashboard.html'));
    })
  );
});
"""
    with open(SW_PATH, "w", encoding="utf-8") as f:
        f.write(sw_content)
    print(f"Updated {SW_PATH}")

if __name__ == "__main__":
    patch_dashboard(DASHBOARD_UI)
    patch_dashboard(DASHBOARD_ASSETS)
    patch_manifest()
    patch_sw()
    print("ALL PATCHES APPLIED.")
