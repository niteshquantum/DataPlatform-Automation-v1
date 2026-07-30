@echo off
setlocal

set "ROOT=%~dp0..\.."
set "CONFIG=%ROOT%\config\python.conf"

set "PYTHON_EXE="

if exist "%CONFIG%" (
    for /f "tokens=1,2 delims==" %%A in (%CONFIG%) do (
        if "%%A"=="PYTHON_EXE" set "PYTHON_EXE=%%B"
    )
)

if "%PYTHON_EXE%"=="" (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        set "PYTHON_EXE=%%i"
        goto :python_found
    )
)

:python_found

if "%PYTHON_EXE%"=="" (
    echo PYTHON NOT FOUND
    exit /b 1
)

echo.
echo =====================================
echo VALIDATING PYTHON REQUIREMENTS
echo =====================================
echo.

echo Using Python:
echo %PYTHON_EXE%

"%PYTHON_EXE%" --version || exit /b 1

echo Checking PyYAML...
"%PYTHON_EXE%" -c "import yaml" || exit /b 1

echo Checking python-dotenv...
"%PYTHON_EXE%" -c "import dotenv" || exit /b 1

echo Checking mysql-connector-python...
"%PYTHON_EXE%" -c "import mysql.connector" || exit /b 1

echo Checking pymongo...
"%PYTHON_EXE%" -c "from pymongo import MongoClient" || exit /b 1

echo Checking pandas...
"%PYTHON_EXE%" -c "import pandas" || exit /b 1

echo.
echo =====================================
echo PYTHON REQUIREMENTS VALIDATED
echo =====================================
echo.