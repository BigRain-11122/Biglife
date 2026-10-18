# BigLife OS loop - headless round launcher (10-min cadence, silent law).
# Ported 2026-09-23 from the proven BigMoney pattern (Tools/iteration_loop.ps1).
#
# v2 (2026-10-19 liveness-budget port, group decision D-20261019-04, fleet
# dead-window root-cure rollout): the 2026-09-23 port carried a 20-min
# wall-clock kill (MiniGame short-round legacy). Legitimate long rounds
# crossing it were tree-killed mid-flight (heartbeat "round timeout killed
# (age over 20min)" rows on 10-17/10-18). v2 kills only on EVIDENCE:
# $RoundSilenceMinutes of ZERO output activity (true hang) or the
# $RoundTimeoutMinutes hard cap; kills are recursive tree kills with a
# post-kill self-check. Canonical source: quant/bigmoney/Tools/
# iteration_loop.ps1 @ 945c3f60, adapted to this repo's log paths.
#
# ENCODING RULE: this file must stay PURE ASCII. powershell.exe 5.1 decodes
# BOM-less .ps1 as ANSI/GBK. All Chinese content lives in
# Tools\iteration_prompt.txt (UTF-8, read at runtime with explicit -Encoding).
#
# Self-heal recipe (run from an agent round when Get-ScheduledTask
# BigLife-OSLoop is missing - path-agnostic, works on any machine):
#   powershell -NoProfile -ExecutionPolicy Bypass -File Tools/register_loop_task.ps1
param(
    [string]$Project = (Split-Path -Parent $PSScriptRoot),
    [int]$LockMaxAgeMinutes = 45,
    [int]$RoundTimeoutMinutes = 240,
    [int]$RoundSilenceMinutes = 25
)
$ErrorActionPreference = 'Continue'
Set-Location $Project
$logDir = Join-Path $Project 'logs\os-loop'
New-Item -ItemType Directory -Force $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runLog = Join-Path $logDir "run_$stamp.log"
$roundOut = Join-Path $logDir "round_$stamp.out"
$roundErr = Join-Path $logDir "round_$stamp.err"
$heart = Join-Path $Project 'state\heartbeat.txt'

function Log([string]$m) {
    $line = "$(Get-Date -Format 'HH:mm:ss') $m"
    Write-Output $line
    Add-Content -Path $runLog -Value $line -Encoding UTF8
}
function Beat([string]$m) {
    New-Item -ItemType Directory -Force (Split-Path -Parent $heart) | Out-Null
    Add-Content -Path $heart -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') os-loop: $m" -Encoding UTF8
}

# v2 kill face (D-20261019-04 port): recursive tree kill + post-kill
# self-check. One-level kills left deep-tree grandchildren alive in the BM
# 2026-10-17 starvation case - collect the descendant chain breadth-first
# (seen-set guards PID-reuse cycles, 256-node bound), kill deepest-first,
# then re-scan: any survivor logs a ZOMBIE_SURVIVOR row (never silent).
function Kill-RoundTree([int]$rootPid) {
    $seen = @{}
    $frontier = @($rootPid)
    $ordered = @()
    while ($frontier.Count -gt 0 -and $ordered.Count -lt 256) {
        $next = @()
        foreach ($pp in $frontier) {
            $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$pp" -ErrorAction SilentlyContinue)
            foreach ($k in $kids) {
                if (-not $seen.ContainsKey($k.ProcessId)) {
                    $seen[$k.ProcessId] = $true
                    $ordered += $k.ProcessId
                    $next += $k.ProcessId
                }
            }
        }
        $frontier = $next
    }
    if ($ordered.Count -gt 1) { [array]::Reverse($ordered) }
    foreach ($procId in $ordered) { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue }
    Stop-Process -Id $rootPid -Force -ErrorAction SilentlyContinue
    return ,$ordered
}
function Stop-RoundTreeChecked([int]$rootPid, [string]$why) {
    $killed = Kill-RoundTree $rootPid
    Log "kill tree ($why): root=$rootPid descendants_killed=$($killed.Count)"
    Start-Sleep -Seconds 2
    $survivors = 0
    foreach ($procId in $killed) {
        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
            $survivors++
            Log "ZOMBIE_SURVIVOR pid=$procId survived tree-kill ($why) -- audit lane face"
        }
    }
    if ($survivors -eq 0) { Log "kill tree self-check ($why): 0 survivors (child-clear verified)" }
    return $survivors
}

