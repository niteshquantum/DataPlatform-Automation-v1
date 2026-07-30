@echo off
setlocal

echo.
echo =====================================
echo VALIDATING POSTGRESQL PORT
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

python "%PROJECT_ROOT%\scripts\python\postgresql\setup\validate_port.py"

if errorlevel 1 (
    echo.
    echo ERROR: POSTGRESQL PORT VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL PORT VALIDATED
echo =====================================
echo.

exit /b 0