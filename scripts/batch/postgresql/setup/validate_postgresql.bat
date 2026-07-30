@echo off
setlocal

echo.
echo =====================================
echo VALIDATING POSTGRESQL
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python "%PROJECT_ROOT%\scripts\python\postgresql\setup\validate_postgresql.py"

if errorlevel 1 (
    echo.
    echo ERROR: POSTGRESQL VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL VALIDATED
echo =====================================
echo.

exit /b 0