# Voice Agent Demo - Start Script
# Runs both backend and frontend servers

Write-Host "Starting Voice Agent Demo..." -ForegroundColor Cyan
Write-Host ""

# Start Backend (FastAPI)
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Yellow

$scriptPath = $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\backend'; .\venv\Scripts\Activate.ps1; python main.py"

# Wait for backend to initialize
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# Start Frontend (React)
Write-Host "Starting React Frontend on port 5173..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Application will open in your browser shortly..." -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

Set-Location frontend
npm run dev
