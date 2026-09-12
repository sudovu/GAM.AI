# GAM.AI Windows Setup & Desktop Launcher
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host '          GAM.AI WINDOWS SETUP & DESKTOP LAUNCHER          ' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir   = Split-Path -Parent $ScriptDir
$DistExe   = Join-Path $RepoDir 'dist\gam-ai.exe'

If (-not (Test-Path $DistExe)) {
    Write-Host 'Building standalone gam-ai.exe binary...' -ForegroundColor Yellow
    python "$ScriptDir\build_windows_exe.py"
}

If (Test-Path $DistExe) {
    Write-Host "Found gam-ai.exe at: $DistExe" -ForegroundColor Green
    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\GAM.AI.lnk")
    $Shortcut.TargetPath = $DistExe
    $Shortcut.WorkingDirectory = $RepoDir
    $Shortcut.Description = 'GAM.AI Micro Local-First AI Assistant'
    $Shortcut.Save()
    Write-Host "[SUCCESS] Created Desktop Shortcut on Desktop!" -ForegroundColor Green
    Write-Host 'You can now double-click the GAM.AI icon on your Desktop to launch!' -ForegroundColor Cyan
} Else {
    Write-Host 'Error building or locating gam-ai.exe' -ForegroundColor Red
}
