@echo off
setlocal EnableDelayedExpansion

REM =====================================
REM DISCOVER JAVA
REM =====================================

call "%~dp0discover_java.bat"

if errorlevel 1 (
    echo ERROR: JAVA DISCOVERY FAILED
    exit /b 1
)

echo.
echo =====================================
echo VALIDATING LIQUIBASE
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================


if not defined PROJECT_ROOT (
    call "%~dp0set_project_root.bat"
)

set "ROOT=%PROJECT_ROOT%"

set "CONFIG_FILE=%~1"
if not defined CONFIG_FILE set "CONFIG_FILE=%ROOT%\config\windows\mysql.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: CONFIG FILE NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM READ CONFIG
REM =====================================

for /f "tokens=1,2 delims==" %%A in (%CONFIG_FILE%) do (
    if /I "%%A"=="LIQUIBASE_VERSION" set "EXPECTED_VERSION=%%B"
)

if not defined EXPECTED_VERSION (
    echo ERROR: LIQUIBASE_VERSION NOT FOUND IN CONFIG
    exit /b 1
)

set "LIQUIBASE_HOME=%ROOT%\tools\liquibase"
set "LIQUIBASE_BAT=%LIQUIBASE_HOME%\liquibase.bat"

echo Expected Liquibase Version : %EXPECTED_VERSION%
echo.

REM =====================================
REM VALIDATE LIQUIBASE PATHS
REM =====================================

if not exist "%LIQUIBASE_HOME%" (
    echo ERROR: LIQUIBASE DIRECTORY NOT FOUND
    exit /b 1
)

if not exist "%LIQUIBASE_BAT%" (
    echo ERROR: LIQUIBASE.BAT NOT FOUND
    exit /b 1
)

REM =====================================
REM VALIDATE DISCOVERED JAVA
REM =====================================

if not defined JAVA_HOME (
    echo ERROR: JAVA_HOME NOT SET AFTER JAVA DISCOVERY
    exit /b 1
)

if not exist "%JAVA_HOME%\bin\java.exe" (
    echo ERROR: JAVA EXECUTABLE NOT FOUND
    echo Expected: %JAVA_HOME%\bin\java.exe
    exit /b 1
)

echo Java Found:
echo %JAVA_HOME%\bin\java.exe
echo.

echo =====================================
echo JAVA HOME BEFORE LIQUIBASE
echo =====================================
echo JAVA_HOME=%JAVA_HOME%
echo.

"%JAVA_HOME%\bin\java.exe" -version

if errorlevel 1 (
    echo ERROR: JAVA EXECUTION FAILED
    exit /b 1
)

echo.

REM =====================================
REM VALIDATE LIQUIBASE
REM =====================================

echo Checking Liquibase Version...
echo.

set "JAVA_PATH=%JAVA_HOME%\bin\java.exe"
set "LIQUIBASE_VERSION_FILE=%TEMP%\liquibase_version.txt"

call "%LIQUIBASE_BAT%" --version > "%LIQUIBASE_VERSION_FILE%" 2>&1
set "RC=%ERRORLEVEL%"

type "%LIQUIBASE_VERSION_FILE%"

echo.
echo Exit Code=%RC%
echo.

if not "%RC%"=="0" (
    echo ERROR: LIQUIBASE EXECUTION FAILED
    del "%LIQUIBASE_VERSION_FILE%" >nul 2>&1
    exit /b %RC%
)

REM =====================================
REM VALIDATE EXPECTED VERSION
REM =====================================

findstr /C:"Liquibase Version: %EXPECTED_VERSION%" "%LIQUIBASE_VERSION_FILE%" >nul

if errorlevel 1 (
    echo ERROR: LIQUIBASE VERSION MISMATCH
    echo Expected : %EXPECTED_VERSION%
    del "%LIQUIBASE_VERSION_FILE%" >nul 2>&1
    exit /b 1
)

del "%LIQUIBASE_VERSION_FILE%" >nul 2>&1

echo.
echo =====================================
echo LIQUIBASE VALIDATED
echo =====================================
echo.

exit /b 0
