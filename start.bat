@echo off
cd /d %~dp0
title Data Link Backend Server
call python main.py
timeout -t 3
exit /b 0