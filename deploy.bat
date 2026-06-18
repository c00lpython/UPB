@echo off
echo 🚀 UPB Deployment
python -m venv .venv
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Done!
pause