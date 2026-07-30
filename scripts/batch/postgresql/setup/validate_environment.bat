@echo off
setlocal

echo.
echo =====================================
echo VALIDATING POSTGRESQL ENVIRONMENT
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_tools.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_port.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_postgresql.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo POSTGRESQL ENVIRONMENT VALIDATED
echo =====================================
echo.

exit /b 0