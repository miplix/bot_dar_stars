# Инструкция по применению миграции

## Способ 1: Через Supabase Dashboard (РЕКОМЕНДУЕТСЯ) ⭐

1. Откройте [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **SQL Editor** (в боковом меню слева)
4. Скопируйте содержимое файла `migrations/001_create_tables.sql`
5. Вставьте SQL в редактор
6. Нажмите кнопку **Run** (или `Ctrl+Enter`)

✅ Готово! Таблицы будут созданы.

## Способ 2: Через Node.js скрипт

Если у вас есть `SUPABASE_DB_URL` в `.env.local`:

1. Получите Connection String из Supabase Dashboard:
   - Settings → Database → Connection String (URI)
2. Добавьте в `.env.local`:
   ```env
   SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   ```
3. Запустите:
   ```bash
   npm run migrate
   ```

## Способ 3: Через Python скрипт

Если у вас есть `SUPABASE_DB_URL` в основном `.env` файле:

1. Добавьте в `.env`:
   ```env
   SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   ```
2. Запустите:
   ```bash
   python scripts/apply_migration.py
   ```

## Что создаст миграция?

Миграция создаст следующие таблицы:

- ✅ `telegram_users` - пользователи бота
- ✅ `telegram_calculations` - расчеты даров
- ✅ `telegram_gifts_knowledge` - база знаний о дарах
- ✅ `telegram_ai_interactions` - история взаимодействий с ИИ
- ✅ `telegram_payments` - платежи
- ✅ `telegram_alphabet` - алфавит для анализа слов
- ✅ `telegram_promocodes` - промокоды
- ✅ `telegram_promocode_usage` - использования промокодов
- ✅ `telegram_ma_zhi_kun_positions` - позиции Ма-Жи-Кун
- ✅ `telegram_gift_fields` - поля (1-9)

А также создаст необходимые индексы для оптимизации запросов.

## Проверка после применения

После применения миграции вы можете проверить созданные таблицы:

1. В Supabase Dashboard → Table Editor
2. Или через Next.js приложение: http://localhost:3000 (если запущено)
