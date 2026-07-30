@echo off
setlocal EnableDelayedExpansion

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT SETUP FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo =====================================
echo MSSQL OBJECTS VALIDATION
echo =====================================
echo.

python scripts\python\common\objects\validate_objects.py mssql

if errorlevel 1 (
    echo ERROR: MSSQL OBJECTS VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MSSQL OBJECTS VALIDATION SUCCESSFUL
echo =====================================
echo.

exit /b 0
