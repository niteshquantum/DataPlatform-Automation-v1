@echo off
setlocal EnableDelayedExpansion

echo.
echo =====================================
echo RUNNING LIQUIBASE
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

set "CONFIG_FILE=%ROOT%\config\windows\mssql.conf"

REM =====================================
REM VALIDATE CONFIG
REM =====================================

if not exist "%CONFIG_FILE%" (
    echo ERROR: CONFIG FILE NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM READ CONFIG
REM =====================================

for /f "tokens=1,2 delims==" %%A in (%CONFIG_FILE%) do (
    if /I "%%A"=="MSSQL_HOST" set "MSSQL_HOST=%%B"
    if /I "%%A"=="MSSQL_PORT" set "MSSQL_PORT=%%B"
    if /I "%%A"=="MSSQL_DB" set "MSSQL_DB=%%B"
    if /I "%%A"=="MSSQL_USER" set "MSSQL_USER=%%B"
    if /I "%%A"=="MSSQL_PASSWORD" set "MSSQL_PASSWORD=%%B"
    if /I "%%A"=="MSSQL_DRIVER_VERSION" set "MSSQL_DRIVER_VERSION=%%B"
)

REM =====================================
REM VALIDATE LIQUIBASE
REM =====================================

call "%ROOT%\scripts\batch\mssql\setup\validate_liquibase.bat"

if errorlevel 1 exit /b 1

REM =====================================
REM VALIDATE JDBC DRIVER
REM =====================================

call "%ROOT%\scripts\batch\mssql\setup\validate_mssql_driver.bat"

if errorlevel 1 exit /b 1

REM =====================================
REM PATHS
REM =====================================

set "LB_BAT=%ROOT%\tools\liquibase\liquibase.bat"

set "DRIVER=%ROOT%\tools\drivers\mssql-jdbc-%MSSQL_DRIVER_VERSION%.jre11.jar"

if not exist "%DRIVER%" (
    echo ERROR: JDBC DRIVER NOT FOUND
    echo Expected: %DRIVER%
    exit /b 1
)

cd /d "%ROOT%"

set "CHANGELOG=%~1"
if "%CHANGELOG%"=="" set "CHANGELOG=liquibase\mssql\master.xml"

if not exist "%CHANGELOG%" (
    echo ERROR: CHANGELOG NOT FOUND
    echo Expected: %CD%\%CHANGELOG%
    exit /b 1
)

echo Database : %MSSQL_DB%
echo Host     : %MSSQL_HOST%
echo Port     : %MSSQL_PORT%
echo User     : %MSSQL_USER%
echo Driver   : %DRIVER%
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

if defined MSSQL_PASSWORD (
    set "PASSWORD_OPTION=--password=%MSSQL_PASSWORD%"
)

REM =====================================
REM RUN LIQUIBASE
REM =====================================

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.microsoft.sqlserver.jdbc.SQLServerDriver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:sqlserver://%MSSQL_HOST%:%MSSQL_PORT%;databaseName=%MSSQL_DB%;encrypt=true;trustServerCertificate=true" ^
--username=%MSSQL_USER% ^
%PASSWORD_OPTION% ^
update

if errorlevel 1 (
    echo.
    echo ERROR: LIQUIBASE UPDATE FAILED
    exit /b 1
)

echo.
echo =====================================
echo LIQUIBASE UPDATE COMPLETED
echo =====================================
echo.

exit /b 0
