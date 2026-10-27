@echo off
setlocal EnableExtensions DisableDelayedExpansion
for %%I in ("%~dp0..") do set "VRAC_PROJECT_ROOT=%%~fI"
cd /d "%VRAC_PROJECT_ROOT%"
if errorlevel 1 exit /b 1

set "VRAC_PYTHON=%VRAC_PROJECT_ROOT%\.venv\Scripts\python.exe"
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
set "UV_OFFLINE=1"
set "MPLCONFIGDIR=%VRAC_PROJECT_ROOT%\.cache\matplotlib"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"

if not exist "%VRAC_PYTHON%" (
    echo Ambiente ausente. Siga a instalacao descrita no README.md.
    exit /b 1
)
if exist "%VRAC_UV%" (
    "%VRAC_UV%" lock --check --offline
    if errorlevel 1 exit /b 1
)
"%VRAC_PYTHON%" -m ruff check .
if errorlevel 1 exit /b 1
"%VRAC_PYTHON%" -m ruff format --check .
if errorlevel 1 exit /b 1
"%VRAC_PYTHON%" -m pytest -m "not integration"
if errorlevel 1 exit /b 1
echo Verificacoes offline concluidas.
exit /b 0
