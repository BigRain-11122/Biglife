# Registers the BigLife QA resident service (local HTTP 127.0.0.1:8792, silent).
# PATH-AGNOSTIC: derives every path from this script's own location. Idempotent -Force.
# Self-heal: fires every 5 minutes; a live server keeps the task in Running state so
# repeated triggers are ignored (IgnoreNew), a dead server is restarted next fire.
# Zero-window law: wscript//InvisibleRunner.vbs wrapper, no console ever flashes.
$Project = Split-Path -Parent $PSScriptRoot
$qa = Join-Path $Project 'Tools\citizen_qa.py'
$vbs = Join-Path $Project 'Tools\InvisibleRunner.vbs'
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = 'D:\ComfyUI\python_embeded\python.exe' }
if (-not (Test-Path $qa)) { Write-Output "FATAL: $qa missing"; exit 1 }
if (-not (Test-Path $vbs)) { Write-Output "FATAL: $vbs missing"; exit 1 }
if (-not (Test-Path $py)) { Write-Output "FATAL: python not found"; exit 1 }
$a = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('//B //nologo "' + $vbs + '" "' + $py + '" -X utf8 "' + $qa + '" --serve --port 8792') `
    -WorkingDirectory $Project
$start = Get-Date -Second 0
while ($start -le (Get-Date)) { $start = $start.AddMinutes(5) }
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'BigLife-QA-Server' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Write-Output "registered BigLife-QA-Server (port 8792, python=$py, first fire $start)"
