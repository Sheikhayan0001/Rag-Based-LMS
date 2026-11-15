@echo off
setlocal
cd /d "%~dp0backend"
echo ==============================================
echo   LPU LIBRARY - Cloud RAG local setup
echo ==============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.12 or newer and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo Could not activate the virtual environment.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and Python version.
  pause
  exit /b 1
)
echo.
echo Setup complete. Add DATABASE_URL, AI_GATEWAY_API_KEY and ADMIN_INGEST_KEY to backend\.env.
echo Then run RUN.bat. No local Ollama server is needed for this cloud RAG version.
pause
