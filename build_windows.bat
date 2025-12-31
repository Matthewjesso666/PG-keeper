@echo off
REM Build a single EXE for WCB Super Advocate using PyInstaller.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pyinstaller --noconfirm --onefile --name WCB_Super_Advocate ^
  --add-data "templates;templates" ^
  --add-data "sample_cases;sample_cases" ^
  wcb_app/main.py

echo Build complete. You can run dist\WCB_Super_Advocate.exe by double-clicking it.
