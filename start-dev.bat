@echo off
REM Batch script to start both backend and frontend for POC Intake

echo Starting POC Intake Development Environment...
echo.

REM Check if uv exists
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'uv' is not installed. Please install uv first.
    echo Visit: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

REM Check if npm exists
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'npm' is not installed. Please install Node.js first.
    echo Visit: https://nodejs.org/
    pause
    exit /b 1
)

echo Starting Backend (FastAPI)...
start "POC Intake Backend" cmd /k "cd backend && echo Starting Backend Server... && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo Starting Frontend (Next.js)...
start "POC Intake Frontend" cmd /k "cd frontend && echo Starting Frontend Server... && npx next dev -p 3000"

timeout /t 3 /nobreak >nul

echo.
echo ====================================
echo POC Intake Development Environment Started!
echo ====================================
echo.
echo Services running:
echo   - Backend:  http://localhost:8000
echo   - Frontend: http://localhost:3000
echo   - API Docs: http://localhost:8000/docs
echo.
echo To test the application:
echo   1. Encode an MRN in PowerShell: [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("YOUR_MRN"))
echo   2. Visit: http://localhost:3000?id=^<encoded_mrn^>
echo.
echo Close this window to keep services running, or press Ctrl+C to stop.
pause