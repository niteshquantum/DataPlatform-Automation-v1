@echo off
setlocal EnableDelayedExpansion

echo.
echo =====================================
echo RUNNING MIGRATION LIQUIBASE
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT INITIALIZATION FAILED
    exit /b 1
)

set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM ARGUMENTS
REM =====================================

set "DB_TYPE=%~1"
set "CHANGELOG=%~2"
set "LB_COMMAND=%~3"

if "%DB_TYPE%"=="" (
    echo ERROR: Database type not provided
    echo Usage: run_liquibase.bat ^<DB_TYPE^> ^<CHANGELOG^> [LB_COMMAND]
    exit /b 1
)

if "%CHANGELOG%"=="" (
    set "CHANGELOG=liquibase\%DB_TYPE%\master.xml"
)

if "%LB_COMMAND%"=="" (
    set "LB_COMMAND=update"
)

REM =====================================
REM MIGRATION CONFIG
REM =====================================

set "CONFIG_FILE=%ROOT%\config\windows\migration\%DB_TYPE%.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: MIGRATION CONFIG NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM READ CONFIG
REM =====================================

set "DB_HOST="
set "DB_PORT="
set "DB_NAME="
set "DB_USER="
set "DB_PASSWORD="
set "DB_DRIVER_VERSION="
set "DB_ODBC_DRIVER="
set "EXPECTED_LIQUIBASE_VERSION="

for /f "tokens=1,2 delims==" %%A in (%CONFIG_FILE%) do (
    set "KEY=%%A"
    set "VALUE=%%B"

    if /I "!KEY!"=="%DB_TYPE%_HOST" set "DB_HOST=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_PORT" set "DB_PORT=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_DB" set "DB_NAME=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_USER" set "DB_USER=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_PASSWORD" set "DB_PASSWORD=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_DRIVER_VERSION" set "DB_DRIVER_VERSION=!VALUE!"
    if /I "!KEY!"=="%DB_TYPE%_ODBC_DRIVER" set "DB_ODBC_DRIVER=!VALUE!"
    if /I "!KEY!"=="LIQUIBASE_VERSION" set "EXPECTED_LIQUIBASE_VERSION=!VALUE!"
)

REM =====================================
REM VALIDATE REQUIRED CONFIG
REM =====================================

if not defined DB_HOST (
    echo ERROR: %DB_TYPE%_HOST NOT FOUND IN MIGRATION CONFIG
    echo File: %CONFIG_FILE%
    exit /b 1
)

if not defined DB_PORT (
    echo ERROR: %DB_TYPE%_PORT NOT FOUND IN MIGRATION CONFIG
    echo File: %CONFIG_FILE%
    exit /b 1
)

if not defined DB_NAME (
    echo ERROR: %DB_TYPE%_DB NOT FOUND IN MIGRATION CONFIG
    echo File: %CONFIG_FILE%
    exit /b 1
)

if not defined DB_USER (
    echo ERROR: %DB_TYPE%_USER NOT FOUND IN MIGRATION CONFIG
    echo File: %CONFIG_FILE%
    exit /b 1
)

