# Registers the BigLife poolgen self-loop (hourly, silent VBS wrapper, :x6 lane).
# CEO order 09-27 ~16:20 (group docs/orders.md): make poolgen a self-loop, not a
# one-shot. Judgment: state/poolgen_run.log shows consecutive timestamps < 24h.
# PATH-AGNOSTIC: every path is derived from this script's own location.
# Pure ASCII (see iteration_loop.ps1 ENCODING RULE). Idempotent via -Force.
# Re-registering refreshes the task definition - safe self-heal.
# Stagger: fires at :x6 past every hour (BigLife-OSLoop lane is :x3 every 10 min,
# FluxVerseTick :x7, BigMoney :x8 - no lane collision).
$Project = Split-Path -Parent $PSScriptRoot
$tick = Join-Path $Project 'Tools\poolgen_loop.ps1'
$vbs = Join-Path $Project 'Tools\InvisibleRunner.vbs'
if (-not (Test-Path $tick)) { Write-Output "FATAL: $tick missing"; exit 1 }
if (-not (Test-Path $vbs)) { Write-Output "FATAL: $vbs missing"; exit 1 }
$a = New-ScheduledTaskAction -Execute 'wscript.exe' `
    -Argument ('//B //nologo "' + $vbs + '" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $tick + '"') `
    -WorkingDirectory $Project
$start = Get-Date -Minute 6 -Second 0
while ($start -le (Get-Date)) { $start = $start.AddHours(1) }
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
# Preferred: S4U, not InteractiveToken - a non-interactive session means no child
# console can reach the CEO desktop (fleet silence rule, 2026-09-29 23:17).
# S4U registration needs an elevated token (0x80070005 otherwise), so fall back to
# the interactive definition instead of leaving the loop unregistered.
$p = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType S4U -RunLevel Limited
try {
    Register-ScheduledTask -TaskName 'BigLife-PoolGenLoop' -Action $a -Trigger $t -Settings $s -Principal $p -Force -ErrorAction Stop | Out-Null
} catch {
    Write-Output "WARN: S4U register denied ($($_.Exception.Message.Trim())) - falling back to interactive"
    Register-ScheduledTask -TaskName 'BigLife-PoolGenLoop' -Action $a -Trigger $t -Settings $s -Force | Out-Null
}
Write-Output "registered BigLife-PoolGenLoop (project=$Project), first fire $start"
