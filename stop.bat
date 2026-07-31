@echo off
REM Matikan backend + frontend Fortunas dengan aman.
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\stop.ps1" %*
pause
