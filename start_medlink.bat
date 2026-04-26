@echo off
echo ==============================================
echo       MedLink Server Startup Script
echo ==============================================
echo.
echo Starting MedLink to run in the background...
echo (This prevents the Python system crash issue)
echo.
powershell -Command "Start-Process -FilePath 'python.exe' -ArgumentList 'app.py' -WindowStyle Hidden"
echo Server started successfully!
echo.
echo You can now open your browser and navigate to:
echo http://127.0.0.1:5000/
echo.
echo To forcefully stop the server later, use stop_medlink.bat
echo.
pause
