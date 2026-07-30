@echo off
setlocal EnableDelayedExpansion

echo.
echo =====================================
echo VALIDATING LIQUIBASE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"
set "ROOT=%PROJECT_ROOT%"
set "CONFIG_FILE=%ROOT%\config\windows\mssql.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: MSSQL CONFIG NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

for /f "tokens=1,2 delims==" %%A in (%CONFIG_FILE%) do (
    if /I "%%A"=="LIQUIBASE_VERSION" set "EXPECTED_VERSION=%%B"
)

if not defined EXPECTED_VERSION (
    echo ERROR: LIQUIBASE_VERSION NOT FOUND IN mssql.conf
    exit /b 1
)

set "LIQUIBASE_HOME=%ROOT%\tools\liquibase"
set "LIQUIBASE_BAT=%LIQUIBASE_HOME%\liquibase.bat"
for /f "delims=" %%I in ('powershell -NoProfile -Command "[System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), 'mssql_liquibase_version_' + [System.Guid]::NewGuid().ToString('N') + '.txt')"') do set "VERSION_OUTPUT=%%I"

if not defined VERSION_OUTPUT (
    echo ERROR: FAILED TO CREATE A UNIQUE LIQUIBASE VERSION OUTPUT FILE NAME
    exit /b 1
)

echo Expected Liquibase Version : %EXPECTED_VERSION%
echo.

if not exist "%LIQUIBASE_HOME%" (
    echo ERROR: LIQUIBASE DIRECTORY NOT FOUND
    exit /b 1
)

if not exist "%LIQUIBASE_BAT%" (
    echo ERROR: LIQUIBASE.BAT NOT FOUND
    exit /b 1
)

where java >nul 2>&1
if errorlevel 1 (
    echo ERROR: JAVA NOT FOUND
    exit /b 1
)

echo Java Found:
where java

if exist "%VERSION_OUTPUT%" (
    echo ERROR: LIQUIBASE VERSION OUTPUT FILE ALREADY EXISTS
    echo File: %VERSION_OUTPUT%
    exit /b 1
)

echo.
echo Checking Liquibase Version...
echo.

call "%LIQUIBASE_BAT%" --version > "%VERSION_OUTPUT%" 2>&1
if errorlevel 1 (
    echo ERROR: LIQUIBASE EXECUTION FAILED
    if exist "%VERSION_OUTPUT%" type "%VERSION_OUTPUT%"
    call :cleanup_version_output
    exit /b 1
)

type "%VERSION_OUTPUT%"

findstr /C:"Liquibase Version: %EXPECTED_VERSION%" "%VERSION_OUTPUT%" >nul
if errorlevel 1 (
    echo.
    echo ERROR: LIQUIBASE VERSION MISMATCH
    echo Expected : %EXPECTED_VERSION%
    call :cleanup_version_output
    exit /b 1
)

call :cleanup_version_output
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo LIQUIBASE VALIDATED
echo =====================================
echo.

exit /b 0

:cleanup_version_output
if exist "%VERSION_OUTPUT%" del "%VERSION_OUTPUT%"
if exist "%VERSION_OUTPUT%" (
    echo ERROR: FAILED TO REMOVE LIQUIBASE VERSION OUTPUT FILE
    echo File: %VERSION_OUTPUT%
    exit /b 1
)
exit /b 0
