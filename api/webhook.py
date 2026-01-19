"""
Webhook endpoint для Vercel serverless функции
Обрабатывает обновления от Telegram
"""
import asyncio
import json
import logging
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для отслеживания инициализации
_initialized = False
_init_lock = None

# Импортируем компоненты бота
try:
    from bot import dp, bot, init_bot_components
    
    async def ensure_initialized():
        """Обеспечивает инициализацию компонентов бота"""
        global _initialized, _init_lock
        if not _initialized:
            if _init_lock is None:
                _init_lock = asyncio.Lock()
            async with _init_lock:
                if not _initialized:
                    logger.info("Инициализация компонентов бота...")
                    await init_bot_components()
                    _initialized = True
                    logger.info("Компоненты бота инициализированы")
except Exception as e:
    logger.error(f"Ошибка при импорте бота: {e}", exc_info=True)
    dp = None
    bot = None
    init_bot_components = None

def handler(req):
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
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Bot components not initialized'})
            }
        
        # Обработка GET запроса (для проверки работоспособности)
        if req.method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'ok',
                    'message': 'Telegram bot webhook is running'
                })
            }
        
        # Обработка POST запроса от Telegram
        if req.method != 'POST':
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Получаем тело запроса
        body = req.body
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
        else:
            update_data = body  # Если уже dict
        
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

