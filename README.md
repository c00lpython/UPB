# UPB - Universal Parser Builder

**No-code конструктор парсеров с собственным браузером и визуальным выделением данных**

## 🎯 Возможности (v1)

- 🕸️ **Встроенный браузер** (на базе QWebEngineView)
- 🖱️ **Умный Select**: как `Ctrl+Shift+C` в Chrome, но автоматически сохраняет XPath + URL + пример текста
- 📊 **Variables Manager**: таблица с типами (Static/Dynamic/Network)
- 🔧 **Сборка монолитного парсера** в один `.py` файл
- 📁 **Экспорт в Excel**
- 🧪 **Тестовый режим**: проверка парсера без выхода из UPB

## 🚀 Быстрый старт

### 1. Установка зависимостей

Скачайте `requirements.txt` (см. ниже) и выполните:

```bash
pip install -r requirements.txt
playwright install chromium   # для генерации парсеров