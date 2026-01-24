# Быстрый старт Next.js + Supabase

## Шаг 1: Настройка переменных окружения

Создайте файл `.env.local` в корне проекта со следующим содержимым:

```env
NEXT_PUBLIC_SUPABASE_URL=https://ypxrrjyineyhdrhxdwrk.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=ваш-anon-key
```

**Где найти ключи:**
1. Откройте панель Supabase: https://supabase.com/dashboard
2. Выберите ваш проект
3. Перейдите в Settings > API
4. Скопируйте:
   - **URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon/public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Шаг 2: Запуск проекта

```bash
# Установка зависимостей (если еще не установлены)
npm install

# Запуск сервера разработки
npm run dev
```

Откройте браузер: http://localhost:3000

## Что дальше?

- Главная страница (`app/page.tsx`) показывает список пользователей из таблицы `telegram_users`
- API endpoint (`app/api/users/route.ts`) доступен по адресу `/api/users`
- Клиенты Supabase находятся в `lib/supabase.ts` (клиент) и `lib/supabase-server.ts` (сервер)

## Использование в коде

### Получение данных в компоненте:

```typescript
'use client'
import { supabase } from '@/lib/supabase'

const { data, error } = await supabase
  .from('telegram_users')
  .select('*')
```

### В API Route:

```typescript
import { supabaseServer } from '@/lib/supabase-server'

const { data, error } = await supabaseServer
  .from('telegram_users')
  .select('*')
```

## Структура проекта

```
.
├── app/              # Next.js App Router
│   ├── page.tsx     # Главная страница
│   ├── layout.tsx   # Корневой layout
│   └── api/         # API routes
├── lib/             # Утилиты
│   ├── supabase.ts         # Клиент для браузера
│   └── supabase-server.ts  # Клиент для сервера
└── package.json     # Зависимости
```

## Проблемы?

1. **Ошибка подключения к Supabase**: Проверьте переменные окружения в `.env.local`
2. **Ошибка компиляции**: Убедитесь, что все зависимости установлены (`npm install`)
3. **Пустой список пользователей**: Проверьте, что в базе данных есть записи в таблице `telegram_users`
