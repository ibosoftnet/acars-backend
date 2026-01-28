@echo off
cd /d %~dp0
title Ibosoft ACARS Backend
call python main.py
timeout -t 3
exit /b 0