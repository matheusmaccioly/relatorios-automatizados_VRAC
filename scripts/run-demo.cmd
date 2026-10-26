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

if not exist "%VRAC_PYTHON%" (
    echo Ambiente ausente. Siga a instalacao descrita no README.md.
    exit /b 1
)
echo DEMONSTRACAO: somente dados sinteticos em acesso local.
"%VRAC_PYTHON%" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
if errorlevel 1 exit /b 1
exit /b 0
