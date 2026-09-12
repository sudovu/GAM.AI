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
    private android.speech.tts.TextToSpeech tts;
    private boolean ttsReady = false;

    private static final String PREFS_NAME = "gam_ai_prefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final String DEFAULT_SERVER_URL = "http://127.0.0.1:8080";

    public GamAiBridge(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        try {
            tts = new android.speech.tts.TextToSpeech(context.getApplicationContext(), new android.speech.tts.TextToSpeech.OnInitListener() {
                @Override
                public void onInit(int status) {
                    if (status == android.speech.tts.TextToSpeech.SUCCESS) {
                        ttsReady = true;
                        try {
                            tts.setLanguage(java.util.Locale.US);
                        } catch (Exception ignored) {}
                    }
                }
            });
        } catch (Exception e) {
            android.util.Log.e("GAM_AI_TTS", "Failed to init TextToSpeech", e);
        }
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
    public boolean isNetworkConnected() {
        try {
            android.net.ConnectivityManager cm = (android.net.ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (cm != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    android.net.Network net = cm.getActiveNetwork();
                    if (net != null) {
                        android.net.NetworkCapabilities cap = cm.getNetworkCapabilities(net);
                        return cap != null && cap.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_INTERNET);
                    }
                } else {
                    android.net.NetworkInfo info = cm.getActiveNetworkInfo();
                    return info != null && info.isConnected();
                }
            }
        } catch (Exception ignored) {}
        return true;
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

    @JavascriptInterface
    public void speakText(final String text, final String lang, final float pitch, final float rate) {
        if (text == null || text.trim().isEmpty()) return;
        if (tts != null && ttsReady) {
            try {
                if (lang != null && !lang.isEmpty()) {
                    if (lang.startsWith("hi")) {
                        tts.setLanguage(new java.util.Locale("hi", "IN"));
                    } else if (lang.startsWith("ne")) {
                        int res = tts.setLanguage(new java.util.Locale("ne", "NP"));
                        if (res == android.speech.tts.TextToSpeech.LANG_MISSING_DATA || res == android.speech.tts.TextToSpeech.LANG_NOT_SUPPORTED) {
                            tts.setLanguage(new java.util.Locale("hi", "IN"));
                        }
                    } else {
                        tts.setLanguage(java.util.Locale.US);
                    }
                }
                tts.setPitch(pitch > 0 ? pitch : 1.0f);
                tts.setSpeechRate(rate > 0 ? rate : 1.0f);
                tts.speak(text, android.speech.tts.TextToSpeech.QUEUE_FLUSH, null, "GAM_AI_SPEECH_" + System.currentTimeMillis());
            } catch (Exception e) {
                android.util.Log.e("GAM_AI_TTS", "speakText error", e);
            }
        }
    }

    @JavascriptInterface
    public void stopSpeaking() {
        if (tts != null) {
            try {
                tts.stop();
            } catch (Exception ignored) {}
        }
    }

    @JavascriptInterface
    public boolean isSpeaking() {
        if (tts != null) {
            try {
                return tts.isSpeaking();
            } catch (Exception ignored) {}
        }
        return false;
    }

    @JavascriptInterface
    public String fetchHttp(String urlString) {
        if (urlString == null || urlString.trim().isEmpty()) return "";
        try {
            java.net.URL url = new java.net.URL(urlString);
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36");
            conn.setRequestProperty("Accept", "application/json, text/plain, */*");
            conn.setConnectTimeout(9000);
            conn.setReadTimeout(9000);
            conn.setInstanceFollowRedirects(true);
            int code = conn.getResponseCode();
            if (code >= 200 && code < 400) {
                java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(conn.getInputStream(), java.nio.charset.StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line).append("\n");
                }
                reader.close();
                return sb.toString();
            }
        } catch (Exception e) {
            android.util.Log.e("GAM_AI_HTTP", "fetchHttp failed for: " + urlString, e);
        }
        return "";
    }

    @JavascriptInterface
    public String fetchHttpPost(String urlString, String jsonBody) {
        if (urlString == null || urlString.trim().isEmpty()) return "";
        try {
            java.net.URL url = new java.net.URL(urlString);
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36");
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conn.setRequestProperty("Accept", "application/json, text/plain, */*");
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);
            conn.setDoOutput(true);
            if (jsonBody != null) {
                byte[] input = jsonBody.getBytes(java.nio.charset.StandardCharsets.UTF_8);
                try (java.io.OutputStream os = conn.getOutputStream()) {
                    os.write(input, 0, input.length);
                }
            }
            int code = conn.getResponseCode();
            java.io.InputStream stream = (code >= 200 && code < 400) ? conn.getInputStream() : conn.getErrorStream();
            if (stream != null) {
                java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(stream, java.nio.charset.StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line).append("\n");
                }
                reader.close();
                return sb.toString();
            }
        } catch (Exception e) {
            android.util.Log.e("GAM_AI_HTTP", "fetchHttpPost failed for: " + urlString, e);
        }
        return "";
    }

    public void destroy() {
        if (tts != null) {
            try {
                tts.stop();
                tts.shutdown();
            } catch (Exception ignored) {}
        }
    }
}
