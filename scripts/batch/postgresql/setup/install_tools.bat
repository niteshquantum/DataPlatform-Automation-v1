@echo off
setlocal

echo.
echo =====================================
echo INSTALLING POSTGRESQL TOOLS
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM INSTALL TERRAFORM
REM =====================================

echo [1/4] Installing Terraform...
call "%ROOT%\scripts\batch\common\install_terraform.bat"

if errorlevel 1 (
    echo ERROR: TERRAFORM INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM INSTALL LIQUIBASE
REM =====================================

echo [2/4] Installing Liquibase...
call "%ROOT%\scripts\batch\common\install_liquibase.bat"

if errorlevel 1 (
    echo ERROR: LIQUIBASE INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM INSTALL POSTGRESQL JDBC DRIVER
REM =====================================

echo [3/4] Installing PostgreSQL JDBC Driver...
call "%ROOT%\scripts\batch\postgresql\setup\install_postgresql_driver.bat"

if errorlevel 1 (
    echo ERROR: POSTGRESQL JDBC DRIVER INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM VALIDATE INSTALLED TOOLS
REM =====================================

echo [4/4] Validating Installed Tools...
call "%ROOT%\scripts\batch\postgresql\setup\validate_tools.bat"

if errorlevel 1 (
    echo ERROR: TOOL VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL TOOLS INSTALLED SUCCESSFULLY
echo =====================================
echo.

exit /b 0