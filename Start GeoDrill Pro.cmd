@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" tools\launch.py %*
if errorlevel 1 pause
