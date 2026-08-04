@echo off
setlocal EnableDelayedExpansion

echo.
echo =====================================
echo CREATE DATABASE
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

REM Get project root from script location
set "ROOT=%~dp0..\..\..\.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"

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
)

REM =====================================
REM VALIDATE CONFIG VALUES
REM =====================================

if not defined MYSQL_HOST (
echo ERROR: MYSQL_HOST NOT DEFINED
exit /b 1
)

if not defined MYSQL_PORT (
echo ERROR: MYSQL_PORT NOT DEFINED
exit /b 1
)

if not defined MYSQL_DB (
echo ERROR: MYSQL_DB NOT DEFINED
exit /b 1
)

if not defined MYSQL_USER (
echo ERROR: MYSQL_USER NOT DEFINED
exit /b 1
)

REM =====================================
REM MYSQL CLIENT
REM =====================================

set "MYSQL_EXE=%ROOT%\databases\mysql\server\bin\mysql.exe"

if not exist "%MYSQL_EXE%" (
    echo ERROR: MYSQL CLIENT NOT FOUND
    echo Expected: %MYSQL_EXE%
    exit /b 1
)

echo Host     : %MYSQL_HOST%
echo Port     : %MYSQL_PORT%
echo Database : %MYSQL_DB%
echo User     : %MYSQL_USER%
echo.

REM =====================================
REM BUILD PASSWORD OPTION
REM =====================================

set "MYSQL_PASSWORD_OPTION="

if defined MYSQL_PASSWORD (
set "MYSQL_PASSWORD_OPTION=-p%MYSQL_PASSWORD%"
)

REM =====================================
REM CREATE DATABASE
REM =====================================

echo Creating database if not exists...
echo.

echo -----------------------------------
echo MYSQL_EXE: %MYSQL_EXE%
echo MYSQL_PASSWORD_OPTION: %MYSQL_PASSWORD_OPTION%
echo Current PATH: %PATH%
echo Working Directory: %CD%
for /f "delims=" %%W in ('where mysql 2^>nul') do echo Resolved mysql.exe location: %%W
echo Exact command that will be executed:
echo   "%MYSQL_EXE%" -h %MYSQL_HOST% -u %MYSQL_USER% -P %MYSQL_PORT% %MYSQL_PASSWORD_OPTION% -e "CREATE DATABASE IF NOT EXISTS %MYSQL_DB%;"
echo -----------------------------------

"%MYSQL_EXE%" ^
-h %MYSQL_HOST% ^
-u %MYSQL_USER% ^
-P %MYSQL_PORT% ^
%MYSQL_PASSWORD_OPTION% ^
-e "CREATE DATABASE IF NOT EXISTS %MYSQL_DB%;"

if errorlevel 1 (
echo.
echo ERROR: DATABASE CREATION FAILED
exit /b 1
)

echo.
echo DATABASE READY : %MYSQL_DB%
echo.
echo =====================================
echo DATABASE VALIDATED
echo =====================================
echo.

exit /b 0