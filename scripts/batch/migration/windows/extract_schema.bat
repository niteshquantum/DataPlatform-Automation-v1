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
REM EXTRACT SOURCE SCHEMA
REM =====================================

echo.
echo =====================================
echo EXTRACT SOURCE SCHEMA
echo =====================================
echo.

python "%PROJECT_ROOT%\scripts\python\migration\extract_schema.py"

set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo SOURCE SCHEMA EXTRACTION FAILED
    echo Exit Code: %RC%
    exit /b %RC%
)

echo.
echo SOURCE SCHEMA EXTRACTION COMPLETED
echo.

exit /b 0
