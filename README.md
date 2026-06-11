# UPB - Universal Parsers Builder

**No-Code конструктор парсеров с кастомным браузером и визуальным редактором**

![UPB Screenshot](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-latest-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Возможности

### 🌐 Browser
- 📌 **Режим SELECT** — один клик для изъятия переменных (XPath + URL + пример текста)
- 🔒 **Отдельные профили** для каждого проекта — куки и логины изолированы
- 📑 **Много вкладок** с сохранением в память проекта
- 🛠️ **DevTools** справа (Chrome DevTools) — можно скрыть
- 🔍 **View in Browser** — подсветка элементов на странице из VM таблицы

### 📁 Project Manager
- ⚡ **Быстрое создание** проектов
- 🔄 **Авто-открытие** последнего проекта при запуске
- 💾 **Сохранение сессий**: вкладки, логины, куки, переменные
- 👁️ **Preview переменных** и статистика проекта

### 📊 VM (Variable Manager)
- 📋 **Таблица с редактированием**: Name, XPath/CSS, Type, URL, Sample Text
- 🔍 **Поиск и фильтрация** по всем колонкам
- 🖱️ **Контекстное меню**: View in Browser, Copy, Delete
- 📤 **Импорт из Select** режима браузера
- 💾 **Экспорт** в Excel (variables.xlsx)

### 🧩 SE (Script Editor)
- 🎨 **Визуальный нод-редактор** — drag & drop блоков
- 🔌 **Соединения** между блоками с разными типами портов
- ✏️ **Property Editor** с IntelliSense для переменных
- 🔀 **IfBlock** с true/false ветками
- ⌨️ **IntelliSense** — автодополнение переменных и ключей доступа (Name, XPath, URL, Sample)
- 🏗️ **Компилятор** в script.txt

### 🚀 Build & Export (в разработке)
- ⚙️ Генерация parser config (config.conf)
- 📦 Упаковка проекта для UPBParser

## 📦 Установка

```bash
# Клонируем репозиторий
git clone https://github.com/LightWorker228/UPB.git
cd UPB

# Создаём виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Устанавливаем зависимости
pip install -r requirements.txt

# Запускаем
python main.py