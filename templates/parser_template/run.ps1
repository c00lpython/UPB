param(
    [switch]$Bot
)
if ($Bot) {
    Write-Host "🚀 Запуск Telegram-бота..." -ForegroundColor Cyan
    python bot_main.py
} else {
    Write-Host "🚀 Запуск парсера..." -ForegroundColor Cyan
    python main.py
}