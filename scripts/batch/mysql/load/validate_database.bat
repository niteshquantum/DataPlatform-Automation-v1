@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT SETUP FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python scripts\python\mysql\load\validate_database.py

if errorlevel 1 (
    echo.
    echo DATABASE VALIDATION FAILED
    exit /b 1
)

echo.
echo DATABASE VALIDATION SUCCESSFUL
echo.

exit /b 0
