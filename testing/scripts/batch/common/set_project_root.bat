@echo off

set "PROJECT_ROOT=%~dp0..\..\.."

for %%I in ("%PROJECT_ROOT%") do (
    set "PROJECT_ROOT=%%~fI"
)

if not exist "%PROJECT_ROOT%\config" (
    echo ERROR: INVALID PROJECT ROOT
    echo PROJECT_ROOT=%PROJECT_ROOT%
    exit /b 1
)

exit /b 0
