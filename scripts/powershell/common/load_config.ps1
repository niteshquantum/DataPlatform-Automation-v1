$ErrorActionPreference = "Stop"

function Load-Config {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigFile
    )

    if (!(Test-Path $ConfigFile)) {
        throw "Configuration file not found: $ConfigFile"
    }

    $Config = @{}

    foreach ($Line in Get-Content $ConfigFile) {

        $Line = $Line.Trim()

        if ($Line -eq "" -or $Line.StartsWith("#")) {
            continue
        }

        $Parts = $Line.Split("=", 2)

        if ($Parts.Count -eq 2) {
            $Config[$Parts[0].Trim()] = $Parts[1].Trim()
        }
    }

    return $Config
}