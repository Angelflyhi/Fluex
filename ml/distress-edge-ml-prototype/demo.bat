@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [2/3] Training model (open datasets)...
python -m src.train
if errorlevel 1 goto :fail

echo [3/3] Running local demo on bundled dataset...
python -m src.local_demo
if errorlevel 1 goto :fail

echo.
echo Demo completed. Check:
echo   artifacts\demo_results.md
echo   artifacts\demo_results.csv
echo   artifacts\demo_results.json
exit /b 0

:fail
echo Demo failed. See logs above.
exit /b 1
