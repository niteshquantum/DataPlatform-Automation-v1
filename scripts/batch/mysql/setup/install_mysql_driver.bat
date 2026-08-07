@echo off
setlocal

echo.
echo =====================================
echo INSTALLING MYSQL DRIVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"
set "DATA_PLATFORM_CONFIG_FILE=%ROOT%\config\windows\mysql.conf"

if defined DATA_PLATFORM_TOOLS_ROOT (
    set "TOOLS_ROOT=%DATA_PLATFORM_TOOLS_ROOT%"
) else (
    set "TOOLS_ROOT=C:\Program Files\DataPlatform\tools"
)

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\..\powershell\mysql\download_mysql_driver.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: MYSQL DRIVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo MYSQL DRIVER INSTALLATION SUCCESSFUL
echo.

exit /b 0
