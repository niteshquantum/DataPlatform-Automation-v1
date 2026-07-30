@echo off


echo =====================================
echo MYSQL DESTROY
echo =====================================
echo.

call scripts\batch\mysql\stop_mysql.bat

if exist databases\mysql (
    rmdir /s /q databases\mysql
)

if exist logs (
    rmdir /s /q logs
)

echo.
echo =====================================
echo MYSQL DESTROY SUCCESSFUL
echo =====================================
echo.