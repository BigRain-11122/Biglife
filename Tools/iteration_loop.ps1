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
# 2026-11-17 CEO order: run resident generation in the daytime window too.
# Default law (D-20261020-02) still yields 09:00-19:00; this env is the explicit
# opt-out the CEO asked for. Remove these four lines to restore pure yielding.
$env:BIGLIFE_IGNORE_YIELD_WINDOW = '1'
$env:BIGLIFE_MODEL = 'qwen3.5:9b'
$env:BIGLIFE_LLM_URL = 'http://127.0.0.1:11434/v1/chat/completions'
$env:BIGLIFE_VRAM_LIMIT = '0.85'
# 2026-11-19 evening: 3 -> 4. GPU util sits at ~15% while two ring segments run,
# i.e. the card is idle between requests, not saturated. One more in-flight ring
# segment keeps the two ollama slots packed. VRAM is unchanged (same model, the
# slots are fixed by OLLAMA_NUM_PARALLEL); revert to 3 if throughput does not rise.
# 2026-11-20 13:0x measured with the tuned server: 2 parallel short generations
# = 48/minute (~2,880/hour) wall-clock, while production only reached ~720/hour.
# So the card is NOT the limit - the request feed is: two slots idle between
# seats. Queued requests cost no VRAM, so raise the segment count to 6 (5 ring
# segments + 1 other-face) and keep both slots permanently fed.
$env:BIGLIFE_CONCURRENCY = '6'
Set-Location $Project

