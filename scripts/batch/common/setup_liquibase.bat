@echo off

echo.
echo =====================================
echo SETTING UP LIQUIBASE
echo =====================================
echo.

REM Ensure MySQL Driver exists
call "%~dp0install_mysql_driver.bat"

if errorlevel 1 (
    exit /b 1
)

REM Ensure Liquibase exists
call "%~dp0install_liquibase.bat"

if errorlevel 1 (
    exit /b 1
)

echo.
echo =====================================
echo RUNNING LIQUIBASE
echo =====================================
echo.

"%~dp0..\..\..\tools\liquibase\liquibase.bat" ^
--classpath="%~dp0..\..\..\tools\drivers\mysql-connector-j-9.5.0.jar" ^
--defaults-file="%~dp0..\..\..\liquibase\mysql\liquibase.properties" ^
update

if errorlevel 1 (
    echo.
    echo LIQUIBASE UPDATE FAILED
    exit /b 1
)

echo.
echo LIQUIBASE UPDATE SUCCESSFUL
echo.