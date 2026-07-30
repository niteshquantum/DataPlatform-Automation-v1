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

set "CONFIG_FILE=%ROOT%\config\windows\mysql.conf"

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
if /I "%%A"=="MYSQL_HOST" set "MYSQL_HOST=%%B"
if /I "%%A"=="MYSQL_PORT" set "MYSQL_PORT=%%B"
if /I "%%A"=="MYSQL_DB" set "MYSQL_DB=%%B"
if /I "%%A"=="MYSQL_USER" set "MYSQL_USER=%%B"
if /I "%%A"=="MYSQL_PASSWORD" set "MYSQL_PASSWORD=%%B"
if /I "%%A"=="MYSQL_DRIVER_VERSION" set "MYSQL_DRIVER_VERSION=%%B"
)

REM =====================================
REM VALIDATE LIQUIBASE
REM =====================================

call "%ROOT%\scripts\batch\mysql\setup\validate_liquibase.bat"

if errorlevel 1 (
exit /b 1
)

REM =====================================
REM VALIDATE JDBC DRIVER
REM =====================================

call "%ROOT%\scripts\batch\mysql\setup\validate_mysql_driver.bat"

if errorlevel 1 (
exit /b 1
)

REM =====================================
REM PATHS
REM =====================================

set "LB_BAT=%ROOT%\tools\liquibase\liquibase.bat"

set "DRIVER=%ROOT%\tools\drivers\mysql-connector-j-%MYSQL_DRIVER_VERSION%.jar"

if not exist "%DRIVER%" (
echo ERROR: JDBC DRIVER NOT FOUND
echo Expected: %DRIVER%
exit /b 1
)

cd /d "%ROOT%"

set "CHANGELOG=%~1"
if "%CHANGELOG%"=="" set "CHANGELOG=liquibase\mysql\master.xml"

if not exist "%CHANGELOG%" (
    echo ERROR: CHANGELOG NOT FOUND
    echo Expected: %CD%\%CHANGELOG%
    exit /b 1
)

echo Database : %MYSQL_DB%
echo Host     : %MYSQL_HOST%
echo Port     : %MYSQL_PORT%
echo User     : %MYSQL_USER%
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

if defined MYSQL_PASSWORD (
set "PASSWORD_OPTION=--password=%MYSQL_PASSWORD%"
)

REM =====================================
REM RUN LIQUIBASE
REM =====================================

call "%LB_BAT%" ^
--classpath="%DRIVER%" ^
--driver=com.mysql.cj.jdbc.Driver ^
--search-path="%ROOT%" ^
--changeLogFile="%CHANGELOG%" ^
--url="jdbc:mysql://%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%" ^
--username=%MYSQL_USER% ^
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
