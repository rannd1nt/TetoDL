#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive binary test suite for TetoDL on Windows.
    Produces JUnit XML for GitHub Actions integration.
.DESCRIPTION
    Tests every CLI flag combination against a real YouTube URL.
    Builds a JUnit XML report at $PSScriptRoot/../test-results.xml.
.PARAMETER Binary
    Path to the tetodl.exe binary.
.PARAMETER TestUrl
    Single-video YouTube URL (short, good for testing all features).
.PARAMETER PlaylistUrl
    Playlist YouTube URL.
.PARAMETER Timeout
    Per-test timeout in seconds.
.PARAMETER YtdlpUpdate
    If set, also runs yt-dlp update check test (requires network).
#>
param(
    [Parameter(Mandatory)][string]$Binary,
    [string]$TestUrl = "https://youtu.be/jQhArAdrAtU",
    [string]$PlaylistUrl = "https://youtube.com/playlist?list=PLCmop9hr8TtM",
    [int]$Timeout = 120,
    [bool]$YtdlpUpdate = $false
)

$ErrorActionPreference = "Stop"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
$outDir = Join-Path (Join-Path $PSScriptRoot "..") "test-results"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outDir = Resolve-Path $outDir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
$passed = @()
$failed = @()
$skipped = @()
$startTime = Get-Date

function Run-Test($name, $cliArgs, [int]$timeout = $Timeout) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan

    $result = [ordered]@{ Name = $name; Status = "pass"; Message = ""; Output = "" }

    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "cmd.exe"
        $psi.Arguments = "/c `"$Binary $cliArgs`""
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
        $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

        $proc = [System.Diagnostics.Process]::Start($psi)
        $output = $proc.StandardOutput.ReadToEnd() + $proc.StandardError.ReadToEnd()
        $completed = $proc.WaitForExit($timeout * 1000)

        if (-not $completed) {
            $proc.Kill()
            throw "TIMEOUT after ${timeout}s"
        }

        $exitCode = $proc.ExitCode
        $result.Output = $output
        Write-Host "  EXIT: $exitCode" -ForegroundColor $(if ($exitCode -eq 0) {"Green"} else {"Red"})
        Write-Host "  OUTPUT:" -ForegroundColor Yellow
        $output -split "`n" | ForEach-Object { Write-Host "    $_" }
        return [PSCustomObject]$result, $exitCode, $output
    } catch {
        $result.Status = "fail"
        $result.Message = $_.Exception.Message
        Write-Host "  FAIL: $($result.Message)" -ForegroundColor Red
        return [PSCustomObject]$result, -1, ""
    }
}

function Run-TestBlocking($name, $cliArgs, [int]$waitSec = 5) {
    Write-Host "`n=== $name ===" -ForegroundColor Cyan

    $result = [ordered]@{ Name = $name; Status = "pass"; Message = ""; Output = "" }

    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Binary
        $psi.Arguments = $cliArgs
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        $proc = [System.Diagnostics.Process]::Start($psi)
        Start-Sleep -Seconds $waitSec

        if ($proc.HasExited) {
            $stdout = $proc.StandardOutput.ReadToEnd()
            $result.Status = "fail"
            $result.Message = "Process exited prematurely (code $($proc.ExitCode))"
            $result.Output = $stdout + $proc.StandardError.ReadToEnd()
            Write-Host "  FAIL: $($result.Message)" -ForegroundColor Red
            return [PSCustomObject]$result
        }

        $proc.CloseMainWindow()
        if (-not $proc.HasExited) {
            Start-Sleep -Seconds 1
            if (-not $proc.HasExited) { $proc.Kill() }
        }

        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()
        $result.Output = $stdout + $stderr

        return [PSCustomObject]$result
    } catch {
        $result.Status = "fail"
        $result.Message = $_.Exception.Message
        Write-Host "  FAIL: $($result.Message)" -ForegroundColor Red
        return [PSCustomObject]$result
    }
}

function Assert-Match($output, $pattern) {
    if ($output -notmatch $pattern) {
        throw "Expected pattern not found: $pattern"
    }
}

function Assert-NotMatch($output, $pattern) {
    if ($output -match $pattern) {
        throw "Unexpected pattern found: $pattern"
    }
}

function Assert-ExitCode($exitCode, $expected = 0) {
    if ($exitCode -ne $expected) {
        throw "Expected exit code $expected, got $exitCode"
    }
}

function Assert-FileExists($path) {
    if (-not (Test-Path $path)) {
        throw "Expected file not found: $path"
    }
}

function Record($result) {
    if ($result.Status -eq "pass") {
        $passed += $result.Name
        Write-Host "  PASS" -ForegroundColor Green
    } else {
        $failed += $result.Name
    }
}

# ---------------------------------------------------------------------------
# 1. COMMAND-LINE PARSING
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 1: Command-Line Parsing" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "help" "--help"
Assert-Match $out "usage"
Record $r

$r, $ec, $out = Run-Test "version" "--version"
Assert-Match $out "\d+\.\d+\.\d+"
Record $r

$r, $ec, $out = Run-Test "info" "--info"
Assert-Match $out "TetoDL"
Record $r

$r, $ec, $out = Run-Test "invalid-flag" "--bogus-flag"
Assert-Match $out "unrecognized|error"
Record $r

$r, $ec, $out = Run-Test "recheck" "--recheck"
Assert-Match $out "(dependency|check|ffmpeg|yt-dlp)"
Record $r

