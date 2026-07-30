@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python scripts\python\mysql\load\validate_loaded_data.py
if errorlevel 1 exit /b 1

echo.
echo LOADED DATA VALIDATION SUCCESSFUL
echo.

exit /b 0
