# BigLife poolgen self-loop tick (hourly cadence, silent law).
# CEO order 09-27 ~16:20 (group docs/orders.md): poolgen must be a self-loop,
# not a one-shot. Root cause fixed here: no cron registration ever existed -
# pool_gen was pull-invoked only when a round's audit reported under-target
# buckets, so at-target water level produced zero runs and poolgen_run.log
# (a one-shot capture file) went stale. This tick closes that loop:
#   - runs pool_gen in idempotent append mode every hour
#   - at target -> zero-gen self-terminate (pools.json rewrite is
#     byte-identical: same dict order, indent=1, ensure_ascii=False)
#   - under target -> bounded refill (--budget 300 soft cap, local Ollama)
#   - ALWAYS appends one timestamped line to state/poolgen_run.log
#     (judgment: consecutive stamps < 24h apart)
#   - exceptions captured into state/poolgen_err.log (never uncaught)
# Concurrency: pool_gen holds state/pool.lock single-write lock (30-min stale);
# this tick adds its own guard so manual runs never overlap scheduled ones.
# Scope: main pool face (axes+sprite). Greet/faq/negative faces stay under the
# per-round audit gate (pool_audit runs every OS round); they can be added to
# this loop later via one line each if ever ordered.
# ENCODING RULE: pure ASCII (see iteration_loop.ps1).
param(
    [string]$Project = (Split-Path -Parent $PSScriptRoot),
    [string]$Source = 'auto'
)
$ErrorActionPreference = 'Continue'
Set-Location $Project
$stateDir = Join-Path $Project 'state'
New-Item -ItemType Directory -Force $stateDir | Out-Null
$runLog = Join-Path $stateDir 'poolgen_run.log'
$errLog = Join-Path $stateDir 'poolgen_err.log'
$lock = Join-Path $stateDir 'poolgen-loop.lock'

# single-instance guard: fresh lock (<10 min) = another tick in flight
if (Test-Path $lock) {
    $age = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes
    if ($age -lt 10) { exit 0 }
}
Set-Content -Path $lock -Value $PID -Encoding ASCII

try {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $gen = Join-Path $Project 'Tools\pool_gen.py'
    if (-not (Test-Path $gen)) {
        Add-Content -Path $errLog -Value "$ts poolgen_loop: FATAL pool_gen.py missing" -Encoding UTF8
        exit 0
    }
    $out = ''
    $code = 1
    try {
        $out = & python -X utf8 $gen --append --target 18 --sprite-target 12 --budget 300 2>&1
        $code = $LASTEXITCODE
    } catch {
        $code = 1
        $out = "EXCEPTION: $_"
    }
    if ($code -ne 0 -and -not (($out -join ' ') -match 'TOTAL=\d+')) {
        Add-Content -Path $errLog -Value "$ts poolgen_loop: exit=$code $($out -join ' | ')" -Encoding UTF8
    }
    $summary = ''
    foreach ($ln in $out) { if ($ln -match 'TOTAL=\d+') { $summary = "$ln" } }
    if (-not $summary) { $summary = [string]($out | Select-Object -Last 1) }
    Add-Content -Path $runLog -Value "=== $ts poolgen_loop tick src=$Source exit=$code === $summary" -Encoding UTF8
    # bounded log: trim to last 2000 lines when over ~256 KB (runtime log, not canon)
    if ((Test-Path $runLog) -and ((Get-Item $runLog).Length -gt 262144)) {
        $keep = Get-Content $runLog -Tail 2000
        Set-Content -Path $runLog -Value $keep -Encoding UTF8
    }
} finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
}
exit 0
