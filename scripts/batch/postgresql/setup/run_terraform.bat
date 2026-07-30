@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"
set "TF=%ROOT%\tools\terraform\terraform.exe"

if not exist "%TF%" (
    echo ERROR: Terraform not found.
    exit /b 1
)

cd /d "%ROOT%\terraform\postgresql"

echo.
echo =====================================
echo TERRAFORM INIT
echo =====================================
echo.

"%TF%" init
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo TERRAFORM APPLY
echo =====================================
echo.

"%TF%" apply -auto-approve
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo POSTGRESQL DEPLOYMENT SUCCESSFUL
echo =====================================
echo.

exit /b 0