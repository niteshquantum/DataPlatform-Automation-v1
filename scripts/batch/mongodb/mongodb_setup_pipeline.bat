@echo off
setlocal

call "%~dp0..\common\set_project_root.bat"

@REM call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\install_python_requirements.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\validate_python_requirements.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\common\validate_java_runtime.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\install_tools.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\validate_tools.bat"
@REM if errorlevel 1 exit /b 1

echo.
echo =====================================
echo CHECKING MONGODB INSTANCE STATE
echo =====================================
echo.

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('"%PROJECT_ROOT%\scripts\batch\mongodb\setup\check_instance.bat"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo ERROR: Failed to determine instance state.
    exit /b 1
)

echo Instance State: %INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo Reusing existing MongoDB instance.
    goto :validate_mongodb
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo Starting existing MongoDB instance.
    call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\start_mongodb.bat"
    if errorlevel 1 exit /b 1
    goto :validate_mongodb
)

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo Deploying MongoDB instance.
    call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\run_terraform.bat"
    if errorlevel 1 exit /b 1

    echo Starting MongoDB instance.
    call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\start_mongodb.bat"
    if errorlevel 1 exit /b 1
    goto :validate_mongodb
)

echo ERROR: Unexpected instance state: %INST_INSTANCE_STATE%
if defined INST_ERROR echo %INST_ERROR%
exit /b 1

:validate_mongodb
call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\validate_port.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\validate_mongodb.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mongodb\setup\validate_environment.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo MONGODB SETUP SUCCESSFUL
echo =====================================
echo.

exit /b 0
