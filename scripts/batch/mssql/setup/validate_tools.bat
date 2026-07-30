@echo off
setlocal

echo.
echo =====================================
echo VALIDATING TOOLS
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM TERRAFORM
REM =====================================

if not exist "%ROOT%\tools\terraform\terraform.exe" (
    echo ERROR: TERRAFORM NOT FOUND
    exit /b 1
)

echo Checking Terraform...
"%ROOT%\tools\terraform\terraform.exe" version

REM =====================================
REM LIQUIBASE
REM =====================================

echo Checking Liquibase...
call "%ROOT%\scripts\batch\mssql\setup\validate_liquibase.bat"
if errorlevel 1 exit /b 1

REM =====================================
REM SQLCMD
REM =====================================

echo Checking SQLCMD...
call "%ROOT%\scripts\batch\mssql\setup\validate_sqlcmd.bat"
if errorlevel 1 exit /b 1

REM =====================================
REM MSSQL DRIVER
REM =====================================

echo Checking MSSQL JDBC Driver...
call "%ROOT%\scripts\batch\mssql\setup\validate_mssql_driver.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo TOOLS VALIDATED SUCCESSFULLY
echo =====================================
echo.

exit /b 0
