# PowerShell script to start both backend and frontend for POC Intake

Write-Host "Starting POC Intake Development Environment..." -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-CommandExists "uv")) {
    Write-Host "Error: 'uv' is not installed. Please install uv first." -ForegroundColor Red
    Write-Host "Visit: https://github.com/astral-sh/uv" -ForegroundColor Cyan
    exit 1
}

if (-not (Test-CommandExists "npm")) {
    Write-Host "Error: 'npm' is not installed. Please install Node.js first." -ForegroundColor Red
    Write-Host "Visit: https://nodejs.org/" -ForegroundColor Cyan
    exit 1
}

# Start Backend
Write-Host "Starting Backend (FastAPI)..." -ForegroundColor Yellow
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; Write-Host 'Starting Backend Server...' -ForegroundColor Green; uv run python main.py" -PassThru

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Yellow
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; Write-Host 'Starting Frontend Server...' -ForegroundColor Green; npx next dev" -PassThru

Start-Sleep -Seconds 3

# Display status
Write-Host ""
Write-Host "✅ POC Intake Development Environment Started!" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  - Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To test the application:" -ForegroundColor Yellow
Write-Host "  1. Encode an MRN: echo -n 'YOUR_MRN' | base64" -ForegroundColor White
Write-Host "  2. Visit: http://localhost:3000?id=<encoded_mrn>" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow

# Keep the script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backend.HasExited -or $frontend.HasExited) {
            Write-Host "One of the services has stopped!" -ForegroundColor Red
            break
        }
    }
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    if (-not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Services stopped." -ForegroundColor Green
}