@echo off
chcp 65001 >nul
echo.
echo ══════════════════════════════════════════════════
echo   KI-PRAXIS — Video Producer
echo ══════════════════════════════════════════════════
echo.

:: API Key setzen (hier deinen Key eintragen)
set ELEVENLABS_API_KEY=sk_399f2501d72e20f56c09dbeb2c7e070cc0ce90cbd5bfe515

echo Starte Video-Produktion...
echo Skript: strategy\skript-video-01.md
echo.

python produce.py strategy/skript-video-01.md

echo.
if exist "output\skript-video-01*.mp4" (
    echo ══════════════════════════════════════════════════
    echo   FERTIG! Video liegt in: output\
    echo   Doppelklick auf die MP4-Datei zum Ansehen
    echo ══════════════════════════════════════════════════
) else (
    echo Fuer nur Voiceover-Test:
    echo   python produce.py strategy/skript-video-01.md --only-voiceover
)
pause