# 2026-11-17 CEO order: no cross-stealing. Layered schedule instead of a hard skip.
#   training owns the GPU  -> LLM lanes yield, but the zero-GPU faces still run
#                            (daily rebuild / lint / qc / event-replay gate)
#   training idle          -> normal round (LLM production allowed)
# Rationale: 12G card, training ~7.5G + 9B ~6.6G cannot coexist (observed twice:
# TRAIN EXITCODE -1, no traceback, at step 154/1632). An idle round wasted 10 min;
# running the deterministic faces keeps the day's visible surfaces fresh for free.
$__train = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'train_network' }
if ($__train) {
    # 2026-11-17 FIX: the watchdog judges liveness by logs/os-loop/run_*.log mtime,
    # and this branch exited before that file was created - so training hours read
    # as "dead" to any monitor. Create the run log here and append each face result.
    $__logDir = Join-Path $Project 'logs\os-loop'
    New-Item -ItemType Directory -Force $__logDir | Out-Null
    $__runLog = Join-Path $__logDir ('run_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
    "yield-llm: training owns GPU - deterministic faces only" | Out-File -FilePath $__runLog -Encoding UTF8
    Write-Output "$(Get-Date -Format 'HH:mm:ss') yield-llm: training owns GPU - deterministic faces only"
    $__py = 'C:\Users\sjs20\AppData\Local\Programs\Python\Python314\python.exe'
    foreach ($__job in @(
        @{ n = 'round_daily'; a = @('-X', 'utf8', 'Tools\round_daily.py', '--run') },
        @{ n = 'ring_lint';   a = @('-X', 'utf8', 'Tools\ring_lint.py', '--today-only') },
        @{ n = 'qc_census';   a = @('-X', 'utf8', 'Tools\qc_census.py') },
        @{ n = 'events_gate'; a = @('-X', 'utf8', 'Tools\events_refresh.py', '--gate') }
    )) {
        try {
            & $__py @($__job.a) 2>&1 | Out-Null
            Write-Output "$(Get-Date -Format 'HH:mm:ss')   det-face $($__job.n) rc=$LASTEXITCODE"
            Add-Content -Path $__runLog -Encoding UTF8 -Value (
                "$(Get-Date -Format 'HH:mm:ss')   det-face $($__job.n) rc=$LASTEXITCODE")
        } catch {
            Write-Output "$(Get-Date -Format 'HH:mm:ss')   det-face $($__job.n) failed"
            Add-Content -Path $__runLog -Encoding UTF8 -Value (
                "$(Get-Date -Format 'HH:mm:ss')   det-face $($__job.n) FAILED")
        }
    }
    # 2026-11-17 FIX: this branch exits BEFORE Beat() is defined, so nothing wrote
    # a heartbeat during training and the liveness check went silent (observed:
    # heartbeat.txt frozen at 17:13:49 for 65 min while the loop fired every 10).
    # Write the heartbeat inline instead of depending on the later-defined function.
    # NOTE: this file MUST stay pure ASCII (PS 5.1 decodes BOM-less .ps1 as GBK).
    try {
        $__hb = Join-Path $Project 'state\heartbeat.txt'
        New-Item -ItemType Directory -Force (Split-Path -Parent $__hb) | Out-Null
        Add-Content -Path $__hb -Encoding UTF8 -Value (
            "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') os-loop: yield-llm training (deterministic faces only)")
    } catch { Write-Output "heartbeat write failed (non-blocking): $_" }
    exit 0
}

$logDir = Join-Path $Project 'logs\os-loop'
New-Item -ItemType Directory -Force $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runLog = Join-Path $logDir "run_$stamp.log"
$roundOut = Join-Path $logDir "round_$stamp.out"
$roundErr = Join-Path $logDir "round_$stamp.err"
$heart = Join-Path $Project 'state\heartbeat.txt'

# v3 (2026-10-28 group-root resolution, decisions D-20261028-03 / D-20261028-04):
# resolve the group repo root ONLY through `git rev-parse --show-toplevel` over
# the repo root and its parents. Never assume a fixed relative depth (`..\..`)
# and never trust a hard-coded mirror path: a stale mirror (D:\FluxGroup)
# resolves successfully yet silently serves an old world (false green).
# Several candidates may resolve (each nested repo reports its own top); the
# live tree wins by cph4\evolution-ledger.md mtime. Returns $null when nothing
# resolves - callers must then fail closed.
function Resolve-GroupRoot([string]$Start) {
    $tops = New-Object System.Collections.Generic.List[string]
    $cur = $Start
    for ($i = 0; $i -lt 6 -and $cur; $i++) {
        $top = $null
        try { $top = (& git -C $cur rev-parse --show-toplevel 2>$null | Select-Object -First 1) } catch { $top = $null }
        if ($top) {
            $top = $top.Trim()
            if ((Test-Path (Join-Path $top 'cph4')) -and -not ($tops -contains $top)) { $tops.Add($top) }
        }
        $cur = Split-Path -Parent $cur
    }
    $best = $null
    $bestTicks = -1L
    foreach ($t in $tops) {
        $ledger = Join-Path $t 'cph4\evolution-ledger.md'
        $ticks = 0L
        if (Test-Path $ledger) { $ticks = (Get-Item $ledger).LastWriteTimeUtc.Ticks }
        if ($ticks -gt $bestTicks) { $bestTicks = $ticks; $best = $t }
    }
    return $best
}

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
    # 2026-11-17 CEO order "fill resident generation across 7x24": pump the window
    # with deterministic batches BEFORE spending it on an agent round (an agent
    # usually ran one --batch 3 in ~1 min, leaving ~9 of 10 minutes idle).
    # Single source of truth for the gate: resident_loop.admit (training /
    # swap-out / loaded model / vram / mem). Gate closed -> run the zero-GPU
    # faces and stop; never fall through to an agent round that would fight for
    # the same VRAM (that fight is what killed training twice today).
    $__py = 'C:\Users\sjs20\AppData\Local\Programs\Python\Python314\python.exe'
    $__pump = Join-Path $Project 'Tools\produce_pump.py'
    $__detFaces = @(
        @{ n = 'round_daily'; a = @('-X', 'utf8', 'Tools\round_daily.py', '--run') },
        @{ n = 'ring_lint';   a = @('-X', 'utf8', 'Tools\ring_lint.py', '--today-only') },
        @{ n = 'qc_census';   a = @('-X', 'utf8', 'Tools\qc_census.py') },
        @{ n = 'events_gate'; a = @('-X', 'utf8', 'Tools\events_refresh.py', '--gate') }
    )
    # 2026-11-18 Steward seat: decide-and-act per the standing charter.
    # Scope is data/ops only (persona repair, orphan lock, batch policy, task
    # restart); it never edits source code. Heavy scans self-throttle to 1/hour
    # inside the script, so calling it every cycle is cheap. Non-blocking.
    $__steward = Join-Path $Project 'Tools\resident_steward.py'
    if (Test-Path $__steward) {
        try {
            & $__py -X utf8 $__steward --decide 2>&1 |
                Out-File -FilePath $runLog -Append -Encoding UTF8
            Log "steward rc=$LASTEXITCODE"
        } catch { Log "steward failed (non-blocking): $_" }
    }
    # Persona rewrite backlog (CEO 2026-11-20: all local compute into optimisation).
    # Priority ladder (2026-11-20 data-driven, not fixed):
    #   Today's rings are the baseline every resident must get -> they keep the
    #   machine until the due pool runs dry. Only then does the one-off persona
    #   backlog take all the capacity. Proxy for "rings done" = the loop log's
    #   most recent window reported "rings exhausted" (the pump prints it when a
    #   batch hands over to the scheduler).
    #   rings still running -> 1 shard (240/h, leaves 2 ollama slots to the pump)
    #   rings exhausted     -> 3 shards (720/h, backlog devours the window)
    $__tail = ''
    $__ringlog = Join-Path $Project 'state\resident-loop.log'
    if (Test-Path $__ringlog) {
        $__tail = (Get-Content $__ringlog -Tail 40 -Encoding UTF8 -ErrorAction SilentlyContinue) -join "`n"
    }
    if ($__tail -match 'rings exhausted') { $__shards = 3 } else { $__shards = 1 }
    $__rw = Join-Path $Project 'Tools\rewrite_persona.py'
    if (Test-Path $__rw) {
        for ($__s = 0; $__s -lt $__shards; $__s++) {
            try {
                Start-Process -FilePath $__py -WindowStyle Hidden -ArgumentList @(
                    '-X', 'utf8', $__rw, '--limit', '40',
                    '--shard', "$__s", '--shards', "$__shards") | Out-Null
            } catch { Log "persona-rewrite shard $__s failed: $_" }
        }
        Log "persona-rewrite: $__shards shard(s) launched async"
    }
    # Batch size comes from batch-policy.json so the steward's decisions actually
    # land (before this, the pump was pinned to 8 and the policy was decorative).
    $__batch = 8
    try {
        $__pol = Get-Content (Join-Path $Project 'Tools\batch-policy.json') -Raw -ErrorAction Stop |
            ConvertFrom-Json
        if ($__pol.batch) { $__batch = [int]$__pol.batch }
    } catch { }
    if (Test-Path $__pump) {
        $__gateOpen = $false
        $__gateWhy = ''
        try {
            # 2026-11-18 22:4x: dry-run's own reason was thrown away, so a 1h45m
            # closed gate left only "yield busy" in the heartbeat and no way to
            # tell whether it was VRAM, memory, a foreign loaded model or swap.
            # Capture it and ride it into the heartbeat (truncated, ASCII-safe path).
            $__why = (& $__py -X utf8 $__pump --dry-run 2>&1 | Out-String).Trim()
            $__gateOpen = ($LASTEXITCODE -eq 0)
            if (-not $__gateOpen) {
                $__gateWhy = ($__why -replace "\s+", ' ')
                if ($__gateWhy.Length -gt 120) { $__gateWhy = $__gateWhy.Substring(0, 120) }
            }
        } catch { $__gateOpen = $false }
        if ($__gateOpen) {
            Log 'pump: gate open - filling window with deterministic batches (7x24)'
            try {
                # 2026-11-19 13:1x evidence: a 9-minute pump window plus pre-steps
            # (steward/behavior/startup) and post-steps (commit/export) measured
            # 10-11 minutes - LONGER than the 10-minute trigger interval - so the
            # next trigger hit a still-running instance and was swallowed by
            # MultipleInstances=IgnoreNew. Measured window gaps alternated between
            # 599s and 1140-1221s: every second round was lost, halving throughput
            # (what the user saw as "stopped again"). Fix is headroom, not length:
            # shrink the window to 7 minutes so a whole round fits inside 10.
            & $__py -X utf8 $__pump --minutes 7 --batch $__batch 2>&1 |
                    Out-File -FilePath $runLog -Append -Encoding UTF8
                Log "pump finished rc=$LASTEXITCODE"
            } catch { Log "pump failed (non-blocking): $_" }
            Beat 'pump done'
            exit 0
        }
        Log 'pump: gate closed (machine busy) - zero-GPU faces only, agent suppressed'
        foreach ($__job in $__detFaces) {
            try {
                & $__py @($__job.a) 2>&1 | Out-Null
                Log "  det-face $($__job.n) rc=$LASTEXITCODE"
            } catch { Log "  det-face $($__job.n) failed" }
        }
        Beat "yield busy: $__gateWhy"
        exit 0
    }
    $codelyPath = (Get-Command codely -ErrorAction SilentlyContinue).Source
    if (-not $codelyPath) { Log 'FATAL: codely not on PATH for this context'; Beat 'error codely missing'; exit 2 }
    $promptFile = Join-Path $Project 'Tools\iteration_prompt.txt'
    if (-not (Test-Path $promptFile)) { Log 'FATAL: iteration_prompt.txt missing'; Beat 'error prompt file missing'; exit 2 }
    $prompt = (Get-Content -Raw -Encoding UTF8 $promptFile).Trim()
    if ($prompt.Length -lt 50) { Log 'FATAL: iteration_prompt.txt too short'; Beat 'error prompt file empty'; exit 2 }
    if ($prompt.Contains('"')) { $prompt = $prompt.Replace('"', "'") }
    $argLine = '-y -p "' + $prompt + '"'
    Log "spawning headless round (hard-cap ${RoundTimeoutMinutes}min, silence-kill ${RoundSilenceMinutes}min, prompt_chars=$($prompt.Length))"
    # T0 CLOUD-OFF guard (CEO 2026-10-20): automation is local-only; never spawn the cloud CLI.
    $__co = Resolve-GroupRoot $Project
    if (-not $__co) {
        # Fail closed (D-20261028-03 @3): an unresolvable group root counts as
        # cloud-off, so no round is spawned against an unknown world.
        Log 'CLOUD-OFF guard: group root unresolved -> fail-closed, round suppressed'
        exit 0
    }
    # R35 repair (2026-11-12, BigLife patrol seat; supersedes R25-1/R34-1):
    # the v3 guard above already fails closed when the group root cannot be
    # resolved. The second block that lived here (`if ($__co) { ... exit 0 }`)
    # fired on the NORMAL path (root resolved), so every tick suppressed itself
    # and Start-Process below was unreachable - 2,553 zero-product rounds since
    # 2026-10-28 05:04:25. Removed: a resolved world spawns the round again.
    # R35: a spawn that throws must leave a log row + non-zero task result
    # (silent throw + rc=0 is what hid this defect for 15 days).
    try {
        $p = Start-Process -FilePath $codelyPath -ArgumentList $argLine -WorkingDirectory $Project -PassThru -NoNewWindow -RedirectStandardOutput $roundOut -RedirectStandardError $roundErr -ErrorAction Stop
    } catch {
        Log "FATAL: Start-Process failed: $($_.Exception.Message)"
        Beat 'error spawn-failed'
        exit 3
    }
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
