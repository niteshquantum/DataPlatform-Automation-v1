@echo off
setlocal

REM =====================================
REM ROOT PATH
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM TERRAFORM PATH
REM =====================================

set TF=%ROOT%\tools\terraform\terraform.exe

REM =====================================
REM CHECK TERRAFORM
REM =====================================

if not exist "%TF%" (
echo Terraform is not installed.
echo Run install_terraform.bat first.
exit /b 1
)

REM =====================================
REM GO TO MYSQL TERRAFORM
REM =====================================

cd /d "%ROOT%\terraform\mysql"

echo.
echo =====================================
echo TERRAFORM INIT
echo =====================================
echo.

"%TF%" init
if errorlevel 1 (
echo ERROR: TERRAFORM INIT FAILED
exit /b 1
)

echo.
echo =====================================
echo TERRAFORM APPLY
echo =====================================
echo.

"%TF%" apply ^
-target=null_resource.download_mysql_windows ^
-target=null_resource.extract_mysql_windows ^
-target=null_resource.init_mysql_windows ^
-target=null_resource.start_mysql_windows ^
-target=null_resource.create_mysql_user_windows ^
-auto-approve
if errorlevel 1 (
echo ERROR: TERRAFORM APPLY FAILED
exit /b 1
)

exit /b 0
