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

if exist "%MYSQL_EXE%" goto mysql_ready

echo Resolving mysql.exe from existing MySQL service...

set "RESOLVE_SCRIPT=%TEMP%\mysql_resolve_%RANDOM%.ps1"
set "RESOLVE_OUTPUT=%TEMP%\mysql_resolve_output_%RANDOM%.txt"

> "%RESOLVE_SCRIPT%" echo $svc = Get-CimInstance Win32_Service -Filter "Name='MySQLAutomation'" -ErrorAction SilentlyContinue
>> "%RESOLVE_SCRIPT%" echo if($svc -and $svc.PathName){
>> "%RESOLVE_SCRIPT%" echo     $p = $svc.PathName -split 'mysqld.exe'
>> "%RESOLVE_SCRIPT%" echo     if($p.Count -gt 1){
>> "%RESOLVE_SCRIPT%" echo         Join-Path $p[0].Trim() 'mysql.exe'
>> "%RESOLVE_SCRIPT%" echo     }
>> "%RESOLVE_SCRIPT%" echo }

powershell -NoProfile -ExecutionPolicy Bypass -File "%RESOLVE_SCRIPT%" > "%RESOLVE_OUTPUT%" 2>&1

set /p MYSQL_EXE=<"%RESOLVE_OUTPUT%"

del /f "%RESOLVE_SCRIPT%" >nul 2>&1
del /f "%RESOLVE_OUTPUT%" >nul 2>&1

if not exist "%MYSQL_EXE%" (
    echo ERROR: MYSQL CLIENT NOT FOUND
    echo Expected: %MYSQL_EXE%
    exit /b 1
)

:mysql_ready

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