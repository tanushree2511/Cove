@echo off
:: ─────────────────────────────────────────────────────────────
::  VisionArchive AI — Windows launcher
::  Usage: double-click or run in Command Prompt
:: ─────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion

title VisionArchive AI

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║        VisionArchive AI — Starting up        ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Resolve script directory ──────────────────────────────────
set "SCRIPT_DIR=%~dp0"
:: Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: ── 1. Virtualenv setup ───────────────────────────────────────
if not exist "%SCRIPT_DIR%\.venv\" (
    echo [VisionArchive] No .venv found — creating virtualenv...
    python -m venv "%SCRIPT_DIR%\.venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtualenv. Is Python 3.10+ installed?
        pause
        exit /b 1
    )
    echo [VisionArchive] Installing dependencies...
    "%SCRIPT_DIR%\.venv\Scripts\pip" install --upgrade pip -q
    "%SCRIPT_DIR%\.venv\Scripts\pip" install -r "%SCRIPT_DIR%\requirements.txt"
    echo [VisionArchive] Virtualenv ready.
) else (
    echo [VisionArchive] Using existing virtualenv at .venv
)

:: ── 2. GPU setting (safe default for Windows) ─────────────────
:: NVIDIA GPU detection on Windows is complex; default to CPU.
:: Set VISION_FORCE_CPU=0 manually if you have a supported GPU.
set "VISION_FORCE_CPU=1"
set "VISION_USE_GPU=0"
echo [VisionArchive] GPU: CPU mode (set VISION_FORCE_CPU=0 for GPU)

:: ── 3. Model and data directories ────────────────────────────
set "VISION_MODEL_DIR=%SCRIPT_DIR%\models"
set "VISION_USER_DATA=%APPDATA%\VisionArchive"
if not exist "%VISION_USER_DATA%\" mkdir "%VISION_USER_DATA%"
echo [VisionArchive] Model dir : %VISION_MODEL_DIR%
echo [VisionArchive] User data : %VISION_USER_DATA%

:: ── 4. Worker count ───────────────────────────────────────────
set "VISION_AI_WORKERS=%NUMBER_OF_PROCESSORS%"
echo [VisionArchive] AI workers: %VISION_AI_WORKERS%

:: ── 5. Kill stale processes on required ports ─────────────────
echo [VisionArchive] Freeing ports 8000 and 8001...

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [VisionArchive] Killing PID !PID! on port 8000
        taskkill /F /PID !PID! >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8001 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [VisionArchive] Killing PID !PID! on port 8001
        taskkill /F /PID !PID! >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8080 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [VisionArchive] Killing PID !PID! on port 8080
        taskkill /F /PID !PID! >nul 2>&1
    )
)

:: ── Log directory ─────────────────────────────────────────────
if not exist "%SCRIPT_DIR%\.logs\" mkdir "%SCRIPT_DIR%\.logs"

:: ── 6. Start cove-api ─────────────────────────────────────────
echo [VisionArchive] Starting cove-api   (port 8000)...
start "cove-api" /B cmd /c "cd /d "%SCRIPT_DIR%\cove" && set VISION_FORCE_CPU=%VISION_FORCE_CPU%&& set VISION_MODEL_DIR=%VISION_MODEL_DIR%&& set VISION_AI_WORKERS=%VISION_AI_WORKERS%&& "..\..\.venv\Scripts\python" -m uvicorn api.server:app --host 0.0.0.0 --port 8000 > "..\..\.logs\cove-api.log" 2>&1"

:: ── 7. Start video-api ────────────────────────────────────────
echo [VisionArchive] Starting video-api  (port 8001)...
start "video-api" /B cmd /c "cd /d "%SCRIPT_DIR%\videoModules" && set VISION_FORCE_CPU=%VISION_FORCE_CPU%&& set VISION_MODEL_DIR=%VISION_MODEL_DIR%&& set VISION_AI_WORKERS=%VISION_AI_WORKERS%&& "..\..\.venv\Scripts\python" -m uvicorn api:app --host 0.0.0.0 --port 8001 > "..\..\.logs\video-api.log" 2>&1"

:: ── 8. Start frontend ─────────────────────────────────────────
echo [VisionArchive] Starting frontend   (port 8080)...
start "frontend" /B cmd /c "cd /d "%SCRIPT_DIR%\frontend" && npm run dev -- --port 8080 > "..\.logs\frontend.log" 2>&1"

:: ── 9. Wait then open browser ─────────────────────────────────
echo [VisionArchive] Waiting 5 seconds for services to initialise...
timeout /t 5 /nobreak >nul
echo [VisionArchive] Opening browser at http://localhost:8080
start http://localhost:8080

:: ── 10. Instructions ──────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║  ✅  VisionArchive is running!               ║
echo  ║                                              ║
echo  ║  🌐  http://localhost:8080                   ║
echo  ║                                              ║
echo  ║  Logs are in .logs\                          ║
echo  ║  Close this window (or Ctrl+C) to stop.     ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Press Ctrl+C to stop all services.
echo.

:: Keep window open so the user can Ctrl+C
pause >nul
