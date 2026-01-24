"""
API endpoint для автоматической установки webhook в Vercel
Будет вызываться после деплоя для установки webhook
"""
import os
import json
import logging
import requests
from http.server import BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _handler_function(req):
    """
    Обработчик для установки webhook
    Можно вызвать вручную или через Vercel deployment webhook
    """
    try:
        # Получаем метод запроса
        method = getattr(req, 'method', None) or req.get('method', 'GET')
        
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
            # Пытаемся получить из заголовков запроса
            headers = getattr(req, 'headers', None) or req.get('headers', {})
            if isinstance(headers, dict) and 'host' in headers:
                vercel_url = f"https://{headers['host']}"
            elif hasattr(req, 'headers') and hasattr(req.headers, 'get'):
                host = req.headers.get('host')
                if host:
                    vercel_url = f"https://{host}"
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

# Определяем класс handler для Vercel (он ожидает класс, наследующий BaseHTTPRequestHandler)
class handler(BaseHTTPRequestHandler):
    """Класс handler для Vercel Python runtime"""
    
    def do_GET(self):
        """Обработка GET запроса"""
        result = _handler_function({
            'method': 'GET',
            'body': None,
            'headers': dict(self.headers)
        })
        self.send_response(result['statusCode'])
        for key, value in result['headers'].items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(result['body'].encode('utf-8'))
    
    def do_POST(self):
        """Обработка POST запроса"""
        # Читаем тело запроса
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        # Создаем объект запроса
        req_obj = {
            'method': 'POST',
            'body': body.decode('utf-8') if body else None,
            'headers': dict(self.headers)
        }
        
        result = _handler_function(req_obj)
        self.send_response(result['statusCode'])
        for key, value in result['headers'].items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(result['body'].encode('utf-8'))
    
    def log_message(self, format, *args):
        """Переопределяем логирование"""
        logger.info(f"{self.address_string()} - {format % args}")

