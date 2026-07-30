@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo VALIDATING LOADED DATA
echo =====================================
echo.

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

cd /d "%PROJECT_ROOT%"

python scripts\python\mongodb\load\validate_loaded_data.py

if errorlevel 1 (
    echo.
    echo LOADED DATA VALIDATION FAILED
    exit /b 1
)

echo.
echo LOADED DATA VALIDATION SUCCESSFUL
echo.

exit /b 0
