@echo off
setlocal

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0set_project_root.bat"

REM =====================================
REM INSTALL 7-ZIP
REM =====================================

powershell.exe -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\common\install_7zip.ps1"

if errorlevel 1 (
    echo.
    echo 7-ZIP INSTALLATION FAILED
    exit /b 1
)

echo.
echo [SUCCESS] 7-ZIP READY
exit /b 0