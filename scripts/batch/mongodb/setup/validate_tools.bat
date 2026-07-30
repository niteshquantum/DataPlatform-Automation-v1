@echo off
setlocal

echo.
echo =====================================
echo VALIDATING TOOLS
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM TERRAFORM
REM =====================================

if not exist "%ROOT%\tools\terraform\terraform.exe" (
    echo WARNING: TERRAFORM NOT FOUND
    echo Terraform is required only for NO_INSTANCE deployment.
    echo Skipping Terraform validation.
    goto :tools_done
)

echo Checking Terraform...
"%ROOT%\tools\terraform\terraform.exe" version

echo TERRAFORM VALIDATED

:tools_done

echo.
echo =====================================
echo TOOLS VALIDATION COMPLETED
echo =====================================
echo.

exit /b 0