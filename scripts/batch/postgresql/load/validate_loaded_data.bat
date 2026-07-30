@echo off
setlocal

echo.
echo =====================================
echo VALIDATING POSTGRESQL LOADED DATA
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python scripts\python\postgresql\load\validate_loaded_data.py

if errorlevel 1 (
    echo.
    echo POSTGRESQL LOADED DATA VALIDATION FAILED
    exit /b 1
)

echo.
echo POSTGRESQL LOADED DATA VALIDATION SUCCESSFUL
echo.

exit /b 0