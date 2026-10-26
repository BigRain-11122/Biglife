# Registers the BigLife 10-minute OS loop (silent VBS wrapper, staggered :x3 lane).
# PATH-AGNOSTIC: every path is derived from this script's own location.
# Pure ASCII (see iteration_loop.ps1 ENCODING RULE). Idempotent via -Force.
# Re-registering refreshes the task definition - safe self-heal.
$Project = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $Project 'Tools\iteration_loop.ps1'
$vbs = Join-Path $Project 'Tools\InvisibleRunner.vbs'
if (-not (Test-Path $launcher)) { Write-Output "FATAL: $launcher missing"; exit 1 }
if (-not (Test-Path $vbs)) { Write-Output "FATAL: $vbs missing"; exit 1 }
$a = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('//B //nologo "' + $vbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '"') `
    -WorkingDirectory $Project
# stagger: fire at :x3 past every 10 minutes (FluxVerseTick uses :x7, BigMoney :x8)
$start = Get-Date -Minute 3 -Second 0
while ($start -le (Get-Date)) { $start = $start.AddMinutes(10) }
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 25)
# Preferred: S4U, not InteractiveToken - a non-interactive session means no child
# console can reach the CEO desktop (fleet silence rule, 2026-09-29 23:17).
# S4U registration needs an elevated token (0x80070005 otherwise), so fall back to
# the interactive definition instead of leaving the loop unregistered.
$p = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType S4U -RunLevel Limited
try {
    Register-ScheduledTask -TaskName 'BigLife-OSLoop' -Action $a -Trigger $t -Settings $s -Principal $p -Force -ErrorAction Stop | Out-Null
} catch {
    Write-Output "WARN: S4U register denied ($($_.Exception.Message.Trim())) - falling back to interactive"
    Register-ScheduledTask -TaskName 'BigLife-OSLoop' -Action $a -Trigger $t -Settings $s -Force | Out-Null
}
Write-Output "registered BigLife-OSLoop (project=$Project), first fire $start"
