@echo off
REM Double click this to present. It serves this folder and opens the deck.
REM Everything it needs is in the folder, so the wifi can be off.
cd /d "%~dp0"
start "deck server" /min cmd /c node serve.mjs
timeout /t 2 /nobreak >nul
start "" "http://localhost:8791/deck.html"
echo.
echo   Deck running at http://localhost:8791/deck.html
echo   Press F in the deck for fullscreen, Space or the clicker to go on,
echo   M to mute, Home to start over, 0 to 9 to jump to a stop.
echo.
echo   Close this window when the pitch is done.
echo.
pause
