@echo off
REM Run the WCB Super Advocate wizard from source for testing.
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m wcb_app.main wizard
