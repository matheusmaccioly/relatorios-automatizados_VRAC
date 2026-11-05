[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8501,
    [ValidateSet('supabase', 'postgres', 'memory')]
    [string]$Source = 'supabase'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'uv-env.ps1')

if (-not (Test-Path -LiteralPath $VracPython -PathType Leaf)) {
    throw 'Ambiente ausente. Execute .\scripts\bootstrap.ps1 primeiro.'
}

# Este comando sempre inicia somente uma demonstracao sintetica local.
$env:VRAC_ENVIRONMENT = 'development'
$env:VRAC_DATA_MODE = 'synthetic'
$env:VRAC_DEMO_SOURCE = $Source
Write-Host 'DEMONSTRACAO: somente dados sinteticos em acesso local.'
Push-Location $VracProjectRoot
try {
    & $VracPython -m streamlit run app.py --server.address 127.0.0.1 --server.port $Port --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
    if ($LASTEXITCODE -ne 0) { throw 'A demonstracao encerrou com erro.' }
}
finally {
    Pop-Location
}
