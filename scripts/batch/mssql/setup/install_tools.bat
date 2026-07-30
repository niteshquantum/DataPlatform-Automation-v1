@echo off
setlocal

echo.
echo =====================================
echo INSTALLING MSSQL TOOLS
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

echo [1/5] Installing Terraform...
call "%ROOT%\scripts\batch\common\install_terraform.bat"

if errorlevel 1 (
    echo ERROR: TERRAFORM INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM INSTALL LIQUIBASE
REM =====================================

echo [2/5] Installing Liquibase...
call "%ROOT%\scripts\batch\common\install_liquibase.bat"

if errorlevel 1 (
    echo ERROR: LIQUIBASE INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM INSTALL SQLCMD
REM =====================================

echo [3/5] Installing SQLCMD...
call "%ROOT%\scripts\batch\mssql\setup\install_sqlcmd.bat"

if errorlevel 1 (
    echo ERROR: SQLCMD INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM INSTALL MSSQL JDBC DRIVER
REM =====================================

echo [4/5] Installing MSSQL JDBC Driver...
call "%ROOT%\scripts\batch\mssql\setup\install_mssql_driver.bat"

if errorlevel 1 (
    echo ERROR: MSSQL JDBC DRIVER INSTALLATION FAILED
    exit /b 1
)

REM =====================================
REM VALIDATE INSTALLED TOOLS
REM =====================================

echo [5/5] Validating Installed Tools...
call "%ROOT%\scripts\batch\mssql\setup\validate_tools.bat"

if errorlevel 1 (
    echo ERROR: TOOL VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MSSQL TOOLS INSTALLED SUCCESSFULLY
echo =====================================
echo.

exit /b 0