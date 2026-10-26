[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'uv-env.ps1')

if (-not (Test-Path -LiteralPath $VracPython -PathType Leaf)) {
    throw 'Ambiente ausente. Execute .\scripts\bootstrap.ps1 primeiro.'
}

Push-Location $VracProjectRoot
try {
    if (Test-Path -LiteralPath $VracUv -PathType Leaf) {
        & $VracUv lock --check --offline
        if ($LASTEXITCODE -ne 0) { throw 'O lock esta desatualizado ou indisponivel offline.' }
    }
    & $VracPython -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw 'A verificacao de estilo encontrou problemas.' }
    & $VracPython -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw 'A verificacao de formatacao encontrou problemas.' }
    & $VracPython -m pytest
    if ($LASTEXITCODE -ne 0) { throw 'A suite de testes falhou.' }
    Write-Host 'Verificacoes offline concluidas.'
}
finally {
    Pop-Location
}
