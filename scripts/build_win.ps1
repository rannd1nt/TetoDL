<#
.SYNOPSIS
    TetoDL Windows Local Build & Deploy Pipeline (Hermetic, Zero-Bandwidth Cached).
.DESCRIPTION
    Builds the standalone tetodl.exe binary natively on Windows using a lightweight,
    isolated uv + Indygreg Python 3.12 environment without polluting the host OS.
.PARAMETER Force
    Force overwrite if an existing tetodl.exe is installed in %LOCALAPPDATA%\TetoDL.
.PARAMETER SkipInstall
    Only compile the binary to dist\tetodl.exe; do not install to %LOCALAPPDATA%\TetoDL.
.PARAMETER Clean
    Clean build caches, PyInstaller dist/build folders, and venv before building.
.PARAMETER Test
    Run post-build smoke verification tests (--version, --help).
.PARAMETER ProjectDir
    Root directory of the project in Windows path format.
#>
param(
    [switch]$Force,
    [switch]$SkipInstall,
    [switch]$Clean,
    [switch]$Test,
    [string]$ProjectDir = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Log-Info([string]$msg)    { Write-Host "  [*] $msg" -ForegroundColor Cyan }
function Log-Success([string]$msg) { Write-Host "  [+] $msg" -ForegroundColor Green }
function Log-Warn([string]$msg)    { Write-Host "  [-] $msg" -ForegroundColor Yellow }
function Log-Error([string]$msg)   { Write-Host "  [!] $msg" -ForegroundColor Red }
function Log-Fatal([string]$msg)   { Write-Host "`n  [!] FATAL: $msg`n" -ForegroundColor Red; exit 1 }

# ─────────────────────────────────────────────────────────────────────────────
# 1. Resolve Project Root & Handle UNC Paths (WSL)
# ─────────────────────────────────────────────────────────────────────────────
if ([string]::IsNullOrWhiteSpace($ProjectDir)) {
    $resolved = Resolve-Path (Join-Path $PSScriptRoot "..")
} else {
    $resolved = Resolve-Path $ProjectDir
}

# In PowerShell, ProviderPath strips any 'Microsoft.PowerShell.Core\FileSystem::' prefix
$ProjectDir = if ($resolved.ProviderPath) { $resolved.ProviderPath } else { $resolved.Path }

# If ProjectDir is a UNC path (e.g. \\wsl.localhost\...), map to temporary drive for full CMD/PyInstaller compatibility
$mappedDrive = $null
$workDir = $ProjectDir
if ($ProjectDir -like "\\*" -or $ProjectDir -like "*\\wsl*") {
    $usedDrives = (Get-PSDrive -PSProvider FileSystem).Name
    foreach ($letter in [char[]]"ZYXWVUTSRQPONMLKJIHGFEDCBA") {
        if ($usedDrives -notcontains [string]$letter) {
            $mappedDrive = "${letter}:"
            break
        }
    }
    if ($mappedDrive) {
        Log-Info "Mounting UNC path to temporary drive letter ($mappedDrive)..."
        New-PSDrive -Name $mappedDrive.TrimEnd(':') -PSProvider FileSystem -Root $ProjectDir | Out-Null
        $workDir = "$mappedDrive\"
    }
}

Log-Info "Working directory: $workDir (Project: $ProjectDir)"
Set-Location $workDir

# ─────────────────────────────────────────────────────────────────────────────
# 2. Pre-flight Safety Guard: Active Installation Check
# ─────────────────────────────────────────────────────────────────────────────
$installDir = "$env:LOCALAPPDATA\TetoDL"
$targetExe = "$installDir\tetodl.exe"

if ((-not $SkipInstall) -and (-not $Force)) {
    if (Test-Path $targetExe) {
        Write-Host ""
        Log-Error "Active TetoDL installation detected at:"
        Write-Host "      $targetExe" -ForegroundColor Yellow
        Write-Host ""
        Log-Error "Refusing to overwrite active installation to avoid state conflict."
        Write-Host "      Please remove the existing installation first:" -ForegroundColor White
        Write-Host "          tetodl --uninstall" -ForegroundColor Cyan
        Write-Host "      Or pass -Force to overwrite." -ForegroundColor White
        Write-Host ""
        if ($mappedDrive) { Remove-PSDrive -Name $mappedDrive.TrimEnd(':') -Force -ErrorAction SilentlyContinue }
        exit 1
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. Setup Isolated Developer Cache (tetodl-dev)
# ─────────────────────────────────────────────────────────────────────────────
$toolsDir = "$env:LOCALAPPDATA\tetodl-dev"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Acquire / Verify Portable 'uv'
# ─────────────────────────────────────────────────────────────────────────────
$uvExe = Get-Command "uv.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
if (-not $uvExe) {
    $localUv = "$toolsDir\uv.exe"
    if (Test-Path $localUv) {
        $uvExe = $localUv
    } else {
        Log-Info "Standalone 'uv' not detected on Windows host. Downloading portable uv (~15MB)..."
        $uvZipUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
        $uvZipPath = "$toolsDir\uv.zip"
        try {
            $wc = [System.Net.WebClient]::new()
            $wc.DownloadFile($uvZipUrl, $uvZipPath)
            $wc.Dispose()
            Expand-Archive -Path $uvZipPath -DestinationPath "$toolsDir\uv_tmp" -Force
            $foundUv = Get-ChildItem -Path "$toolsDir\uv_tmp" -Filter "uv.exe" -Recurse | Select-Object -ExpandProperty FullName -First 1
            if ($foundUv) {
                Move-Item -Path $foundUv -Destination $localUv -Force
            } else {
                throw "uv.exe not found in extracted archive"
            }
            Remove-Item "$toolsDir\uv_tmp" -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item $uvZipPath -Force -ErrorAction SilentlyContinue
            $uvExe = $localUv
            Log-Success "Portable 'uv' acquired successfully: $uvExe"
        } catch {
            if ($mappedDrive) { Remove-PSDrive -Name $mappedDrive.TrimEnd(':') -Force -ErrorAction SilentlyContinue }
            Log-Fatal "Failed to acquire portable 'uv': $_"
        }
    }
} else {
    Log-Success "Using existing system 'uv': $uvExe"
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. Acquire / Verify ffmpeg.exe (Zero Bandwidth Reuse)
# ─────────────────────────────────────────────────────────────────────────────
$localFfmpeg = Join-Path $workDir "ffmpeg.exe"
$projFfmpeg = Join-Path $ProjectDir "ffmpeg.exe"
$cachedFfmpeg = Join-Path $toolsDir "ffmpeg.exe"

if (-not (Test-Path $localFfmpeg)) {
    if (Test-Path $projFfmpeg) {
        Copy-Item -Path $projFfmpeg -Destination $localFfmpeg -Force
        Log-Success "Reused ffmpeg.exe from project root."
    } elseif (Test-Path $cachedFfmpeg) {
        Log-Info "Reusing cached ffmpeg.exe from $cachedFfmpeg (0 bytes downloaded)..."
        Copy-Item -Path $cachedFfmpeg -Destination $localFfmpeg -Force
    } else {
        # Check Temp for any existing PyInstaller MEI unpacks or WinGet archives
        $meiFfmpeg = Get-ChildItem -Path "$env:LOCALAPPDATA\Temp" -Filter "ffmpeg.exe" -Recurse -Depth 3 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($meiFfmpeg -and (Test-Path $meiFfmpeg.FullName)) {
            Log-Success "Discovered existing ffmpeg.exe at $($meiFfmpeg.FullName) (0 bytes downloaded)"
            Copy-Item -Path $meiFfmpeg.FullName -Destination $cachedFfmpeg -Force
            Copy-Item -Path $meiFfmpeg.FullName -Destination $localFfmpeg -Force
        } else {
            Log-Warn "No cached ffmpeg.exe found. tetodl.spec will retrieve it during compilation."
        }
    }
} else {
    Log-Success "ffmpeg.exe verified in working directory."
}

if ((Test-Path $localFfmpeg) -and (-not (Test-Path $cachedFfmpeg))) {
    Copy-Item -Path $localFfmpeg -Destination $cachedFfmpeg -Force -ErrorAction SilentlyContinue
}
if ((Test-Path $localFfmpeg) -and (-not (Test-Path $projFfmpeg))) {
    Copy-Item -Path $localFfmpeg -Destination $projFfmpeg -Force -ErrorAction SilentlyContinue
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. Hermetic Python Virtual Environment via 'uv'
# ─────────────────────────────────────────────────────────────────────────────
$venvDir = "$toolsDir\venv"

if ($Clean -and (Test-Path $venvDir)) {
    Log-Info "Cleaning virtual environment at $venvDir..."
    Remove-Item $venvDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
    Log-Info "Setting up isolated Python 3.12 environment via 'uv'..."
    & $uvExe python install 3.12
    if ($LASTEXITCODE -ne 0) { Log-Fatal "Failed to install Python 3.12 via uv." }

    & $uvExe venv $venvDir --python 3.12
    if ($LASTEXITCODE -ne 0) { Log-Fatal "Failed to initialize venv via uv." }
    Log-Success "Virtual environment initialized at $venvDir"
}

$venvPython = "$venvDir\Scripts\python.exe"

Log-Info "Syncing dependencies with uv pip (standard standalone build)..."
# Clean up any leftover editable pointers from prior builds
Get-ChildItem -Path "$venvDir\Lib\site-packages" -Filter "*editable*" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
& $uvExe pip install --reinstall-package tetodl ".[windows]" pyinstaller --python $venvPython
if ($LASTEXITCODE -ne 0) { Log-Fatal "Failed to install dependencies with uv pip." }
Log-Success "All dependencies resolved and cached into isolated virtual environment."

# ─────────────────────────────────────────────────────────────────────────────
# 7. PyInstaller Compilation
# ─────────────────────────────────────────────────────────────────────────────
if ($Clean) {
    Log-Info "Cleaning build/ and dist/ directories..."
    Remove-Item "$ProjectDir\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$ProjectDir\dist" -Recurse -Force -ErrorAction SilentlyContinue
}

$pyinstallerExe = "$venvDir\Scripts\pyinstaller.exe"
Log-Info "Compiling binary with PyInstaller..."

$specArgs = @("tetodl.spec")
if ($Clean) { $specArgs += "--clean" }

$buildStart = Get-Date
& $pyinstallerExe @specArgs
if ($LASTEXITCODE -ne 0) { Log-Fatal "PyInstaller compilation failed with exit code $LASTEXITCODE." }

$buildDuration = [math]::Round(((Get-Date) - $buildStart).TotalSeconds, 1)
$distExe = "$ProjectDir\dist\tetodl.exe"

if (-not (Test-Path $distExe)) {
    Log-Fatal "Expected binary output not found: $distExe"
}

$binarySizeMb = [math]::Round(((Get-Item $distExe).Length / 1MB), 2)
Log-Success "Compilation successful in ${buildDuration}s -> $distExe (${binarySizeMb} MB)"

# ─────────────────────────────────────────────────────────────────────────────
# 8. Installation to %LOCALAPPDATA%\TetoDL
# ─────────────────────────────────────────────────────────────────────────────
if (-not $SkipInstall) {
    Log-Info "Deploying binary to $installDir..."
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }

    # Handle running tetodl process lock
    $runningProcs = Get-Process -Name "tetodl" -ErrorAction SilentlyContinue
    if ($runningProcs) {
        if ($Force) {
            Log-Warn "Active TetoDL process detected ($($runningProcs.Count) instance(s)). Terminating for clean update (-Force active)..."
            Stop-Process -Name "tetodl" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        } else {
            Log-Fatal "TetoDL binary is currently running ($targetExe). Please stop it (e.g. 'tetodl service daemon remove') or pass -Force to overwrite."
        }
    }

    $copied = $false
    for ($i = 1; $i -le 5; $i++) {
        try {
            Copy-Item -Path $distExe -Destination $targetExe -Force -ErrorAction Stop
            $copied = $true
            break
        } catch {
            if ($i -lt 5) {
                Log-Warn "Target binary locked by Windows, waiting for release (attempt $i/5)..."
                Start-Sleep -Seconds 1
            } else {
                Log-Fatal "Cannot overwrite '$targetExe': $_"
            }
        }
    }
    Log-Success "Installed binary to: $targetExe"

    # Verify/Update User PATH
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
        Log-Success "Added $installDir to Windows User PATH environment variable."
    }
} else {
    Log-Info "Skipping installation (-SkipInstall flag active)."
}

# ─────────────────────────────────────────────────────────────────────────────
# 9. Smoke Verification Tests
# ─────────────────────────────────────────────────────────────────────────────
if ($Test) {
    $testBinary = if (-not $SkipInstall) { $targetExe } else { $distExe }
    Log-Info "Running smoke verification tests on: $testBinary"

    # Test 1: --version
    Write-Host ""
    Write-Host "      [Smoke Test] --version" -ForegroundColor Cyan
    $verOut = & "$testBinary" --version 2>&1
    Write-Host "      $verOut" -ForegroundColor Gray
    if ($LASTEXITCODE -ne 0) { Log-Fatal "Smoke test '--version' failed!" }

    # Test 2: --help
    Write-Host "      [Smoke Test] --help" -ForegroundColor Cyan
    $helpOut = & "$testBinary" --help 2>&1 | Select-Object -First 3
    foreach ($line in $helpOut) { Write-Host "      $line" -ForegroundColor Gray }
    if ($LASTEXITCODE -ne 0) { Log-Fatal "Smoke test '--help' failed!" }

    Log-Success "All smoke verification tests passed!"
}

if ($mappedDrive) {
    Remove-PSDrive -Name $mappedDrive.TrimEnd(':') -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Log-Success "Local Windows build pipeline finished successfully."
Write-Host ""
