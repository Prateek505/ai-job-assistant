@echo off
echo ============================================
echo    AI Job Assistant - Production Server
echo ============================================
echo.

cd /d "%~dp0backend"

echo Starting server on http://localhost:8000
echo.
echo To expose via ngrok, run in another terminal:
echo   ngrok http 8000
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
