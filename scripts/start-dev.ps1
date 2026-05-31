[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SetupOnly,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host "Usage: .\scripts\start-dev.ps1 [-SkipInstall] [-SetupOnly]"
    Write-Host ""
    Write-Host "Starts the AI PR Review Assistant local development environment."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipInstall  Do not run pip install or npm install."
    Write-Host "  -SetupOnly    Prepare env files and dependencies, but do not start servers."
    exit 0
}

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$BackendLog = Join-Path $BackendDir ".start-dev-uvicorn.log"
$BackendErr = Join-Path $BackendDir ".start-dev-uvicorn.err.log"
$FrontendLog = Join-Path $FrontendDir ".start-dev-vite.log"
$FrontendErr = Join-Path $FrontendDir ".start-dev-vite.err.log"
$PidFile = Join-Path $RootDir ".start-dev-pids"

function Assert-Command {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command '$Name'. $InstallHint"
    }
}

function Ensure-EnvFile {
    param([Parameter(Mandatory = $true)][string]$Directory)

    $envFile = Join-Path $Directory ".env"
    $exampleFile = Join-Path $Directory ".env.example"

    if (-not (Test-Path -LiteralPath $envFile)) {
        Copy-Item -LiteralPath $exampleFile -Destination $envFile
        Write-Host "Created $envFile from .env.example"
    }
}

function Test-PortInUse {
    param([Parameter(Mandatory = $true)][int]$Port)

    try {
        return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    } catch {
        return $false
    }
}

function Wait-HttpOk {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

Write-Host "AI PR Review Assistant local dev startup"
Write-Host "Root: $RootDir"

Assert-Command -Name "python" -InstallHint "Install Python 3.11+ and make sure it is on PATH."
Assert-Command -Name "node" -InstallHint "Install Node.js 20+ and make sure it is on PATH."
Assert-Command -Name "npm" -InstallHint "Install npm with Node.js."

Ensure-EnvFile -Directory $BackendDir
Ensure-EnvFile -Directory $FrontendDir

if (-not (Test-Path -LiteralPath $BackendPython)) {
    Write-Host "Creating backend virtual environment..."
    Push-Location $BackendDir
    try {
        python -m venv .venv
    } finally {
        Pop-Location
    }
}

if (-not $SkipInstall) {
    Write-Host "Installing backend dependencies..."
    Push-Location $BackendDir
    try {
        & $BackendPython -m pip install -r requirements.txt
    } finally {
        Pop-Location
    }

    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    try {
        npm install
    } finally {
        Pop-Location
    }
}

if ($SetupOnly) {
    Write-Host "Setup complete. Servers were not started because -SetupOnly was used."
    exit 0
}

$pidEntries = @()
if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force
}

if (Test-PortInUse -Port 8000) {
    Write-Host "Port 8000 is already in use. Backend was not started."
} else {
    Write-Host "Starting backend on http://localhost:8000 ..."
    $backendProcess = Start-Process -FilePath "powershell" `
        -WindowStyle Hidden `
        -WorkingDirectory $BackendDir `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            ".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
        ) `
        -RedirectStandardOutput $BackendLog `
        -RedirectStandardError $BackendErr `
        -PassThru
    $pidEntries += "backend=$($backendProcess.Id)"
}

if (Test-PortInUse -Port 5173) {
    Write-Host "Port 5173 is already in use. Frontend was not started."
} else {
    Write-Host "Starting frontend on http://localhost:5173 ..."
    $frontendProcess = Start-Process -FilePath "powershell" `
        -WindowStyle Hidden `
        -WorkingDirectory $FrontendDir `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command",
            "npm run dev -- --host 127.0.0.1 --port 5173"
        ) `
        -RedirectStandardOutput $FrontendLog `
        -RedirectStandardError $FrontendErr `
        -PassThru
    $pidEntries += "frontend=$($frontendProcess.Id)"
}

if ($pidEntries.Count -gt 0) {
    Set-Content -LiteralPath $PidFile -Value $pidEntries -Encoding ASCII
}

$backendReady = Wait-HttpOk -Url "http://localhost:8000/health" -TimeoutSeconds 30
$frontendReady = Wait-HttpOk -Url "http://localhost:5173" -TimeoutSeconds 30

Write-Host ""
Write-Host "Local URLs:"
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000/health"
Write-Host ""
Write-Host "Logs:"
Write-Host "  Backend stdout: $BackendLog"
Write-Host "  Backend stderr: $BackendErr"
Write-Host "  Frontend stdout: $FrontendLog"
Write-Host "  Frontend stderr: $FrontendErr"
Write-Host "  PID file:        $PidFile"
Write-Host ""
Write-Host "Stop servers:"
Write-Host "  .\scripts\stop-dev.ps1"

if (-not $backendReady -or -not $frontendReady) {
    Write-Host ""
    Write-Host "One or more services did not respond before the timeout."
    Write-Host "Check the log files above for details."
    exit 1
}

Write-Host ""
Write-Host "Development environment is ready."
