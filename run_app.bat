@echo off
echo Starting RuralHealth AI...
pip install -r backend/requirements.txt
start http://127.0.0.1:5000
python backend/app.py
pause