if not defined DB_DRIVER_VERSION (
    echo ERROR: %DB_TYPE%_DRIVER_VERSION NOT FOUND IN MIGRATION CONFIG
    echo File: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM VALIDATE LIQUIBASE
REM =====================================

call "%ROOT%\scripts\batch\common\validate_liquibase.bat" "%CONFIG_FILE%"

if errorlevel 1 (
    echo ERROR: LIQUIBASE VALIDATION FAILED
    exit /b 1
)

REM =====================================
REM VALIDATE JDBC DRIVER
REM =====================================

echo.
echo =====================================
echo VALIDATING %DB_TYPE% JDBC DRIVER
echo =====================================
echo.

set "DRIVER_DIR=%ROOT%\tools\drivers"

if not exist "%DRIVER_DIR%" (
    echo ERROR: DRIVER DIRECTORY NOT FOUND
    echo Expected: %DRIVER_DIR%
    exit /b 1
)

if /I "%DB_TYPE%"=="MSSQL" (
    set "EXPECTED_DRIVER=%DRIVER_DIR%\mssql-jdbc-%DB_DRIVER_VERSION%.jre11.jar"
) else if /I "%DB_TYPE%"=="MYSQL" (
    set "EXPECTED_DRIVER=%DRIVER_DIR%\mysql-connector-j-%DB_DRIVER_VERSION%.jar"
) else if /I "%DB_TYPE%"=="POSTGRESQL" (
    set "EXPECTED_DRIVER=%DRIVER_DIR%\postgresql-%DB_DRIVER_VERSION%.jar"
) else (
    echo ERROR: Unsupported database type for driver validation: %DB_TYPE%
    exit /b 1
)

if not exist "%EXPECTED_DRIVER%" (
    echo ERROR: EXPECTED JDBC DRIVER NOT FOUND
    echo Expected: %EXPECTED_DRIVER%
    exit /b 1
)

echo Driver Found:
echo %EXPECTED_DRIVER%
echo.
echo =====================================
echo %DB_TYPE% JDBC DRIVER VALIDATED
echo =====================================
echo.

REM =====================================
REM PATHS
REM =====================================

set "LB_BAT=%ROOT%\tools\liquibase\liquibase.bat"
set "DRIVER=%EXPECTED_DRIVER%"

if not exist "%LB_BAT%" (
    echo ERROR: LIQUIBASE EXECUTABLE NOT FOUND
    echo Expected: %LB_BAT%
    exit /b 1
)

cd /d "%ROOT%"

if not exist "%CHANGELOG%" (
    echo ERROR: CHANGELOG NOT FOUND
    echo Expected: %ROOT%\%CHANGELOG%
    exit /b 1
)

REM =====================================
REM REPORT
REM =====================================

echo.
echo Database : %DB_TYPE%
echo Host     : %DB_HOST%
echo Port     : %DB_PORT%
echo DB       : %DB_NAME%
echo User     : %DB_USER%
echo Driver   : %DRIVER%
echo Changelog: %CHANGELOG%
echo.

echo JAVA_HOME : %JAVA_HOME%
echo.

java -version

if errorlevel 1 (
    echo ERROR: JAVA EXECUTION FAILED
    exit /b 1
)

echo.

REM =====================================
REM PASSWORD OPTION
REM =====================================

set "PASSWORD_OPTION="

if defined DB_PASSWORD (
    set "PASSWORD_OPTION=--password=%DB_PASSWORD%"
)

REM =====================================
REM JDBC URL
REM =====================================

if /I "%DB_TYPE%"=="MSSQL" (
    set "JDBC_URL=jdbc:sqlserver://%DB_HOST%:%DB_PORT%;databaseName=%DB_NAME%;encrypt=true;trustServerCertificate=true"
    set "DRIVER_CLASS=com.microsoft.sqlserver.jdbc.SQLServerDriver"
) else if /I "%DB_TYPE%"=="MYSQL" (
    set "JDBC_URL=jdbc:mysql://%DB_HOST%:%DB_PORT%/%DB_NAME%"
    set "DRIVER_CLASS=com.mysql.cj.jdbc.Driver"
) else if /I "%DB_TYPE%"=="POSTGRESQL" (
    set "JDBC_URL=jdbc:postgresql://%DB_HOST%:%DB_PORT%/%DB_NAME%"
    set "DRIVER_CLASS=org.postgresql.Driver"
) else (
    echo ERROR: Unsupported database type: %DB_TYPE%
    exit /b 1
)

REM =====================================
REM RUN LIQUIBASE
REM =====================================

call "%LB_BAT%" ^
    --classpath="%DRIVER%" ^
    --driver=%DRIVER_CLASS% ^
    --search-path="%ROOT%" ^
    --changeLogFile="%CHANGELOG%" ^
    --url="%JDBC_URL%" ^
    --username=%DB_USER% ^
    %PASSWORD_OPTION% ^
    %LB_COMMAND%

set "LIQUIBASE_RC=%ERRORLEVEL%"

if not "%LIQUIBASE_RC%"=="0" (
    echo.
    echo ERROR: %DB_TYPE% LIQUIBASE %LB_COMMAND% FAILED
    echo Exit Code: %LIQUIBASE_RC%
    exit /b %LIQUIBASE_RC%
)

echo.
echo =====================================
echo %DB_TYPE% LIQUIBASE %LB_COMMAND% COMPLETED
echo =====================================
echo.

exit /b 0
