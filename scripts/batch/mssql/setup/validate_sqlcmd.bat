@echo off
setlocal

echo.
echo =====================================
echo VALIDATING SQLCMD
echo =====================================
echo.

where sqlcmd >nul 2>&1

if errorlevel 1 (
    echo ERROR: SQLCMD NOT FOUND
    exit /b 1
)

echo SQLCMD FOUND

sqlcmd -?

if errorlevel 1 (
    echo ERROR: SQLCMD VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo SQLCMD VALIDATED
echo =====================================
echo.

exit /b 0