[CmdletBinding()]
param(
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host "Usage: .\scripts\stop-dev.ps1"
    Write-Host ""
    Write-Host "Stops local development servers started by scripts\start-dev.ps1."
    exit 0
}

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$PidFile = Join-Path $RootDir ".start-dev-pids"
$processIds = New-Object System.Collections.Generic.HashSet[int]

if (Test-Path -LiteralPath $PidFile) {
    foreach ($line in Get-Content -LiteralPath $PidFile) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $parsed = 0
            if ([int]::TryParse($parts[1], [ref]$parsed)) {
                [void]$processIds.Add($parsed)
            }
        }
    }
}

foreach ($port in 8000, 5173) {
    try {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($listener in $listeners) {
            [void]$processIds.Add([int]$listener.OwningProcess)
        }
    } catch {
        Write-Host "Could not inspect port $port. $_"
    }
}

if ($processIds.Count -eq 0) {
    Write-Host "No local dev server processes found."
} else {
    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            Stop-Process -Id $processId -Force
            Write-Host "Stopped process $processId ($($process.ProcessName))."
        } catch {
            Write-Host "Process $processId is not running."
        }
    }
}

if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force
}

Write-Host "Local dev servers stopped."
