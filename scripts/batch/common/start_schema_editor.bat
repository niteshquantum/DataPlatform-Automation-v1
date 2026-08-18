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

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

start "Schema Editor" /b cmd /c "%PYTHON_CMD% \"%PROJECT_ROOT%\scripts\schema_editor\app.py\" %SCHEMA_EDITOR_DATABASE% >> \"%START_LOG%\" 2>&1"

if errorlevel 1 (
    echo ERROR: Failed to launch Schema Editor in background.
    exit /b 1
)

echo Schema Editor background launch started for database %SCHEMA_EDITOR_DATABASE% on port %SCHEMA_EDITOR_PORT%
exit /b 0
