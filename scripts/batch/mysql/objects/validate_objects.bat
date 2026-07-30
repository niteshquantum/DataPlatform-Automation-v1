@echo off
setlocal EnableDelayedExpansion

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo =====================================
echo MYSQL OBJECTS VALIDATION
echo =====================================
echo.

python scripts\python\common\objects\validate_objects.py mysql

if errorlevel 1 (
echo ERROR: OBJECTS VALIDATION FAILED
exit /b 1
)

echo.
echo =====================================
echo MYSQL OBJECTS VALIDATION SUCCESSFUL
echo =====================================
echo.

exit /b 0
