# Настройка Telegram бота на Vercel

Этот бот теперь поддерживает работу через webhook на Vercel.

## ⚠️ Важные замечания

1. **База данных**: Vercel имеет файловую систему только для чтения, кроме директории `/tmp`. Код автоматически определяет Vercel и использует `/tmp/bot_database.db`. **⚠️ ВАЖНО**: Данные в `/tmp` временные (ephemeral storage) и теряются при каждом перезапуске функции. Для постоянного хранения данных рекомендуется использовать внешнюю базу данных.

2. **Переменные окружения**: Убедитесь, что все переменные окружения установлены в Vercel:
   - `BOT_TOKEN` - токен Telegram бота (обязательно)
   - `DEEPSEEK_API_KEY` - ключ API для DeepSeek AI (обязательно)
   - `ADMIN_IDS` - ID администраторов через запятую, например: `123456789,987654321` (обязательно)
   - `DATABASE_PATH` - путь к базе данных (опционально, по умолчанию: `/tmp/bot_database.db` на Vercel)

## Шаги настройки

### 1. Деплой на Vercel

```bash
# Установите Vercel CLI если еще не установлен
npm i -g vercel

# Войдите в Vercel
vercel login

# Деплой проекта
vercel
```

Или подключите репозиторий GitHub к Vercel через веб-интерфейс.

### 2. Установка переменных окружения в Vercel

1. Перейдите в настройки проекта на Vercel
2. Откройте раздел "Environment Variables"
3. Добавьте все необходимые переменные:
   - `BOT_TOKEN`
   - `DEEPSEEK_API_KEY`
   - `ADMIN_IDS`
   - `DATABASE_PATH` - по умолчанию используется `/tmp/bot_database.db` на Vercel (можно не устанавливать)

### 3. Получение URL вашего приложения

После деплоя вы получите URL вида: `https://your-app.vercel.app`

### 4. Установка webhook в Telegram

После успешного деплоя установите webhook, используя скрипт:

```bash
python setup_webhook.py https://your-app.vercel.app/api/webhook
```

Или вручную через Bot API:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook"
```

### 5. Проверка webhook

Проверьте, что webhook установлен правильно:

```bash
python setup_webhook.py info
```

Или через Bot API:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

### 6. Тестирование

Отправьте сообщение боту в Telegram. Если все настроено правильно, бот должен ответить.

## Устранение проблем

### Бот не отвечает

1. Проверьте логи в Vercel Dashboard → Deployments → Functions
2. Убедитесь, что webhook установлен правильно: `python setup_webhook.py info`
3. Проверьте, что все переменные окружения установлены
4. Проверьте, что URL webhook правильный и доступен

### Ошибки базы данных

На Vercel используется `/tmp` директория для SQLite. **⚠️ ВАЖНО**: 
- Данные в `/tmp` **временные** и теряются при каждом перезапуске функции
- Для продакшена с постоянным хранением данных используйте:
  - Внешнюю базу данных (PostgreSQL, MySQL)
  - Облачные сервисы (Supabase, PlanetScale, Railway)
  - Или храните резервные копии базы данных в облачном хранилище (S3, Cloudflare R2)

### Потеря данных в базе

Если данные в базе теряются после перезапуска - это нормально для `/tmp` директории. Решения:
1. Использовать внешнюю базу данных (рекомендуется для продакшена)
2. Реализовать автоматическое резервное копирование в облачное хранилище
3. Использовать базу данных в памяти с периодическим экспортом

### Ошибки при деплое

1. Убедитесь, что все зависимости указаны в `requirements.txt`
2. Проверьте, что версия Python совместима (указана в `runtime.txt`)
3. Проверьте логи деплоя в Vercel Dashboard

## Возврат к polling режиму

Если хотите вернуться к polling (например, для локальной разработки):

```bash
python setup_webhook.py delete
```

После этого запустите бота локально:

```bash
python bot.py
```

## Структура проекта

```
.
├── api/
│   └── webhook.py          # Vercel serverless функция для webhook
├── bot.py                   # Основной файл бота
├── vercel.json              # Конфигурация Vercel
├── setup_webhook.py         # Скрипт для установки webhook
├── requirements.txt         # Зависимости Python
└── VERCEL_SETUP.md          # Этот файл
```

## Дополнительные ресурсы

- [Vercel Python Documentation](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Telegram Bot API - Webhook](https://core.telegram.org/bots/api#setwebhook)
- [Aiogram Documentation](https://docs.aiogram.dev/)

