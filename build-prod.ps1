# GitHub Repository Analyzer - Build Script (PowerShell)
$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GitHub Repository Analyzer - Build" -ForegroundColor Cyan
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

# Step 1: Build Backend
Write-Host "[1/3] Building backend executable..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\backend"
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue

& $pythonCmd scripts/build_backend.py
if ($LASTEXITCODE -ne 0) { throw "Backend build failed" }

Write-Host "[OK] Backend built: backend\dist\backend.exe" -ForegroundColor Green

# Step 2: Build Frontend
Write-Host ""
Write-Host "[2/3] Building frontend..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
}

Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

Write-Host "[OK] Frontend built: frontend\dist\" -ForegroundColor Green

# Step 3: Package Electron App
Write-Host ""
Write-Host "[3/3] Packaging Electron desktop app..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$rootDir\frontend"
Remove-Item -Path "dist-electron" -Recurse -Force -ErrorAction SilentlyContinue
npm run electron:build:win
if ($LASTEXITCODE -ne 0) { throw "Electron packaging failed" }

# Done
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:     backend\dist\backend.exe" -ForegroundColor White
Write-Host "  Frontend:    frontend\dist\" -ForegroundColor White
Write-Host "  Desktop App: frontend\dist-electron\" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"