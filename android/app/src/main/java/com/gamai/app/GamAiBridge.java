package com.gamai.app;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.BatteryManager;
import android.os.Build;
import android.os.PowerManager;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

/**
 * JavaScript Bridge exposing Android device capabilities, tablet detection,
 * background music playback WakeLock, and local server connectivity to GAM.AI.
 */
public class GamAiBridge {
    private final Context context;
    private final SharedPreferences prefs;
    private PowerManager.WakeLock wakeLock;

    private static final String PREFS_NAME = "gam_ai_prefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final String DEFAULT_SERVER_URL = "http://127.0.0.1:8080";

    public GamAiBridge(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    @JavascriptInterface
    public boolean isNativeApp() {
        return true;
    }

    @JavascriptInterface
    public String getPlatform() {
        return "android";
    }

    @JavascriptInterface
    public void requestPermissions() {
        if (context instanceof MainActivity) {
            ((MainActivity) context).runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    ((MainActivity) context).checkAndRequestPermissions();
                }
            });
        }
    }

    @JavascriptInterface
    public boolean hasMicPermission() {
        return context.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) == android.content.pm.PackageManager.PERMISSION_GRANTED;
    }

    @JavascriptInterface
    public boolean hasCameraPermission() {
        return context.checkSelfPermission(android.Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED;
    }

    /**
     * Detects if running on an Android tablet (ScreenLayout >= LARGE).
     */
    @JavascriptInterface
    public boolean isTablet() {
        try {
            int screenLayout = context.getResources().getConfiguration().screenLayout;
            int screenSize = screenLayout & Configuration.SCREENLAYOUT_SIZE_MASK;
            return screenSize >= Configuration.SCREENLAYOUT_SIZE_LARGE;
        } catch (Exception ignored) {}
        return false;
    }

    /**
     * Acquires a partial wake lock to allow uninterrupted background music/audio playback.
     */
    @JavascriptInterface
    public void acquireWakeLock() {
        try {
            if (wakeLock == null) {
                PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
                if (pm != null) {
                    wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "GAMAI:MusicPlaybackWakeLock");
                }
            }
            if (wakeLock != null && !wakeLock.isHeld()) {
                // Hold wake lock with safety timeout of 3 hours
                wakeLock.acquire(180 * 60 * 1000L);
            }
        } catch (Exception ignored) {}
    }

    /**
     * Releases the background audio playback wake lock.
     */
    @JavascriptInterface
    public void releaseWakeLock() {
        try {
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
            }
        } catch (Exception ignored) {}
    }

    @JavascriptInterface
    public boolean isWakeLockHeld() {
        return wakeLock != null && wakeLock.isHeld();
    }

    @JavascriptInterface
    public int getBatteryLevel() {
        try {
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent batteryStatus = context.registerReceiver(null, ifilter);
            if (batteryStatus != null) {
                int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
                if (level >= 0 && scale > 0) {
                    return (int) ((level / (float) scale) * 100);
                }
            }
        } catch (Exception ignored) {}
        return 100;
    }

    @JavascriptInterface
    public boolean isCharging() {
        try {
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent batteryStatus = context.registerReceiver(null, ifilter);
            if (batteryStatus != null) {
                int status = batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                return status == BatteryManager.BATTERY_STATUS_CHARGING ||
                       status == BatteryManager.BATTERY_STATUS_FULL;
            }
        } catch (Exception ignored) {}
        return false;
    }

    @JavascriptInterface
    public long getAvailableRamMb() {
        try {
            ActivityManager actManager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo memInfo = new ActivityManager.MemoryInfo();
            if (actManager != null) {
                actManager.getMemoryInfo(memInfo);
                return memInfo.availMem / (1024 * 1024);
            }
        } catch (Exception ignored) {}
        return 512;
    }

    @JavascriptInterface
    public long getTotalRamMb() {
        try {
            ActivityManager actManager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo memInfo = new ActivityManager.MemoryInfo();
            if (actManager != null) {
                actManager.getMemoryInfo(memInfo);
                return memInfo.totalMem / (1024 * 1024);
            }
        } catch (Exception ignored) {}
        return 1024;
    }

    @JavascriptInterface
    public String getServerUrl() {
        return prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL);
    }

    @JavascriptInterface
    public void setServerUrl(String url) {
        if (url != null && !url.trim().isEmpty()) {
            prefs.edit().putString(KEY_SERVER_URL, url.trim()).apply();
        }
    }

    @JavascriptInterface
    public void showToast(String message) {
        if (message != null && !message.isEmpty()) {
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
        }
    }

    @JavascriptInterface
    public void vibrate(int milliseconds) {
        try {
            Vibrator v = (Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    v.vibrate(VibrationEffect.createOneShot(milliseconds, VibrationEffect.DEFAULT_AMPLITUDE));
                } else {
                    v.vibrate(milliseconds);
                }
            }
        } catch (Exception ignored) {}
    }
}
