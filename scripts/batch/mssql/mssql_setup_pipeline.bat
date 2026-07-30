@echo off
setlocal

call "%~dp0..\common\set_project_root.bat"

call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\install_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\validate_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\common\validate_java_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\install_tools.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo CHECKING MSSQL INSTANCE STATE
echo =====================================
echo.

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('"%PROJECT_ROOT%\scripts\batch\mssql\setup\check_instance.bat"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo ERROR: Failed to determine instance state.
    exit /b 1
)

echo Instance State: %INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo Reusing existing MSSQL instance.
    goto :configure_user
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo Starting existing MSSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mssql\setup\start_mssql.bat"
    if errorlevel 1 exit /b 1
    goto :configure_user
)

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo Deploying project-local MSSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mssql\setup\deploy_mssql_gdrive.bat"
    if errorlevel 1 exit /b 1

    echo.
    echo =====================================
    echo CHECKING ADMINISTRATOR PRIVILEGES FOR CONFIGURATION
    echo =====================================
    echo.

    set "ADMIN_STATUS="

    call "%PROJECT_ROOT%\scripts\batch\common\check_admin_privileges.bat"
    if errorlevel 1 (
        set "ADMIN_STATUS=false"
    ) else (
        set "ADMIN_STATUS=true"
    )

    echo Administrator Status: %ADMIN_STATUS%

    if /I "%ADMIN_STATUS%"=="true" (
        echo.
        echo =====================================
        echo CONFIGURING SQL SERVER
        echo =====================================
        echo.
        call "%PROJECT_ROOT%\scripts\batch\mssql\setup\configure_mssql.bat"
        if errorlevel 1 exit /b 1
    ) else (
        echo Administrator privileges not available.
        echo SQL Server network configuration will be skipped.
    )

    echo Starting MSSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mssql\setup\start_mssql.bat"
    if errorlevel 1 exit /b 1
    goto :configure_user
)

echo ERROR: Unexpected instance state: %INST_INSTANCE_STATE%
if defined INST_ERROR echo %INST_ERROR%
exit /b 1

:configure_user
echo.
echo =====================================
echo CONFIGURING MSSQL USER
echo =====================================
echo.
call "%PROJECT_ROOT%\scripts\batch\mssql\setup\configure_mssql_user.bat"
if errorlevel 1 exit /b 1

:validate_environment
call "%PROJECT_ROOT%\scripts\batch\mssql\setup\validate_environment.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo MSSQL SETUP SUCCESSFUL
echo =====================================
echo.

exit /b 0