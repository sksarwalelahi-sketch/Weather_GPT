$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$defaultPython = Join-Path $root ".venv\Scripts\python.exe"
# Direct GRIB parsing is optional. Prefer the shared environment so Windows
# Application Control does not block startup on an unapproved Conda executable.
$gfsPython = if ($env:WEATHERGPT_GFS_PYTHON) {
    $env:WEATHERGPT_GFS_PYTHON
} else {
    $defaultPython
}
$frontend = Join-Path $root "Frontend"
$logs = Join-Path $root ".runtime-logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null

if (-not (Test-Path $defaultPython)) {
    throw "Python environment not found: $defaultPython"
}

if (-not (Test-Path $gfsPython)) {
    throw "M1 Python environment not found: $gfsPython"
}
if ($gfsPython -ne $defaultPython) {
    $gfsLibraryBin = Join-Path (Split-Path $gfsPython) "Library\bin"
    if (Test-Path $gfsLibraryBin) {
        $env:PATH = "$gfsLibraryBin;$env:PATH"
    }
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$Python,
        [string]$WorkingDirectory,
        [string]$Arguments,
        [string]$LogDirectory
    )

    $existing = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object {
            $_.CommandLine -like "*uvicorn*app.main:app*8000*" -or
            $_.CommandLine -like "*uvicorn*api.main:app*8001*" -or
            $_.CommandLine -like "*uvicorn*app.api:app*8002*"
        }

    if ($Name -eq "M1" -and ($existing | Where-Object CommandLine -Like "*8000*")) { return }
    if ($Name -eq "M3" -and ($existing | Where-Object CommandLine -Like "*8001*")) { return }
    if ($Name -eq "M2" -and ($existing | Where-Object CommandLine -Like "*8002*")) { return }

    $logPrefix = $Name.ToLowerInvariant()
    try {
        Start-Process `
            -FilePath $Python `
            -WorkingDirectory $WorkingDirectory `
            -ArgumentList $Arguments `
            -RedirectStandardOutput (Join-Path $LogDirectory "$logPrefix.log") `
            -RedirectStandardError (Join-Path $LogDirectory "$logPrefix.error.log") `
            -WindowStyle Hidden
    } catch {
        if ($Name -eq "M1" -and $Python -ne $defaultPython) {
            Write-Warning "M1 environment was blocked by Windows Application Control. Retrying with the shared .venv; direct GRIB parsing is optional."
            Start-Process `
                -FilePath $defaultPython `
                -WorkingDirectory $WorkingDirectory `
                -ArgumentList $Arguments `
                -RedirectStandardOutput (Join-Path $LogDirectory "$logPrefix.log") `
                -RedirectStandardError (Join-Path $LogDirectory "$logPrefix.error.log") `
                -WindowStyle Hidden
        } else {
            throw "Could not start $Name using $Python. Windows Application Control may be blocking this executable. $($_.Exception.Message)"
        }
    }
    Write-Host "$Name starting..."
}

try {
    docker inspect weathergpt-redis *> $null
    docker start weathergpt-redis *> $null
} catch {
    docker run -d --name weathergpt-redis -p 6379:6379 redis:7-alpine *> $null
}

Start-ServiceProcess `
    -Name "M1" `
    -Python $gfsPython `
    -WorkingDirectory (Join-Path $root "Data") `
    -Arguments "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
    -LogDirectory $logs

Start-ServiceProcess `
    -Name "M3" `
    -Python $defaultPython `
    -WorkingDirectory (Join-Path $root "Intelligence") `
    -Arguments "-m uvicorn api.main:app --host 127.0.0.1 --port 8001" `
    -LogDirectory $logs

Start-ServiceProcess `
    -Name "M2" `
    -Python $defaultPython `
    -WorkingDirectory (Join-Path $root "LLM") `
    -Arguments "-m uvicorn app.api:app --host 127.0.0.1 --port 8002" `
    -LogDirectory $logs

$checks = @(
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8001/health",
    "http://127.0.0.1:8002/"
)

foreach ($url in $checks) {
    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        $service = switch -Regex ($url) {
            '8000' { 'm1' }
            '8001' { 'm3' }
            '8002' { 'm2' }
        }
        $log = Join-Path $logs "$service.error.log"
        if (Test-Path $log) {
            Get-Content $log -Tail 30
        }
        throw "Service did not become ready: $url"
    }
}

if (-not (Get-Process node -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like "*WeatherGPT-AI*Frontend*" })) {
    Start-Process `
        -FilePath "cmd.exe" `
        -WorkingDirectory $frontend `
        -ArgumentList "/c", "npm run dev -- --hostname 127.0.0.1 --port 3000 > `"$($logs)\frontend.log`" 2>&1" `
        -WindowStyle Hidden
    Write-Host "Frontend starting..."
}

$uiUrl = "http://127.0.0.1:3000"
Write-Host "WeatherGPT UI: $uiUrl"

$uiReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        Invoke-WebRequest -Uri "$uiUrl/" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $uiReady = $true
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $uiReady) {
    Get-Content (Join-Path $logs "frontend.log") -Tail 30 -ErrorAction SilentlyContinue
    throw "Frontend did not become ready: $uiUrl"
}

Start-Process $uiUrl

Write-Host ""
Write-Host "WeatherGPT is running at $uiUrl" -ForegroundColor Green
Write-Host "Stop services with: .\stop-weathergpt.ps1"
