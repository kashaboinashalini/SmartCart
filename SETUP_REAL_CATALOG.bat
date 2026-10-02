@echo off
setlocal
cd /d "%~dp0"
echo.
echo ================================================
echo SmartCart - REAL PRODUCT PHOTO SETUP
echo ================================================
echo This downloads source-backed real catalog photographs.
echo It will stop instead of using generated/fake images.
echo.
python scripts\sync_real_catalog.py
if errorlevel 1 (
  echo.
  echo REAL CATALOG SETUP FAILED.
  echo Read the message above and fix the internet/source issue.
  pause
  exit /b 1
)
echo.
echo Real catalog ready. Starting SmartCart on port 5174...
python run.py
pause
