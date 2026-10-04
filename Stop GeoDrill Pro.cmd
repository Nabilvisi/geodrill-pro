@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" tools\launch.py --stop
if errorlevel 1 pause
