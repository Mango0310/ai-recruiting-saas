@echo off
echo ============================================
echo   AI Recruiting SaaS - Start All Services
echo ============================================

echo.
echo [1/3] Starting Backend (port 8000)...
start "AI-Recruit-Backend" cmd /c "cd /d "D:\honor share\ai-recruiting-saas\backend" && .\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/3] Starting Frontend (port 3000)...
start "AI-Recruit-Frontend" cmd /c "cd /d "D:\honor share\ai-recruiting-saas\frontend" && npm run dev"

echo [3/3] Starting ngrok Tunnel...
start "AI-Recruit-ngrok" cmd /c "D:\honor share\ai-recruiting-saas\tools\ngrok\ngrok.exe http 3000"

echo.
echo All services starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo ngrok:    Check the ngrok window for the public URL
echo.
echo Close this window or press Ctrl+C in each window to stop.
echo ============================================
pause
