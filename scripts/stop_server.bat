@echo off
echo Stopping any running Flask Python servers...
taskkill /F /IM python.exe >nul 2>&1
echo Done! Flask server has been stopped.
pause
