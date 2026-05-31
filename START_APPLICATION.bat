@echo off
echo ============================================================
echo    JOB AI PROJECT - Quick Start Script
echo ============================================================
echo.

REM Check if Docker is running
echo [1/5] Checking Docker status...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Docker is not running!
    echo The application will use SQLite instead of PostgreSQL.
    echo To use PostgreSQL, start Docker Desktop and run: docker-compose up -d
    echo.
) else (
    echo Docker is running. Starting services...
    docker-compose up -d
    echo.
)

REM Check frontend dependencies
echo [2/5] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
) else (
    echo Frontend dependencies already installed.
    echo.
)

REM Check Playwright browsers
echo [3/5] Checking Playwright browsers...
cd backend
python -c "import playwright; print('Playwright installed')" >nul 2>&1
if %errorlevel% equ 0 (
    echo Playwright is installed. Installing browsers...
    playwright install chromium
    echo.
) else (
    echo Playwright not found. Skipping browser installation.
    echo.
)
cd ..

REM Start backend
echo [4/5] Starting backend server...
echo Backend will run on: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
start cmd /k "cd backend && uvicorn app.main:app --reload --port 8000"
timeout /t 3 >nul

REM Start frontend
echo [5/5] Starting frontend development server...
echo Frontend will run on: http://localhost:5173
start cmd /k "cd frontend && npm run dev"
timeout /t 3 >nul

echo.
echo ============================================================
echo    APPLICATION STARTED SUCCESSFULLY!
echo ============================================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Press any key to open the application in your browser...
pause >nul
start http://localhost:5173
