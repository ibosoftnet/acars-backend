@echo off
REM ============================================================
REM Ibosoft ACARS Backend - Virtual Environment Setup
REM ------------------------------------------------------------
REM Creates a Python virtual environment in .\venv and installs
REM all required packages from requirements.txt into it.
REM Run this once after first checkout, and again whenever the
REM requirements.txt is updated.
REM ============================================================

cd /d %~dp0
title Ibosoft ACARS Backend - venv setup

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.x first.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment in .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists at .\venv — reusing it.
)

echo.
echo Upgrading pip inside the venv ...
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing requirements from requirements.txt ...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setup complete. You can now run start.bat to launch the backend.
echo ============================================================
pause
exit /b 0
