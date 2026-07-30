@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"
set "TF=%ROOT%\tools\terraform\terraform.exe"

if not exist "%TF%" (
    echo ERROR: Terraform not found.
    exit /b 1
)

cd /d "%ROOT%\terraform\mongodb"

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

for /f "tokens=1* delims==" %%A in ('findstr /R "^MONGODB_PORT=" "%ROOT%\config\windows\mongodb.conf"') do set "MONGO_PORT=%%B"

"%TF%" apply -auto-approve -var="mongodb_port=%MONGO_PORT%"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo MONGODB DEPLOYMENT SUCCESSFUL
echo =====================================
echo.

exit /b 0