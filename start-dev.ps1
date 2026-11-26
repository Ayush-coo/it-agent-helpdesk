$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$backendRoot = Join-Path $projectRoot "backend"
$frontendRoot = Join-Path $projectRoot "frontend"

$pythonExecutable = $null
$pythonPrefixArguments = @()
$pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -notlike "*\WindowsApps\*") {
    $pythonExecutable = $pythonCommand.Source
} else {
    $pythonLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        $pythonExecutable = $pythonLauncher.Source
        $pythonPrefixArguments = @("-3")
    } else {
        $pythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
        $installations = Get-ChildItem $pythonRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending
        foreach ($installation in $installations) {
            $candidate = Join-Path $installation.FullName "python.exe"
            if (Test-Path $candidate) {
                $pythonExecutable = $candidate
                break
            }
        }
    }
}

if (-not $pythonExecutable) {
    throw "Python was not found. Install Python and add it to PATH, or install the Python launcher."
}

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    throw "npm.cmd was not found. Install Node.js LTS and reopen this terminal."
}

Push-Location $backendRoot
try {
    & $pythonExecutable @pythonPrefixArguments -c "import fastapi, uvicorn"
    if ($LASTEXITCODE -ne 0) {
        throw "Backend dependencies are missing. Run: & `"$pythonExecutable`" -m pip install -r `"$backendRoot\requirements.txt`""
    }
} finally {
    Pop-Location
}

Write-Host "Starting Backend (uvicorn)..." -ForegroundColor Green
Start-Process `
    -FilePath $pythonExecutable `
    -ArgumentList (($pythonPrefixArguments + @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000")) -join " ") `
    -WorkingDirectory $backendRoot

Write-Host "Starting Frontend (Vite)..." -ForegroundColor Green
Start-Process `
    -FilePath $npmCommand.Source `
    -ArgumentList "run dev" `
    -WorkingDirectory $frontendRoot

Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Frontend UI: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Open http://localhost:5173/login after both services finish starting." -ForegroundColor Cyan
