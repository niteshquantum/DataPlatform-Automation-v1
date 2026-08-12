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
REM GENERATE TARGET DDL
REM =====================================

echo.
echo =====================================
echo GENERATE TARGET DDL
echo =====================================
echo.

python "%PROJECT_ROOT%\scripts\python\migration\generate_ddl.py"

set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo TARGET DDL GENERATION FAILED
    echo Exit Code: %RC%
    exit /b %RC%
)

echo.
echo TARGET DDL GENERATION COMPLETED
echo.

exit /b 0
