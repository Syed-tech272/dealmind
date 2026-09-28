@echo off
title DealMind
cd /d "%~dp0"
echo Starting DealMind on http://localhost:8000  (Ctrl+C to stop)
start "" "http://localhost:8000"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
