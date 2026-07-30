@echo off

call scripts\batch\mysql\initialize_logs.bat

echo. >> logs\mysql_load.log
echo ================================================== >> logs\mysql_load.log
echo MYSQL LOAD STARTED %DATE% %TIME% >> logs\mysql_load.log
echo ================================================== >> logs\mysql_load.log

call scripts\batch\mysql\validate_environment.bat >> logs\mysql_load.log 2>&1

if errorlevel 1 (
    echo MYSQL LOAD FAILED >> logs\mysql_load.log
    exit /b 1
)

call scripts\batch\mysql\load_data.bat >> logs\mysql_load.log 2>&1

if errorlevel 1 (
    echo MYSQL LOAD FAILED >> logs\mysql_load.log
    exit /b 1
)

echo MYSQL LOAD COMPLETED %DATE% %TIME% >> logs\mysql_load.log