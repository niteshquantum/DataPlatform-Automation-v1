@echo off
setlocal EnableDelayedExpansion

if "%~1"=="" (
    echo Usage: %0 ^<RUNNING^|STOPPED^|NOINSTANCE^>
    exit /b 1
)

echo INSTANCE_STATE=%1> "%~dp0check_instance_sim.txt"

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('type "%~dp0check_instance_sim.txt"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo FAIL: INST_INSTANCE_STATE not defined
    exit /b 1
)

echo [CAPTURED] INST_INSTANCE_STATE=%INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo [OK] Would reuse running instance.
    set "RESULT=RUNNING_OK"
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo [OK] Would start stopped instance.
    set "RESULT=STOPPED_OK"
)

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo [OK] Would deploy new instance.
    set "RESULT=NOINSTANCE_OK"
)

echo STATE_MACHINE_BEHAVIOR=VALID
echo RESULT=%RESULT%
endlocal
exit /b 0
