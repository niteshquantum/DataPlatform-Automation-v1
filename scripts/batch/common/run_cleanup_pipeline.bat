@echo off
setlocal
setlocal EnableExtensions EnableDelayedExpansion

if "%~1"=="" (
    echo [ERROR] Missing required argument: cleanupMode
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Missing required argument: database
    exit /b 1
)

set CLEANUP_MODE=%~1
set DATABASE=%~2

if /I not "%CLEANUP_MODE%"=="full" if /I not "%CLEANUP_MODE%"=="partial" if /I not "%CLEANUP_MODE%"=="dryrun" (
    echo [ERROR] Invalid cleanup mode: %CLEANUP_MODE%. Allowed: full, partial, dryrun
    exit /b 1
)

set RESOLVED_DATABASE=%DATABASE%
if /I "%DATABASE%"=="mysql" set RESOLVED_DATABASE=MySQL
if /I "%DATABASE%"=="mssql" set RESOLVED_DATABASE=MSSQL
if /I "%DATABASE%"=="postgresql" set RESOLVED_DATABASE=PostgreSQL
if /I "%DATABASE%"=="mongodb" set RESOLVED_DATABASE=MongoDB

echo [INFO] Common cleanup runner invoked
echo [INFO] Cleanup mode: %CLEANUP_MODE%
echo [INFO] Database: %RESOLVED_DATABASE%
echo [INFO] Operating system: Windows

exit /b 0
