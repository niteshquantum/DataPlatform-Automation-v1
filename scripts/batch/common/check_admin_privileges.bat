@echo off
setlocal

echo.
echo =====================================
echo CHECKING ADMINISTRATOR PRIVILEGES
echo =====================================
echo.

powershell.exe -NoProfile -NonInteractive -Command ^
"$identity = [Security.Principal.WindowsIdentity]::GetCurrent(); ^
$principal = New-Object Security.Principal.WindowsPrincipal($identity); ^
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 0 } else { exit 1 }"

if %ERRORLEVEL% EQU 0 (
    echo Administrator privileges detected.
    exit /b 0
)

echo Administrator privileges not available.
exit /b 1
