@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\launch_panel.py %*
  if errorlevel 1 pause
  exit /b
)
where python >nul 2>nul
if %errorlevel%==0 (
  python tools\launch_panel.py %*
  if errorlevel 1 pause
  exit /b
)
echo Falta Python 3.12 ou superior.
echo Instale em https://www.python.org/downloads/ e consulte docs\INSTALACAO.md.
pause
exit /b 1
