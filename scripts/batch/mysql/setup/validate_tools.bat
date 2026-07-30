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

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"

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
call "%~dp0validate_liquibase.bat"
if errorlevel 1 (
    echo Liquibase not found. Installing...
    call "%ROOT%\scripts\batch\common\install_liquibase.bat"
    if errorlevel 1 (
        echo ERROR: LIQUIBASE INSTALLATION FAILED
        exit /b 1
    )
    echo Re-checking Liquibase...
    call "%~dp0validate_liquibase.bat"
    if errorlevel 1 exit /b 1
)

REM =====================================
REM MYSQL DRIVER
REM =====================================
echo Checking MySQL Driver...
call "%~dp0validate_mysql_driver.bat"
if errorlevel 1 (
    echo MySQL Driver not found. Installing...
    call "%ROOT%\scripts\batch\mysql\setup\install_mysql_driver.bat"
    if errorlevel 1 (
        echo ERROR: MYSQL JDBC DRIVER INSTALLATION FAILED
        exit /b 1
    )
    echo Re-checking MySQL Driver...
    call "%~dp0validate_mysql_driver.bat"
    if errorlevel 1 exit /b 1
)

echo TERRAFORM VALIDATED
echo.
echo =====================================
echo TOOLS VALIDATED SUCCESSFULLY
echo =====================================
echo.
exit /b 0
