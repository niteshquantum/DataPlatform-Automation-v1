@echo off
setlocal

for /f "tokens=1,2 delims==" %%A in (config\windows\mssql.conf) do (
if /I "%%A"=="MSSQL_DRIVER_VERSION" set "MSSQL_DRIVER_VERSION=%%B"
)

set DRIVER=tools\drivers\mssql-jdbc-%MSSQL_DRIVER_VERSION%.jre11.jar

if not exist "%DRIVER%" (
echo MSSQL DRIVER NOT FOUND
exit /b 1
)

echo MSSQL DRIVER FOUND
echo %DRIVER%

exit /b 0