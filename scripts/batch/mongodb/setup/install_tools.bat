@echo off
setlocal

echo.
echo =====================================
echo INSTALLING MONGODB TOOLS
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

echo [1/2] Installing Terraform...
call "%ROOT%\scripts\batch\common\install_terraform.bat"

if errorlevel 1 (
    echo ERROR: TERRAFORM INSTALLATION FAILED
    exit /b 1
)

echo [2/2] Validating Installed Tools...
call "%ROOT%\scripts\batch\mongodb\setup\validate_tools.bat"

if errorlevel 1 (
    echo ERROR: TOOL VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MONGODB TOOLS INSTALLED SUCCESSFULLY
echo =====================================
echo.

exit /b 0