param([string]$ServiceName = "MongoDBAutomation")

$svc = Get-CimInstance Win32_Service -Filter "Name='$ServiceName'" -ErrorAction SilentlyContinue
if ($svc) {
    $p = $svc.PathName.Trim()
    if ($p -match '^"([^"]+)"') {
        $exe = $Matches[1]
    } else {
        $exe = ($p -split ' ')[0]
    }
    Write-Output ($svc.ProcessId.ToString() + '|' + $exe)
} else {
    Write-Output "NOT_FOUND"
}
