# deploy.ps1
Write-Host "🚀 UPB Deployment Script" -ForegroundColor Cyan
python -m venv .venv
.\.venv\Scripts\Activate
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✅ Зависимости установлены" -ForegroundColor Green