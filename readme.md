# Telegram Game Bot

Простой бот-игра для Telegram на Python с использованием [python-telegram-bot](https://python-telegram-bot.org/) и [MongoDB](https://www.mongodb.com/).

## Возможности
- `/start` — регистрация игрока и показ меню действий
- Административные команды `/game_start`, `/game_stop`, `/game_reset`
- Автоматическая инициализация коллекций MongoDB и кнопок

## Переменные окружения
Создайте файл `.env` со следующими параметрами (можно использовать `.env.example` как шаблон):

```
BOT_TOKEN=telegram-bot-token
MONGO_URI=mongodb://root:root@mongo:27017/tg_cosmetics?authSource=admin
MONGO_DB_NAME=tg_cosmetics
INITIAL_ADMIN_ID=123456789
ADMIN_IDS=987654321,123456789
```

- `BOT_TOKEN` — токен Telegram-бота
- `MONGO_URI` — строка подключения к MongoDB
- `MONGO_DB_NAME` — имя базы данных (по умолчанию `tg_cosmetics`)
- `INITIAL_ADMIN_ID` — основной администратор, создается в документе игры при инициализации
- `ADMIN_IDS` — дополнительные администраторы через запятую

## Локальный запуск
1. Установите Python 3.11+ и MongoDB.
2. Создайте и заполните `.env`.
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Инициализируйте базу (создаст документ игры и кнопки):
   ```bash
   python init_db.py --reset
   ```
5. Запустите бота:
   ```bash
   python bot.py
   ```

## Запуск через Docker
Для быстрого разворачивания используйте скрипт `deploy.sh`, который подготовит `.env`, поднимет MongoDB, заполнит базу и соберёт контейнер бота.

```bash
./deploy.sh
```

Скрипт предполагает наличие Docker и Docker Compose v2 (`docker compose`). После выполнения логи бота доступны командой:

```bash
docker compose logs -f bot
```

При необходимости повторной инициализации базы данных выполните:

```bash
docker compose run --rm bot python init_db.py --reset
```

Затем перезапустите бота:

```bash
docker compose up -d --build bot
```
