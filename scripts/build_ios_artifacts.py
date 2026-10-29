#!/usr/bin/env python3
"""Build iOS direct-install artifacts for GAM.AI:
- Apple Configuration Profile (.mobileconfig) for 1-Tap iOS Home Screen App
- Apple OTA Installation Manifest (manifest.plist) for itms-services://
- iOS Application Package (.ipa) for Sideloading (AltStore / SideStore / Scarlet / TrollStore)
- App Icons in all iOS Retina and PWA resolutions
"""

import os
import sys
import shutil
import base64
import zipfile
import plistlib
import uuid

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UI_DIR = os.path.join(REPO_ROOT, "gam_ai", "ui")
DIST_DIR = os.path.join(REPO_ROOT, "dist")
IOS_DIR = os.path.join(REPO_ROOT, "ios")
ICONS_DIR = os.path.join(IOS_DIR, "icons")

WEBSITE_ROOT = r"C:\Users\Sudo\Projects\gautambhuwan.com.np"
WEBSITE_DOWNLOADS = os.path.join(WEBSITE_ROOT, "downloads", "gam-ai") if os.path.isdir(WEBSITE_ROOT) else None
WEBSITE_GAM_AI = os.path.join(WEBSITE_ROOT, "gam-ai") if os.path.isdir(WEBSITE_ROOT) else None

VERSION = "1.7.1"
BUNDLE_ID = "com.gamai.app"
APP_NAME = "GAM.AI"
APP_URL = "https://gautambhuwan.com.np/gam-ai/"

def setup_dirs():
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(IOS_DIR, exist_ok=True)
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(os.path.join(UI_DIR, "icons"), exist_ok=True)
    os.makedirs(os.path.join(REPO_ROOT, "android", "app", "src", "main", "assets", "icons"), exist_ok=True)
    if WEBSITE_DOWNLOADS:
        os.makedirs(WEBSITE_DOWNLOADS, exist_ok=True)
    if WEBSITE_GAM_AI:
        os.makedirs(WEBSITE_GAM_AI, exist_ok=True)
        os.makedirs(os.path.join(WEBSITE_GAM_AI, "icons"), exist_ok=True)

def ensure_icons():
    sizes = [57, 60, 120, 152, 180, 192, 512, 1024]
    missing = [sz for sz in sizes if not os.path.exists(os.path.join(ICONS_DIR, f"icon-{sz}.png"))]
    if not missing:
        return

    if Image is None:
        print("  ! Pillow not installed, skipping dynamic icon generation.")
        return

    print("  -> Generating master icons...")
    master_size = 1024
    img = Image.new('RGBA', (master_size, master_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(master_size):
        r = int(10 + (30 - 10) * (y / master_size))
        g = int(15 + (41 - 15) * (y / master_size))
        b = int(29 + (59 - 29) * (y / master_size))
        draw.line([(0, y), (master_size, y)], fill=(r, g, b, 255))

    center = master_size // 2
    radius = int(master_size * 0.38)
    for i in range(16, 0, -1):
        alpha = int(12 * (17 - i) / 16)
        draw.ellipse([center - radius - i*2, center - radius - i*2, center + radius + i*2, center + radius + i*2], outline=(56, 189, 248, alpha), width=3)

    draw.ellipse([center - radius, center - radius, center + radius, center + radius], outline=(56, 189, 248, 255), width=24)
    inner_radius = int(radius * 0.72)
    draw.ellipse([center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius], outline=(16, 185, 129, 255), width=16)

    core_r = int(inner_radius * 0.52)
    for cr in range(core_r, 0, -2):
        t = cr / core_r
        cr_r = int(56 * (1 - t) + 16 * t)
        cr_g = int(189 * (1 - t) + 185 * t)
        cr_b = int(248 * (1 - t) + 129 * t)
        draw.ellipse([center - cr, center - cr, center + cr, center + cr], fill=(cr_r, cr_g, cr_b, 255))

    node_r = 28
    nodes = [
        (center, center - radius), (center, center + radius),
        (center - radius, center), (center + radius, center),
        (center, center - inner_radius), (center, center + inner_radius),
        (center - inner_radius, center), (center + inner_radius, center),
    ]
    for nx, ny in nodes:
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r], fill=(56, 189, 248, 255), outline=(255, 255, 255, 230), width=6)
    draw.ellipse([center - 20, center - 20, center + 20, center + 20], fill=(255, 255, 255, 255))

    for sz in sizes:
        resized = img.resize((sz, sz), Image.Resampling.LANCZOS)
        p = os.path.join(ICONS_DIR, f"icon-{sz}.png")
        resized.save(p, 'PNG')

