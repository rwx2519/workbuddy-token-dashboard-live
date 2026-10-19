# ASCII-only script (PS 5.1 safe)
$ErrorActionPreference = "Continue"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$py   = "C:\Users\MR.SHI\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$dir  = "C:\Users\MR.SHI\WorkBuddy\2026-09-18-21-33-18"

# 1) Desktop shortcut (Edge app mode)
$ws  = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("C:\Users\MR.SHI\Desktop\TokenDashboard.lnk")
$lnk.TargetPath = $edge
$lnk.Arguments  = '--app=http://127.0.0.1:8619/'
$lnk.IconLocation = "$edge,10"
$lnk.Description = "Token Dashboard (http://127.0.0.1:8619/)"
$lnk.Save()
Write-Output "shortcut created: Desktop\TokenDashboard.lnk"

# 2) Try direct taskbar pin
$pinDir = "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
try {
  Copy-Item "C:\Users\MR.SHI\Desktop\TokenDashboard.lnk" -Destination (Join-Path $pinDir "TokenDashboard.lnk") -Force
  Write-Output "copied to taskbar pin folder"
} catch { Write-Output "pin copy failed: $_" }

# 3) Register logon task: server + live monitor + refresher
$a1 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c start `"`" /min `"$py`" `"$dir\dashboard_server.py`""
$a2 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c start `"`" /min `"$py`" `"$dir\live_tokens.py`""
$a3 = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c start `"`" /min `"$py`" `"$dir\watch_dashboard.py`""
$t  = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "TokenDashboard" -Action $a1,$a2,$a3 -Trigger $t -Force | Out-Null
Write-Output "scheduled task registered: TokenDashboard (at logon)"
