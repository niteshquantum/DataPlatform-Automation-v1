@echo off
setlocal EnableDelayedExpansion

call "%~dp0set_project_root.bat"
if errorlevel 1 exit /b 1

set "SCHEMA_EDITOR_DATABASE=%~1"
if not defined SCHEMA_EDITOR_DATABASE set "SCHEMA_EDITOR_DATABASE=postgresql"

set "SCHEMA_EDITOR_PORT="
for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\config\common\network.conf") do (
    if /I "%%A"=="SCHEMA_EDITOR_PORT" set "SCHEMA_EDITOR_PORT=%%B"
)
if not defined SCHEMA_EDITOR_PORT set "SCHEMA_EDITOR_PORT=5000"

if not exist "%PROJECT_ROOT%\outputs\logs" (
    mkdir "%PROJECT_ROOT%\outputs\logs" >nul 2>&1
)
set "LOG_DIR=%PROJECT_ROOT%\outputs\logs"
set "START_LOG=%LOG_DIR%\schema_editor_%SCHEMA_EDITOR_DATABASE%.log"
set "APP_PATH=%PROJECT_ROOT%\scripts\schema_editor\app.py"
set "LAUNCHER=%LOG_DIR%\schema_editor_launch_%SCHEMA_EDITOR_DATABASE%.bat"

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
) else (
    set "PYTHON_EXE=python"
    set "PYTHON_ARGS="
)

echo Starting Schema Editor for database %SCHEMA_EDITOR_DATABASE% on port %SCHEMA_EDITOR_PORT%...

type nul > "%START_LOG%"

(
    echo @echo off
    echo cd /d "%PROJECT_ROOT%"
    echo set "SCHEMA_EDITOR_PORT=%SCHEMA_EDITOR_PORT%"
    echo "%PYTHON_EXE%" %PYTHON_ARGS% "%APP_PATH%" %SCHEMA_EDITOR_DATABASE% 1^>^>"%START_LOG%" 2^>^&1
) > "%LAUNCHER%"

if not exist "%LAUNCHER%" (
    echo ERROR: Failed to create Schema Editor launcher script.
    exit /b 1
)

start "Schema Editor" /b cmd /c "%LAUNCHER%"
if errorlevel 1 (
    echo ERROR: Failed to launch Schema Editor background process.
    if exist "%LAUNCHER%" del /f /q "%LAUNCHER%" >nul 2>&1
    exit /b 1
)

for /l %%N in (1,1,30) do (
    call :check_ready
    if errorlevel 1 (
        ping -n 2 127.0.0.1 >nul 2>&1
    ) else (
        goto :verified
    )
)

echo ERROR: Schema Editor did not become ready on localhost:%SCHEMA_EDITOR_PORT% within 30 seconds.
goto :fail

:check_ready
netstat -an | findstr /R /C:":%SCHEMA_EDITOR_PORT% .*LISTENING" >nul 2>&1
if errorlevel 1 exit /b 1

curl.exe -s -o nul --connect-timeout 3 --max-time 5 "http://127.0.0.1:%SCHEMA_EDITOR_PORT%/" >nul 2>&1
if errorlevel 1 exit /b 1

exit /b 0

:verified
echo Schema Editor started successfully for database %SCHEMA_EDITOR_DATABASE% on port %SCHEMA_EDITOR_PORT%.
echo Log file: %START_LOG%
if exist "%LAUNCHER%" del /f /q "%LAUNCHER%" >nul 2>&1
exit /b 0

:fail
if exist "%START_LOG%" (
    echo.
    echo --- Schema Editor log ---
    type "%START_LOG%"
    echo --- end log ---
) else (
    echo No Schema Editor log was produced at: %START_LOG%
)
if exist "%LAUNCHER%" del /f /q "%LAUNCHER%" >nul 2>&1
exit /b 1
