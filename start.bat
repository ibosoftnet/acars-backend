@echo off
cd /d %~dp0
title Ibosoft ACARS Backend

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .\venv
    echo Run install-venv.bat first to set up the environment.
    timeout -t 5
    exit /b 1
)

call venv\Scripts\python.exe main.py

timeout -t 3
exit /b 0