# ---- single-instance guard v2 (group standard D-20260925-03:
# lock holds PID, liveness probe before takeover, CreateNew atomic grab) ----
$lock = Join-Path $logDir 'round.lock'
$lockProcPattern = 'powershell|pwsh|codely|node|python'
function Test-RoundPidAlive([int]$procId) {
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if (-not $p) { return $false }
    return ($p.ProcessName -match $lockProcPattern)
}
if (Test-Path $lock) {
    $raw = ''
    try { $raw = (Get-Content -Raw $lock -ErrorAction Stop).Trim() } catch {}
    $oldPid = 0
    if ([int]::TryParse($raw, [ref]$oldPid) -and $oldPid -gt 0) {
        if (Test-RoundPidAlive $oldPid) {
            Log "skip: previous round still running (pid=$oldPid alive)"; Beat 'skip (round in flight)'; exit 0
        }
        Log "stale lock pid=$oldPid not alive - taking over"
    } else {
        # legacy timestamp-format lock (pre-v2): age fallback only for the transition
        $age = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes
        if ($age -lt $LockMaxAgeMinutes) { Log "skip: legacy lock fresh (age=$([int]$age)min)"; Beat 'skip (round in flight)'; exit 0 }
        Log "legacy lock expired (age=$([int]$age)min) - taking over"
    }
    Remove-Item -Path $lock -Force -ErrorAction SilentlyContinue
}
try {
    $fs = New-Object System.IO.FileStream($lock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $sw = New-Object System.IO.StreamWriter($fs)
    $sw.Write($PID.ToString())
    $sw.Dispose()
} catch {
    Log "skip: lock atomically grabbed by a concurrent launcher (CreateNew lost)"; Beat 'skip (round in flight)'; exit 0
}

try {
    Log "BigLife os-loop round start $stamp"
    # T-20260925-11 (group decision D-20260925-08): behavior regen rhythm -
    # deterministic bucket/weather change check each tick; rerun only on
    # change; failure is non-blocking for the agent round.
    try {
        $behAuto = & python -X utf8 (Join-Path $Project 'Tools\behavior.py') --auto 2>&1
        Log "behavior-auto: $behAuto"
    } catch { Log "behavior-auto failed (non-blocking): $_" }
    $codelyPath = (Get-Command codely -ErrorAction SilentlyContinue).Source
    if (-not $codelyPath) { Log 'FATAL: codely not on PATH for this context'; Beat 'error codely missing'; exit 2 }
    $promptFile = Join-Path $Project 'Tools\iteration_prompt.txt'
    if (-not (Test-Path $promptFile)) { Log 'FATAL: iteration_prompt.txt missing'; Beat 'error prompt file missing'; exit 2 }
    $prompt = (Get-Content -Raw -Encoding UTF8 $promptFile).Trim()
    if ($prompt.Length -lt 50) { Log 'FATAL: iteration_prompt.txt too short'; Beat 'error prompt file empty'; exit 2 }
    if ($prompt.Contains('"')) { $prompt = $prompt.Replace('"', "'") }
    $argLine = '-y -p "' + $prompt + '"'
    Log "spawning headless round (hard-cap ${RoundTimeoutMinutes}min, silence-kill ${RoundSilenceMinutes}min, prompt_chars=$($prompt.Length))"
    $p = Start-Process -FilePath $codelyPath -ArgumentList $argLine -WorkingDirectory $Project -PassThru -NoNewWindow -RedirectStandardOutput $roundOut -RedirectStandardError $roundErr
    $null = $p.Handle
    # hold the worker pid in the lock: if this launcher is hard-killed, an
    # orphaned worker is still detected as alive by the next tick (D-20260925-03)
    try { Set-Content -Path $lock -Value $p.Id -Encoding ASCII } catch {}
    # v2 liveness budget (D-20261019-04): poll in 30s slices. "Activity" = the
    # round's stdout/stderr redirect files gaining bytes. Kill ONLY on evidence
    # of a hang (silent for $RoundSilenceMinutes) or the $RoundTimeoutMinutes
    # hard cap; a productive long round streams output and is never killed by
    # wall clock alone.
    $startAt = Get-Date
    $lastMove = Get-Date
    $lastSize = -1L
    while (-not $p.WaitForExit(30000)) {
        $size = 0L
        foreach ($f in @($roundOut, $roundErr)) {
            try { $fi = Get-Item $f -ErrorAction SilentlyContinue; if ($fi) { $size += $fi.Length } } catch { }
        }
        if ($size -ne $lastSize) { $lastSize = $size; $lastMove = Get-Date }
        $silentMin = ((Get-Date) - $lastMove).TotalMinutes
        $totalMin = ((Get-Date) - $startAt).TotalMinutes
        if ($silentMin -ge $RoundSilenceMinutes) {
            Log "ROUND SILENCE-KILL: no output for $([int]$silentMin)min (total $([int]$totalMin)min) - killing headless process tree"
            try { $null = Stop-RoundTreeChecked $p.Id 'silence-kill' } catch { Log "kill failed: $_" }
            Beat "round silence-killed (no output $([int]$silentMin)min, total $([int]$totalMin)min)"
            exit 3
        }
        if ($totalMin -ge $RoundTimeoutMinutes) {
            Log "ROUND HARD-CAP after ${RoundTimeoutMinutes}min - killing headless process tree"
            try { $null = Stop-RoundTreeChecked $p.Id 'hard-cap' } catch { Log "kill failed: $_" }
            Beat "round hard-cap killed (age over ${RoundTimeoutMinutes}min)"
            exit 3
        }
    }
    $p.Refresh()
    Log "headless round finished exit=$($p.ExitCode) (ran $([int]((Get-Date) - $startAt).TotalMinutes)min)"
    Beat "round done exit=$($p.ExitCode)"
    exit $p.ExitCode
}
finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
}
