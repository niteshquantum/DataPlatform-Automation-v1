@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo DEPLOYING SQL SERVER
echo =====================================
echo.

REM =====================================
REM MEDIA SOURCE CONFIG
REM =====================================

set "MSSQL_MEDIA_SOURCE=gdrive"

if not exist "%PROJECT_ROOT%\config\windows\mssql_media.conf" (
    echo MSSQL media config not found.
    echo Using default media source: gdrive
) else (
    for /f "tokens=1,2 delims==" %%A in ('type "%PROJECT_ROOT%\config\windows\mssql_media.conf"') do (
        if /I "%%A"=="MSSQL_MEDIA_SOURCE" if not "%%B"=="" set "MSSQL_MEDIA_SOURCE=%%B"
    )
)

echo.
echo Media Source : %MSSQL_MEDIA_SOURCE%
echo.

if /I not "%MSSQL_MEDIA_SOURCE%"=="gdrive" if /I not "%MSSQL_MEDIA_SOURCE%"=="microsoft" (
    echo.
    echo ERROR: Invalid MSSQL_MEDIA_SOURCE=%MSSQL_MEDIA_SOURCE%
    echo Valid values: gdrive, microsoft
    exit /b 1
)

if /I "%MSSQL_MEDIA_SOURCE%"=="microsoft" (

    REM =====================================
    REM DOWNLOAD MSSQL OFFICIAL BOOTSTRAPPER
    REM =====================================

    echo.
    echo =====================================
    echo DOWNLOADING SQL SERVER
    echo =====================================
    echo.

    call "%~dp0\download_mssql.bat"

    if errorlevel 1 (
        echo.
        echo SQL SERVER DOWNLOAD FAILED
        exit /b 1
    )

    REM =====================================
    REM PREPARE INSTALLATION MEDIA
    REM =====================================

    echo.
    echo =====================================
    echo PREPARING SQL SERVER INSTALLATION MEDIA
    echo =====================================
    echo.

    call "%~dp0\prepare_mssql_media.bat"

    if errorlevel 1 (
        echo.
        echo PREPARATION OF INSTALLATION MEDIA FAILED
        exit /b 1
    )

) else (

    REM =====================================
    REM DOWNLOAD MSSQL MEDIA (GDRIVE)
    REM =====================================

    echo.
    echo =====================================
    echo DOWNLOADING SQL SERVER MEDIA
    echo =====================================
    echo.

    call "%~dp0\download_mssql_media.bat"

    if errorlevel 1 (
        echo.
        echo SQL SERVER MEDIA DOWNLOAD FAILED
        exit /b 1
    )

    echo.
    echo SQL SERVER MEDIA READY
    echo.
)

REM =====================================
REM GENERATE CONFIGURATION FILE
REM =====================================

echo.
echo =====================================
echo GENERATING SQL SERVER CONFIGURATION FILE
echo =====================================
echo.

call "%~dp0\generate_configuration_file.bat"

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

call "%~dp0\install_mssql.bat"

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