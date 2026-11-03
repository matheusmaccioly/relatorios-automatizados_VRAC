@echo off
setlocal EnableExtensions DisableDelayedExpansion
for %%I in ("%~dp0..") do set "VRAC_PROJECT_ROOT=%%~fI"
cd /d "%VRAC_PROJECT_ROOT%"
if errorlevel 1 goto error

set "VRAC_PYTHON=%VRAC_PROJECT_ROOT%\.venv\Scripts\python.exe"
set "MPLCONFIGDIR=%VRAC_PROJECT_ROOT%\.cache\matplotlib"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
set "VRAC_ENVIRONMENT=development"
set "VRAC_DATA_MODE=synthetic"
set "VRAC_DEMO_SOURCE=postgres"

if not exist "%VRAC_PYTHON%" (
    echo Ambiente Python ausente. Siga a instalacao descrita no README.md.
    goto error
)
echo DEMONSTRACAO LOCAL: dados sinteticos na porta 8516.
echo Mantenha esta janela aberta enquanto usa a aplicacao.
"%VRAC_PYTHON%" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8516 --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
if errorlevel 1 goto error
exit /b 0

:error
echo Nao foi possivel iniciar a demonstracao. Confira a mensagem acima.
pause
exit /b 1
