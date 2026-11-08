@echo off
chcp 65001 >nul
title MORL Training Monitor
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_training_monitor.ps1"
if errorlevel 1 pause
