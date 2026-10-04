@echo off
:: ─────────────────────────────────────────────────────────────
::  Cove — Windows launcher
::  Usage: double-click or run in Command Prompt
:: ─────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion

title Cove

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║        Cove — Starting up        ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Resolve script directory ──────────────────────────────────
set "SCRIPT_DIR=%~dp0"
:: Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: ── 1. Virtualenv setup ───────────────────────────────────────
if not exist "%SCRIPT_DIR%\.venv\" (
    echo [Cove] No .venv found — creating virtualenv...
    python -m venv "%SCRIPT_DIR%\.venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtualenv. Is Python 3.10+ installed?
        pause
        exit /b 1
    )
    echo [Cove] Installing dependencies...
    "%SCRIPT_DIR%\.venv\Scripts\pip" install --upgrade pip -q
    "%SCRIPT_DIR%\.venv\Scripts\pip" install -r "%SCRIPT_DIR%\requirements.txt"
    echo [Cove] Selecting the onnxruntime build for this PC...
    "%SCRIPT_DIR%\.venv\Scripts\python" "%SCRIPT_DIR%\scripts\install_runtime.py"
    echo [Cove] Virtualenv ready.
) else (
    echo [Cove] Using existing virtualenv at .venv
)

:: ── Node.js: make sure npm is reachable (the installer's PATH entry is missing in some shells) ──
where npm >nul 2>&1
if errorlevel 1 (
    if exist "%ProgramFiles%\nodejs\npm.cmd" (
        set "PATH=%PATH%;%ProgramFiles%\nodejs"
    ) else (
        echo [ERROR] npm not found. Install Node.js from https://nodejs.org and re-run.
        pause
        exit /b 1
    )
)

:: ── 2. Hardware ─────────────────────────────────────────────────
:: The app detects the hardware itself (CPU cores, NVIDIA / AMD / Intel / Qualcomm GPUs and NPUs) and benchmarks the
:: options on first start, keeping the fastest. Set COVE_FORCE_CPU=1 beforehand to disable accelerators.
echo [Cove] Hardware: auto-detected at start-up (see http://localhost:8000/hardware)

:: ── 3. Model and data directories ────────────────────────────
set "COVE_MODEL_DIR=%SCRIPT_DIR%\models"
set "COVE_USER_DATA=%APPDATA%\Cove"
if not exist "%COVE_USER_DATA%\" mkdir "%COVE_USER_DATA%"
echo [Cove] Model dir : %COVE_MODEL_DIR%
echo [Cove] User data : %COVE_USER_DATA%

:: ── 4. Worker count ───────────────────────────────────────────

:: ── 5. Kill stale processes on required ports ─────────────────
echo [Cove] Freeing ports 8000 and 8001...

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [Cove] Killing PID !PID! on port 8000
        taskkill /F /PID !PID! >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8001 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [Cove] Killing PID !PID! on port 8001
        taskkill /F /PID !PID! >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8080 "') do (
    set "PID=%%a"
    if not "!PID!"=="0" (
        echo [Cove] Killing PID !PID! on port 8080
        taskkill /F /PID !PID! >nul 2>&1
    )
)

:: ── Log directory ─────────────────────────────────────────────
if not exist "%SCRIPT_DIR%\.logs\" mkdir "%SCRIPT_DIR%\.logs"

:: ── 6. Start cove-api ─────────────────────────────────────────
echo [Cove] Starting cove-api   (port 8000)...
start "cove-api" /B cmd /c "cd /d "%SCRIPT_DIR%\cove" && set COVE_MODEL_DIR=%COVE_MODEL_DIR%&& "%SCRIPT_DIR%\.venv\Scripts\python" -m uvicorn api.server:app --host 0.0.0.0 --port 8000 > "%SCRIPT_DIR%\.logs\cove-api.log" 2>&1"

:: ── 7. Start video-api ────────────────────────────────────────
echo [Cove] Starting video-api  (port 8001)...
start "video-api" /B cmd /c "cd /d "%SCRIPT_DIR%\videoModules" && set COVE_MODEL_DIR=%COVE_MODEL_DIR%&& "%SCRIPT_DIR%\.venv\Scripts\python" -m uvicorn api:app --host 0.0.0.0 --port 8001 > "%SCRIPT_DIR%\.logs\video-api.log" 2>&1"

:: ── 8. Start frontend ─────────────────────────────────────────
echo [Cove] Starting frontend   (port 8080)...
start "frontend" /B cmd /c "cd /d "%SCRIPT_DIR%\frontend" && npm run dev -- --port 8080 > "..\.logs\frontend.log" 2>&1"

:: ── 9. Wait then open browser ─────────────────────────────────
echo [Cove] Waiting 5 seconds for services to initialise...
timeout /t 5 /nobreak >nul
echo [Cove] Opening browser at http://localhost:8080
start http://localhost:8080

:: ── 10. Instructions ──────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║  ✅  Cove is running!               ║
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
