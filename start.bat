@echo off
CALL venv\Scripts\activate
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0
pause