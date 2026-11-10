@echo off
REM Startet den TikTok-KI-Generator (Windows). Einfach doppelklicken.
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo [FEHLER] Python wurde nicht gefunden.
  echo Bitte installiere Python von https://www.python.org/downloads/
  echo und setze beim Installieren das Haekchen "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Erster Start: richte Programmumgebung ein ^(dauert 1-3 Minuten^) ...
  %PY% -m venv .venv
  if errorlevel 1 ( echo [FEHLER] Konnte die Umgebung nicht anlegen. & pause & exit /b 1 )
)

set "VPY=.venv\Scripts\python.exe"
fc /b requirements.txt .venv\installed.txt >nul 2>&1
if errorlevel 1 (
  echo Installiere benoetigte Pakete ...
  "%VPY%" -m pip install --upgrade pip >nul
  "%VPY%" -m pip install -r requirements.txt
  if errorlevel 1 ( echo [FEHLER] Installation fehlgeschlagen - Internetverbindung pruefen. & pause & exit /b 1 )
  copy /y requirements.txt .venv\installed.txt >nul
)

"%VPY%" app.py
pause
