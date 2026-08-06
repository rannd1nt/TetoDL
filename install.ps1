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
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

try { $Host.UI.RawUI.WindowTitle = "TetoDL Installer" } catch {}

function Fail-Install([string]$msg) {
    Write-Host ""
    Write-Host "  [!] $msg" -ForegroundColor Red
    Write-Host "  Download manually from: https://github.com/rannd1nt/tetodl/releases" -ForegroundColor Yellow
    if (-not $Force) {
        Read-Host "  Press Enter to exit"
    }
    exit 1
}

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
    $expectedSize = 0
    foreach ($a in $release.assets) {
        if ($a.name -eq "tetodl.exe") {
            $expectedSize = [long]$a.size
            break
        }
    }
    Write-Host "  Latest version: $tag" -ForegroundColor Green
}
catch {
    Fail-Install "Failed to fetch release info: $_"
}

# ─────────────────────────────────────────────────
# 4. Download binary (with retries + validation)
# ─────────────────────────────────────────────────
$downloadUrl = "https://github.com/$repo/releases/download/$tag/tetodl.exe"
$outputPath = "$installDir\tetodl.exe"

function Test-TetoDLBinary([string]$path, [long]$size) {
    if (-not (Test-Path $path)) { return $false }
    try {
        $len = (Get-Item $path).Length
        return ($len -eq $size) -or ($len -gt 5MB)
    } catch {
        return $false
    }
}

$downloaded = $false
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue

foreach ($attempt in 1..3) {
    Write-Host ""
    if ($attempt -gt 1) {
        Write-Host "  Downloading tetodl.exe (attempt $attempt/3)" -ForegroundColor Yellow
    } else {
        Write-Host "  Downloading tetodl.exe" -NoNewline -ForegroundColor Yellow
    }

    try {
        if ($curl) {
            # curl.exe is bundled with Windows 10 1803+; it handles redirects,
            # TLS and timeouts far better than System.Net.WebClient.
            & $curl.Source --location --fail --retry 3 --retry-delay 2 `
                --connect-timeout 20 --max-time 900 `
                --output $outputPath $downloadUrl
            if ($LASTEXITCODE -ne 0) {
                Write-Host "`r  Downloading tetodl.exe ... curl failed (exit $LASTEXITCODE)." -ForegroundColor Red
                $err = $true
            } else {
                $err = $false
            }
        } else {
            $wc = [System.Net.WebClient]::new()
            try {
                $wc.DownloadFile($downloadUrl, $outputPath)
                $err = $false
            } finally {
                $wc.Dispose()
            }
        }

        if (-not $err -and (Test-TetoDLBinary $outputPath $expectedSize)) {
            $downloaded = $true
            Write-Host "`r  Downloading tetodl.exe ... Done!" -ForegroundColor Green
            break
        }
        Write-Host "`r  Downloading tetodl.exe ... invalid file." -ForegroundColor Red
    }
    catch {
        Write-Host "`r  Downloading tetodl.exe ... failed: $_" -ForegroundColor Red
    }
    finally {
        if (-not $downloaded -and (Test-Path $outputPath)) {
            Remove-Item $outputPath -Force -ErrorAction SilentlyContinue
        }
    }
    if ($attempt -lt 3) { Start-Sleep -Seconds 3 }
}

if (-not $downloaded) {
    Fail-Install "Could not download tetodl.exe"
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
        Write-Host "  Launching TetoDL in a new window..." -ForegroundColor Yellow
        Start-Process -FilePath "$installDir\tetodl.exe"
    }
}
