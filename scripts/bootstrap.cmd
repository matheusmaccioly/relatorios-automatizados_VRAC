@echo off
setlocal EnableExtensions DisableDelayedExpansion
for %%I in ("%~dp0..") do set "VRAC_PROJECT_ROOT=%%~fI"
cd /d "%VRAC_PROJECT_ROOT%"
if errorlevel 1 exit /b 1

set "VRAC_UV_VERSION=0.13.5"
set "VRAC_UV=%VRAC_PROJECT_ROOT%\.tools\uv\uv.exe"
set "UV_CACHE_DIR=%VRAC_PROJECT_ROOT%\.cache\uv"
set "UV_PYTHON_INSTALL_DIR=%VRAC_PROJECT_ROOT%\.tools\python"
set "UV_PYTHON_BIN_DIR=%VRAC_PROJECT_ROOT%\.tools\bin"
set "UV_PYTHON_CACHE_DIR=%VRAC_PROJECT_ROOT%\.cache\python"
set "UV_CREDENTIALS_DIR=%VRAC_PROJECT_ROOT%\.cache\uv-credentials"
set "UV_PROJECT_ENVIRONMENT=%VRAC_PROJECT_ROOT%\.venv"
set "UV_NO_CONFIG=1"
set "UV_NO_ENV_FILE=1"
set "UV_PYTHON_NO_REGISTRY=1"
set "UV_PYTHON_INSTALL_REGISTRY=0"
set "UV_PYTHON_INSTALL_BIN=0"
set "UV_PYTHON_PREFERENCE=only-managed"

if not exist "uv.lock" (
    echo uv.lock ausente. O mantenedor deve gerar e revisar o lock primeiro.
    exit /b 1
)
if not exist ".python-version" (
    echo .python-version ausente. Reponha o arquivo versionado antes de continuar.
    exit /b 1
)

set "VRAC_ARCH=%PROCESSOR_ARCHITEW6432%"
if not defined VRAC_ARCH set "VRAC_ARCH=%PROCESSOR_ARCHITECTURE%"
if /i "%VRAC_ARCH%"=="AMD64" (
    set "VRAC_UV_ASSET=uv-x86_64-pc-windows-msvc.zip"
    set "VRAC_UV_HASH=a38b8d1902b7cfbc76b423ba1bb456f623f42064cdc72628b6075b89afd1019a"
) else if /i "%VRAC_ARCH%"=="ARM64" (
    set "VRAC_UV_ASSET=uv-aarch64-pc-windows-msvc.zip"
    set "VRAC_UV_HASH=09f47edf90726084a70f9426f6e3ca4f46e9bf7cbf23b1716ec64d60b055fae3"
) else (
    echo O bootstrap suporta Windows x64 ou ARM64.
    exit /b 1
)

rem Comandos fixos inline: nao carrega .ps1 nem altera ExecutionPolicy.
rem TLS e validacao de certificado permanecem ativos.
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; $version = [System.IO.File]::ReadAllText((Join-Path $env:VRAC_PROJECT_ROOT '.python-version')).Trim(); if ($version -notmatch '\A3\.12\.\d+\z') { throw '.python-version deve indicar Python 3.12 com patch fixado.' }; if (-not (Test-Path -LiteralPath $env:VRAC_UV -PathType Leaf)) { $downloads = Join-Path $env:VRAC_PROJECT_ROOT '.tools\downloads'; New-Item -ItemType Directory -Path $downloads -Force | Out-Null; $archive = Join-Path $downloads $env:VRAC_UV_ASSET; $checksum = $archive + '.sha256'; $url = 'https://github.com/astral-sh/uv/releases/download/' + $env:VRAC_UV_VERSION + '/' + $env:VRAC_UV_ASSET; Write-Host ('Baixando uv ' + $env:VRAC_UV_VERSION + ' para o projeto...'); Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archive -TimeoutSec 120; Invoke-WebRequest -UseBasicParsing -Uri ($url + '.sha256') -OutFile $checksum -TimeoutSec 60; $published = [regex]::Match((Get-Content -LiteralPath $checksum -Raw).Trim(), '\A([0-9a-fA-F]{64})(?:\s|$)'); $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash; if (-not $published.Success -or $published.Groups[1].Value -ne $env:VRAC_UV_HASH -or $actual -ne $env:VRAC_UV_HASH) { throw 'SHA256 divergente. Download nao sera executado.' }; Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $env:VRAC_PROJECT_ROOT '.tools\uv') -Force }; $installed = & $env:VRAC_UV --version; if ($LASTEXITCODE -ne 0 -or $installed -notmatch '\Auv 0\.13\.5(?:\s|$)') { throw 'O executavel local deve ser uv 0.13.5.' }; Write-Host $installed"
if errorlevel 1 exit /b 1

set "VRAC_PYTHON_VERSION="
set /p VRAC_PYTHON_VERSION=<".python-version"
"%VRAC_UV%" python install "%VRAC_PYTHON_VERSION%"
if errorlevel 1 exit /b 1
"%VRAC_UV%" sync --locked
if errorlevel 1 exit /b 1
echo Ambiente preparado. Execute scripts\check.cmd e scripts\run-demo.cmd.
exit /b 0
