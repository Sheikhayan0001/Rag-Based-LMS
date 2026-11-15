@echo off
setlocal
cd /d "%~dp0backend"
if not exist .venv\Scripts\activate.bat (
  echo Run SETUP.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
if not exist .env copy .env.example .env >nul
echo Starting LPU Library RAG backend...
echo Open http://127.0.0.1:8000 in your browser.
python -m uvicorn app.main:app --reload --port 8000
