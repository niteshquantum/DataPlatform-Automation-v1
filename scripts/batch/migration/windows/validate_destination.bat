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
REM VALIDATE DESTINATION
REM =====================================

echo.
echo =====================================
echo VALIDATE DESTINATION
echo =====================================
echo.

python "%PROJECT_ROOT%\scripts\python\migration\validate_destination.py"

set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo DESTINATION VALIDATION FAILED
    echo Exit Code: %RC%
    exit /b %RC%
)

echo.
echo DESTINATION VALIDATION COMPLETED
echo.

exit /b 0
