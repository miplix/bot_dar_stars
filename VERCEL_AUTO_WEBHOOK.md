# Автоматическая установка webhook на Vercel

Теперь webhook можно установить автоматически после деплоя!

## 🔧 Настройка

### 1. Добавьте переменную окружения (опционально)

В настройках проекта Vercel → Environment Variables добавьте:

- `WEBHOOK_BASE_URL` - базовый URL вашего приложения (если Vercel не может определить автоматически)
  - Например: `https://bot-dar-stars-nf4r.vercel.app`
  - **Обычно не нужно** - Vercel сам определит через `VERCEL_URL`

### 2. После деплоя вызовите endpoint установки webhook

Есть несколько способов:

#### Способ 1: Через браузер или curl (рекомендуется)

После успешного деплоя откройте в браузере или выполните curl:

```bash
curl https://bot-dar-stars-nf4r.vercel.app/api/setup-webhook
```

Или просто откройте в браузере:
```
https://bot-dar-stars-nf4r.vercel.app/api/setup-webhook
```

Вы должны увидеть:
```json
{
  "ok": true,
  "message": "Webhook successfully set",
  "url": "https://bot-dar-stars-nf4r.vercel.app/api/webhook",
  "description": "Webhook was set"
}
```

#### Способ 2: Автоматически через Vercel Deployment Webhook

1. Перейдите в Vercel Dashboard → Settings → Git → Deploy Hooks
2. Создайте новый Deploy Hook с URL:
   ```
   https://bot-dar-stars-nf4r.vercel.app/api/setup-webhook
   ```
3. Webhook будет вызываться автоматически после каждого деплоя

#### Способ 3: Через GitHub Actions (если используете GitHub)

Создайте файл `.github/workflows/auto-webhook.yml`:

```yaml
name: Auto Setup Webhook

on:
  workflow_dispatch:
  push:
    branches: [ main, master ]

jobs:
  setup-webhook:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Webhook
        run: |
          curl -X GET https://bot-dar-stars-nf4r.vercel.app/api/setup-webhook
```

## ✅ Проверка webhook

После установки проверьте webhook:

### Через браузер:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

### Через скрипт:
```bash
python setup_webhook.py info
```

Или:
```bash
python setup_webhook.py info YOUR_BOT_TOKEN
```

## 🔄 Что происходит при вызове `/api/setup-webhook`

1. Endpoint получает `BOT_TOKEN` из переменных окружения Vercel
2. Автоматически определяет URL приложения через `VERCEL_URL` (или использует `WEBHOOK_BASE_URL`)
3. Формирует полный URL webhook: `https://your-app.vercel.app/api/webhook`
4. Устанавливает webhook через Telegram Bot API
5. Возвращает результат (успех или ошибку)

## ⚠️ Важно

- `BOT_TOKEN` должен быть установлен в переменных окружения Vercel
- Вызывайте `/api/setup-webhook` после каждого деплоя (или настройте автоматический вызов)
- URL webhook формируется автоматически, но можно переопределить через `WEBHOOK_BASE_URL`

## 🛠️ Устранение проблем

### Webhook не устанавливается

1. Проверьте, что `BOT_TOKEN` установлен в Vercel:
   - Vercel Dashboard → Settings → Environment Variables

2. Проверьте логи в Vercel:
   - Deployments → View Function Logs

3. Проверьте URL приложения:
   - Убедитесь, что URL правильный и доступен

### Ошибка "BOT_TOKEN not found"

Установите `BOT_TOKEN` в переменных окружения Vercel:
- Settings → Environment Variables → Add New
- Name: `BOT_TOKEN`
- Value: ваш токен бота

## 📝 Структура

```
api/
├── webhook.py          # Обработка обновлений от Telegram
└── setup_webhook.py    # Автоматическая установка webhook
```

## 🎯 Рекомендация

**Лучший способ**: Настройте Vercel Deploy Hook, чтобы webhook устанавливался автоматически после каждого успешного деплоя!

1. Vercel Dashboard → Settings → Git → Deploy Hooks
2. Создайте hook с URL: `https://bot-dar-stars-nf4r.vercel.app/api/setup-webhook`
3. Готово! Webhook будет устанавливаться автоматически! 🚀

