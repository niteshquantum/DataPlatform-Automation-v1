$ErrorActionPreference = "Stop"

# =====================================
# CONFIGURATION
# =====================================

$MaxAttempts = 3
$RetryDelaySeconds = 2

# =====================================
# READ PARAMETERS FROM ENVIRONMENT
# =====================================

$Url = $env:DOWNLOAD_URL

if ([string]::IsNullOrWhiteSpace($Url)) {
    throw "DOWNLOAD_URL environment variable is required."
}

$OutputPath = $env:DOWNLOAD_OUTPUT_PATH

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    throw "DOWNLOAD_OUTPUT_PATH environment variable is required."
}

# =====================================
# VALIDATE OUTPUT DIRECTORY
# =====================================

$OutputDir = Split-Path $OutputPath -Parent

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$TempPath = "$OutputPath.tmp"

# =====================================
# HELPER: VALIDATE ZIP INTEGRITY
# =====================================

function Test-ZipIntegrity {
    param(
        [string]$Path
    )

    if (!(Test-Path $Path)) {
        return $false
    }

    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
        $zip.Dispose()
        return $true
    }
    catch {
        return $false
    }
}

# =====================================
# HELPER: REMOVE FILE SAFELY
# =====================================

function Remove-FileSafely {
    param(
        [string]$Path
    )

    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Force -ErrorAction Stop
    }
}

# =====================================
# CHECK EXISTING ARCHIVE
# =====================================

if (Test-Path $OutputPath) {
    Write-Host "Existing archive found: $OutputPath"

    if (Test-ZipIntegrity -Path $OutputPath) {
        Write-Host "Existing archive is valid. Reusing."
        exit 0
    }

    Write-Host "Existing archive is corrupt or incomplete. Removing..."
    Remove-FileSafely -Path $OutputPath
}

# =====================================
# DOWNLOAD WITH RETRY
# =====================================

$DownloadSuccess = $false
$LastError = ""

for ($Attempt = 1; $Attempt -le $MaxAttempts; $Attempt++) {

    Write-Host "Download attempt $Attempt of $MaxAttempts..."

    Remove-FileSafely -Path $TempPath

    try {

        $ProgressPreference = 'SilentlyContinue'

        Invoke-WebRequest `
            -Uri $Url `
            -OutFile $TempPath `
            -ErrorAction Stop

        if (!(Test-Path $TempPath)) {
            throw "Download completed but temporary file not found: $TempPath"
        }

        $TempSize = (Get-Item $TempPath).Length

        if ($TempSize -eq 0) {
            throw "Downloaded file is empty: $TempPath"
        }

        if (!(Test-ZipIntegrity -Path $TempPath)) {
            throw "Downloaded archive is corrupt or incomplete."
        }

        Move-Item -LiteralPath $TempPath -Destination $OutputPath -Force -ErrorAction Stop

        if (!(Test-Path $OutputPath)) {
            throw "Failed to move downloaded archive to final path."
        }

        Write-Host "Download successful: $OutputPath"
        $DownloadSuccess = $true
        break
    }
    catch {
        $LastError = $_.Exception.Message
        Write-Host "Attempt $Attempt failed: $LastError"

        Remove-FileSafely -Path $TempPath
    }

    if ($Attempt -lt $MaxAttempts) {
        Write-Host "Retrying in $RetryDelaySeconds seconds..."
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

if (!$DownloadSuccess) {
    Write-Host ""
    Write-Host "======================================="
    Write-Host "DOWNLOAD FAILED AFTER $MaxAttempts ATTEMPTS"
    Write-Host "======================================="
    Write-Host "URL     : $Url"
    Write-Host "Output  : $OutputPath"
    Write-Host "Last error: $LastError"
    Write-Host "======================================="
    Write-Host ""

    Remove-FileSafely -Path $TempPath
    Remove-FileSafely -Path $OutputPath

    exit 1
}

Write-Host ""
Write-Host "======================================="
Write-Host "DOWNLOAD COMPLETE"
Write-Host "======================================="
Write-Host "URL    : $Url"
Write-Host "Output : $OutputPath"
Write-Host "======================================="
Write-Host ""

exit 0
