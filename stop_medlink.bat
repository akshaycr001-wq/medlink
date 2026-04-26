@echo off
echo ==============================================
echo       MedLink Server Shutdown Script
echo ==============================================
echo.
echo Stopping all running Python instances of the MedLink server...
taskkill /F /IM python.exe /T
echo.
echo MedLink Server has been completely stopped!
echo.
pause
