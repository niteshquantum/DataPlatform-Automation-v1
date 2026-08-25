@echo off
setlocal EnableDelayedExpansion

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

set "ROOT=%PROJECT_ROOT%"

if "%ROOT%"=="" (
    echo ERROR: PROJECT ROOT NOT FOUND
    exit /b 1
)

REM =====================================
REM CONFIG
REM =====================================

set "CONFIG_FILE=%ROOT%\config\windows\mysql.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: CONFIG FILE NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

for /f "tokens=1,* delims==" %%A in (%CONFIG_FILE%) do (
    if /I "%%A"=="MYSQL_HOST" set "MYSQL_HOST=%%B"
    if /I "%%A"=="MYSQL_PORT" set "MYSQL_PORT=%%B"
    if /I "%%A"=="MYSQL_DB" set "MYSQL_DB=%%B"
    if /I "%%A"=="MYSQL_USER" set "MYSQL_USER=%%B"
    if /I "%%A"=="MYSQL_PASSWORD" set "MYSQL_PASSWORD=%%B"
    if /I "%%A"=="MYSQL_DRIVER_VERSION" set "MYSQL_DRIVER_VERSION=%%B"
)

REM =====================================
REM CHANGELOG
REM =====================================

set "CHANGELOG=%~1"

if "%CHANGELOG%"=="" (
    set "CHANGELOG=liquibase\mysql\master.xml"
)

REM =====================================
REM LIQUIBASE PATHS
REM =====================================

set "LB_BAT=%ROOT%\tools\liquibase\liquibase.bat"
set "DRIVER=%ROOT%\tools\drivers\mysql-connector-j-%MYSQL_DRIVER_VERSION%.jar"

echo.
echo ROOT       : %ROOT%
echo LIQUIBASE  : %LB_BAT%
echo DRIVER     : %DRIVER%
echo CHANGELOG  : %CHANGELOG%
echo.

if not exist "%LB_BAT%" (
    echo ERROR: LIQUIBASE.BAT NOT FOUND
    echo Expected: %LB_BAT%
    exit /b 1
)

if not exist "%DRIVER%" (
    echo ERROR: JDBC DRIVER NOT FOUND
    echo Expected: %DRIVER%
    exit /b 1
)
echo.
echo ROOT = [%ROOT%]
echo LB_BAT = [%LB_BAT%]
echo DRIVER = [%DRIVER%]
echo CHANGELOG = [%CHANGELOG%]
echo MYSQL_HOST = [%MYSQL_HOST%]
echo MYSQL_DB = [%MYSQL_DB%]
echo MYSQL_USER = [%MYSQL_USER%]
echo.
pause
REM =====================================
REM CLEAR CHECKSUMS
REM =====================================

echo =====================================
echo CLEARING LIQUIBASE CHECKSUMS
echo =====================================

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.mysql.cj.jdbc.Driver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:mysql://%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%" ^
--username="%MYSQL_USER%" ^
--password="%MYSQL_PASSWORD%" ^
clearCheckSums

if errorlevel 1 (
    echo ERROR: LIQUIBASE CLEAR CHECKSUMS FAILED
    exit /b 1
)

REM =====================================
REM RUN UPDATE
REM =====================================

echo.
echo =====================================
echo RUNNING LIQUIBASE UPDATE
echo =====================================

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.mysql.cj.jdbc.Driver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:mysql://%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%" ^
--username="%MYSQL_USER%" ^
--password="%MYSQL_PASSWORD%" ^
update

if errorlevel 1 (
    echo ERROR: LIQUIBASE UPDATE FAILED
    exit /b 1
)

echo.
echo =====================================
echo LIQUIBASE UPDATE COMPLETED
echo =====================================

exit /b 0