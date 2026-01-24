# Bot Dar Stars

Проект Telegram-бота с вебхуком на Vercel, утилитами для миграций и Next.js
страницами для помощи в настройке.

## Быстрый старт

- Установите зависимости: `pip install -r requirements.txt`
- Создайте `.env` на основе `docs/env.example.bot`
- Запуск бота: `python -m src.bot`
- Запуск через скрипт: `bash scripts/run.sh`

## Структура проекта

- `src/` — основной Python‑код бота и логики
- `api/` — Vercel serverless endpoints (webhook)
- `scripts/` — утилиты для миграций, диагностики, обслуживания
- `docs/` — документация и примеры `.env`
- `migrations/` — SQL‑миграции для базы
- `tests/` — тестовые скрипты
- `app/` — Next.js интерфейс
- `supabase/` — конфиги и миграции Supabase

## Документация

- Настройка Vercel: `docs/VERCEL_SETUP.md`, `docs/VERCEL_QUICKSTART.md`
- Миграции и база: `docs/HOW_TO_APPLY_MIGRATION.md`, `docs/README_POSTGRES.md`
- Supabase: `docs/SUPABASE_SETUP.md`, `docs/QUICK_START_SUPABASE.md`
- Next.js: `docs/README_NEXTJS.md`, `docs/QUICKSTART_NEXTJS.md`

