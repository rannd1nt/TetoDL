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

$Host.UI.RawUI.WindowTitle = "TetoDL Installer"

Write-Host "╔══════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       TetoDL Installer           ║" -ForegroundColor Cyan
Write-Host "║          (Windows)               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════╝" -ForegroundColor Cyan
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
Write-Host "  Downloading tetodl.exe ..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath -UseBasicParsing
}
catch {
    Write-Host "  [!] Download failed: $_" -ForegroundColor Red
    exit 1
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
Write-Host "  Run 'tetodl --help' to get started." -ForegroundColor Cyan

# ─────────────────────────────────────────────────
# 6. Post-install prompt
# ─────────────────────────────────────────────────
if (-not $Force) {
    Write-Host ""
    $runNow = Read-Host "  Run tetodl --help now? (Y/n)"
    if ($runNow -ne "n") {
        & "$installDir\tetodl.exe" --help
    }
}
