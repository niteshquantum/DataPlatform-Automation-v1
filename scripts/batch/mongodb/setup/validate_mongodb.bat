@echo off
setlocal

echo.
echo =====================================
echo VALIDATING MONGODB
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python "%PROJECT_ROOT%\scripts\python\mongodb\setup\validate_instance.py"

if errorlevel 1 (
    echo.
    echo MONGODB INSTANCE VALIDATION FAILED
    exit /b 1
)

echo.
echo MONGODB INSTANCE VALIDATION SUCCESSFUL
echo.

exit /b 0