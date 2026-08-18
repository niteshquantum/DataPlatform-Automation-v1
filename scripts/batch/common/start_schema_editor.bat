@echo off
setlocal

call "%~dp0set_project_root.bat"
if errorlevel 1 exit /b 1

set "SCHEMA_EDITOR_DATABASE=%~1"
if not defined SCHEMA_EDITOR_DATABASE set "SCHEMA_EDITOR_DATABASE=postgresql"

set "SCHEMA_EDITOR_PORT="
for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\config\common\network.conf") do (
    if /I "%%A"=="SCHEMA_EDITOR_PORT" set "SCHEMA_EDITOR_PORT=%%B"
)
if not defined SCHEMA_EDITOR_PORT set "SCHEMA_EDITOR_PORT=5000"

if exist "%PROJECT_ROOT%\outputs\logs" (
    set "LOG_DIR=%PROJECT_ROOT%\outputs\logs"
) else (
    mkdir "%PROJECT_ROOT%\outputs\logs" >nul 2>&1
    set "LOG_DIR=%PROJECT_ROOT%\outputs\logs"
)

set "START_LOG=%LOG_DIR%\schema_editor_%SCHEMA_EDITOR_DATABASE%.log"
set "APP_PATH=%PROJECT_ROOT%\scripts\schema_editor\app.py"

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
) else (
    set "PYTHON_EXE=python"
    set "PYTHON_ARGS="
)

set "START_CMD=\"%PYTHON_EXE%\" %PYTHON_ARGS% \"%APP_PATH%\" %SCHEMA_EDITOR_DATABASE% >> \"%START_LOG%\" 2>&1"

start "Schema Editor" /b cmd /c %START_CMD%
if errorlevel 1 (
    echo ERROR: Failed to launch Schema Editor in background.
    exit /b 1
)

for /l %%N in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-NetTCPConnection -LocalPort %SCHEMA_EDITOR_PORT% -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }).Count -gt 0" >nul 2>&1
    if not errorlevel 1 goto :started
    ping -n 2 127.0.0.1 >nul 2>&1
)

echo ERROR: Schema Editor did not start listening on localhost:%SCHEMA_EDITOR_PORT% within 30 seconds.
if exist "%START_LOG%" (
    echo Log file: %START_LOG%
    type "%START_LOG%"
)
exit /b 1

:started
if exist "%START_LOG%" (
    echo Schema Editor started successfully for database %SCHEMA_EDITOR_DATABASE% on port %SCHEMA_EDITOR_PORT%.
    echo Log file: %START_LOG%
) else (
    echo Schema Editor started successfully for database %SCHEMA_EDITOR_DATABASE% on port %SCHEMA_EDITOR_PORT%.
)
exit /b 0
