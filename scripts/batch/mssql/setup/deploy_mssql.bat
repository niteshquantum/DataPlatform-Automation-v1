@echo off
setlocal

echo.
echo =====================================
echo DEPLOYING SQL SERVER
echo =====================================
echo.

call "%~dp0\download_mssql.bat"
if errorlevel 1 exit /b 1

call "%~dp0\prepare_mssql_media.bat"
if errorlevel 1 exit /b 1

call "%~dp0\generate_configuration_file.bat"
if errorlevel 1 exit /b 1

call "%~dp0\install_mssql.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo SQL SERVER DEPLOYMENT SUCCESSFUL
echo =====================================
echo.

exit /b 0