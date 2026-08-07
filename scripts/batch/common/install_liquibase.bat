@echo off
setlocal

echo.
echo =====================================
echo INSTALLING LIQUIBASE
echo =====================================
echo.

if defined DATA_PLATFORM_TOOLS_ROOT (
    set "TOOLS_ROOT=%DATA_PLATFORM_TOOLS_ROOT%"
) else (
    set "TOOLS_ROOT=C:\Program Files\DataPlatform\tools"
)

if exist "%TOOLS_ROOT%\liquibase\liquibase.bat" (
    echo Liquibase already installed. Skipping installation.
    exit /b 0
)

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\powershell\download_liquibase.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: LIQUIBASE INSTALLATION FAILED
    exit /b 1
)

echo.
echo LIQUIBASE INSTALLATION SUCCESSFUL
echo.

exit /b 0
