"""
Webhook endpoint для Vercel serverless функции
Обрабатывает обновления от Telegram
"""
import asyncio
import json
import logging
import sys
import os
import types
from http.server import BaseHTTPRequestHandler

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные для отслеживания инициализации
_initialized = False
_init_lock = None
dp = None
bot = None
init_bot_components = None
_import_error = None

# Определяем ensure_initialized как обычную async функцию
async def ensure_initialized():
    """Обеспечивает инициализацию компонентов бота"""
    global _initialized, _init_lock, dp, bot, init_bot_components
    if not _initialized and dp and bot and init_bot_components:
        if _init_lock is None:
            _init_lock = asyncio.Lock()
        async with _init_lock:
            if not _initialized:
                logger.info("Инициализация компонентов бота...")
                try:
                    await init_bot_components()
                    _initialized = True
                    logger.info("Компоненты бота инициализированы")
                except Exception as init_error:
                    logger.error(f"Ошибка при инициализации: {init_error}", exc_info=True)
                    raise

# Импортируем компоненты бота
try:
    logger.info("Импорт компонентов бота...")
    from bot import dp, bot, init_bot_components
    logger.info("Компоненты бота успешно импортированы")
except Exception as e:
    _import_error = str(e)
    logger.error(f"Ошибка при импорте бота: {e}", exc_info=True)
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    dp = None
    bot = None
    init_bot_components = None

# Определяем функцию handler
def _handler_function(req):
    """
    Обработчик для Vercel serverless функции
    
    Args:
        req: объект запроса от Vercel
        
    Returns:
        dict: ответ в формате Vercel
    """
    try:
        # Проверяем наличие компонентов
        if dp is None or bot is None:
            error_msg = 'Bot components not initialized'
            if _import_error:
                error_msg += f': {_import_error}'
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'ok': False,
                    'error': error_msg,
                    'details': 'Make sure BOT_TOKEN, DEEPSEEK_API_KEY, and ADMIN_IDS are set in Vercel environment variables',
                    'import_error': _import_error if _import_error else None
                })
            }
        
        # Обработка GET запроса (для проверки работоспособности)
        method = getattr(req, 'method', None) or (req.get('method', 'GET') if isinstance(req, dict) else 'GET')
        if method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'ok',
                    'message': 'Telegram bot webhook is running'
                })
            }
        
        # Обработка POST запроса от Telegram
        if method != 'POST':
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Получаем тело запроса
        body = getattr(req, 'body', None) or (req.get('body', None) if isinstance(req, dict) else None)
        if body is None:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Empty request body'})
            }
        
        if isinstance(body, str):
            update_data = json.loads(body)
        elif isinstance(body, bytes):
            update_data = json.loads(body.decode('utf-8'))
        elif isinstance(body, dict):
            update_data = body  # Если уже dict
        else:
            logger.error(f"Unknown body type: {type(body)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid request body format'})
            }
        
        logger.info(f"Получено обновление: {update_data.get('update_id')}")
        
        # Создаем новый event loop для асинхронной обработки
        # В Vercel каждая функция работает изолированно
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Обрабатываем обновление
        try:
            # Инициализируем компоненты если нужно
            loop.run_until_complete(ensure_initialized())
            
            # Обрабатываем обновление
            loop.run_until_complete(dp.feed_update(bot, update_data))
            
            logger.info(f"Обновление {update_data.get('update_id')} обработано")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке обновления: {e}", exc_info=True)
            raise
        
        # Отправляем успешный ответ
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
        
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}", exc_info=True)
        
        # Отправляем ошибку
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': False, 'error': str(e)[:200]})
        }

# Определяем класс handler для Vercel (он ожидает класс, наследующий BaseHTTPRequestHandler)
class handler(BaseHTTPRequestHandler):
    """Класс handler для Vercel Python runtime"""
    
    def do_GET(self):
        """Обработка GET запроса"""
        result = _handler_function({
            'method': 'GET',
            'body': None
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
