@echo off
title GitHub Analyzer - Build

setlocal enabledelayedexpansion
set ROOT_DIR=%~dp0
set PYTHON_CMD=
set NODE_CMD=

echo ============================================
echo   GitHub Repository Analyzer - Build
echo ============================================
echo.

:: ======== Find Python ========
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe" & goto :found_python
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto :found_python
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & goto :found_python
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & goto :found_python

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :found_python
)

echo [ERROR] Python not found.
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found_python
for /f "tokens=*" %%a in ('%PYTHON_CMD% --version 2^>^&1') do set PY_VER=%%a
echo [OK] %PY_VER%

:: ======== Find Node.js ========
node --version >nul 2>&1
if %errorlevel% equ 0 (
    set NODE_CMD=node
    goto :found_node
)

if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD="C:\Program Files\nodejs\node.exe" & goto :found_node
if exist "C:\Program Files (x86)\nodejs\node.exe" set NODE_CMD="C:\Program Files (x86)\nodejs\node.exe" & goto :found_node

echo [ERROR] Node.js not found.
echo Please install Node.js 18+ from https://nodejs.org/
echo.
pause
exit /b 1

:found_node
for /f "tokens=*" %%a in ('%NODE_CMD% --version 2^>^&1') do set NODE_VER=%%a
echo [OK] Node.js %NODE_VER%
echo.

:: Add Node.js dir to PATH (for npm)
for %%i in (%NODE_CMD%) do set "NODE_DIR=%%~dpi"
set "PATH=%NODE_DIR%;%PATH%"

:: ======== Auto-Configure Environment ========

:: Check Python dependencies
echo [SETUP] Checking Python dependencies...
%PYTHON_CMD% -m pip install -r "%ROOT_DIR%backend\requirements.txt" -q --no-warn-script-location
if %errorlevel% neq 0 (
    echo [ERROR] Python dependency installation failed
    pause
    exit /b 1
)
echo [OK] Python dependencies ready

:: Check .env file
if not exist "%ROOT_DIR%backend\.env" (
    if exist "%ROOT_DIR%backend\.env.example" (
        echo [SETUP] Creating .env from .env.example...
        copy "%ROOT_DIR%backend\.env.example" "%ROOT_DIR%backend\.env" >nul
        echo [OK] .env created from .env.example
    ) else (
        echo [WARN] No .env or .env.example found
    )
) else (
    echo [OK] .env file found
)

echo.

:: ============================================
:: Step 1: Build Backend (PyInstaller)
:: ============================================
echo.
echo [1/3] Building backend executable...
echo.

cd /d "%ROOT_DIR%backend"

if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1

%PYTHON_CMD% scripts\build_backend.py
if %errorlevel% neq 0 (
    echo [ERROR] Backend build failed
    pause
    exit /b 1
)

echo [OK] Backend built: backend\dist\backend.exe

:: ============================================
:: Step 2: Build Frontend (Vite)
:: ============================================
echo.
echo [2/3] Building frontend...
echo.

cd /d "%ROOT_DIR%frontend"

if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    if !errorlevel! neq 0 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
)

if exist "dist" rmdir /s /q "dist" >nul 2>&1

npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    pause
    exit /b 1
)

echo [OK] Frontend built: frontend\dist\

:: ============================================
:: Step 3: Package Electron App
:: ============================================
echo.
echo [3/3] Packaging Electron desktop app...
echo.

cd /d "%ROOT_DIR%frontend"

if exist "dist-electron" rmdir /s /q "dist-electron" >nul 2>&1

npm run electron:build:win
if %errorlevel% neq 0 (
    echo [ERROR] Electron packaging failed
    pause
    exit /b 1
)

:: ============================================
echo.
echo ============================================
echo   Build Complete!
echo.
echo   Backend: backend\dist\backend.exe
echo   Frontend: frontend\dist\
echo   Desktop App: frontend\dist-electron\
echo ============================================
echo.

pause