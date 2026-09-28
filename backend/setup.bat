@echo off
title DealMind setup
cd /d "%~dp0"
echo [1/3] Creating virtual environment...
if not exist ".venv\Scripts\python.exe" python -m venv .venv
echo [2/3] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo [3/3] Preparing .env...
if not exist ".env" ( copy ".env.example" ".env" >nul & echo    Created .env - OPEN IT and paste your GROQ + HINDSIGHT keys, then run seed.bat )
echo.
echo Done. Next: edit .env with your keys, then run  seed.bat  then  run.bat
pause
