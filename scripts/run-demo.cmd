@echo off
setlocal EnableExtensions DisableDelayedExpansion
for %%I in ("%~dp0..") do set "VRAC_PROJECT_ROOT=%%~fI"
cd /d "%VRAC_PROJECT_ROOT%"
if errorlevel 1 exit /b 1

set "VRAC_PYTHON=%VRAC_PROJECT_ROOT%\.venv\Scripts\python.exe"
set "MPLCONFIGDIR=%VRAC_PROJECT_ROOT%\.cache\matplotlib"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
set "VRAC_ENVIRONMENT=development"
set "VRAC_DATA_MODE=synthetic"
set "VRAC_DEMO_SOURCE=supabase"
if "%~1"=="--memory" (
    set "VRAC_DEMO_SOURCE=memory"
) else if "%~1"=="--postgres" (
    set "VRAC_DEMO_SOURCE=postgres"
) else if "%~1"=="--supabase" (
    set "VRAC_DEMO_SOURCE=supabase"
) else if not "%~1"=="" (
    echo Argumento invalido. Use run-demo.cmd [--supabase ou --memory ou --postgres [porta]].
    exit /b 1
)
set "VRAC_PORT=8501"
if not "%~2"=="" set "VRAC_PORT=%~2"
if not "%~3"=="" (
    echo Argumento invalido. Use run-demo.cmd [--supabase ou --memory ou --postgres [porta]].
    exit /b 1
)
for /f "delims=0123456789" %%A in ("%VRAC_PORT%") do (
    echo Porta invalida. Use um numero entre 1024 e 65535.
    exit /b 1
)
if "%VRAC_PORT:~0,1%"=="0" (
    echo Porta invalida. Use um numero entre 1024 e 65535.
    exit /b 1
)
if %VRAC_PORT% LSS 1024 (
    echo Porta invalida. Use um numero entre 1024 e 65535.
    exit /b 1
)
if %VRAC_PORT% GTR 65535 (
    echo Porta invalida. Use um numero entre 1024 e 65535.
    exit /b 1
)

if not exist "%VRAC_PYTHON%" (
    echo Ambiente ausente. Siga a instalacao descrita no README.md.
    exit /b 1
)
echo POC LOCAL: escolha a origem na tela. Supabase exige conta e departamentos autorizados.
"%VRAC_PYTHON%" -m streamlit run app.py --server.address 127.0.0.1 --server.port %VRAC_PORT% --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
if errorlevel 1 exit /b 1
exit /b 0