# ---------------------------------------------------------------------------
# 2. VIDEO DOWNLOADS
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 2: Video Downloads" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "video-basic" "-v `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "video-resolution" "-v -r 720p `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

# ---------------------------------------------------------------------------
# 3. AUDIO DOWNLOADS (core features)
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 3: Audio Downloads" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "audio-basic" "-a `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "audio-format-mp3" "-a -f mp3 `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "audio-format-m4a" "-a -f m4a `"$TestUrl`""
Assert-ExitCode $ec 0
Record $r

$r, $ec, $out = Run-Test "audio-smart-cover" "-a --smart-cover `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-Match $out "(cover|Cover|iTunes|thumb)"
Record $r

$r, $ec, $out = Run-Test "audio-no-cover" "-a --no-cover `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "Processing cover|Embedding cover"
Record $r

$r, $ec, $out = Run-Test "audio-lyrics" "-a --lyrics `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-Match $out "(lyrics|Lyrics|Genius)"
Record $r

$r, $ec, $out = Run-Test "audio-cut" "-a --cut 0:10-0:20 `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "audio-quiet" "-a --quiet `"$TestUrl`""
Assert-ExitCode $ec 0
Record $r

$r, $ec, $out = Run-Test "audio-output-path" "-a -o `"$outDir\custom_output`" `"$TestUrl`""
Assert-ExitCode $ec 0
Record $r

$r, $ec, $out = Run-Test "audio-combo" "-a --smart-cover --lyrics -f m4a `"$TestUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

# ---------------------------------------------------------------------------
# 4. THUMBNAIL
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 4: Thumbnail" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "thumbnail-only" "--thumbnail-only `"$TestUrl`""
Assert-ExitCode $ec 0
Record $r

$r, $ec, $out = Run-Test "thumbnail-format-png" "--thumbnail-only -f png `"$TestUrl`""
Assert-ExitCode $ec 0
Record $r

# ---------------------------------------------------------------------------
# 5. PLAYLISTS
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 5: Playlists" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "playlist-basic" "-a `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "playlist-items" "-a --items 1 `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "playlist-async" "-a --async `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "playlist-async-items" "-a --async --items 1 `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "playlist-group" "-a --group `"TestGroup`" `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-Match $out "(group|Group|TestGroup)"
Record $r

$r, $ec, $out = Run-Test "playlist-m3u" "-a --m3u `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

$r, $ec, $out = Run-Test "playlist-async-group-m3u" "-a --async --group TestFull --m3u `"$PlaylistUrl`""
Assert-ExitCode $ec 0
Assert-NotMatch $out "ffmpeg is not installed"
Record $r

# ---------------------------------------------------------------------------
# 7. DAEMON
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 6: Daemon" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r = Run-TestBlocking "daemon-run" "daemon -r" 8
Assert-NotMatch $r.Output "Directory.*does not exist|RuntimeError"
Assert-Match $r.Output "(http://|Uvicorn|running on)"
Record $r

# ---------------------------------------------------------------------------
# 8. YT-DLP UPDATE (optional, requires network)
# ---------------------------------------------------------------------------
if ($YtdlpUpdate -eq $true) {
    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host "  PHASE 7: yt-dlp Update Check" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow

    $r, $ec, $out = Run-Test "ytdlp-update-check" "--recheck"
    Assert-Match $out "(yt-dlp|version|update)"
    Record $r

    $r, $ec, $out = Run-Test "ytdlp-version-info" "--version"
    Assert-Match $out "\d+\.\d+\.\d+"
    Record $r
}

# ---------------------------------------------------------------------------
# 9. UTILITY COMMANDS
# ---------------------------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  PHASE 8: Utility Commands" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

$r, $ec, $out = Run-Test "history" "--history"
Assert-ExitCode $ec 0
Record $r

$r, $ec, $out = Run-Test "uninstall-cancel" "--uninstall" 15
Assert-NotMatch $out "Traceback|unhandled exception"
Record $r

# ---------------------------------------------------------------------------
# Generate JUnit XML
# ---------------------------------------------------------------------------
$endTime = Get-Date
$total = $passed.Count + $failed.Count
$duration = [math]::Round(($endTime - $startTime).TotalSeconds, 2)

$xml = '<?xml version="1.0"?>' + "`n"
$xml += "<testsuite name=""tetodl.windows"" tests=""$total"" failures=""$($failed.Count)"" time=""$duration"">" + "`n"

foreach ($name in $passed) {
    $xml += "  <testcase name=""$name"" classname=""tetodl.windows"" time=""0"" />" + "`n"
}

foreach ($name in $failed) {
    $xml += "  <testcase name=""$name"" classname=""tetodl.windows"" time=""0"">" + "`n"
    $xml += '    <failure message="Test failed" type="AssertionError"/>' + "`n"
    $xml += "  </testcase>" + "`n"
}

$xml += "</testsuite>" + "`n"

$xmlPath = Join-Path $PSScriptRoot ".." "test-results.xml"
$xml | Out-File -FilePath $xmlPath -Encoding utf8 -Force

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "  RESULTS: $($passed.Count)/$total passed, $($failed.Count) failed" -ForegroundColor $(if ($failed.Count -eq 0) { "Green" } else { "Red" })
Write-Host "  Report: $xmlPath" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

if ($failed.Count -gt 0) {
    exit 1
}
