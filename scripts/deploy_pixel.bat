@echo off
echo ======================================================================
echo           GAM.AI GOOGLE PIXEL USB DEBUGGING AUTO-DEPLOYER
echo ======================================================================

set JAVA_HOME=C:\Users\Sudo\.jdks\jbr-21.0.11
set ANDROID_HOME=C:\Users\Sudo\AppData\Local\Android\Sdk
set PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%PATH%

python scripts\build_apk.py --install

pause
