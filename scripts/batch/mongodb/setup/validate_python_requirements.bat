@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo VALIDATING PYTHON REQUIREMENTS
echo =====================================
echo.

python --version
if errorlevel 1 exit /b 1

REM Common requirements
python -c "import yaml"
if errorlevel 1 exit /b 1

python -c "import dotenv"
if errorlevel 1 exit /b 1

python -c "import pandas"
if errorlevel 1 exit /b 1

REM MongoDB specific requirement
python -c "import pymongo"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo PYTHON REQUIREMENTS VALIDATED
echo =====================================
echo.

exit /b 0