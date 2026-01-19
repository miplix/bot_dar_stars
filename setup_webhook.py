"""
Скрипт для установки webhook в Telegram Bot API
Использование: python setup_webhook.py <YOUR_WEBHOOK_URL>
"""
import sys
import os
import requests
from config import Config

def set_webhook(webhook_url: str):
    """Установка webhook для Telegram бота"""
    bot_token = Config.BOT_TOKEN
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        return False
    
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    data = {
        "url": webhook_url
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ Webhook успешно установлен!")
            print(f"   URL: {webhook_url}")
            print(f"   Описание: {result.get('description', 'N/A')}")
            return True
        else:
            print(f"❌ Ошибка при установке webhook:")
            print(f"   {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

def delete_webhook():
    """Удаление webhook (возврат к polling)"""
    bot_token = Config.BOT_TOKEN
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        return False
    
    api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    
    try:
        response = requests.post(api_url, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            print("✅ Webhook успешно удален! Бот вернется к polling режиму.")
            return True
        else:
            print(f"❌ Ошибка при удалении webhook:")
            print(f"   {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

def get_webhook_info():
    """Получение информации о текущем webhook"""
    bot_token = Config.BOT_TOKEN
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
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
                print("   ❌ Webhook не установлен (используется polling)")
        else:
            print(f"❌ Ошибка при получении информации: {result.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python setup_webhook.py <webhook_url>  - установить webhook")
        print("  python setup_webhook.py delete         - удалить webhook")
        print("  python setup_webhook.py info           - информация о webhook")
        print("\nПример:")
        print("  python setup_webhook.py https://your-app.vercel.app/api/webhook")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "delete":
        delete_webhook()
    elif command == "info":
        get_webhook_info()
    else:
        webhook_url = sys.argv[1]
        if not webhook_url.startswith("https://"):
            print("❌ Webhook URL должен начинаться с https://")
            sys.exit(1)
        set_webhook(webhook_url)

