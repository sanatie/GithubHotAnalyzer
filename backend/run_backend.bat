@echo off
title GitHub Backend API
cd /d "%~dp0"

:: Use passed Python command or default
set PYTHON_CMD=%1
if "%PYTHON_CMD%"=="" set PYTHON_CMD=python

echo Starting backend server with %PYTHON_CMD%...
%PYTHON_CMD% run.py
echo Backend server stopped.
pause