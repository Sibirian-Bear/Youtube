@echo off
chcp 65001 >nul
echo.
echo ══════════════════════════════════════════════════
echo   KI-PRAXIS — Windows Setup
echo ══════════════════════════════════════════════════
echo.

:: Python prüfen
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    echo Bitte installiere Python von: https://python.org/downloads
    echo Wichtig: Haken setzen bei "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python gefunden
python --version

:: pip upgrade
python -m pip install --upgrade pip --quiet

:: Dependencies installieren
echo.
echo Installiere Abhängigkeiten...
pip install requests colorama Pillow moviepy playwright --quiet
if errorlevel 1 (
    echo [FEHLER] Installation fehlgeschlagen
    pause
    exit /b 1
)

:: Playwright Browser installieren
echo Installiere Playwright Browser (Chromium)...
playwright install chromium --quiet 2>nul
echo [OK] Setup abgeschlossen

:: FFmpeg prüfen
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [HINWEIS] FFmpeg fehlt - wird fuer das fertige Video benoetigt
    echo Download: https://ffmpeg.org/download.html (Windows builds)
    echo Oder per winget: winget install ffmpeg
    echo.
)

echo.
echo ══════════════════════════════════════════════════
echo   Setup fertig! Naechster Schritt:
echo   Fuehre run_video.bat aus
echo ══════════════════════════════════════════════════
pause
