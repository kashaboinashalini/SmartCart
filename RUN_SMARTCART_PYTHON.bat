@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  call ".venv\Scripts\activate.bat"
  python -m pip install -r requirements.txt
) else (
  call ".venv\Scripts\activate.bat"
)
echo.
echo [1/2] Preparing the real product-photo catalog...
python scripts\sync_real_catalog.py
if errorlevel 1 (
  echo.
  echo Real catalog preparation failed. SmartCart will not start with fake images.
  pause
  exit /b 1
)
echo.
echo [2/2] Starting SmartCart on http://localhost:5174
python run.py
pause
