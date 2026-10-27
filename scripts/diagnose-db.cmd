@echo off
setlocal EnableExtensions DisableDelayedExpansion
for %%I in ("%~dp0..") do set "VRAC_PROJECT_ROOT=%%~fI"
cd /d "%VRAC_PROJECT_ROOT%"
if errorlevel 1 exit /b 1
if not exist ".venv\Scripts\python.exe" (
    echo Ambiente ausente. Siga o README.md.
    exit /b 1
)
".venv\Scripts\python.exe" -m vrac.db diagnose %*
exit /b %ERRORLEVEL%
