@echo off
setlocal

echo.
echo =====================================
echo DEPLOYING SQL SERVER
echo =====================================
echo.

REM =====================================
REM DOWNLOAD MSSQL MEDIA
REM =====================================

echo.
echo =====================================
echo DOWNLOADING SQL SERVER MEDIA
echo =====================================
echo.

call "%~dp0download_mssql_media.bat"

if errorlevel 1 (
    echo.
    echo SQL SERVER MEDIA DOWNLOAD FAILED
    exit /b 1
)

echo.
echo SQL SERVER MEDIA READY
echo.

REM =====================================
REM GENERATE CONFIGURATION FILE
REM =====================================

echo.
echo =====================================
echo GENERATING SQL SERVER CONFIGURATION FILE
echo =====================================
echo.

call "%~dp0generate_configuration_file.bat"

if errorlevel 1 (
    echo.
    echo CONFIGURATION FILE GENERATION FAILED
    exit /b 1
)

echo.
echo CONFIGURATION FILE GENERATED SUCCESSFULLY
echo.

REM =====================================
REM INSTALL SQL SERVER
REM =====================================

echo.
echo =====================================
echo INSTALLING SQL SERVER
echo =====================================
echo.

call "%~dp0install_mssql.bat"

if errorlevel 1 (
    echo.
    echo SQL SERVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo SQL SERVER INSTALLATION SUCCESSFUL
echo.

echo.
echo =====================================
echo SQL SERVER DEPLOYMENT SUCCESSFUL
echo =====================================
echo.

exit /b 0