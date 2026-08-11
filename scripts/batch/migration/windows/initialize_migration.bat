@echo off
setlocal

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT INITIALIZATION FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

REM =====================================
REM RUN MIGRATION INITIALIZATION
REM =====================================

echo.
echo =====================================
echo INITIALIZE MIGRATION
echo =====================================
echo.

python "%PROJECT_ROOT%\scripts\python\migration\initialize.py"

set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo MIGRATION INITIALIZATION FAILED
    echo Exit Code: %RC%
    exit /b %RC%
)

echo.
echo MIGRATION INITIALIZATION COMPLETED
echo.

exit /b 0
