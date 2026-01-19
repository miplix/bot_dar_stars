"""
Скрипт для установки webhook в Telegram Bot API
Использование: 
  python setup_webhook.py <YOUR_WEBHOOK_URL>
  python setup_webhook.py <YOUR_WEBHOOK_URL> <BOT_TOKEN>
"""
import sys
import os
import requests

def get_bot_token():
    """Получение BOT_TOKEN из различных источников"""
    # Сначала проверяем аргументы командной строки
    if len(sys.argv) >= 3:
        return sys.argv[2]
    
    # Затем переменные окружения
    token = os.getenv('BOT_TOKEN')
    if token:
        return token
    
    # Пытаемся импортировать из config (если есть .env файл)
    try:
        from config import Config
        if Config.BOT_TOKEN:
            return Config.BOT_TOKEN
    except:
        pass
    
    return None

def set_webhook(webhook_url: str, bot_token: str = None):
    """Установка webhook для Telegram бота"""
    if not bot_token:
        bot_token = get_bot_token()
    
    if not bot_token:
        print("[ERROR] BOT_TOKEN не найден!")
        print("\nУстановите токен одним из способов:")
        print("  1. Переменная окружения: set BOT_TOKEN=your_token (Windows) или export BOT_TOKEN=your_token (Linux/Mac)")
        print("  2. Как второй аргумент: python setup_webhook.py <URL> <TOKEN>")
        print("  3. Создайте .env файл с BOT_TOKEN=your_token")
        return False
    
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    data = {
        "url": webhook_url
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print(f"[OK] Webhook успешно установлен!")
            print(f"   URL: {webhook_url}")
            print(f"   Описание: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"[ERROR] Ошибка при установке webhook:")
            print(f"   {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

def delete_webhook(bot_token: str = None):
    """Удаление webhook (возврат к polling)"""
    if not bot_token:
        bot_token = get_bot_token()
    
    if not bot_token:
        print("[ERROR] BOT_TOKEN не найден!")
        print("\nУстановите токен одним из способов:")
        print("  1. Переменная окружения: set BOT_TOKEN=your_token (Windows) или export BOT_TOKEN=your_token (Linux/Mac)")
        print("  2. Как второй аргумент: python setup_webhook.py delete <TOKEN>")
        return False
    
    api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        response = requests.post(api_url, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("[OK] Webhook успешно удален! Бот вернется к polling режиму.")
            return True
        else:
            print(f"[ERROR] Ошибка при удалении webhook:")
            print(f"   {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

def get_webhook_info(bot_token: str = None):
    """Получение информации о текущем webhook"""
    if not bot_token:
        bot_token = get_bot_token()
    
    if not bot_token:
        print("[ERROR] BOT_TOKEN не найден!")
        print("\nУстановите токен одним из способов:")
        print("  1. Переменная окружения: set BOT_TOKEN=your_token (Windows) или export BOT_TOKEN=your_token (Linux/Mac)")
        print("  2. Как второй аргумент: python setup_webhook.py info <TOKEN>")
        return
    
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(api_url, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            info = result.get("result", {})
            url = info.get("url", "")
            pending_count = info.get("pending_update_count", 0)
            last_error_date = info.get("last_error_date")
            last_error_message = info.get("last_error_message")
            
            print("📋 Информация о webhook:")
            if url:
                print(f"   URL: {url}")
                print(f"   Ожидающих обновлений: {pending_count}")
                if last_error_date:
                    print(f"   Последняя ошибка: {last_error_message or 'N/A'}")
            else:
                print("   [WARNING] Webhook не установлен (используется polling)")
        else:
            print(f"[ERROR] Ошибка при получении информации: {result.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python setup_webhook.py <webhook_url> [BOT_TOKEN]  - установить webhook")
        print("  python setup_webhook.py delete [BOT_TOKEN]         - удалить webhook")
        print("  python setup_webhook.py info [BOT_TOKEN]           - информация о webhook")
        print("\nПример:")
        print("  python setup_webhook.py https://your-app.vercel.app/api/webhook")
        print("  python setup_webhook.py https://your-app.vercel.app/api/webhook YOUR_BOT_TOKEN")
        print("\nИли установите BOT_TOKEN как переменную окружения:")
        print("  Windows: set BOT_TOKEN=your_token")
        print("  Linux/Mac: export BOT_TOKEN=your_token")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    bot_token = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('https://') else None
    
    if command == "delete":
        delete_webhook(bot_token)
    elif command == "info":
        get_webhook_info(bot_token)
    else:
        webhook_url = sys.argv[1]
        if not webhook_url.startswith("https://"):
            print("[ERROR] Webhook URL должен начинаться с https://")
            sys.exit(1)
        set_webhook(webhook_url, bot_token)

