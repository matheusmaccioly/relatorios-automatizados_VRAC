[CmdletBinding()]
param([switch]$SqlServer, [switch]$Postgres)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
. (Join-Path $PSScriptRoot 'uv-env.ps1')

# Release e hashes conferidos nos assets oficiais da Astral em 26/10/2026.
# https://github.com/astral-sh/uv/releases/expanded_assets/0.13.5
$uvVersion = '0.13.5'
$architecture = [System.Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITEW6432')
if ([string]::IsNullOrEmpty($architecture)) {
    $architecture = [System.Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE')
}
switch ($architecture) {
    'AMD64' {
        $asset = 'uv-x86_64-pc-windows-msvc.zip'
        $expectedHash = 'a38b8d1902b7cfbc76b423ba1bb456f623f42064cdc72628b6075b89afd1019a'
    }
    'ARM64' {
        $asset = 'uv-aarch64-pc-windows-msvc.zip'
        $expectedHash = '09f47edf90726084a70f9426f6e3ca4f46e9bf7cbf23b1716ec64d60b055fae3'
    }
    default { throw 'O bootstrap suporta Windows x64 ou ARM64. Solicite um ambiente compativel.' }
}

Push-Location $VracProjectRoot
try {
    if (-not (Test-Path -LiteralPath 'uv.lock' -PathType Leaf)) {
        throw 'uv.lock ausente. O mantenedor deve gerar e revisar o lock antes do bootstrap.'
    }
    $pythonVersion = (Get-Content -LiteralPath '.python-version' -Raw).Trim()
    if ($pythonVersion -notmatch '^3\.12(?:\.\d+)?$') {
        throw '.python-version deve indicar uma versao compativel de Python 3.12.'
    }

    if (-not (Test-Path -LiteralPath $VracUv -PathType Leaf)) {
        $downloadDirectory = Join-Path $VracProjectRoot '.tools\downloads'
        $uvDirectory = Join-Path $VracProjectRoot '.tools\uv'
        New-Item -ItemType Directory -Path $downloadDirectory -Force | Out-Null
        $archivePath = Join-Path $downloadDirectory $asset
        $checksumPath = "$archivePath.sha256"
        $releaseUrl = "https://github.com/astral-sh/uv/releases/download/$uvVersion"
        Write-Host "Baixando uv $uvVersion para o projeto..."
        Invoke-WebRequest -UseBasicParsing -Uri "$releaseUrl/$asset" -OutFile $archivePath -TimeoutSec 120
        Invoke-WebRequest -UseBasicParsing -Uri "$releaseUrl/$asset.sha256" -OutFile $checksumPath -TimeoutSec 60
        $checksumText = (Get-Content -LiteralPath $checksumPath -Raw).Trim()
        if ($checksumText -notmatch '^([0-9a-fA-F]{64})(?:\s|$)') {
            throw 'Formato invalido do checksum oficial. Download nao sera executado.'
        }
        $publishedHash = $Matches[1]
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
        if ($publishedHash -ne $expectedHash -or $actualHash -ne $expectedHash) {
            throw 'SHA256 divergente. Download nao sera executado; revise a origem.'
        }
        Expand-Archive -LiteralPath $archivePath -DestinationPath $uvDirectory -Force
    }

    $installedVersion = & $VracUv --version
    if ($LASTEXITCODE -ne 0 -or $installedVersion -notmatch '^uv 0\.13\.5(?:\s|$)') {
        throw "O executavel local deve ser uv $uvVersion. Revise .tools/uv antes de continuar."
    }
    & $VracUv python install $pythonVersion
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o Python local.' }
    $vracSyncArguments = @('sync', '--locked', '--extra', 'supabase')
    if ($SqlServer) { $vracSyncArguments += @('--extra', 'sqlserver') }
    if ($Postgres) { $vracSyncArguments += @('--extra', 'postgres') }
    & $VracUv @vracSyncArguments
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias do lock.' }
    Write-Host 'Ambiente preparado. Execute .\scripts\check.ps1 e .\scripts\run-demo.ps1.'
}
finally {
    Pop-Location
}