def copy_icons():
    print("[1/5] Distributing iOS & PWA Icons...")
    ensure_icons()
    icon_files = [
        "icon-57.png", "icon-60.png", "icon-120.png", "icon-152.png",
        "icon-180.png", "icon-192.png", "icon-512.png", "icon-1024.png"
    ]
    targets = [
        os.path.join(UI_DIR, "icons"),
        os.path.join(REPO_ROOT, "android", "app", "src", "main", "assets", "icons"),
        IOS_DIR
    ]
    if WEBSITE_DOWNLOADS:
        targets.append(WEBSITE_DOWNLOADS)
    if WEBSITE_GAM_AI:
        targets.append(os.path.join(WEBSITE_GAM_AI, "icons"))

    for target in targets:
        os.makedirs(target, exist_ok=True)
        for f in icon_files:
            src = os.path.join(ICONS_DIR, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(target, f))
    
    icon192 = os.path.join(ICONS_DIR, "icon-192.png")
    if os.path.exists(icon192):
        shutil.copy2(icon192, os.path.join(UI_DIR, "icon.png"))
        if WEBSITE_GAM_AI:
            shutil.copy2(icon192, os.path.join(WEBSITE_GAM_AI, "icon.png"))
    print("  -> Icons successfully copied to all targets.")

