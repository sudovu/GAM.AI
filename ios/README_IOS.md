# GAM.AI iOS & iPadOS Direct Installation Ecosystem

This directory contains the production files for direct iOS & iPadOS distribution without Apple App Store review, Mac hardware, or developer account requirements.

## Files & Components

1. **`gam-ai.mobileconfig` & `gam-ai-v1.6.0.mobileconfig`**:
   - Official Apple Configuration Profile (`com.apple.webClip.managed`).
   - Embeds a high-resolution base64 PNG icon and launches the app full-screen (`FullScreen: true`, `IsRemovable: true`) without Safari browser chrome.
   - **Zero Certificate Expiration**: Does not require 7-day re-signing. Once installed, it remains on the home screen permanently.

2. **`manifest.plist`**:
   - Apple Wireless Application Distribution Manifest for the `itms-services://` protocol.
   - Enables 1-tap browser-initiated installation prompts on Safari:
     `itms-services://?action=download-manifest&url=https://gautambhuwan.com.np/downloads/gam-ai/manifest.plist`

3. **`icons/`**:
   - Master iOS Retina & iPad assets: `icon-57.png`, `icon-60.png`, `icon-120.png`, `icon-152.png`, `icon-180.png`, `icon-192.png`, `icon-512.png`, `icon-1024.png`.

4. **Standalone IPA (`gam-ai-v1.6.0.ipa`)**:
   - Packaged inside `Payload/GAM.AI.app` with `Info.plist`, offline WebKit runtime, icons, and runner stub.
   - Fully compatible with AltStore (`altstore://install?url=...`), SideStore, Scarlet, TrollStore, and Sideloadly.

## Installation Methods for Users

### 1. 1-Tap Apple Configuration Profile (Recommended)
1. In Safari on iOS, download `gam-ai.mobileconfig`.
2. Tap **Allow** on the profile download alert.
3. Open iOS **Settings** &rarr; Tap **Profile Downloaded: GAM.AI** at the top.
4. Tap **Install** (enter device passcode if prompted).
5. GAM.AI appears directly on the iOS Home Screen.

### 2. Safari "Add to Home Screen" (PWA)
1. Open `https://gautambhuwan.com.np/gam-ai/` in Safari.
2. Tap the **Share** button (`⎋`).
3. Tap **Add to Home Screen** (`➕`).
4. Tap **Add**.

### 3. Sideloading (.ipa)
1. Download `gam-ai-v1.6.0.ipa`.
2. Sideload via AltStore, TrollStore, SideStore, or Scarlet.
