@echo off
setlocal

cd /d "%~dp0"
set "PORT=8501"
set "URL=http://localhost:%PORT%"

where python >nul 2>&1
if errorlevel 1 (
    echo Python tidak ditemukan. Install Python terlebih dahulu.
    pause
    exit /b 1
)

echo Menjalankan CM Broadcast Generator...

netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo Aplikasi sudah berjalan. Membuka browser...
    start "" "%URL%"
    exit /b 0
)

start "" powershell.exe -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process '%URL%'"
python -m streamlit run streamlit_app.py --server.headless true --server.port %PORT%

endlocal