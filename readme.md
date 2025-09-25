# Telegram Festive Bot

Простой Telegram-бот, который по команде или кнопке «Старт» поздравляет пользователя с праздником и использует MongoDB для хранения справочных данных о брендах.

## Возможности
- `/start` или нажатие кнопки «Старт» в клавиатуре отправляет праздничное поздравление.

## Файловая структура
```
app/
├── config.py           # Загрузка настроек приложения и параметров MongoDB
├── database/           # Работа с MongoDB и инициализация коллекций
│   ├── __init__.py
│   └── management.py
├── handlers/           # Обработчики команд и сообщений
│   ├── __init__.py
│   └── start.py
└── keyboards/          # Описание клавиатур
    ├── __init__.py
    └── main.py
bot.py                  # Точка входа и запуск бота
scripts/
├── __init__.py
└── init_db.py          # Скрипт подготовки базы данных
```

## Переменные окружения
Создайте файл `.env` по примеру `.env.example` и заполните его:

```
BOT_TOKEN=ваш_токен_бота
MONGO_URI=mongodb://root:root@mongo:27017/tg_cosmetics?authSource=admin
MONGO_DB_NAME=tg_cosmetics
INITIAL_ADMIN_ID=123456789
```

`INITIAL_ADMIN_ID` используется для автоматического добавления администратора в коллекцию `admins` при инициализации базы данных.

## Подготовка базы данных
Перед запуском рекомендуется инициализировать MongoDB:

```bash
python -m scripts.init_db
```

## Локальный запуск
1. Установите Python 3.11+.
2. Создайте и заполните `.env`.
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Подготовьте базу данных (см. выше).
5. Запустите бота:
   ```bash
   python bot.py
   ```

## Запуск через Docker
Используйте `docker compose` для запуска MongoDB и бота:

```bash
docker compose up -d --build mongo bot
```

После запуска можно подготовить базу данных в контейнере бота:

```bash
docker compose run --rm bot python -m scripts.init_db
```

Логи бота можно посмотреть командой:

```bash
docker compose logs -f bot
```

Для удобства доступен скрипт 
```bash 
./deploy.sh
```
который запускает MongoDB, инициализирует базу и поднимает контейнер с ботом автоматически.
