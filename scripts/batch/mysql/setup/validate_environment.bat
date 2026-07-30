@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"

echo.
echo =====================================
echo ENVIRONMENT VALIDATION STARTED
echo =====================================
echo.

echo [1/5] Validating Python Runtime...
call "%ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 (
    echo ERROR: PYTHON RUNTIME VALIDATION FAILED
    exit /b 1
)

echo [2/5] Validating Python Requirements...
call "%ROOT%\scripts\batch\mysql\setup\validate_python_requirements.bat"
if errorlevel 1 (
    echo ERROR: PYTHON REQUIREMENTS VALIDATION FAILED
    exit /b 1
)

echo [3/5] Validating Tools...
call "%ROOT%\scripts\batch\mysql\setup\validate_tools.bat"
if errorlevel 1 (
    echo ERROR: TOOLS VALIDATION FAILED
    exit /b 1
)

echo [4/5] Validating MySQL Port...
call "%ROOT%\scripts\batch\mysql\setup\validate_port.bat"
if errorlevel 1 (
    echo ERROR: MYSQL PORT VALIDATION FAILED
    exit /b 1
)

echo [5/5] Validating MySQL...
call "%ROOT%\scripts\batch\mysql\setup\validate_mysql.bat"
if errorlevel 1 (
    echo ERROR: MYSQL VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo ENVIRONMENT VALIDATION SUCCESSFUL
echo =====================================
echo.

exit /b 0
