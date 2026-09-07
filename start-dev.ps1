# GitHub Repository Analyzer - Dev Mode (PowerShell)
$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GitHub Repository Analyzer - Dev Mode" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ======== Find Python ========
$pythonCmd = $null
$pythonPaths = @(
    "python", "py"
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
)

foreach ($p in $pythonPaths) {
    try {
        $ver = & $p --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $p
            Write-Host "[OK] $ver" -ForegroundColor Green
            break
        }
    } catch { continue }
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found." -ForegroundColor Red
    Write-Host "Install from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

# ======== Find Node.js ========
$nodeCmd = $null
$nodePaths = @(
    "node"
    "C:\Program Files\nodejs\node.exe"
    "C:\Program Files (x86)\nodejs\node.exe"
)

foreach ($n in $nodePaths) {
    try {
        $ver = & $n --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $nodeCmd = $n
            Write-Host "[OK] Node.js $ver" -ForegroundColor Green
            break
        }
    } catch { continue }
}

if (-not $nodeCmd) {
    Write-Host "[ERROR] Node.js not found." -ForegroundColor Red
    Write-Host "Install from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"; exit 1
}

# Add Node.js dir to PATH (for npm)
$nodeDir = Split-Path $nodeCmd -Parent
$env:PATH = "$nodeDir;$env:PATH"

Write-Host ""

# ======== Auto-Configure Environment ========

# Check Python dependencies
Write-Host "[SETUP] Checking Python dependencies..." -ForegroundColor Yellow
$pipResult = & $pythonCmd -m pip install -r "$rootDir\backend\requirements.txt" -q --no-warn-script-location 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python dependency installation failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}
Write-Host "[OK] Python dependencies ready" -ForegroundColor Green

# Check .env file
if (-not (Test-Path "$rootDir\backend\.env")) {
    if (Test-Path "$rootDir\backend\.env.example") {
        Write-Host "[SETUP] Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item "$rootDir\backend\.env.example" "$rootDir\backend\.env"
        Write-Host "[OK] .env created - please edit backend\.env to set your API key" -ForegroundColor Green
    } else {
        Write-Host "[WARN] No .env or .env.example found" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] .env file found" -ForegroundColor Green
}

# Check Node.js dependencies
if (-not (Test-Path "$rootDir\frontend\node_modules")) {
    Write-Host "[SETUP] Installing Node.js dependencies..." -ForegroundColor Yellow
    Set-Location "$rootDir\frontend"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"; exit 1
    }
    Set-Location $rootDir
    Write-Host "[OK] Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[OK] Node.js dependencies found" -ForegroundColor Green
}

Write-Host ""

# ======== Start Services ========

# Start backend
Write-Host "[1/2] Starting backend server..." -ForegroundColor Yellow
$backendJob = Start-Job -Name "GitHubBackend" -ScriptBlock {
    param($dir, $python)
    Set-Location $dir
    if ($python -eq "python" -or $python -eq "py") {
        python run.py
    } else {
        & $python run.py
    }
} -ArgumentList "$rootDir\backend", $pythonCmd

Start-Sleep -Seconds 3

# Start frontend
Write-Host "[2/2] Starting frontend dev server..." -ForegroundColor Yellow
$frontendJob = Start-Job -Name "GitHubFrontend" -ScriptBlock {
    param($dir, $nodeDir)
    $env:PATH = "$nodeDir;$env:PATH"
    Set-Location $dir
    npm run dev
} -ArgumentList "$rootDir\frontend", $nodeDir

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Waiting for frontend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Gray

try {
    while ($true) {
        Start-Sleep -Seconds 2
        $jb = Get-Job -Name "GitHubBackend" -ErrorAction SilentlyContinue
        $jf = Get-Job -Name "GitHubFrontend" -ErrorAction SilentlyContinue
        if (-not $jb -and -not $jf) { break }
        if ($jb -and $jb.State -eq "Failed") {
            Write-Host "[ERROR] Backend crashed" -ForegroundColor Red
            Receive-Job -Job $jb -ErrorAction SilentlyContinue
            break
        }
    }
} finally {
    Write-Host ""; Write-Host "Stopping services..." -ForegroundColor Yellow
    Get-Job -Name "GitHubBackend" | Stop-Job -PassThru | Remove-Job -ErrorAction SilentlyContinue
    Get-Job -Name "GitHubFrontend" | Stop-Job -PassThru | Remove-Job -ErrorAction SilentlyContinue
    Write-Host "Services stopped." -ForegroundColor Green
    Read-Host "Press Enter to exit"
}