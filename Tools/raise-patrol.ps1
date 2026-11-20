# BigLife patrol frequency raiser - RUN AS ADMINISTRATOR (one click, idempotent).
#
# Why this file exists: the BigLife-* tasks are registered as S4U, and changing a
# trigger on an S4U task needs elevation (Set-ScheduledTask -> 0x80070005,
# schtasks /Change -> prompts for the account password). So the agent cannot raise
# its own patrol cadence; this script is the human-run half of that contract.
#
# What it does (idempotent, read-back verified, no task re-registration):
#   BigLife-Watchdog        -> every 2 minutes   (was 30)
#   BigLife-HealthSweep     -> every 10 minutes  (was 30)
#   BigLife-QualitySentinel -> every 20 minutes  (was 60)
# It only edits Trigger.Repetition.Interval, so S4U logon type, the VBS hidden
# wrapper and the task actions are all preserved.
#
# Usage: right-click -> Run with PowerShell (as administrator), or from an
# elevated prompt:  powershell -NoProfile -ExecutionPolicy Bypass -File raise-patrol.ps1

$ErrorActionPreference = 'Stop'
$plan = [ordered]@{
    'BigLife-Watchdog'        = 'PT2M'
    'BigLife-HealthSweep'     = 'PT10M'
    'BigLife-QualitySentinel' = 'PT20M'
}

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$pr = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host 'NOT ADMIN: re-run this script with "Run as administrator".' -ForegroundColor Red
    exit 1
}

$fail = 0
foreach ($name in $plan.Keys) {
    $want = $plan[$name]
    try {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction Stop
        $task.Triggers[0].Repetition.Interval = $want
        Set-ScheduledTask -TaskName $name -Trigger $task.Triggers | Out-Null
        $got = (Get-ScheduledTask -TaskName $name).Triggers[0].Repetition.Interval
        $logon = (Get-ScheduledTask -TaskName $name).Principal.LogonType
        if ($got -eq $want) {
            Write-Host ("OK   {0,-24} {1}  (logon={2})" -f $name, $got, $logon) -ForegroundColor Green
        } else {
            Write-Host ("WARN {0,-24} wanted {1}, got {2}" -f $name, $want, $got) -ForegroundColor Yellow
            $fail = 1
        }
    } catch {
        Write-Host ("FAIL {0,-24} {1}" -f $name, $_.Exception.Message) -ForegroundColor Red
        $fail = 1
    }
}

Write-Host ''
Write-Host 'Verify any time with:  Get-ScheduledTask BigLife-* | % { $_.TaskName + " " + $_.Triggers[0].Repetition.Interval }'
exit $fail
