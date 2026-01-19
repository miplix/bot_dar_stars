"""
API endpoint для автоматической установки webhook в Vercel
Будет вызываться после деплоя для установки webhook
"""
import os
import json
import logging
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(req):
    """
    Обработчик для установки webhook
    Можно вызвать вручную или через Vercel deployment webhook
    """
    try:
        # Получаем BOT_TOKEN из переменных окружения
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'ok': False,
                    'error': 'BOT_TOKEN not found in environment variables'
                })
            }
        
        # Получаем URL webhook из переменных окружения или определяем автоматически
        # Vercel предоставляет VERCEL_URL в переменных окружения
        vercel_url = os.getenv('VERCEL_URL')
        if not vercel_url:
            # Если VERCEL_URL нет, пытаемся получить из запроса
            if hasattr(req, 'headers') and 'host' in req.headers:
                vercel_url = f"https://{req.headers['host']}"
            else:
                # Используем фиксированный URL из запроса или из переменной
                vercel_url = os.getenv('WEBHOOK_BASE_URL', 'https://bot-dar-stars-nf4r.vercel.app')
        
        # Убираем http:// или https:// если есть
        vercel_url = vercel_url.replace('http://', '').replace('https://', '')
        webhook_url = f"https://{vercel_url}/api/webhook"
        
        logger.info(f"Setting webhook to: {webhook_url}")
        
        # Устанавливаем webhook через Telegram Bot API
        api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        
        data = {
            "url": webhook_url
        }
        
        try:
            response = requests.post(api_url, json=data, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Webhook successfully set: {webhook_url}")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'ok': True,
                        'message': 'Webhook successfully set',
                        'url': webhook_url,
                        'description': result.get('description', 'N/A')
                    })
                }
            else:
                error_msg = result.get('description', 'Unknown error')
                logger.error(f"Failed to set webhook: {error_msg}")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'ok': False,
                        'error': error_msg
                    })
                }
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'ok': False,
                    'error': str(e)
                })
            }
        
    except Exception as e:
        logger.error(f"Error in handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'ok': False,
                'error': str(e)
            })
        }

