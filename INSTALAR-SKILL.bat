@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 INSTALAR-SKILL.py %*
  if errorlevel 1 pause
  exit /b
)
where python >nul 2>nul
if %errorlevel%==0 (
  python INSTALAR-SKILL.py %*
  if errorlevel 1 pause
  exit /b
)
echo Instale Python 3.12 ou superior: https://www.python.org/downloads/
pause
exit /b 1
