@echo off
title DealMind seed
cd /d "%~dp0"
echo Seeding pipeline + memories into Hindsight...
".venv\Scripts\python.exe" -m app.seed
pause
