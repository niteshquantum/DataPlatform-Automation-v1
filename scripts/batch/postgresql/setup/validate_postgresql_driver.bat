@echo off
setlocal EnableDelayedExpansion

echo.
echo =====================================
echo VALIDATING POSTGRESQL JDBC DRIVER
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"
set "CONFIG_FILE=%ROOT%\config\windows\postgresql.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: POSTGRESQL CONFIG NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM READ CONFIG
REM =====================================

for /f "tokens=1,2 delims==" %%A in (%CONFIG_FILE%) do (
    if /I "%%A"=="POSTGRESQL_DRIVER_VERSION" set "EXPECTED_VERSION=%%B"
)

if not defined EXPECTED_VERSION (
    echo ERROR: POSTGRESQL_DRIVER_VERSION NOT FOUND IN postgresql.conf
    exit /b 1
)

echo Expected Driver Version : %EXPECTED_VERSION%
echo.

REM =====================================
REM DRIVER DIRECTORY
REM =====================================

set "DRIVER_DIR=%ROOT%\tools\drivers"

if not exist "%DRIVER_DIR%" (
    echo ERROR: DRIVER DIRECTORY NOT FOUND
    echo Expected: %DRIVER_DIR%
    exit /b 1
)

REM =====================================
REM EXPECTED JAR
REM =====================================

set "EXPECTED_JAR=%DRIVER_DIR%\postgresql-%EXPECTED_VERSION%.jar"

if not exist "%EXPECTED_JAR%" (
    echo ERROR: EXPECTED JDBC DRIVER NOT FOUND
    echo Expected: %EXPECTED_JAR%
    exit /b 1
)

echo Driver Found:
echo %EXPECTED_JAR%

echo.
echo =====================================
echo POSTGRESQL JDBC DRIVER VALIDATED
echo =====================================
echo.

exit /b 0