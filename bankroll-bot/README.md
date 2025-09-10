# Bankroll Telegram Bot

**Stack:** Python 3.11+, aiogram 3.x, SQLAlchemy 2.x, PostgreSQL (prod) / SQLite (local)

Бот ведёт банкролл покерного игрока: кэш и MTT (включая PKO), поддерживает несколько параллельных сессий,
ребаи/аддоны (только «+»), завершение через единую кнопку **🏁 Cashout / Finish**, отчёты по периодам
(неделя/месяц/год/кастом), историю и базовые правки. Кнопки на английском с эмодзи, тексты — на русском.

---

## 🚀 Быстрый старт (локально)

1. Установите Python 3.11+.
2. Скачайте архив проекта и распакуйте его.
3. В терминале перейдите в папку проекта и создайте виртуальное окружение:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

4. Установите зависимости:

```bash
pip install -r requirements.txt
```

5. Создайте файл `.env` на основе примера:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
# Для локальной разработки используем SQLite-файл
DATABASE_URL=sqlite+aiosqlite:///./bankroll.db
# Для PostgreSQL (Railway/Cloud) используйте, например:
# DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME
TZ=Europe/Moscow
LOG_LEVEL=INFO
```

6. Запустите бота:

```bash
python -m app.main
```

При первом запуске таблицы создадутся автоматически. В Telegram напишите боту `/start`.

---

## ☁️ Деплой на Railway

1. Создайте новый проект на Railway и подключите ваш GitHub-репозиторий.
2. В Railway добавьте плагин **PostgreSQL** (Add Plugin → PostgreSQL). Скопируйте `DATABASE_URL`.
3. В переменные окружения Railway добавьте:
   - `TELEGRAM_BOT_TOKEN` — токен бота
   - `DATABASE_URL` — строка подключения Railway Postgres (формат: `postgresql+asyncpg://...`)
   - `TZ`, `LOG_LEVEL` (опционально)
4. Railway сам запустит сборку.

### Procfile
```
web: python -m app.main
```

> Если Railway просит порт, не требуется — это телеграм-бот, он сам делает исходящие запросы.

---

## 📁 Структура проекта

```
app/
  __init__.py
  main.py
  config.py
  db.py
  models.py
  enums.py
  keyboards.py
  states.py
  services.py
  utils.py
  handlers/
    __init__.py
    start.py
    menu.py
    sessions.py
    tournaments.py
    cash.py
    payouts.py
    history.py
    report.py
    settings.py
requirements.txt
Procfile
.env.example
README.md
```

---

## 🧭 Основные команды
- `/start` — регистрация/приветствие и главное меню
- `New Session` — мастер запуска сессии (Online/Offline → Cash/MTT → Game → Room/Place → Валюта → …)
- `+ Rebuy` / `+ Addon` — добавление только «+» (если активных турниров несколько, бот уточнит какой)
- `Cashout / Finish` — закрытие любой активной сессии (кэш/турнир, PKO со сплитом баунти по желанию)
- `History` — последние записи, базовые правки
- `Report` — отчёт за Week/Month/Year/Custom по выбранной валюте
- `Settings` — настройки, валюты по умолчанию для румов/мест, управление банкроллами
