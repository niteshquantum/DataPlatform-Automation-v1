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
echo PYTHON VERSION
echo =====================================
echo.

echo Using Python:
echo %PYTHON_EXE%

"%PYTHON_EXE%" --version || exit /b 1

echo.
echo =====================================
echo INSTALLING PYTHON REQUIREMENTS
echo =====================================
echo.

pushd "%ROOT%"
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo INSTALL FAILED
    popd
    exit /b 1
)
popd

echo.
echo =====================================
echo PYTHON REQUIREMENTS INSTALLED
echo =====================================
echo.