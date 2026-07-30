@echo off
setlocal



set "ROOT=%CD%"
if not exist "%ROOT%\config\python.conf" (
set "ROOT=%~dp0..\..\..\.."
)

set "CONFIG=%ROOT%\config\python.conf"

if not exist "%CONFIG%" (
    echo WARNING: python.conf NOT FOUND
    echo Auto-detecting Python from PATH...
)

set PYTHON_EXE=

for /f "tokens=1,2 delims==" %%A in (%CONFIG%) do (
if "%%A"=="PYTHON_EXE" set PYTHON_EXE=%%B
)

REM =====================================
REM AUTO DETECT PYTHON
REM =====================================

if "%PYTHON_EXE%"=="" (


    for /f "delims=" %%i in ('where python 2^>nul') do (
        set PYTHON_EXE=%%i
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

echo.
echo Python Version:
"%PYTHON_EXE%" --version

echo.
echo Checking PyYAML...
"%PYTHON_EXE%" -c "import yaml"
if errorlevel 1 (
echo PyYAML Missing
exit /b 1
)

echo Checking python-dotenv...
"%PYTHON_EXE%" -c "import dotenv"
if errorlevel 1 (
echo python-dotenv Missing
exit /b 1
)

echo Checking pyodbc...
"%PYTHON_EXE%" -c "import pyodbc"
if errorlevel 1 (
echo pyodbc Missing
exit /b 1
)

echo Checking pandas...
"%PYTHON_EXE%" -c "import pandas"
if errorlevel 1 (
echo pandas Missing
exit /b 1
)

echo.
echo =====================================
echo PYTHON REQUIREMENTS VALIDATED
echo =====================================
echo.
