# voice_synth.ps1 - local SAPI voice synthesis for citizen clips (voice line v0).
# Local-compute law compliant: SAPI on-box, zero cloud, zero tokens.
# Reads: census/export/citizens-light.jsonl (creed/name) +
#        census/export/citizen-voice.jsonl (params; auto-regenerated if missing).
# Params are deterministic per citizen (Tools/voice_manifest.py), clips are
# engine output (no byte-determinism claim - see cognition/VOICE-POOL.md).
# Usage:
#   .\voice_synth.ps1 -Ids "C-00010,C-00017" -OutDir ..\census\export\voice-samples
param(
    [Parameter(Mandatory = $true)][string]$Ids,
    [string]$OutDir = "",
    [switch]$Cache
)
$ErrorActionPreference = "Stop"
$Tool = $PSScriptRoot
$Co = Split-Path -Parent $Tool
$LightPath = Join-Path $Co "census\export\citizens-light.jsonl"
$VoicePath = Join-Path $Co "census\export\citizen-voice.jsonl"
if (-not $OutDir) {
    $OutDir = Join-Path $Co ("census\export\" + $(if ($Cache) { "voice-cache" } else { "voice-samples" }))
}
if (-not (Test-Path $LightPath)) { Write-Output "FATAL: missing $LightPath"; exit 1 }
if (-not (Test-Path $VoicePath)) {
    Write-Output "voice manifest missing - regenerating (R3 face)"
    $py = "python"
    & $py -X utf8 (Join-Path $Tool "voice_manifest.py") | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output "FATAL: voice_manifest.py failed"; exit 1 }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# rate percent -> SAPI absspeed (-10..10)
function Get-AbsSpeed([int]$pct) {
    $v = [Math]::Round($pct / 2.5)
    if ($v -gt 10) { $v = 10 }
    if ($v -lt -10) { $v = -10 }
    return $v
}
function Escape-Xml([string]$s) {
    return ($s -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;' -replace '"', '&quot;' -replace "'", '&apos;')
}

$want = $Ids -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$made = @()
foreach ($cid in $want) {
    $vrow = $null; $lrow = $null
    foreach ($ln in [System.IO.File]::ReadLines($VoicePath)) {
        if ($ln -notmatch $cid) { continue }
        $vrow = $ln | ConvertFrom-Json; if ($vrow.id -eq $cid) { break }
    }
    foreach ($ln in [System.IO.File]::ReadLines($LightPath)) {
        if ($ln -notmatch $cid) { continue }
        $lrow = $ln | ConvertFrom-Json; if ($lrow.id -eq $cid) { break }
    }
    if (-not $vrow -or -not $lrow) { Write-Output "SKIP $cid (not found)"; continue }
    if ($vrow.blocked) { Write-Output "SKIP $cid (honored seat, persona-reserved)"; continue }
    $creed = [string]$lrow.creed
    if ($creed.Length -gt 40) { $creed = $creed.Substring(0, 40) }
    $text = if ($creed) { "$creed" + [char]0x6211 + [char]0x662F + "$($lrow.name)" + [char]0x3002 } else { [char]0x6211 + [char]0x662F + "$($lrow.name)" + [char]0x3002 }
    $ssml = "<pitch absmiddle=`"$($vrow.voice.pitch)`"/><rate absspeed=`"$(Get-AbsSpeed $vrow.voice.rate)`"/><volume level=`"$($vrow.voice.vol)`"/>" + (Escape-Xml $text)
    $wav = Join-Path $OutDir "$cid.wav"
    $fs = New-Object -ComObject SAPI.SpFileStream
    $fs.Open($wav, 3, 0)   # 3 = SSFMCreateForWrite
    $v = New-Object -ComObject SAPI.SpVoice
    $v.AudioOutputStream = $fs
    $null = $v.Speak($ssml, 8)   # 8 = SPF_IS_XML, synchronous
    $fs.Close()
    $bytes = (Get-Item $wav).Length
    $made += [ordered]@{
        id = $cid; name = $lrow.name; species = $lrow.species
        pitch = $vrow.voice.pitch; rate = $vrow.voice.rate; vol = $vrow.voice.vol
        text = $text; file = "$cid.wav"; bytes = $bytes
    }
    Write-Output "OK $cid $($lrow.name) -> $wav ($bytes B)"
}
if ($made.Count -gt 0) {
    $mf = Join-Path $OutDir "manifest.json"
    $old = @()
    if (Test-Path $mf) { $old = @(Get-Content $mf -Raw -Encoding UTF8 | ConvertFrom-Json) }
    $all = @($old) + @($made)
    $all | ConvertTo-Json -Depth 5 | Set-Content $mf -Encoding UTF8
    Write-Output ("clips=" + $made.Count + " manifest=" + $mf)
}
