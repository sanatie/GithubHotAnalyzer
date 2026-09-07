@echo off
title GitHub Frontend Dev
cd /d "%~dp0"

:: Use passed Node.js path to set PATH, or use default
if not "%1"=="" (
    set "PATH=%~dp1;%PATH%"
)

echo Starting frontend dev server...
npm run dev
echo Frontend server stopped.
pause