@echo off
setlocal

echo.
echo =====================================
echo DEPLOYING POSTGRESQL
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: Unable to determine project root.
    exit /b 1
)

set "ROOT=%PROJECT_ROOT%"
set "TF=%ROOT%\tools\terraform\terraform.exe"

REM =====================================
REM CHECK TERRAFORM
REM =====================================

if not exist "%TF%" (
    echo ERROR: Terraform not found:
    echo %TF%
    exit /b 1
)

REM =====================================
REM GO TO TERRAFORM DIRECTORY
REM =====================================

cd /d "%ROOT%\terraform\postgresql"

if errorlevel 1 (
    echo ERROR: Unable to access Terraform directory.
    exit /b 1
)

REM =====================================
REM TERRAFORM INIT
REM =====================================

echo.
echo =====================================
echo TERRAFORM INIT
echo =====================================
echo.

"%TF%" init

if errorlevel 1 (
    echo ERROR: Terraform initialization failed.
    exit /b 1
)

REM =====================================
REM TERRAFORM VALIDATE
REM =====================================

echo.
echo =====================================
echo TERRAFORM VALIDATE
echo =====================================
echo.

"%TF%" validate

if errorlevel 1 (
    echo ERROR: Terraform validation failed.
    exit /b 1
)

REM =====================================
REM TERRAFORM APPLY
REM =====================================

echo.
echo =====================================
echo TERRAFORM APPLY
echo =====================================
echo.

"%TF%" apply ^
-target=null_resource.install_postgresql_windows ^
-auto-approve

if errorlevel 1 (
    echo ERROR: Terraform deployment failed.
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL DEPLOYMENT COMPLETED
echo =====================================
echo.

exit /b 0
