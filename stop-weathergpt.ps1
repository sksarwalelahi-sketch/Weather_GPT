$ports = @(8000, 8001, 8002, 3000)

foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
}

Write-Host "WeatherGPT application services stopped."
