@echo off
setlocal

echo.
echo =====================================
echo VALIDATING TOOLS
echo =====================================
echo.

REM =====================================
REM TERRAFORM
REM =====================================

if not exist tools\terraform\terraform.exe (
echo ERROR: TERRAFORM NOT FOUND
exit /b 1
)

echo Checking Terraform...
tools\terraform\terraform.exe version
echo Checking Liquibase...
call "%~dp0validate_liquibase.bat"
if errorlevel 1 exit /b 1

echo Checking MySQL Driver...
call "%~dp0..\mysql\setup\validate_mysql_driver.bat"
if errorlevel 1 exit /b 1

echo TERRAFORM VALIDATED




echo.
echo =====================================
echo TOOLS VALIDATED SUCCESSFULLY
echo =====================================
echo.

exit /b 0
