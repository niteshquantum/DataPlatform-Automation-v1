@echo off
setlocal

echo.
echo =====================================
echo VALIDATING MSSQL PORT
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

python "%PROJECT_ROOT%\scripts\python\mssql\setup\validate_port.py"

if errorlevel 1 (
    echo.
    echo PORT VALIDATION FAILED
    exit /b 1
)

echo.
echo PORT VALIDATION SUCCESSFUL
echo.

exit /b 0