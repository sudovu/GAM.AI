# Proguard rules for GAM.AI Android Application
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-keep class com.gamai.app.GamAiBridge { *; }