def build_mobileconfig():
    print("[2/5] Generating Apple Configuration Profile (.mobileconfig)...")
    icon_path = os.path.join(ICONS_DIR, "icon-180.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(UI_DIR, "icons", "icon-180.png")

    with open(icon_path, "rb") as f:
        icon_bytes = f.read()

    webclip_uuid = str(uuid.uuid4()).upper()
    profile_uuid = str(uuid.uuid4()).upper()

    profile_dict = {
        "PayloadDisplayName": f"{APP_NAME} Edge AI App",
        "PayloadIdentifier": f"{BUNDLE_ID}.profile",
        "PayloadOrganization": "GAM.AI - Edge Intelligence",
        "PayloadRemovalDisallowed": False,
        "PayloadType": "Configuration",
        "PayloadUUID": profile_uuid,
        "PayloadVersion": 1,
        "PayloadDescription": "Installs GAM.AI Local-First Edge Intelligence directly onto your iPhone or iPad Home Screen as a standalone full-screen application.",
        "PayloadContent": [
            {
                "FullScreen": True,
                "Icon": icon_bytes,
                "IsRemovable": True,
                "Label": APP_NAME,
                "PayloadDescription": f"Configures {APP_NAME} standalone app clip for iOS",
                "PayloadDisplayName": f"{APP_NAME} Standalone App",
                "PayloadIdentifier": f"{BUNDLE_ID}.webclip",
                "PayloadType": "com.apple.webClip.managed",
                "PayloadUUID": webclip_uuid,
                "PayloadVersion": 1,
                "Precomposed": True,
                "URL": APP_URL
            }
        ]
    }

    out_paths = [
        os.path.join(DIST_DIR, f"gam-ai-v{VERSION}.mobileconfig"),
        os.path.join(DIST_DIR, "gam-ai.mobileconfig"),
        os.path.join(IOS_DIR, f"gam-ai-v{VERSION}.mobileconfig"),
        os.path.join(IOS_DIR, "gam-ai.mobileconfig"),
    ]
    if WEBSITE_DOWNLOADS:
        out_paths.extend([
            os.path.join(WEBSITE_DOWNLOADS, f"gam-ai-v{VERSION}.mobileconfig"),
            os.path.join(WEBSITE_DOWNLOADS, "gam-ai.mobileconfig")
        ])
    if WEBSITE_GAM_AI:
        out_paths.append(os.path.join(WEBSITE_GAM_AI, "gam-ai.mobileconfig"))

    for p in out_paths:
        with open(p, "wb") as f:
            plistlib.dump(profile_dict, f, fmt=plistlib.FMT_XML)
        print(f"  -> Generated: {p} ({os.path.getsize(p):,} bytes)")

def build_manifest_plist():
    print("[3/5] Generating Apple OTA Manifest (manifest.plist)...")
    manifest_dict = {
        "items": [
            {
                "assets": [
                    {
                        "kind": "software-package",
                        "url": f"https://gautambhuwan.com.np/downloads/gam-ai/gam-ai-v{VERSION}.ipa"
                    },
                    {
                        "kind": "display-image",
                        "needs-shine": False,
                        "url": "https://gautambhuwan.com.np/downloads/gam-ai/icon-57.png"
                    },
                    {
                        "kind": "full-size-image",
                        "needs-shine": False,
                        "url": "https://gautambhuwan.com.np/downloads/gam-ai/icon-512.png"
                    }
                ],
                "metadata": {
                    "bundle-identifier": BUNDLE_ID,
                    "bundle-version": VERSION,
                    "kind": "software",
                    "title": APP_NAME,
                    "subtitle": "Edge AI & Offline Intelligence",
                    "items": []
                }
            }
        ]
    }

    out_paths = [
        os.path.join(DIST_DIR, "manifest.plist"),
        os.path.join(IOS_DIR, "manifest.plist"),
    ]
    if WEBSITE_DOWNLOADS:
        out_paths.append(os.path.join(WEBSITE_DOWNLOADS, "manifest.plist"))
    if WEBSITE_GAM_AI:
        out_paths.append(os.path.join(WEBSITE_GAM_AI, "manifest.plist"))

    for p in out_paths:
        with open(p, "wb") as f:
            plistlib.dump(manifest_dict, f, fmt=plistlib.FMT_XML)
        print(f"  -> Generated: {p}")

def build_ipa():
    print("[4/5] Building iOS Application Package (gam-ai-v1.7.1.ipa)...")
    build_temp = os.path.join(DIST_DIR, "ipa_build")
    payload_dir = os.path.join(build_temp, "Payload")
    app_dir = os.path.join(payload_dir, f"{APP_NAME}.app")

    if os.path.exists(build_temp):
        shutil.rmtree(build_temp)
    os.makedirs(app_dir, exist_ok=True)

    info_plist = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": APP_NAME,
        "CFBundleExecutable": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": APP_NAME,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": "15",
        "LSRequiresIPhoneOS": True,
        "UIRequiresFullScreen": True,
        "UIStatusBarStyle": "UIStatusBarStyleLightContent",
        "UIViewControllerBasedStatusBarAppearance": False,
        "UISupportedInterfaceOrientations": [
            "UIInterfaceOrientationPortrait",
            "UIInterfaceOrientationLandscapeLeft",
            "UIInterfaceOrientationLandscapeRight"
        ],
        "UISupportedInterfaceOrientations~ipad": [
            "UIInterfaceOrientationPortrait",
            "UIInterfaceOrientationPortraitUpsideDown",
            "UIInterfaceOrientationLandscapeLeft",
            "UIInterfaceOrientationLandscapeRight"
        ],
        "CFBundleIcons": {
            "CFBundlePrimaryIcon": {
                "CFBundleIconFiles": ["AppIcon60x60", "AppIcon76x76", "AppIcon83.5x83.5"],
                "CFBundleIconName": "AppIcon"
            }
        },
        "NSAppTransportSecurity": {
            "NSAllowsArbitraryLoads": True
        },
        "NSCameraUsageDescription": "GAM.AI uses the camera for Live Vision / Lens intelligence analysis.",
        "NSMicrophoneUsageDescription": "GAM.AI uses the microphone for voice queries and continuous speech recognition."
    }

    with open(os.path.join(app_dir, "Info.plist"), "wb") as f:
        plistlib.dump(info_plist, f, fmt=plistlib.FMT_XML)

    for sz, name in [(120, "AppIcon60x60@2x.png"), (180, "AppIcon60x60@3x.png"), (152, "AppIcon76x76@2x~ipad.png"), (512, "iTunesArtwork.png"), (1024, "iTunesArtwork@2x.png")]:
        src = os.path.join(ICONS_DIR, f"icon-{sz}.png")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(app_dir, name))

    for item in os.listdir(UI_DIR):
        if item in ["__pycache__", "cli.py", "web.py", "__init__.py"]:
            continue
        s = os.path.join(UI_DIR, item)
        d = os.path.join(app_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    runner_path = os.path.join(app_dir, APP_NAME)
    with open(runner_path, "wb") as f:
        f.write(b"#!/bin/sh\nexec open http://localhost:8080/dashboard.html\n")
    try:
        os.chmod(runner_path, 0o755)
    except Exception:
        pass

    out_ipas = [
        os.path.join(DIST_DIR, f"gam-ai-v{VERSION}.ipa"),
        os.path.join(DIST_DIR, "gam-ai.ipa"),
    ]
    if WEBSITE_DOWNLOADS:
        out_ipas.extend([
            os.path.join(WEBSITE_DOWNLOADS, f"gam-ai-v{VERSION}.ipa"),
            os.path.join(WEBSITE_DOWNLOADS, "gam-ai-latest.ipa")
        ])

    for out_ipa in out_ipas:
        with zipfile.ZipFile(out_ipa, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(payload_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, build_temp)
                    zf.write(full_p, arcname=rel_p)
        print(f"  -> IPA Created: {out_ipa} ({os.path.getsize(out_ipa):,} bytes)")

    shutil.rmtree(build_temp, ignore_errors=True)

def deploy_web_app():
    if not WEBSITE_GAM_AI:
        return
    print("[5/5] Deploying Web PWA to website root (gautambhuwan.com.np/gam-ai)...")
    for item in os.listdir(UI_DIR):
        if item in ["__pycache__", "cli.py", "web.py", "__init__.py"]:
            continue
        s = os.path.join(UI_DIR, item)
        d = os.path.join(WEBSITE_GAM_AI, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    src_dash = os.path.join(WEBSITE_GAM_AI, "dashboard.html")
    dst_idx = os.path.join(WEBSITE_GAM_AI, "index.html")
    if os.path.exists(src_dash):
        shutil.copy2(src_dash, dst_idx)
        print(f"  -> Created: {dst_idx}")

    print("  -> Web App deployed successfully!")

if __name__ == "__main__":
    setup_dirs()
    copy_icons()
    build_mobileconfig()
    build_manifest_plist()
    build_ipa()
    deploy_web_app()
    print("\nSUCCESS: All iOS direct installation artifacts generated!")
