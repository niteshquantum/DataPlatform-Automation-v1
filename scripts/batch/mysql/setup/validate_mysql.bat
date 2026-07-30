@echo off
setlocal

echo.
echo =====================================
echo VALIDATING MYSQL
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo PROJECT_ROOT=%PROJECT_ROOT%
echo PYTHONPATH=%PYTHONPATH%
echo.

python "%PROJECT_ROOT%\scripts\python\mysql\setup\validate_instance.py"

if errorlevel 1 (
    echo.
    echo MYSQL INSTANCE VALIDATION FAILED
    exit /b 1
)

echo.
echo MYSQL INSTANCE VALIDATION SUCCESSFUL
echo.

exit /b 0