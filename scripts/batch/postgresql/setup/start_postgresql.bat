@echo off
setlocal

echo.
echo =====================================
echo STARTING POSTGRESQL
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: Unable to determine project root.
    exit /b 1
)

set "ROOT=%PROJECT_ROOT%"

set "START_SCRIPT=%ROOT%\scripts\powershell\postgresql\start_postgresql.ps1"

REM =====================================
REM CHECK SCRIPT
REM =====================================

if not exist "%START_SCRIPT%" (
    echo ERROR: PostgreSQL start script not found:
    echo %START_SCRIPT%
    exit /b 1
)

REM =====================================
REM START POSTGRESQL
REM =====================================

powershell.exe ^
-NoProfile ^
-NonInteractive ^
-ExecutionPolicy Bypass ^
-File "%START_SCRIPT%"

if errorlevel 1 (
    echo ERROR: PostgreSQL startup failed.
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL START COMPLETED
echo =====================================
echo.

exit /b 0
