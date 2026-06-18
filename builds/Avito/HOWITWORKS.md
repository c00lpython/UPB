# HOW IT WORKS — UPB Parser

## 🧠 Архитектура

UPB Parser состоит из четырёх основных компонентов, которые работают вместе:

### 1. Parser Engine (`parser.py`)
- Запускает CloakBrowser (stealth Chromium)
- Эмулирует человеческое поведение (humanize=True)
- Извлекает данные со страниц

### 2. Shell Processor (`main.py`)
- Читает `script.txt`
- Парсит команды
- Выполняет блоки последовательно

### 3. Data Storage (`output_handler.py` + `db_handler.py`)
- Сохраняет данные в `results/user_{id}/{project}/`
- Хранит метаданные в SQLite (таблица `user_results`)

### 4. Telegram Bot (`bot.py` + `bot_main.py`)
- Регистрация/логин пользователей
- Показывает только файлы текущего пользователя
- Скачивание файлов

---

## 🔄 Полный цикл работы

### 1. Регистрация в боте

```
User → /register → Bot → Enter username → Enter password → Enter email → DB → ✅ Welcome!
```

### 2. Создание `script.txt`

```txt
start_session(project='AvitoTest', --user='alex')
open_url(url='https://avito.ru/...')
wait(seconds=2)
scroll_to_bottom(wait=1000, max_attempts=10)
parse_data(var='[data-marker="item-title"]')
save_data(data='results', format='excel', path='./avito')
end_session()
```

### 3. Запуск парсера

```
User → python main.py → parser.py → DB (user_id) → CloakBrowser → данные → output_handler → results/user_{id}/ → DB (user_results) → Telegram уведомление
```

### 4. Просмотр результатов в боте

```
User → /results → Bot → DB (user_results) → Список файлов → User → Выбор файла → Bot → Скачивание
```

---

## 🥷 CloakBrowser — как это работает

CloakBrowser — патченный Chromium с **58 C++ патчами**:

| Уровень | Что изменяет |
|---------|--------------|
| Canvas | Шум в пикселях |
| WebGL | Vendor / Renderer |
| Audio | Аудио-отпечаток |
| GPU | Информация о видеокарте |
| Screen | Размеры экрана |
| WebRTC | IP в ICE-кандидатах |
| Automation | `navigator.webdriver`, CDP-следы |

### `humanize=True` — эмуляция человека

| Действие | Без humanize | С humanize=True |
|----------|-------------|-----------------|
| Клик | Мгновенный | Кривая Безье + задержка |
| Ввод | Мгновенный | Случайная скорость |
| Скролл | Мгновенный | Ускорение → замедление |
| Паузы | Нет | 0.3-1.5 сек |

### Профиль браузера (`profile/`)

Хранит:
- Cookies
- Local Storage
- History
- Service Workers
- IndexedDB

→ Браузер выглядит как **реальный пользователь**, а не чистый экземпляр.

---

## 📊 Хранение данных

### Структура папок

```
results/
├── user_1/
│   └── AvitoTest/
│       ├── avito_iphones_20260617_171157.xlsx
│       ├── avito_iphones_20260617_171157.csv
│       ├── avito_iphones_20260617_171157.json
│       └── report_20260617_171157.html
└── user_2/
    └── GoogleTest/
        └── ...
```

### Таблица `user_results` (SQLite)

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | FOREIGN KEY → users |
| `project_name` | TEXT | Название проекта |
| `file_path` | TEXT | Полный путь к файлу |
| `file_name` | TEXT | Имя файла |
| `records` | INTEGER | Количество записей |
| `created_at` | TIMESTAMP | Дата создания |

---

## 🔧 Команды `script.txt`

| Команда | Описание | Пример |
|---------|----------|--------|
| `start_session` | Запуск браузера | `start_session(project='Test', --user='alex')` |
| `open_url` | Открыть URL | `open_url(url='https://avito.ru')` |
| `wait` | Задержка | `wait(seconds=3)` |
| `scroll` | Скролл | `scroll(direction='down', amount=500)` |
| `scroll_to_bottom` | Скролл до конца | `scroll_to_bottom(wait=1000, max_attempts=10)` |
| `click` | Клик | `click(selector='button', type='css')` |
| `type_text` | Ввод текста | `type_text(selector='input', text='Hello')` |
| `parse_data` | Извлечение данных | `parse_data(var='.item', extract='text')` |
| `screenshot` | Скриншот | `screenshot(filename='page.png')` |
| `save_data` | Сохранение | `save_data(path='./output')` |
| `send_telegram` | Уведомление | `send_telegram(msg='Done!')` |
| `end_session` | Завершение | `end_session(close=True)` |

---

## 🐛 Обработка ошибок

| Ситуация | Решение |
|----------|---------|
| Пользователь не найден | Данные сохраняются в общую папку `results/{project}/` |
| Нет интернета | CloakBrowser скачивает бинарник при первом запуске |
| Avito бан | Используется профиль браузера + ротация селекторов |
| Telegram таймаут | Увеличены таймауты до 60 секунд |

---

## 🚀 Деплой

### Локально

```bash
python main.py      # парсер
python bot_main.py  # бот
```

### VPS (Ubuntu)

```bash
sudo apt update
sudo apt install python3-pip python3-venv
git clone https://github.com/your/upb-parser.git
cd upb-parser
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запуск через screen
screen -S parser
python main.py
Ctrl+A D

screen -S bot
python bot_main.py
Ctrl+A D
```

---

## 📄 Лицензия

**Закрытая лицензия (Proprietary)**. Все права защищены.
Копирование, модификация, распространение и коммерческое использование без письменного разрешения правообладателя запрещены.