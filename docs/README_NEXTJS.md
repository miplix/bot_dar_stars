# Next.js веб-интерфейс для Bot Dar Stars

Веб-приложение на Next.js для подключения к Supabase и отображения данных из базы данных Telegram бота.

## Установка

1. Установите зависимости:
```bash
npm install
```

2. Создайте файл `.env.local` на основе существующих переменных окружения:
```bash
# Используйте значения из вашего .env файла
NEXT_PUBLIC_SUPABASE_URL=https://ouodquakgyyeiyihmoxg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here  # Опционально, для серверных операций
```

3. Запустите сервер разработки:
```bash
npm run dev
```

Приложение будет доступно по адресу [http://localhost:3000](http://localhost:3000)

## Структура проекта

- `app/` - директория приложения Next.js (App Router)
  - `page.tsx` - главная страница с отображением пользователей
  - `layout.tsx` - корневой layout
  - `globals.css` - глобальные стили
  - `api/users/route.ts` - API endpoint для получения пользователей
- `lib/` - утилиты и библиотеки
  - `supabase.ts` - клиент Supabase для клиентской части
  - `supabase-server.ts` - клиент Supabase для серверной части
- `.env.local.example` - пример файла с переменными окружения

## Использование Supabase

### В клиентских компонентах (Client Components)

```typescript
'use client'

import { supabase } from '@/lib/supabase'
import { useEffect, useState } from 'react'

export default function MyComponent() {
  const [data, setData] = useState([])

  useEffect(() => {
    async function fetchData() {
      const { data, error } = await supabase
        .from('telegram_users')
        .select('*')
      
      if (!error) {
        setData(data)
      }
    }
    
    fetchData()
  }, [])

  return <div>{/* ваш компонент */}</div>
}
```

### В серверных компонентах и API Routes

```typescript
import { supabaseServer } from '@/lib/supabase-server'

export async function GET() {
  const { data, error } = await supabaseServer
    .from('telegram_users')
    .select('*')
  
  return Response.json({ data, error })
}
```

## Переменные окружения

### Обязательные

- `NEXT_PUBLIC_SUPABASE_URL` - URL вашего Supabase проекта
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Anon/Public ключ для клиентской части

### Опциональные

- `SUPABASE_SERVICE_ROLE_KEY` - Service Role ключ для серверных операций (имеет полные права доступа!)
- `SUPABASE_URL` - альтернативное имя для совместимости
- `SUPABASE_API_KEY` - альтернативное имя для service role key

**ВАЖНО:** Переменные с префиксом `NEXT_PUBLIC_` доступны в клиентском коде. Service Role Key никогда не должен быть доступен в клиентском коде!

## Команды

- `npm run dev` - запуск сервера разработки
- `npm run build` - сборка production версии
- `npm run start` - запуск production сервера
- `npm run lint` - проверка кода линтером

## Деплой

Проект готов к деплою на Vercel, Netlify или другой платформе, поддерживающей Next.js.

Не забудьте настроить переменные окружения на платформе деплоя!
