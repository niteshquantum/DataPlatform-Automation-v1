@echo off
setlocal

echo ===================================
echo INSTALL POSTGRESQL DRIVER
echo ===================================

powershell -ExecutionPolicy Bypass ^
-File "%~dp0..\..\powershell\download_postgresql_driver copy.ps1"

exit /b %ERRORLEVEL%