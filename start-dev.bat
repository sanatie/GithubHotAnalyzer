@echo off
title GitHub Analyzer - Dev Mode

set ROOT_DIR=%~dp0
set PYTHON_CMD=
set NODE_CMD=

echo ============================================
echo   GitHub Repository Analyzer - Dev Mode
echo ============================================
echo.

:: ======== Find Python ========
:: First preference: the project's own venv, to avoid a PATH (e.g. TRAE) Python
if exist "%ROOT_DIR%backend\.venv\Scripts\python.exe" set "PYTHON_CMD=%ROOT_DIR%backend\.venv\Scripts\python.exe" & goto :found_python

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
echo.
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
echo.
echo Please install Node.js 18+ from https://nodejs.org/
echo.
pause
exit /b 1

:found_node
for /f "tokens=*" %%a in ('%NODE_CMD% --version 2^>^&1') do set NODE_VER=%%a
echo [OK] Node.js %NODE_VER%
echo.

:: ======== Auto-Configure Environment ========

:: Check Python dependencies
echo [SETUP] Checking Python dependencies...
%PYTHON_CMD% -m pip install -r "%ROOT_DIR%backend\requirements.txt" -q --no-warn-script-location
if %errorlevel% neq 0 (
    echo [WARN] Python dependency install failed, continuing with existing environment, ensure the backend can still start...
)
echo [OK] Python dependencies ready

:: Check .env file
if not exist "%ROOT_DIR%backend\.env" (
    if exist "%ROOT_DIR%backend\.env.example" (
        echo [SETUP] Creating .env from .env.example...
        copy "%ROOT_DIR%backend\.env.example" "%ROOT_DIR%backend\.env" >nul
        echo [OK] .env created - please edit backend\.env to set your API key
    ) else (
        echo [WARN] No .env or .env.example found
    )
) else (
    echo [OK] .env file found
)

:: Check Node.js dependencies
if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [SETUP] Installing Node.js dependencies...
    cd /d "%ROOT_DIR%frontend"
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
    cd /d "%ROOT_DIR%"
    echo [OK] Node.js dependencies installed
) else (
    echo [OK] Node.js dependencies found
)

echo.

:: ======== Start Services ========
echo [1/2] Starting backend server...
echo.

start "GitHub Backend" cmd /c "%ROOT_DIR%backend\run_backend.bat" %PYTHON_CMD%

ping 127.0.0.1 -n 4 >nul

echo [2/2] Starting frontend dev server...
echo.

start "GitHub Frontend" cmd /c "%ROOT_DIR%frontend\run_frontend.bat" %NODE_CMD%

echo.
echo ============================================
echo   Backend: http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:5173
echo   API Docs: http://127.0.0.1:8000/docs
echo ============================================
echo.
echo Waiting for frontend to start...
ping 127.0.0.1 -n 6 >nul

echo Opening browser...
start http://127.0.0.1:5173
echo.
echo Close this window to stop all services.
echo.

pause >nul

echo Stopping services...
taskkill /f /fi "WINDOWTITLE eq GitHub Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq GitHub Frontend" >nul 2>&1
echo Services stopped.
pause