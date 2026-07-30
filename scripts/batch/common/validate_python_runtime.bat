@echo off
setlocal



set "ROOT=%CD%"
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
echo VALIDATING PYTHON RUNTIME
echo =====================================
echo.

echo Using Python:
echo %PYTHON_EXE%

"%PYTHON_EXE%" --version

if errorlevel 1 (
    echo PYTHON VERSION CHECK FAILED
    exit /b 1
)

echo.
echo =====================================
echo PYTHON RUNTIME VALIDATED
echo =====================================
echo.
