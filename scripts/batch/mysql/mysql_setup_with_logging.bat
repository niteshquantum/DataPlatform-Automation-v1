@echo off

call scripts\batch\mysql\initialize_logs.bat

echo. >> logs\mysql_setup.log
echo ================================================== >> logs\mysql_setup.log
echo MYSQL SETUP STARTED %DATE% %TIME% >> logs\mysql_setup.log
echo ================================================== >> logs\mysql_setup.log

call scripts\batch\mysql\validate_environment.bat >> logs\mysql_setup.log 2>&1

if errorlevel 1 (
    echo MYSQL SETUP FAILED >> logs\mysql_setup.log
    exit /b 1
)

echo MYSQL SETUP COMPLETED %DATE% %TIME% >> logs\mysql_setup.log