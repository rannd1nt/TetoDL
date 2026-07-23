<#
.SYNOPSIS
    TetoDL Windows Installer — Binary Edition
.DESCRIPTION
    Downloads pre-compiled TetoDL binary from GitHub Releases.
    No Python, Git, or ffmpeg required.
    Usage: iwr "https://rannd1nt.github.io/TetoDL/install.ps1" | iex
#>

param(
    [switch]$Force
)

$ProgressPreference = 'SilentlyContinue'
$Host.UI.RawUI.WindowTitle = "TetoDL Installer"

Write-Host ""
Write-Host "  ------------------------------" -ForegroundColor Cyan
Write-Host "         TetoDL Installer         " -ForegroundColor Cyan
Write-Host "            (Windows)             " -ForegroundColor Cyan
Write-Host "  ------------------------------" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────────
# 1. Detect OS architecture
# ─────────────────────────────────────────────────
$arch = if ([Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
Write-Host "  Detected: Windows $arch" -ForegroundColor Gray

# ─────────────────────────────────────────────────
# 2. Determine install directory
# ─────────────────────────────────────────────────
$installDir = "$env:LOCALAPPDATA\TetoDL"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# ─────────────────────────────────────────────────
# 3. Fetch latest release
# ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  Fetching latest release..." -ForegroundColor Yellow

$repo = "rannd1nt/tetodl"
$apiUrl = "https://api.github.com/repos/$repo/releases/latest"

try {
    $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "TetoDL-Installer" }
    $tag = $release.tag_name
    Write-Host "  Latest version: $tag" -ForegroundColor Green
}
catch {
    Write-Host "  [!] Failed to fetch release info: $_" -ForegroundColor Red
    Write-Host "  Download manually from: https://github.com/$repo/releases" -ForegroundColor Yellow
    exit 1
}

# ─────────────────────────────────────────────────
# 4. Download binary
# ─────────────────────────────────────────────────
$downloadUrl = "https://github.com/$repo/releases/download/$tag/tetodl.exe"
$outputPath = "$installDir\tetodl.exe"

Write-Host ""
Write-Host "  Downloading tetodl.exe" -NoNewline -ForegroundColor Yellow

$wc = [System.Net.WebClient]::new()
$task = $wc.DownloadFileTaskAsync($downloadUrl, $outputPath)
$dots = 0

while (-not $task.IsCompleted) {
    Write-Host "`r  Downloading tetodl.exe$('.' * $dots)$(' ' * (3 - $dots))" -NoNewline
    $dots = ($dots + 1) % 4
    Start-Sleep -Milliseconds 500
}

try {
    $task.GetAwaiter().GetResult()
    Write-Host "`r  Downloading tetodl.exe ... Done!" -ForegroundColor Green
} catch {
    Write-Host "`r  [!] Download failed: $_" -ForegroundColor Red
    exit 1
} finally {
    $wc.Dispose()
}

# ─────────────────────────────────────────────────
# 5. Add to PATH
# ─────────────────────────────────────────────────
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$installDir", "User")
    Write-Host "  Added to PATH (user-wide)" -ForegroundColor Green
}

$env:PATH = "$env:PATH;$installDir"

Write-Host ""
Write-Host "  TetoDL installed successfully!" -ForegroundColor Green
Write-Host "  Location: $outputPath" -ForegroundColor Gray
Write-Host ""

# ─────────────────────────────────────────────────
# 6. Post-install prompt
# ─────────────────────────────────────────────────
if (-not $Force) {
    Write-Host ""
    $runNow = Read-Host "  Run tetodl now? (Y/n)"
    if ($runNow -ne "n") {
        & "$installDir\tetodl.exe"
    }
}
