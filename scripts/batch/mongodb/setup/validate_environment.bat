@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"

echo.
echo =====================================
echo ENVIRONMENT VALIDATION STARTED
echo =====================================
echo.

echo [1/6] Validating Python Runtime...
call "%ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 (
    echo ERROR: PYTHON RUNTIME VALIDATION FAILED
    exit /b 1
)

echo [2/6] Validating Python Requirements...
call "%ROOT%\scripts\batch\mongodb\setup\validate_python_requirements.bat"
if errorlevel 1 (
    echo ERROR: PYTHON REQUIREMENTS VALIDATION FAILED
    exit /b 1
)

echo [3/6] Validating Tools...
call "%ROOT%\scripts\batch\mongodb\setup\validate_tools.bat"
if errorlevel 1 (
    echo ERROR: TOOLS VALIDATION FAILED
    exit /b 1
)

echo [4/6] Validating MongoDB Port...
call "%ROOT%\scripts\batch\mongodb\setup\validate_port.bat"
if errorlevel 1 (
    echo ERROR: MONGODB PORT VALIDATION FAILED
    exit /b 1
)

echo [5/6] Validating MongoDB Instance...
call "%ROOT%\scripts\batch\mongodb\setup\validate_mongodb.bat"
if errorlevel 1 (
    echo ERROR: MONGODB INSTANCE VALIDATION FAILED
    exit /b 1
)

echo [6/6] Validating Java Runtime...
call "%ROOT%\scripts\batch\common\validate_java_runtime.bat"
if errorlevel 1 (
    echo ERROR: JAVA RUNTIME VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo ENVIRONMENT VALIDATION SUCCESSFUL
echo =====================================
echo.

exit /b 0
