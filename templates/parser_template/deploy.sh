# deploy.sh
#!/bin/bash
echo "🚀 UPB Deployment Script"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Зависимости установлены"