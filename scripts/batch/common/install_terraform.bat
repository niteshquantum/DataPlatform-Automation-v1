@echo off
setlocal

echo.
echo =====================================
echo INSTALLING TERRAFORM
echo =====================================
echo.

if defined DATA_PLATFORM_TOOLS_ROOT (
    set "TOOLS_ROOT=%DATA_PLATFORM_TOOLS_ROOT%"
) else (
    set "TOOLS_ROOT=C:\Program Files\DataPlatform\tools"
)

set "TF_DIR=%TOOLS_ROOT%\terraform"
set "TF_ZIP=%TOOLS_ROOT%\terraform.zip"

if not exist "%TOOLS_ROOT%" (
    mkdir "%TOOLS_ROOT%" >nul 2>&1
)

if not exist "%TF_DIR%" (
    mkdir "%TF_DIR%" >nul 2>&1
)

if exist "%TF_DIR%\terraform.exe" (
    echo Terraform already installed. Skipping installation.
    exit /b 0
)

echo Downloading Terraform...

powershell -Command "Invoke-WebRequest -Uri 'https://releases.hashicorp.com/terraform/1.13.0/terraform_1.13.0_windows_amd64.zip' -OutFile '%TF_ZIP%'"

if errorlevel 1 (
    echo ERROR: TERRAFORM DOWNLOAD FAILED
    exit /b 1
)

if not exist "%TF_ZIP%" (
    echo ERROR: TERRAFORM ZIP NOT FOUND
    exit /b 1
)

echo Extracting Terraform...

powershell -Command "Expand-Archive '%TF_ZIP%' -DestinationPath '%TF_DIR%' -Force"

if errorlevel 1 (
    echo ERROR: TERRAFORM EXTRACTION FAILED
    exit /b 1
)

del "%TF_ZIP%" >nul 2>&1

if not exist "%TF_DIR%\terraform.exe" (
    echo ERROR: TERRAFORM INSTALLATION VALIDATION FAILED
    exit /b 1
)

echo Terraform Installed Successfully.

exit /b 0
