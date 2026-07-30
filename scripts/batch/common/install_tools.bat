@echo off
setlocal

echo.
echo =====================================
echo INSTALLING TOOLS
echo =====================================
echo.

echo [1/3] Installing Terraform...
call "%~dp0install_terraform.bat"
if errorlevel 1 (
echo ERROR: TERRAFORM INSTALLATION FAILED
exit /b 1
)

echo [2/3] Installing MySQL JDBC Driver...
call "%~dp0install_mysql_driver.bat"
if errorlevel 1 (
echo ERROR: MYSQL JDBC DRIVER INSTALLATION FAILED
exit /b 1
)

echo [3/3] Installing Liquibase...
call "%~dp0install_liquibase.bat"
if errorlevel 1 (
echo ERROR: LIQUIBASE INSTALLATION FAILED
exit /b 1
)
echo [3/3] Validating Liquibase...
call "%~dp0validate_liquibase.bat"
if errorlevel 1 (
echo ERROR: LIQUIBASE validation FAILED
exit /b 1
)


echo.
echo Validating Installed Tools...
echo.

call "%~dp0validate_tools.bat"

if errorlevel 1 (
echo ERROR: TOOL VALIDATION FAILED
exit /b 1
)

echo.
echo =====================================
echo TOOLS INSTALLED SUCCESSFULLY
echo =====================================
echo.

exit /b 0
