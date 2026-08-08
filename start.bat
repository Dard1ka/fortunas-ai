@echo off
REM Nyalakan backend + frontend Fortunas. Tambahkan argumen -Rebuild untuk build ulang web.
REM Contoh: start.bat            (pakai build yang ada)
REM         start.bat -Rebuild   (build ulang frontend React dulu)
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1" %*
pause
