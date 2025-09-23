#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required but not found. Install Docker to continue." >&2
    exit 1
fi

if ! command -v docker compose >/dev/null 2>&1; then
    echo "Docker Compose V2 is required (docker compose command)." >&2
    exit 1
fi

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Создан .env на основе .env.example. Обновите значения токенов перед запуском." >&2
    else
        echo "Файл .env не найден. Создайте его вручную перед запуском." >&2
        exit 1
    fi
fi

printf "Проверяем MongoDB...\n"
docker compose up -d mongo >/dev/null

# Wait for MongoDB to become available
until docker compose exec -T mongo mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
    printf "."
    sleep 2
done
printf "\nMongoDB готова.\n"

printf "Инициализируем базу...\n"
docker compose run --rm bot python init_db.py >/dev/null
printf "База подготовлена.\n"

printf "Собираем и запускаем контейнер бота...\n"
docker compose up -d --build bot >/dev/null
printf "Бот запущен. Логи доступны командой 'docker compose logs -f bot'.\n"
